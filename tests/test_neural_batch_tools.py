"""Smoke tests for batch outer-force runner and comparison CSV builder."""
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import yaml


def test_run_neural_outer_force_dataset_help():
    result = subprocess.run(
        [sys.executable, "tools/run_neural_outer_force_dataset.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--dataset" in result.stdout
    assert "fail-fast" in result.stdout.lower()


def test_build_comparison_closed_loop_help():
    result = subprocess.run(
        [sys.executable, "tools/build_comparison_closed_loop.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--manual-csv" in result.stdout


def test_build_comparison_closed_loop_manual_csv(tmp_path):
    run_a = tmp_path / "classic_run"
    run_a.mkdir()
    metrics_a = {
        "position_rmse_m": 0.12,
        "position_mae_m": 0.10,
        "position_max_err_m": 0.25,
        "termination_reason": "Time limit reached",
        "saturation_percentage": 0.0,
        "degradation_percentage": 0.0,
        "metadata": {"git_commit": "abc123", "command": "test classic"},
    }
    with open(run_a / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_a, f)

    manual = tmp_path / "manual.csv"
    pd.DataFrame(
        [
            {
                "scenario_id": "hold_g01",
                "controller": "classic",
                "split": "test",
                "result_dir": str(run_a),
            }
        ]
    ).to_csv(manual, index=False)

    out_csv = tmp_path / "comparison.csv"
    result = subprocess.run(
        [
            sys.executable,
            "tools/build_comparison_closed_loop.py",
            "--manual-csv",
            str(manual),
            "--out",
            str(out_csv),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    df = pd.read_csv(out_csv)
    assert len(df) == 1
    assert df.iloc[0]["scenario_id"] == "hold_g01"
    assert df.iloc[0]["position_rmse_m"] == 0.12


def test_run_neural_outer_force_dataset_manifest_and_report(tmp_path):
    """Smoke: manifest parsing, _neural_mlp suffix, run_report CSV without full simulation."""
    ds = tmp_path / "ds"
    sc_dir = ds / "scenarios" / "hold"
    sc_dir.mkdir(parents=True)
    with open(sc_dir / "hold_a.yaml", "w", encoding="utf-8") as f:
        yaml.dump({"name": "hold_a", "output": {"dir": "results/hold_a"}}, f)
    pd.DataFrame(
        [
            {
                "scenario_id": "hold_a",
                "family": "hold",
                "split": "ood",
                "scenario_path": "scenarios/hold/hold_a.yaml",
                "result_dir": "results/hold_a",
            }
        ]
    ).to_csv(ds / "manifest.csv", index=False)

    ckpt = tmp_path / "ckpt.pt"
    ckpt.write_text("", encoding="utf-8")
    norm = tmp_path / "norm.json"
    norm.write_text("{}", encoding="utf-8")

    def fake_run_row(
        row,
        dataset,
        checkpoint,
        normalization,
        architecture,
        device,
        no_visualization,
        rerun,
        variant_tag=None,
    ):
        suffix = f"_neural_{architecture}"
        if variant_tag:
            suffix += f"_{variant_tag}"
        out_dir = os.path.join(dataset, row["result_dir"] + suffix)
        return {"scenario_id": row["scenario_id"], "status": "SUCCESS", "result_dir": out_dir}

    argv = [
        "run_neural_outer_force_dataset.py",
        "--dataset",
        str(ds),
        "--checkpoint",
        str(ckpt),
        "--normalization",
        str(norm),
        "--architecture",
        "mlp",
        "--limit",
        "1",
    ]
    tools_dir = Path(__file__).resolve().parent.parent / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import run_neural_outer_force_dataset as mod

    with patch.object(mod, "_run_row", fake_run_row):
        with patch.object(mod, "resolve_architecture", return_value="mlp"):
            with patch.object(sys, "argv", argv):
                mod.main()

    report_path = ds / "run_report_neural_mlp.csv"
    assert report_path.exists()
    report = pd.read_csv(report_path)
    assert report.iloc[0]["scenario_id"] == "hold_a"
    assert report.iloc[0]["status"] == "SUCCESS"
    assert report.iloc[0]["result_dir"].replace("\\", "/").endswith("results/hold_a_neural_mlp")


def test_build_comparison_warns_missing_metrics(tmp_path):
    report = tmp_path / "report.csv"
    pd.DataFrame(
        [{"scenario_id": "ghost", "status": "SUCCESS", "result_dir": "missing_dir"}]
    ).to_csv(report, index=False)

    out_csv = tmp_path / "comparison.csv"
    result = subprocess.run(
        [
            sys.executable,
            "tools/build_comparison_closed_loop.py",
            "--neural-report",
            str(report),
            "--neural-dataset",
            str(tmp_path),
            "--out",
            str(out_csv),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "missing metrics.json" in result.stderr.lower() or "missing metrics.json" in result.stdout.lower()


def test_build_comparison_classic_report_without_result_dir_uses_manifest(tmp_path):
    """Classic run_report.csv often lacks result_dir; resolve via manifest.csv."""
    ds = tmp_path / "classic_ds"
    result_sub = ds / "results" / "hold_a"
    result_sub.mkdir(parents=True)
    with open(result_sub / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "position_rmse_m": 0.05,
                "position_mae_m": 0.04,
                "position_max_err_m": 0.1,
                "termination_reason": "Time limit reached",
                "metadata": {"git_commit": "deadbeef", "command": "classic"},
            },
            f,
        )
    pd.DataFrame(
        [
            {
                "scenario_id": "hold_a",
                "family": "hold",
                "split": "test",
                "scenario_path": "scenarios/hold/hold_a.yaml",
                "result_dir": "results/hold_a",
            }
        ]
    ).to_csv(ds / "manifest.csv", index=False)
    pd.DataFrame([{"scenario_id": "hold_a", "status": "SUCCESS"}]).to_csv(
        ds / "run_report.csv", index=False
    )

    out_csv = tmp_path / "comparison.csv"
    result = subprocess.run(
        [
            sys.executable,
            "tools/build_comparison_closed_loop.py",
            "--classic-report",
            str(ds / "run_report.csv"),
            "--classic-dataset",
            str(ds),
            "--classic-split",
            "test",
            "--out",
            str(out_csv),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    df = pd.read_csv(out_csv)
    assert len(df) == 1
    assert df.iloc[0]["scenario_id"] == "hold_a"
    assert df.iloc[0]["position_rmse_m"] == 0.05


def test_build_comparison_skips_non_success(tmp_path):
    run_ok = tmp_path / "ok"
    run_skip = tmp_path / "skip"
    run_ok.mkdir()
    run_skip.mkdir()
    for d, rmse in ((run_ok, 0.1), (run_skip, 9.9)):
        with open(d / "metrics.json", "w", encoding="utf-8") as f:
            json.dump({"position_rmse_m": rmse, "metadata": {}}, f)

    report = tmp_path / "report.csv"
    pd.DataFrame(
        [
            {"scenario_id": "a", "status": "SUCCESS", "result_dir": str(run_ok)},
            {"scenario_id": "b", "status": "SKIPPED", "result_dir": str(run_skip)},
        ]
    ).to_csv(report, index=False)

    out_csv = tmp_path / "comparison.csv"
    subprocess.run(
        [
            sys.executable,
            "tools/build_comparison_closed_loop.py",
            "--neural-report",
            str(report),
            "--neural-dataset",
            str(tmp_path),
            "--out",
            str(out_csv),
        ],
        check=True,
    )
    df = pd.read_csv(out_csv)
    assert len(df) == 1
    assert df.iloc[0]["scenario_id"] == "a"
