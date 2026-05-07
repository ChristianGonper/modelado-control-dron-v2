import os
import subprocess
import pytest
import pandas as pd
import shutil

@pytest.fixture
def tmp_dataset_dir(tmp_path):
    d = tmp_path / "classic_dataset_test"
    return str(d)

def test_classic_dataset_workflow(tmp_dataset_dir):
    # 1. Generate
    gen_cmd = [
        "uv", "run", "python", "tools/generate_classic_dataset.py",
        "--version", "test_v1",
        "--out", tmp_dataset_dir,
        "--overwrite"
    ]
    result = subprocess.run(gen_cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert os.path.exists(os.path.join(tmp_dataset_dir, "manifest.csv"))
    assert os.path.exists(os.path.join(tmp_dataset_dir, "pids", "pid_hold_test_v1.yaml"))
    
    # Check stratification: Hold should have 18 rows, 12 train, 3 val, 3 test
    df = pd.read_csv(os.path.join(tmp_dataset_dir, "manifest.csv"))
    hold_df = df[df["family"] == "hold"]
    assert len(hold_df) == 18
    assert (hold_df["split"] == "train").sum() == 12
    assert (hold_df["split"] == "val").sum() == 3
    assert (hold_df["split"] == "test").sum() == 3
    
    # Check PID consistency
    assert all(df["pid_id"].str.endswith("test_v1"))
    for pid_id in df["pid_id"].unique():
        assert os.path.exists(os.path.join(tmp_dataset_dir, "pids", f"{pid_id}.yaml"))

    # 2. Run (limit 1 nominal for hold)
    run_cmd = [
        "uv", "run", "python", "tools/run_classic_dataset.py",
        "--dataset", tmp_dataset_dir,
        "--family", "hold",
        "--scenario-id", "hold_g01_P0_nominal_s1042",
        "--no-visualization"
    ]
    result = subprocess.run(run_cmd, capture_output=True, text=True)
    assert result.returncode == 0
    
    # Check result exists
    res_path = os.path.join(tmp_dataset_dir, "results", "hold", "hold_g01_P0_nominal_s1042", "metrics.json")
    assert os.path.exists(res_path)

    # 3. Summarize
    sum_cmd = [
        "uv", "run", "python", "tools/summarize_classic_dataset.py",
        "--dataset", tmp_dataset_dir
    ]
    result = subprocess.run(sum_cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert os.path.exists(os.path.join(tmp_dataset_dir, "summary.csv"))
    
    # Check summary content
    sum_df = pd.read_csv(os.path.join(tmp_dataset_dir, "summary.csv"))
    hold_p0 = sum_df[sum_df["scenario_id"] == "hold_g01_P0_nominal_s1042"].iloc[0]
    # Default PID might not pass strict academic filters (0.40m for hold)
    assert hold_p0["status"] in ["VALID", "INVALID"]
    if hold_p0["status"] == "INVALID":
        assert "Max position error" in str(hold_p0["invalid_reason"])
    assert hold_p0["is_valid"] == (hold_p0["status"] == "VALID")
    assert hold_p0["rmse_m"] > 0
