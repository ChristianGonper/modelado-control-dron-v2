import os
import sys
import shutil
from pathlib import Path
import pytest
import pandas as pd
import yaml

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from tools.generate_outer_force_pid_bank import main as run_pid_bank
from tools.generate_outer_force_dataset import main as run_dataset
from tools.generate_ood_battery import REPRESENTATIVE_MAPPING, generate_battery
from tools.run_classic_transfer_dataset import (
    _transfer_is_current,
    build_transfer_tasks,
    main as run_classic_transfer,
)
from simulador_quad.datasets.classic import build_scenario_config, write_dataset_files
from simulador_quad.datasets.pids import extract_controller_gains, load_frozen_pid_family


def create_mock_classic_dataset(base_dir: Path) -> Path:
    dataset_dir = base_dir / "classic_source"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    scenarios_dir = dataset_dir / "scenarios" / "circle"
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    pids_dir = dataset_dir / "pids"
    pids_dir.mkdir(parents=True, exist_ok=True)

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
        scenario_id="circle_test_01",
        family="circle",
        trajectory_cfg=trajectory_cfg,
        profile_id="P0_nominal",
        pid_config=pid_config,
        seed=1042,
        output_root=str(dataset_dir)
    )

    yaml_path = scenarios_dir / "circle_test_01.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(scenario_cfg, f, sort_keys=False)

    # Write a dummy frozen PID file
    pid_data = {
        "pid_id": "pid_circle_v1",
        "family": "circle",
        "version": "v1",
        **pid_config
    }
    with open(pids_dir / "pid_circle_v1.yaml", "w") as f:
        yaml.dump(pid_data, f)

    # Write dummy frozen PID file for hold as well
    with open(pids_dir / "pid_hold_v1.yaml", "w") as f:
        yaml.dump({"pid_id": "pid_hold_v1", "family": "hold", "version": "v1", **pid_config}, f)

    # Write dummy frozen PID file for lissajous as well
    with open(pids_dir / "pid_lissajous_v1.yaml", "w") as f:
        yaml.dump({"pid_id": "pid_lissajous_v1", "family": "lissajous", "version": "v1", **pid_config}, f)

    # Write dummy frozen PID file for waypoint as well
    with open(pids_dir / "pid_waypoint_v1.yaml", "w") as f:
        yaml.dump({"pid_id": "pid_waypoint_v1", "family": "waypoint", "version": "v1", **pid_config}, f)

    # 2. Write manifest.csv
    manifest_data = [{
        "scenario_id": "circle_test_01",
        "family": "circle",
        "geometry_id": "g01",
        "perturbation_id": "P0_nominal",
        "pid_id": "pid_circle_v1",
        "seed": 1042,
        "split": "test",
        "scenario_path": "scenarios/circle/circle_test_01.yaml",
        "result_dir": "results/circle/circle_test_01"
    }]
    manifest_df = pd.DataFrame(manifest_data)
    manifest_df.to_csv(dataset_dir / "manifest.csv", index=False)

    return dataset_dir


def test_missing_input_manifests_raises_error(tmp_path):
    orig_argv = sys.argv
    # Try dataset generation without proper manifest
    sys.argv = [
        "generate_outer_force_dataset.py",
        "--source-dataset", str(tmp_path / "non_existent"),
        "--pid-bank", str(tmp_path / "non_existent"),
        "--out", str(tmp_path / "out")
    ]
    try:
        with pytest.raises(FileNotFoundError):
            run_dataset()
    finally:
        sys.argv = orig_argv


def test_strict_reject_family_fallback(tmp_path):
    # Setup classic dataset
    source_dir = create_mock_classic_dataset(tmp_path)

    # Setup a PID bank that does NOT have the exact candidate for circle_test_01
    bank_dir = tmp_path / "pid_bank"
    bank_dir.mkdir(parents=True, exist_ok=True)

    # Write a manifest that does not match circle_test_01
    bank_manifest_data = [{
        "scenario_id": "other_test_01_var_0",
        "source_scenario_id": "other_test_01",
        "family": "circle",
        "variant": "base",
        "pid_id": "pid_other_v1",
        "pid_path": "other.yaml",
        "passed_filter": True,
        "position_rmse_m": 0.1,
        "control_effort": 1.0
    }]
    pd.DataFrame(bank_manifest_data).to_csv(bank_dir / "pid_bank_manifest.csv", index=False)

    orig_argv = sys.argv
    sys.argv = [
        "generate_outer_force_dataset.py",
        "--source-dataset", str(source_dir),
        "--pid-bank", str(bank_dir),
        "--out", str(tmp_path / "out_dataset")
    ]
    try:
        # It must fail because no exact match for circle_test_01 is in the bank,
        # and family fallback is strictly disabled!
        with pytest.raises((ValueError, FileNotFoundError)):
            run_dataset()
    finally:
        sys.argv = orig_argv


def test_atomic_write_rollback_on_failure(tmp_path):
    source_dir = create_mock_classic_dataset(tmp_path)
    bank_dir = tmp_path / "pid_bank"

    # Ensure bank fails by running without a valid config or forcing a failure
    orig_argv = sys.argv
    sys.argv = [
        "generate_outer_force_pid_bank.py",
        "--dataset", str(tmp_path / "non_existent"),
        "--out", str(bank_dir)
    ]
    try:
        # Should raise FileNotFoundError / ValueError
        with pytest.raises((FileNotFoundError, ValueError)):
            run_pid_bank()
    finally:
        sys.argv = orig_argv

    # Ensure that target directory 'bank_dir' does not exist or remains empty
    if bank_dir.exists():
        assert len(os.listdir(bank_dir)) == 0


def test_generate_ood_battery_rejects_missing_frozen_pid(tmp_path):
    out_battery_dir = tmp_path / "ood_battery"
    with pytest.raises(FileNotFoundError):
        generate_battery(
            str(out_battery_dir),
            overwrite=True,
            pid_source_dataset=str(tmp_path / "missing_source"),
        )


def test_generate_ood_battery_representative_pid(tmp_path):
    source_dir = create_mock_classic_dataset(tmp_path)
    out_battery_dir = tmp_path / "ood_battery"
    generate_battery(
        str(out_battery_dir),
        overwrite=True,
        pid_source_dataset=str(source_dir),
    )

    manifest_path = out_battery_dir / "manifest.csv"
    assert manifest_path.exists()

    manifest_df = pd.read_csv(manifest_path)
    assert len(manifest_df) == 10

    pids_dir = source_dir / "pids"
    for _, row in manifest_df.iterrows():
        yaml_path = out_battery_dir / row["scenario_path"]
        with open(yaml_path, "r", encoding="utf-8") as file:
            scen_config = yaml.safe_load(file)

        assert scen_config["controller"]["type"] == "classic"
        assert scen_config["output"]["dir"] == f"results/{row['scenario_id']}"

        fam = row["family"]
        expected_pid_fam = REPRESENTATIVE_MAPPING.get(fam, "lissajous")
        assert scen_config["controller"]["pid_family"] == expected_pid_fam

        frozen_pid, _ = load_frozen_pid_family(str(pids_dir), expected_pid_fam)
        assert scen_config["controller"]["Kp_pos"] == frozen_pid["Kp_pos"]
        assert scen_config["controller"]["Kd_pos"] == frozen_pid["Kd_pos"]
        assert scen_config["controller"]["Kp_att"] == frozen_pid["Kp_att"]
        assert scen_config["controller"]["Kd_att"] == frozen_pid["Kd_att"]


def test_run_classic_transfer_dataset_filters_and_diagonal(tmp_path):
    source_dir = create_mock_classic_dataset(tmp_path)

    # We want to run transfer
    orig_argv = sys.argv
    sys.argv = [
        "run_classic_transfer_dataset.py",
        "--dataset", str(source_dir),
        "--pid-source-dataset", str(source_dir),
        "--pid-family", "hold",
        "--split", "test",
        "--no-visualization",
        "--workers", "1"
    ]
    try:
        run_classic_transfer()
    finally:
        sys.argv = orig_argv

    report_path = source_dir / "run_report_classic_transfer.csv"
    assert report_path.exists()

    report_df = pd.read_csv(report_path)
    # circle_test_01 is test split, and we filtered for pid_family='hold'
    assert len(report_df) == 1
    assert report_df.iloc[0]["pid_family"] == "hold"
    assert report_df.iloc[0]["controller_label"] == "classic_pid_hold"


def test_transfer_matrix_counts_and_diagonal(tmp_path):
    source_dir = create_mock_classic_dataset(tmp_path)
    manifest_df = pd.read_csv(source_dir / "manifest.csv")
    pids_dir = source_dir / "pids"
    pid_configs = {
        family: load_frozen_pid_family(str(pids_dir), family)[0]
        for family in ("hold", "circle", "lissajous", "waypoint")
    }
    pid_source_files = {
        family: load_frozen_pid_family(str(pids_dir), family)[1]
        for family in pid_configs
    }
    rows = manifest_df.to_dict("records")

    all_with_native = build_transfer_tasks(
        rows,
        pid_configs,
        pid_source_files,
        pid_family="all",
        include_native=True,
    )
    all_without_native = build_transfer_tasks(
        rows,
        pid_configs,
        pid_source_files,
        pid_family="all",
        include_native=False,
    )
    representative = build_transfer_tasks(
        rows,
        pid_configs,
        pid_source_files,
        pid_family="representative",
    )

    assert len(all_with_native) == len(rows) * 4
    assert len(all_without_native) == len(rows) * 3
    assert len(representative) == len(rows)
    assert all_with_native[0][1] == "hold"


def test_transfer_matrix_expected_sizes_for_published_campaign():
    test_rows = [{"scenario_id": f"s{i:02d}", "family": fam} for i, fam in enumerate(
        ["hold"] * 3 + ["circle"] * 8 + ["lissajous"] * 8 + ["waypoint"] * 4
    )]
    ood_rows = [
        {"scenario_id": f"ood_{i:02d}", "family": fam}
        for i, fam in enumerate(
            ["lemniscate"] * 3
            + ["lissajous"] * 2
            + ["composite"] * 2
            + ["waypoint"] * 3
        )
    ]
    pid_configs = {family: {"family": family, "Kp_pos": [1, 1, 1], "Kd_pos": [1, 1, 1], "Kp_att": [1, 1, 1], "Kd_att": [1, 1, 1]} for family in ("hold", "circle", "lissajous", "waypoint")}
    pid_source_files = {family: f"pid_{family}_v1.yaml" for family in pid_configs}

    assert len(build_transfer_tasks(test_rows, pid_configs, pid_source_files, pid_family="all", include_native=True)) == 92
    assert len(build_transfer_tasks(ood_rows, pid_configs, pid_source_files, pid_family="all", include_native=True)) == 40


def test_transfer_rejects_missing_frozen_pid(tmp_path):
    source_dir = create_mock_classic_dataset(tmp_path)
    pids_dir = source_dir / "pids"
    (pids_dir / "pid_hold_v1.yaml").unlink()

    orig_argv = sys.argv
    sys.argv = [
        "run_classic_transfer_dataset.py",
        "--dataset",
        str(source_dir),
        "--pid-source-dataset",
        str(source_dir),
        "--pid-family",
        "all",
        "--no-visualization",
        "--workers",
        "1",
    ]
    try:
        with pytest.raises(SystemExit):
            run_classic_transfer()
    finally:
        sys.argv = orig_argv


def test_transfer_invalidates_stale_results(tmp_path):
    source_dir = create_mock_classic_dataset(tmp_path)
    pids_dir = source_dir / "pids"

    orig_argv = sys.argv
    sys.argv = [
        "run_classic_transfer_dataset.py",
        "--dataset",
        str(source_dir),
        "--pid-source-dataset",
        str(source_dir),
        "--pid-family",
        "hold",
        "--split",
        "test",
        "--no-visualization",
        "--workers",
        "1",
    ]
    try:
        run_classic_transfer()
    finally:
        sys.argv = orig_argv

    transfer_yaml = source_dir / "scenarios_transfer" / "circle_test_01_with_pid_hold.yaml"
    assert transfer_yaml.exists()
    hold_pid, hold_path = load_frozen_pid_family(str(pids_dir), "hold")
    assert _transfer_is_current(str(transfer_yaml), "hold", hold_pid, hold_path)

    with open(pids_dir / "pid_hold_v1.yaml", "w", encoding="utf-8") as file:
        yaml.dump(
            {
                "pid_id": "pid_hold_v1",
                "family": "hold",
                "version": "v1",
                **extract_controller_gains(hold_pid),
                "Kp_pos": [9.0, 9.0, 9.0],
            },
            file,
        )
    updated_hold_pid, _ = load_frozen_pid_family(str(pids_dir), "hold")
    assert not _transfer_is_current(str(transfer_yaml), "hold", updated_hold_pid, hold_path)


def test_overwrite_clean_residuals(tmp_path):
    # Create target directory
    target_dir = tmp_path / "classic_target"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Put a residual dummy file inside it
    residual_file = target_dir / "old_residual.txt"
    residual_file.write_text("should be cleaned")

    # Write dataset using write_dataset_files with overwrite=True
    write_dataset_files(version="v1", output_root=str(target_dir), overwrite=True)

    # The old residual must be deleted after overwrite
    assert not residual_file.exists()
    assert (target_dir / "manifest.csv").exists()
