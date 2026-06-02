"""Telemetry exports desired_force_W_N, clipped force, and wind when available."""
import json
from pathlib import Path

import numpy as np
import pytest

from simulador_quad.control.neural import NeuralOuterForceController
from simulador_quad.core.contracts import TrajectoryReference, VehicleState
from simulador_quad.core.frames import get_level_quaternion
from simulador_quad.runner import SimulationRunner
from simulador_quad.scenarios.loader import load_scenario, instantiate_scenario
from simulador_quad.telemetry.export import export_telemetry_json
from neural_checkpoint_fixtures import make_dummy_outer_force_checkpoint


@pytest.fixture
def hover_scenario_path(tmp_path):
    import yaml

    cfg = {
        "name": "hover_telemetry_test",
        "seed": 1,
        "vehicle": {
            "mass_kg": 1.0,
            "inertia_B_kg_m2": [[0.05, 0, 0], [0, 0.05, 0], [0, 0, 0.1]],
            "linear_drag_coefficient": [0, 0, 0],
            "rotors": [
                {
                    "position_B_m": [0.17, 0.17, 0],
                    "turning_direction": -1,
                    "k_f": 1e-4,
                    "k_m": 1e-6,
                    "omega_max_rad_s": 1000,
                    "time_constant_s": 0.0,
                },
                {
                    "position_B_m": [0.17, -0.17, 0],
                    "turning_direction": 1,
                    "k_f": 1e-4,
                    "k_m": 1e-6,
                    "omega_max_rad_s": 1000,
                    "time_constant_s": 0.0,
                },
                {
                    "position_B_m": [-0.17, 0.17, 0],
                    "turning_direction": 1,
                    "k_f": 1e-4,
                    "k_m": 1e-6,
                    "omega_max_rad_s": 1000,
                    "time_constant_s": 0.0,
                },
                {
                    "position_B_m": [-0.17, -0.17, 0],
                    "turning_direction": -1,
                    "k_f": 1e-4,
                    "k_m": 1e-6,
                    "omega_max_rad_s": 1000,
                    "time_constant_s": 0.0,
                },
            ],
        },
        "initial_state": {
            "position_W_m": [0, 0, 1],
            "velocity_W_m_s": [0, 0, 0],
            "orientation_WB": None,
            "angular_velocity_B_rad_s": [0, 0, 0],
        },
        "trajectory": {"type": "hold", "position_W_m": [0, 0, 1]},
        "controller": {
            "type": "classic",
            "Kp_pos": [2, 2, 5],
            "Kd_pos": [1, 1, 2],
            "Kp_att": [4, 4, 1],
            "Kd_att": [1.5, 1.5, 0.5],
        },
        "perturbations": {
            "constant_wind_W_m_s": [0.5, 0.2, 0.0],
            "pos_std_m": 0.0,
            "vel_std_m_s": 0.0,
        },
        "timing": {"physics_dt_s": 0.01, "control_dt_s": 0.02, "telemetry_dt_s": 0.05},
        "termination": {"max_duration_s": 0.3, "z_min_m": -0.1},
        "output": {"dir": str(tmp_path / "out"), "telemetry_file": "telemetry.json"},
    }
    path = tmp_path / "hover.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f)
    return str(path)


def test_telemetry_includes_wind(hover_scenario_path, tmp_path):
    config = load_scenario(hover_scenario_path)
    v_params, mixer, actuators, initial_state, trajectory, controller, wind, noise = instantiate_scenario(
        config
    )
    runner = SimulationRunner(
        physics_dt_s=config["timing"]["physics_dt_s"],
        control_dt_s=config["timing"]["control_dt_s"],
        telemetry_dt_s=config["timing"]["telemetry_dt_s"],
        vehicle_params=v_params,
        mixer=mixer,
        actuators=actuators,
        wind_model=wind,
        observation_noise=noise,
        max_duration_s=config["termination"]["max_duration_s"],
        z_min_m=config["termination"]["z_min_m"],
    )
    result = runner.run(initial_state, controller, trajectory)
    telem_path = tmp_path / "telemetry.json"
    export_telemetry_json(result["telemetry"], str(telem_path))

    with open(telem_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) > 0
    assert "perturbation" in data[0]
    assert np.allclose(data[0]["perturbation"]["wind_W_m_s"], [0.5, 0.2, 0.0])


def test_telemetry_exports_desired_force_from_outer_force_controller(tmp_path, hover_scenario_path):
    model_dir = make_dummy_outer_force_checkpoint(tmp_path)
    config = load_scenario(hover_scenario_path)
    v_params, mixer, actuators, initial_state, trajectory, _, wind, noise = instantiate_scenario(
        config
    )
    controller = NeuralOuterForceController(
        checkpoint_path=str(model_dir / "checkpoints" / "mlp_best.pt"),
        normalization_path=str(model_dir / "normalization.json"),
        architecture="mlp",
        feature_version="outer_force_min_v1",
        mass_kg=1.0,
        gravity_m_s2=9.81,
        clip_to_classic_limits=True,
        max_desired_tilt_rad=0.52,
    )
    runner = SimulationRunner(
        physics_dt_s=config["timing"]["physics_dt_s"],
        control_dt_s=config["timing"]["control_dt_s"],
        telemetry_dt_s=config["timing"]["telemetry_dt_s"],
        vehicle_params=v_params,
        mixer=mixer,
        actuators=actuators,
        wind_model=wind,
        observation_noise=noise,
        max_duration_s=config["termination"]["max_duration_s"],
        z_min_m=config["termination"]["z_min_m"],
    )
    result = runner.run(initial_state, controller, trajectory)
    telem_path = tmp_path / "neural_telemetry.json"
    export_telemetry_json(result["telemetry"], str(telem_path))

    with open(telem_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) > 0
    entry = data[0]
    assert "desired_force_W_N" in entry
    assert len(entry["desired_force_W_N"]) == 3
    assert np.all(np.isfinite(entry["desired_force_W_N"]))
    assert "desired_force_clipped_W_N" in entry
    assert len(entry["desired_force_clipped_W_N"]) == 3
    assert np.all(np.isfinite(entry["desired_force_clipped_W_N"]))