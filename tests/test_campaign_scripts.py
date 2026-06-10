import os
import subprocess
import pytest
import pandas as pd
import yaml
import json


@pytest.fixture
def tmp_dataset_dir(tmp_path):
    d = tmp_path / "classic_dataset_test"
    # 1. Generamos el dataset clásico para tener manifest, pids y escenarios
    gen_cmd = [
        "uv", "run", "python", "tools/generate_classic_dataset.py",
        "--version", "test_v1",
        "--out", str(d),
        "--overwrite"
    ]
    result = subprocess.run(gen_cmd, capture_output=True, text=True)
    assert result.returncode == 0
    
    # 2. Correr una simulación clásica para tener un metrics.json de baseline
    run_cmd = [
        "uv", "run", "python", "tools/run_classic_dataset.py",
        "--dataset", str(d),
        "--family", "hold",
        "--scenario-id", "hold_g01_P0_nominal_s1042",
        "--no-visualization"
    ]
    result = subprocess.run(run_cmd, capture_output=True, text=True)
    assert result.returncode == 0
    return str(d)


def test_classic_transfer_and_summarize(tmp_dataset_dir):
    # 1. Ejecutar transferencia clásica con límite de 1 escenario
    transfer_cmd = [
        "uv", "run", "python", "tools/run_classic_transfer_dataset.py",
        "--dataset", tmp_dataset_dir,
        "--family", "hold",
        "--limit", "1",
        "--no-visualization",
        "--workers", "1"
    ]
    result = subprocess.run(transfer_cmd, capture_output=True, text=True)
    assert result.returncode == 0
    
    # Verificar que se creó el archivo de reporte de transferencia
    report_path = os.path.join(tmp_dataset_dir, "run_report_classic_transfer.csv")
    assert os.path.exists(report_path)
    
    # Verificar que el reporte tiene los resultados correspondientes
    df = pd.read_csv(report_path)
    assert len(df) > 0
    assert "scenario_id" in df.columns
    assert "pid_family" in df.columns
    assert "status" in df.columns
    assert "execution_status" in df.columns
    assert "execution_success" in df.columns
    assert "termination_reason" in df.columns
    assert "mission_success" in df.columns
    assert "safety_success" in df.columns
    assert set(df["execution_status"]) <= {"EXECUTED", "SKIPPED"}
    
    # Verify same-family transfer was NOT generated
    same_family_scenario_path = os.path.join(tmp_dataset_dir, "scenarios_transfer", "hold_g01_P0_nominal_s1042_with_pid_hold.yaml")
    assert not os.path.exists(same_family_scenario_path)
    assert len(df[df["pid_family"] == "hold"]) == 0
    
    # Verificar que se generó un escenario de transferencia
    transfer_scenario_path = os.path.join(tmp_dataset_dir, "scenarios_transfer", "hold_g01_P0_nominal_s1042_with_pid_circle.yaml")
    assert os.path.exists(transfer_scenario_path)
    
    # 2. Ejecutar summarize_comparison en modo básico
    out_dir = os.path.join(tmp_dataset_dir, "results_summary")
    sum_cmd = [
        "uv", "run", "python", "tools/summarize_comparison.py",
        "--dataset-classic", tmp_dataset_dir,
        "--dataset-neural", tmp_dataset_dir, # Apuntar a la misma carpeta para evitar errores si no existe el neural
        "--dataset-position", tmp_dataset_dir,
        "--out-dir", out_dir
    ]
    result = subprocess.run(sum_cmd, capture_output=True, text=True)
    assert result.returncode == 0
    
    # Verificar que generó los CSVs de salida
    assert os.path.exists(os.path.join(out_dir, "comparison_all_runs.csv"))
    assert os.path.exists(os.path.join(out_dir, "comparison_summary.csv"))
    
    # Test of the campaign orchestrator dry-run (includes tuning, parameters forwarding, and prerequisites check)
    campaign_cmd = [
        "uv", "run", "python", "tools/run_experimental_campaign.py",
        "--phase", "all",
        "--dry-run",
        "--workers", "2",
        "--tune-seed", "123",
        "--tune-initial-candidates", "16",
        "--tune-rmse-hold", "0.20",
        "--rerun"
    ]
    result = subprocess.run(campaign_cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "Executing:" in result.stdout
    assert "[DRY-RUN] Command skipped." in result.stdout
    assert "PID Base Diagnostic + Tune" in result.stdout or "tune" in result.stdout.lower()
    # Test of parameters forwarding (no vacuous assert)
    assert "--seed 123" in result.stdout
    assert "--initial-candidates 16" in result.stdout
    assert "--workers 2" in result.stdout
    assert "generate_outer_force_pid_bank.py --dataset data/classic_dataset/v1 --out data/outer_force_pid_bank/v1 --workers 2" in result.stdout
    assert "--rmse-hold 0.2" in result.stdout
    assert "generate_ood_battery.py" in result.stdout
    assert "--pid-source-dataset data/classic_dataset/v1" in result.stdout
    assert "run_classic_transfer_dataset.py --dataset data/classic_dataset/v1 --pid-source-dataset data/classic_dataset/v1 --split test --pid-family all --include-native" in result.stdout
    assert "run_classic_transfer_dataset.py --dataset data/neural_ood/battery_v1 --pid-source-dataset data/classic_dataset/v1 --pid-family all --include-native" in result.stdout
    assert "Actionable" in open("tools/run_experimental_campaign.py").read()  # prereq string present

    # Negative prerequisites validation test
    with open("tools/run_experimental_campaign.py") as f:
        src = f.read()
    assert "Actionable: run phase 2 first" in src
    assert "PID Base Diagnostic + Tune" in src


def test_summarize_comparison_neural_matching(tmp_path):
    # Setup mock folders
    classic_dir = tmp_path / "classic"
    neural_dir = tmp_path / "neural"
    position_dir = tmp_path / "position"
    ood_dir = tmp_path / "ood"
    out_dir = tmp_path / "out"

    for d in [classic_dir, neural_dir, position_dir, ood_dir, out_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Classic manifest
    classic_manifest_df = pd.DataFrame([{
        "scenario_id": "scenario_001_hold",
        "family": "hold",
        "split": "test",
        "scenario_path": "scenarios/hold/scenario_001_hold.yaml",
        "result_dir": "results/hold/scenario_001_hold"
    }])
    classic_manifest_df.to_csv(classic_dir / "manifest.csv", index=False)

    # 2. Neural manifest and reports
    neural_manifest_df = pd.DataFrame([{
        "scenario_id": "scenario_001_hold_outer_expert",
        "family": "hold",
        "split": "test",
        "scenario_path": "scenarios/hold/scenario_001_hold_outer_expert.yaml",
        "result_dir": "results/hold/scenario_001_hold_outer_expert"
    }])
    neural_manifest_df.to_csv(neural_dir / "manifest.csv", index=False)

    neural_res_dir = neural_dir / "results/hold/scenario_001_hold_outer_expert_neural_mlp"
    neural_res_dir.mkdir(parents=True, exist_ok=True)
    with open(neural_res_dir / "metrics.json", "w") as f:
        json.dump({
            "position_rmse_m": 0.05,
            "position_max_err_m": 0.1,
            "saturation_percentage": 1.2,
            "degradation_percentage": 0.5,
            "force_norm_clip_percentage": 0.1,
            "force_tilt_clip_percentage": 0.2,
            "termination_reason": "Time limit reached"
        }, f)

    neural_report_df = pd.DataFrame([{
        "scenario_id": "scenario_001_hold_outer_expert",
        "status": "SUCCESS",
        "result_dir": "results/hold/scenario_001_hold_outer_expert_neural_mlp"
    }])
    neural_report_df.to_csv(neural_dir / "run_report_neural_mlp.csv", index=False)

    # 3. Position manifest and reports
    position_manifest_df = pd.DataFrame([{
        "scenario_id": "scenario_001_hold_conservative",
        "family": "hold",
        "split": "test",
        "scenario_path": "scenarios/hold/scenario_001_hold_conservative.yaml",
        "result_dir": "results/hold/scenario_001_hold_conservative"
    }])
    position_manifest_df.to_csv(position_dir / "manifest.csv", index=False)

    pos_res_dir = position_dir / "results/hold/scenario_001_hold_conservative_neural_position_mlp"
    pos_res_dir.mkdir(parents=True, exist_ok=True)
    with open(pos_res_dir / "metrics.json", "w") as f:
        json.dump({
            "position_rmse_m": 0.04,
            "position_max_err_m": 0.08,
            "saturation_percentage": 0.8,
            "degradation_percentage": 0.3,
            "termination_reason": "Time limit reached"
        }, f)

    pos_report_df = pd.DataFrame([{
        "scenario_id": "scenario_001_hold_conservative",
        "status": "SUCCESS",
        "result_dir": "results/hold/scenario_001_hold_conservative_neural_position_mlp"
    }])
    pos_report_df.to_csv(position_dir / "run_report_neural_position_mlp.csv", index=False)

    # 4. OOD manifest and reports
    ood_manifest_df = pd.DataFrame([{
        "scenario_id": "scenario_ood_001",
        "family": "hold",
        "split": "ood",
        "scenario_path": "scenarios/hold/scenario_ood_001.yaml",
        "result_dir": "results/scenario_ood_001"
    }])
    ood_manifest_df.to_csv(ood_dir / "manifest.csv", index=False)

    ood_neural_res_dir = ood_dir / "results/scenario_ood_001_neural_mlp"
    ood_neural_res_dir.mkdir(parents=True, exist_ok=True)
    with open(ood_neural_res_dir / "metrics.json", "w") as f:
        json.dump({
            "position_rmse_m": 0.07,
            "position_max_err_m": 0.14,
            "saturation_percentage": 2.0,
            "degradation_percentage": 1.0,
            "termination_reason": "Time limit reached"
        }, f)

    ood_neural_report_df = pd.DataFrame([{
        "scenario_id": "scenario_ood_001",
        "status": "SUCCESS",
        "result_dir": "results/scenario_ood_001_neural_mlp"
    }])
    ood_neural_report_df.to_csv(ood_dir / "run_report_neural_mlp.csv", index=False)

    # OOD position metrics
    ood_pos_res_dir = ood_dir / "results/scenario_ood_001_neural_position_mlp"
    ood_pos_res_dir.mkdir(parents=True, exist_ok=True)
    with open(ood_pos_res_dir / "metrics.json", "w") as f:
        json.dump({
            "position_rmse_m": 0.06,
            "position_max_err_m": 0.12,
            "saturation_percentage": 1.5,
            "degradation_percentage": 0.7,
            "termination_reason": "Time limit reached"
        }, f)

    ood_pos_report_df = pd.DataFrame([{
        "scenario_id": "scenario_ood_001",
        "status": "SUCCESS",
        "result_dir": "results/scenario_ood_001_neural_position_mlp"
    }])
    ood_pos_report_df.to_csv(ood_dir / "run_report_neural_position_mlp.csv", index=False)

    # 5. Execute summarize_comparison
    cmd = [
        "uv", "run", "python", "tools/summarize_comparison.py",
        "--dataset-classic", str(classic_dir),
        "--dataset-neural", str(neural_dir),
        "--dataset-position", str(position_dir),
        "--dataset-ood", str(ood_dir),
        "--out-dir", str(out_dir)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"summarize_comparison failed: {res.stderr}"

    # Load results
    summary_path = out_dir / "comparison_summary.csv"
    assert summary_path.exists()
    summary_df = pd.read_csv(summary_path)

    # Verify ID classification and OOD position models
    # Check neural_outer_force_mlp test entry
    of_test = summary_df[(summary_df["controller"] == "neural_outer_force_mlp") & (summary_df["split"] == "test")]
    assert len(of_test) == 1
    assert of_test.iloc[0]["family"] == "hold"
    assert of_test.iloc[0]["rmse_mean"] == 0.05

    # Check neural_position_mlp test entry
    pos_test = summary_df[(summary_df["controller"] == "neural_position_mlp") & (summary_df["split"] == "test")]
    assert len(pos_test) == 1
    assert pos_test.iloc[0]["family"] == "hold"
    assert pos_test.iloc[0]["rmse_mean"] == 0.04

    # Check neural_position_mlp ood entry
    pos_ood = summary_df[(summary_df["controller"] == "neural_position_mlp") & (summary_df["split"] == "ood")]
    assert len(pos_ood) == 1
    assert pos_ood.iloc[0]["family"] == "hold"
    assert pos_ood.iloc[0]["rmse_mean"] == 0.06

    # Check neural_outer_force_mlp ood entry
    of_ood = summary_df[(summary_df["controller"] == "neural_outer_force_mlp") & (summary_df["split"] == "ood")]
    assert len(of_ood) == 1
    assert of_ood.iloc[0]["family"] == "hold"
    assert of_ood.iloc[0]["rmse_mean"] == 0.07


def test_runner_failure_propagation(tmp_path):
    dataset_dir = tmp_path / "failed_dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    manifest_df = pd.DataFrame([{
        "scenario_id": "nonexistent_scenario",
        "family": "hold",
        "split": "test",
        "scenario_path": "scenarios/hold/nonexistent.yaml",
        "result_dir": "results/hold/nonexistent"
    }])
    manifest_df.to_csv(dataset_dir / "manifest.csv", index=False)
    
    cmd = [
        "uv", "run", "python", "tools/run_classic_dataset.py",
        "--dataset", str(dataset_dir),
        "--no-visualization"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 1
    assert "Error: One or more simulation runs failed" in res.stdout or "Error: One or more simulation runs failed" in res.stderr
