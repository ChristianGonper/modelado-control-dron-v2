import json
import subprocess
import sys
import yaml
import numpy as np
import pandas as pd
import torch

from simulador_quad.control.classic import ClassicCascadeController
from simulador_quad.control.neural import NeuralPositionController
from simulador_quad.core.contracts import VehicleState, TrajectoryReference
from simulador_quad.core.frames import get_level_quaternion
from simulador_quad.ml.dataset import PositionGainDataset, SequentialPositionGainDataset
from simulador_quad.ml.models import MLPControllerNet
from simulador_quad.scenarios.loader import instantiate_scenario


def _state_ref():
    state = VehicleState(
        position_W_m=np.array([0.1, -0.2, 1.9]),
        velocity_W_m_s=np.array([0.0, 0.1, -0.1]),
        orientation_WB=get_level_quaternion(0.0),
        angular_velocity_B_rad_s=np.array([0.01, -0.02, 0.03]),
        time_s=0.0,
    )
    ref = TrajectoryReference(
        position_W_m=np.array([0.0, 0.0, 2.0]),
        velocity_W_m_s=np.zeros(3),
        acceleration_W_m_s2=np.zeros(3),
        yaw_rad=0.0,
    )
    return state, ref


def test_classic_refactor_preserves_compute_control():
    controller = ClassicCascadeController(1.0, 9.81, np.diag([0.05, 0.05, 0.1]))
    state, ref = _state_ref()

    original = controller.compute_control(0.0, state, ref)
    refactored = controller.compute_control_with_position_gains(state, ref, controller.Kp_pos, controller.Kd_pos)

    assert np.isclose(original.collective_thrust_N, refactored.collective_thrust_N)
    assert np.allclose(original.body_moments_Nm, refactored.body_moments_Nm)


def _write_gain_dataset(tmp_path):
    ds = tmp_path / "gain_ds"
    ep = ds / "ep_0"
    sc_dir = ds / "scenarios"
    ep.mkdir(parents=True)
    sc_dir.mkdir()

    scenario = {
        "controller": {
            "type": "classic",
            "Kp_pos": [4.0, 2.0, 10.0],
            "Kd_pos": [1.0, 2.0, 4.0],
        }
    }
    with open(sc_dir / "scenario.yaml", "w") as f:
        yaml.dump(scenario, f)

    manifest = pd.DataFrame([
        {"split": "train", "result_dir": "ep_0", "scenario_path": "scenarios/scenario.yaml"},
        {"split": "val", "result_dir": "ep_0", "scenario_path": "scenarios/scenario.yaml"},
    ])
    manifest.to_csv(ds / "manifest.csv", index=False)

    telemetry = []
    for t in np.linspace(0.0, 1.0, 12):
        telemetry.append({
            "state": {
                "position_W_m": [0.0, 0.0, 2.0],
                "velocity_W_m_s": [0.0, 0.0, 0.0],
                "orientation_WB": [1.0, 0.0, 0.0, 0.0],
                "angular_velocity_B_rad_s": [0.0, 0.0, 0.0],
            },
            "reference": {
                "position_W_m": [0.0, 0.0, 2.0],
                "velocity_W_m_s": [0.0, 0.0, 0.0],
                "acceleration_W_m_s2": [0.0, 0.0, 0.0],
                "yaw_rad": 0.0,
            },
            "control": {
                "collective_thrust_N": 9.81,
                "body_moments_Nm": [0.0, 0.0, 0.0],
            },
        })
    with open(ep / "telemetry.json", "w") as f:
        json.dump(telemetry, f)

    return ds


def test_position_gain_dataset_targets_log_multipliers(tmp_path):
    ds = _write_gain_dataset(tmp_path)
    dataset = PositionGainDataset(str(ds), split="train")
    _, y = dataset[0]

    expected = np.log(np.array([2.0, 1.0, 2.0, 1.0, 2.0, 2.0]))
    assert y.shape == (6,)
    assert np.allclose(y.numpy(), expected)

    seq = SequentialPositionGainDataset(str(ds), split="train", sequence_length=5)
    x_seq, y_seq = seq[0]
    assert x_seq.shape == (5, 31)
    assert y_seq.shape == (6,)


def test_neural_position_controller_clips_multipliers(tmp_path):
    model_dir = tmp_path / "model"
    (model_dir / "checkpoints").mkdir(parents=True)

    norm_data = {
        "mean_x": [0.0] * 31,
        "std_x": [1.0] * 31,
        "mean_y": [0.0] * 6,
        "std_y": [1.0] * 6,
        "feature_names": ["f"] * 31,
        "target_names": ["t"] * 6,
        "feature_version": "v1_position_gain",
        "epsilon": 1e-8,
    }
    with open(model_dir / "normalization.json", "w") as f:
        json.dump(norm_data, f)

    model = MLPControllerNet(31, 6, hidden_dim=8)
    for param in model.parameters():
        torch.nn.init.constant_(param, 0.0)
    with torch.no_grad():
        model.net[-1].bias[:] = torch.tensor([10.0, -10.0, 0.0, 10.0, -10.0, 0.0])
    torch.save(model.state_dict(), model_dir / "checkpoints" / "mlp_best.pt")

    with open(model_dir / "config.yaml", "w") as f:
        yaml.dump({"architecture": "mlp", "input_dim": 31, "output_dim": 6, "hidden_dim": 8}, f)

    controller = NeuralPositionController(
        checkpoint_path=str(model_dir / "checkpoints" / "mlp_best.pt"),
        normalization_path=str(model_dir / "normalization.json"),
        architecture="mlp",
        inertia_B_kg_m2=np.diag([0.05, 0.05, 0.1]),
        multiplier_clip=np.array([0.25, 4.0]),
    )
    state, ref = _state_ref()
    command = controller.compute_control(0.0, state, ref)

    assert np.allclose(controller.last_gain_multipliers, [4.0, 0.25, 1.0, 4.0, 0.25, 1.0])
    assert np.isfinite(command.collective_thrust_N)
    assert np.all(np.isfinite(command.body_moments_Nm))


def test_instantiate_neural_position_scenario(tmp_path):
    ds = _write_gain_dataset(tmp_path)
    model_dir = tmp_path / "model_scenario"
    (model_dir / "checkpoints").mkdir(parents=True)
    with open(model_dir / "normalization.json", "w") as f:
        json.dump({
            "mean_x": [0.0] * 31,
            "std_x": [1.0] * 31,
            "mean_y": [0.0] * 6,
            "std_y": [1.0] * 6,
            "feature_names": ["f"] * 31,
            "target_names": ["t"] * 6,
            "feature_version": "v1_position_gain",
            "epsilon": 1e-8,
        }, f)
    model = MLPControllerNet(31, 6, hidden_dim=8)
    torch.save(model.state_dict(), model_dir / "checkpoints" / "mlp_best.pt")
    with open(model_dir / "config.yaml", "w") as f:
        yaml.dump({"architecture": "mlp", "input_dim": 31, "output_dim": 6, "hidden_dim": 8}, f)

    scenario = {
        "name": "neural_position_test",
        "vehicle": {
            "mass_kg": 1.0,
            "inertia_B_kg_m2": [[0.05, 0, 0], [0, 0.05, 0], [0, 0, 0.1]],
            "linear_drag_coefficient": [0.0, 0.0, 0.0],
            "rotors": [
                {"position_B_m": [0.17, 0.17, 0], "turning_direction": -1, "k_f": 1e-4, "k_m": 1e-6, "omega_max_rad_s": 1000, "time_constant_s": 0.0},
                {"position_B_m": [0.17, -0.17, 0], "turning_direction": 1, "k_f": 1e-4, "k_m": 1e-6, "omega_max_rad_s": 1000, "time_constant_s": 0.0},
                {"position_B_m": [-0.17, 0.17, 0], "turning_direction": 1, "k_f": 1e-4, "k_m": 1e-6, "omega_max_rad_s": 1000, "time_constant_s": 0.0},
                {"position_B_m": [-0.17, -0.17, 0], "turning_direction": -1, "k_f": 1e-4, "k_m": 1e-6, "omega_max_rad_s": 1000, "time_constant_s": 0.0},
            ],
        },
        "initial_state": {
            "position_W_m": [0.0, 0.0, 2.0],
            "velocity_W_m_s": [0.0, 0.0, 0.0],
            "orientation_WB": None,
            "angular_velocity_B_rad_s": [0.0, 0.0, 0.0],
        },
        "trajectory": {"type": "hold", "position_W_m": [0.0, 0.0, 2.0]},
        "controller": {
            "type": "neural_position",
            "architecture": "mlp",
            "checkpoint_path": str(model_dir / "checkpoints" / "mlp_best.pt"),
            "normalization_path": str(model_dir / "normalization.json"),
        },
        "perturbations": {"constant_wind_W_m_s": [0.0, 0.0, 0.0]},
        "timing": {"physics_dt_s": 0.01, "control_dt_s": 0.02, "telemetry_dt_s": 0.1},
        "termination": {"max_duration_s": 0.2, "z_min_m": -1.0},
        "output": {"dir": str(ds / "out"), "telemetry_file": "telemetry.json", "metrics_file": "metrics.json"},
    }

    *_, controller, _, _ = instantiate_scenario(scenario)
    assert isinstance(controller, NeuralPositionController)


def test_train_neural_position_script_execution(tmp_path):
    ds = _write_gain_dataset(tmp_path)
    out_dir = tmp_path / "position_model"

    result = subprocess.run(
        [
            sys.executable,
            "tools/train_neural_position_controller.py",
            "--dataset",
            str(ds),
            "--architecture",
            "mlp",
            "--out",
            str(out_dir),
            "--epochs",
            "2",
            "--batch-size",
            "8",
            "--hidden-dim",
            "8",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert (out_dir / "normalization.json").exists()
    assert (out_dir / "config.yaml").exists()
    assert (out_dir / "checkpoints" / "mlp_best.pt").exists()
