import os
import shutil
import pytest
import pandas as pd
from simulador_quad.datasets.classic import (
    get_dataset_manifest_data, write_dataset_files, PROFILES, FAMILIES
)

def test_manifest_v1_content():
    manifest = get_dataset_manifest_data()
    assert len(manifest) == 150
    
    # Check counts per family
    # hold: 6 geometries * 3 profiles = 18
    # circle: 8 geometries * 6 profiles = 48
    # lissajous: 8 geometries * 6 profiles = 48
    # waypoint: 6 geometries * 6 profiles = 36
    # Total: 18 + 48 + 48 + 36 = 150. Correct.
    
    df = pd.DataFrame(manifest)
    counts = df.groupby("family").size()
    assert counts["hold"] == 18
    assert counts["circle"] == 48
    assert counts["lissajous"] == 48
    assert counts["waypoint"] == 36
    
    # Check uniqueness of scenario_id
    assert len(df["scenario_id"].unique()) == 150

def test_determinism():
    m1 = get_dataset_manifest_data()
    m2 = get_dataset_manifest_data()
    assert m1 == m2

def test_waypoint_dataset_uses_waypoint_stop_config():
    manifest = get_dataset_manifest_data()
    waypoint_rows = [row for row in manifest if row["family"] == "waypoint"]
    assert waypoint_rows

    for row in waypoint_rows:
        cfg = row["trajectory_cfg"]
        assert cfg["type"] == "waypoint"
        assert "waypoints" in cfg
        assert "times" not in cfg
        assert cfg["max_speed_m_s"] == 0.6
        assert cfg["max_acceleration_m_s2"] == 0.5
        assert cfg["waypoint_tolerance_m"] == 0.20
        assert cfg["waypoint_speed_tolerance_m_s"] == 0.20
        assert cfg["dwell_time_s"] == 0.40

def test_write_dataset(tmp_path):
    output_dir = tmp_path / "v1"
    write_dataset_files("v1", str(output_dir))
    
    assert os.path.exists(output_dir / "manifest.csv")
    assert os.path.exists(output_dir / "README.md")
    
    # Check one YAML
    manifest_df = pd.read_csv(output_dir / "manifest.csv")
    first_path = output_dir / manifest_df.iloc[0]["scenario_path"]
    assert os.path.exists(first_path)
    
    # Verify we can load it and it passes validation
    from simulador_quad.scenarios.loader import load_scenario
    config = load_scenario(str(first_path))
    assert config["name"] == manifest_df.iloc[0]["scenario_id"]
    assert config["vehicle"]["rotors"][0]["omega_max_rad_s"] == 1500.0

    waypoint_row = manifest_df[manifest_df["family"] == "waypoint"].iloc[0]
    waypoint_path = output_dir / waypoint_row["scenario_path"]
    waypoint_config = load_scenario(str(waypoint_path))
    waypoint_trajectory = waypoint_config["trajectory"]
    assert "times" not in waypoint_trajectory
    assert waypoint_trajectory["max_speed_m_s"] == 0.6
    assert waypoint_trajectory["max_acceleration_m_s2"] == 0.5
    assert waypoint_config["termination"]["max_duration_s"] == 60.0

def test_initial_state_consistency(tmp_path):
    output_dir = tmp_path / "v1_init"
    write_dataset_files("v1_init", str(output_dir))

    manifest_df = pd.read_csv(output_dir / "manifest.csv")
    from simulador_quad.scenarios.loader import load_scenario, instantiate_trajectory
    import numpy as np

    # Check ALL generated scenarios to ensure they all follow the rule
    for _, row in manifest_df.iterrows():
        scenario_path = output_dir / row["scenario_path"]
        config = load_scenario(str(scenario_path))

        trajectory = instantiate_trajectory(config["trajectory"])
        ref0 = trajectory.get_reference(0.0)

        initial_pos = np.array(config["initial_state"]["position_W_m"])
        initial_yaw = float(config["initial_state"]["yaw_rad"])

        np.testing.assert_allclose(initial_pos, ref0.position_W_m, atol=1e-6, err_msg=f"Failed for {row['scenario_id']}")
        assert abs(initial_yaw - ref0.yaw_rad) < 1e-6, f"Failed for {row['scenario_id']}"

        # Verify velocity and angular velocity are zero
        assert all(v == 0.0 for v in config["initial_state"]["velocity_W_m_s"])
        assert all(v == 0.0 for v in config["initial_state"]["angular_velocity_B_rad_s"])
        assert config["initial_state"]["orientation_WB"] is None
