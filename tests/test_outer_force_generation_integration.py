import os
import sys
from pathlib import Path

# Add project root to sys.path to import from tools directory
sys.path.append(str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import yaml
import numpy as np

from simulador_quad.datasets.classic import build_scenario_config
from tools.generate_outer_force_pid_bank import main as run_pid_bank
from tools.generate_outer_force_dataset import main as run_dataset


def create_minimal_classic_dataset(tmp_path: Path) -> Path:
    dataset_dir = tmp_path / "classic_source"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    scenarios_dir = dataset_dir / "scenarios" / "hold"
    scenarios_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create a dummy scenario config YAML
    trajectory_cfg = {
        "type": "circle",
        "center_W_m": [0.0, 0.0, 2.0],
        "radius_m": 1.0,
        "omega_rad_s": 0.5,
        "yaw_mode": "forward"
    }
    pid_config = {
        "Kp_pos": [2.0, 2.0, 5.0],
        "Kd_pos": [1.0, 1.0, 2.0],
        "Kp_att": [4.0, 4.0, 1.0],
        "Kd_att": [1.5, 1.5, 0.5],
        "max_body_moments_Nm": [10.0, 10.0, 2.0]
    }
    scenario_cfg = build_scenario_config(
        scenario_id="hold_test_01",
        family="hold",
        trajectory_cfg=trajectory_cfg,
        profile_id="P0_nominal",
        pid_config=pid_config,
        seed=1042,
        output_root=str(dataset_dir)
    )

    yaml_path = scenarios_dir / "hold_test_01.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(scenario_cfg, f, sort_keys=False)

    # 2. Write manifest.csv
    manifest_data = [{
        "scenario_id": "hold_test_01",
        "family": "hold",
        "geometry_id": "g01",
        "perturbation_id": "P0_nominal",
        "pid_id": "classic_hold",
        "seed": 1042,
        "split": "train",
        "scenario_path": "scenarios/hold/hold_test_01.yaml",
        "result_dir": "results/hold/hold_test_01"
    }]
    manifest_df = pd.DataFrame(manifest_data)
    manifest_df.to_csv(dataset_dir / "manifest.csv", index=False)

    return dataset_dir


def test_outer_force_generation_pipeline(tmp_path):
    source_dir = create_minimal_classic_dataset(tmp_path)
    bank_dir = tmp_path / "pid_bank"
    out_dataset_dir = tmp_path / "outer_force_dataset"

    # Save original sys.argv
    orig_argv = sys.argv

    # ----------------------------------------------------
    # Step 1: Run PID Bank Generation
    # ----------------------------------------------------
    sys.argv = [
        "generate_outer_force_pid_bank.py",
        "--dataset", str(source_dir),
        "--out", str(bank_dir),
        "--overwrite",
        "--workers", "2",
    ]
    try:
        run_pid_bank()
    finally:
        sys.argv = orig_argv

    # Assertions on PID Bank
    bank_manifest_path = bank_dir / "pid_bank_manifest.csv"
    assert bank_manifest_path.exists()

    bank_manifest = pd.read_csv(bank_manifest_path)
    # 5 variants after extension with damped options
    assert len(bank_manifest) == 5
    assert set(bank_manifest["variant"]) == {"conservative", "base", "aggressive", "damped", "damped2"}
    assert all(bank_manifest["source_scenario_id"] == "hold_test_01")

    # Verify that variant YAML files contain float lists for Kp_pos and Kd_pos
    for _, row in bank_manifest.iterrows():
        yaml_path = bank_dir / row["pid_path"]
        assert yaml_path.exists()
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert isinstance(data["Kp_pos"], list)
        assert all(isinstance(x, float) for x in data["Kp_pos"])
        assert isinstance(data["Kd_pos"], list)
        assert all(isinstance(x, float) for x in data["Kd_pos"])

    # ----------------------------------------------------
    # Step 2: Run Dataset Generation
    # ----------------------------------------------------
    sys.argv = [
        "generate_outer_force_dataset.py",
        "--source-dataset", str(source_dir),
        "--pid-bank", str(bank_dir),
        "--out", str(out_dataset_dir)
    ]
    try:
        run_dataset()
    finally:
        sys.argv = orig_argv

    # Assertions on Dataset
    out_manifest_path = out_dataset_dir / "manifest.csv"
    assert out_manifest_path.exists()

    out_manifest = pd.read_csv(out_manifest_path)
    assert len(out_manifest) == 1
    assert out_manifest.iloc[0]["scenario_id"] == "hold_test_01_outer_expert"
    assert out_manifest.iloc[0]["source_scenario_id"] == "hold_test_01"

    expert_yaml_path = out_dataset_dir / out_manifest.iloc[0]["scenario_path"]
    assert expert_yaml_path.exists()

    with open(expert_yaml_path) as f:
        expert_cfg = yaml.safe_load(f)

    # Verify that Kp_pos and Kd_pos are serialized as numeric lists and NOT strings
    assert isinstance(expert_cfg["controller"]["Kp_pos"], list)
    assert all(isinstance(x, (float, int)) for x in expert_cfg["controller"]["Kp_pos"])
    assert isinstance(expert_cfg["controller"]["Kd_pos"], list)
    assert all(isinstance(x, (float, int)) for x in expert_cfg["controller"]["Kd_pos"])

    # ----------------------------------------------------
    # Step 3: Test P1 (Expert Safety Selection Filter)
    # ----------------------------------------------------
    # If all candidates fail the safety filters (passed_filter=False), we should raise ValueError
    bank_manifest["passed_filter"] = False
    bank_manifest.to_csv(bank_manifest_path, index=False)

    sys.argv = [
        "generate_outer_force_dataset.py",
        "--source-dataset", str(source_dir),
        "--pid-bank", str(bank_dir),
        "--out", str(tmp_path / "unsafe_dataset_should_fail")
    ]
    try:
        with pytest.raises(ValueError, match="No safe PID candidate found for scenario"):
            run_dataset()
    finally:
        sys.argv = orig_argv


def test_outer_force_generation_waypoint_inner_loop_and_tie_breaker(tmp_path):
    source_dir = tmp_path / "waypoint_source"
    source_dir.mkdir(parents=True, exist_ok=True)
    scenarios_dir = source_dir / "scenarios" / "waypoint"
    scenarios_dir.mkdir(parents=True, exist_ok=True)

    # Create scenario config with custom non-default PID gains and limits
    trajectory_cfg = {
        "type": "waypoint",
        "waypoints": [[0.0, 0.0, 1.0], [1.0, 1.0, 2.0]],
        "max_speed_m_s": 0.6,
        "max_acceleration_m_s2": 0.5,
    }
    pid_config = {
        "Kp_pos": [3.1, 3.2, 7.5],
        "Kd_pos": [1.2, 1.2, 2.4],
        "Kp_att": [4.8, 4.8, 1.2],
        "Kd_att": [1.2, 1.2, 0.4],
        "max_body_moments_Nm": [8.0, 8.0, 1.5]
    }

    scenario_cfg = build_scenario_config(
        scenario_id="waypoint_test_01",
        family="waypoint",
        trajectory_cfg=trajectory_cfg,
        profile_id="P0_nominal",
        pid_config=pid_config,
        seed=1042,
        output_root=str(source_dir)
    )
    # Ensure exact controller settings
    scenario_cfg["controller"] = {
        "type": "classic",
        **pid_config
    }

    yaml_path = scenarios_dir / "waypoint_test_01.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(scenario_cfg, f, sort_keys=False)

    # Write manifest.csv
    manifest_data = [{
        "scenario_id": "waypoint_test_01",
        "family": "waypoint",
        "geometry_id": "g01",
        "perturbation_id": "P0_nominal",
        "pid_id": "classic_waypoint",
        "seed": 1042,
        "split": "train",
        "scenario_path": "scenarios/waypoint/waypoint_test_01.yaml",
        "result_dir": "results/waypoint/waypoint_test_01"
    }]
    pd.DataFrame(manifest_data).to_csv(source_dir / "manifest.csv", index=False)

    # Run Bank Generation
    bank_dir = tmp_path / "waypoint_pid_bank"
    orig_argv = sys.argv
    sys.argv = [
        "generate_outer_force_pid_bank.py",
        "--dataset", str(source_dir),
        "--out", str(bank_dir),
        "--overwrite"
    ]
    try:
        run_pid_bank()
    finally:
        sys.argv = orig_argv

    # Verify variants preserve inner loop and limits
    bank_manifest_path = bank_dir / "pid_bank_manifest.csv"
    assert bank_manifest_path.exists()
    bank_manifest = pd.read_csv(bank_manifest_path)

    for _, row in bank_manifest.iterrows():
        yaml_path = bank_dir / row["pid_path"]
        assert yaml_path.exists()
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        # Verify Kp_att, Kd_att, and limits are preserved exactly
        assert data["Kp_att"] == [4.8, 4.8, 1.2]
        assert data["Kd_att"] == [1.2, 1.2, 0.4]
        assert data["max_body_moments_Nm"] == [8.0, 8.0, 1.5]

        # Verify Kp_pos and Kd_pos are correctly scaled
        var_name = row["variant"]
        if var_name == "base":
            assert np.allclose(data["Kp_pos"], [3.1, 3.2, 7.5])
            assert np.allclose(data["Kd_pos"], [1.2, 1.2, 2.4])
        elif var_name == "conservative":
            assert np.allclose(data["Kp_pos"], [3.1 * 0.7, 3.2 * 0.7, 7.5 * 0.7])
            assert np.allclose(data["Kd_pos"], [1.2 * 0.9, 1.2 * 0.9, 2.4 * 0.9])
        elif var_name == "aggressive":
            assert np.allclose(data["Kp_pos"], [3.1 * 1.3, 3.2 * 1.3, 7.5 * 1.3])
            assert np.allclose(data["Kd_pos"], [1.2 * 1.2, 1.2 * 1.2, 2.4 * 1.2])

    # ----------------------------------------------------
    # Test strict tie-breaker logic
    # ----------------------------------------------------
    # Mock RMSE and Effort:
    # base: RMSE = 1.0, effort = 100.0, passed_filter = True
    # aggressive: RMSE = 0.50, effort = 10.00, passed_filter = True
    # conservative: RMSE = 0.51, effort = 10.05, passed_filter = True  (RMSE within 5% of 0.50: 0.51 <= 0.525)
    # The selector should pick aggressive, NOT conservative, because effort 10.00 < 10.05.
    # New damped variants are set to clearly worse so they do not interfere with the tie test.

    bank_manifest.loc[bank_manifest["variant"] == "base", "position_rmse_m"] = 1.0
    bank_manifest.loc[bank_manifest["variant"] == "base", "control_effort"] = 100.0
    bank_manifest.loc[bank_manifest["variant"] == "base", "passed_filter"] = True

    bank_manifest.loc[bank_manifest["variant"] == "aggressive", "position_rmse_m"] = 0.50
    bank_manifest.loc[bank_manifest["variant"] == "aggressive", "control_effort"] = 10.00
    bank_manifest.loc[bank_manifest["variant"] == "aggressive", "passed_filter"] = True

    bank_manifest.loc[bank_manifest["variant"] == "conservative", "position_rmse_m"] = 0.51
    bank_manifest.loc[bank_manifest["variant"] == "conservative", "control_effort"] = 10.05
    bank_manifest.loc[bank_manifest["variant"] == "conservative", "passed_filter"] = True

    # Make damped variants non-competitive / invalid for this tie test
    for v in ["damped", "damped2"]:
        if (bank_manifest["variant"] == v).any():
            bank_manifest.loc[bank_manifest["variant"] == v, "position_rmse_m"] = 10.0
            bank_manifest.loc[bank_manifest["variant"] == v, "control_effort"] = 999.0
            bank_manifest.loc[bank_manifest["variant"] == v, "passed_filter"] = False

    bank_manifest.to_csv(bank_manifest_path, index=False)

    out_dataset_dir = tmp_path / "waypoint_dataset"
    sys.argv = [
        "generate_outer_force_dataset.py",
        "--source-dataset", str(source_dir),
        "--pid-bank", str(bank_dir),
        "--out", str(out_dataset_dir)
    ]
    try:
        run_dataset()
    finally:
        sys.argv = orig_argv

    # Check manifest and verify that aggressive was selected
    out_manifest_path = out_dataset_dir / "manifest.csv"
    assert out_manifest_path.exists()
    out_manifest = pd.read_csv(out_manifest_path)

    expert_yaml_path = out_dataset_dir / out_manifest.iloc[0]["scenario_path"]
    with open(expert_yaml_path) as f:
        expert_cfg = yaml.safe_load(f)

    # Aggressive pos gains: [3.1 * 1.3, 3.2 * 1.3, 7.5 * 1.3] = [4.03, 4.16, 9.75]
    expected_kp = [3.1 * 1.3, 3.2 * 1.3, 7.5 * 1.3]
    assert np.allclose(expert_cfg["controller"]["Kp_pos"], expected_kp)

    # Verify that Kp_att, Kd_att, and limits are preserved in the final expert scenario config
    assert expert_cfg["controller"]["Kp_att"] == [4.8, 4.8, 1.2]
    assert expert_cfg["controller"]["Kd_att"] == [1.2, 1.2, 0.4]
    assert expert_cfg["controller"]["max_body_moments_Nm"] == [8.0, 8.0, 1.5]
