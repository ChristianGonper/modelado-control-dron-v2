import json
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.append(str(Path(__file__).parent.parent))

from tools.run_classic_transfer_dataset import refresh_transfer_report


def _write_metrics(result_dir: Path, termination_reason: str) -> None:
    result_dir.mkdir(parents=True, exist_ok=True)
    with open(result_dir / "metrics.json", "w", encoding="utf-8") as file:
        json.dump({"termination_reason": termination_reason}, file)


def test_refresh_report_marks_rows_recovered_without_live_provenance(tmp_path):
    dataset = tmp_path / "dataset"
    scenarios = dataset / "scenarios" / "hold"
    scenarios.mkdir(parents=True)
    with open(scenarios / "hold_test.yaml", "w", encoding="utf-8") as file:
        yaml.dump(
            {
                "family": "hold",
                "trajectory": {"type": "hold", "position_W_m": [0, 0, 1], "duration": 5.0},
            },
            file,
        )

    manifest_rows = [
        {
            "scenario_id": "hold_test",
            "family": "hold",
            "scenario_path": "scenarios/hold/hold_test.yaml",
        }
    ]
    pid_configs = {
        "hold": {
            "family": "hold",
            "Kp_pos": [1, 1, 1],
            "Kd_pos": [1, 1, 1],
            "Kp_att": [1, 1, 1],
            "Kd_att": [1, 1, 1],
        }
    }
    pid_source_files = {"hold": str(dataset / "pids" / "pid_hold_v1.yaml")}
    _write_metrics(dataset / "results_transfer" / "hold_test_with_pid_hold", "Time limit reached")

    previous = pd.DataFrame(
        [
            {
                "scenario_id": "hold_test",
                "pid_family": "hold",
                "execution_status": "EXECUTED",
                "status": "EXECUTED",
            }
        ]
    )
    previous_path = dataset / "run_report_classic_transfer.csv"
    previous.to_csv(previous_path, index=False)

    report = refresh_transfer_report(
        manifest_rows,
        str(dataset),
        pid_configs,
        pid_source_files,
        pid_family="hold",
        include_native=True,
        previous_report_path=str(previous_path),
    )

    assert len(report) == 1
    assert report[0]["execution_status"] == "RECOVERED"
    assert report[0]["report_provenance"] == "refreshed"


def test_refresh_report_preserves_live_executed_status(tmp_path):
    dataset = tmp_path / "dataset"
    scenarios = dataset / "scenarios" / "hold"
    scenarios.mkdir(parents=True)
    with open(scenarios / "hold_test.yaml", "w", encoding="utf-8") as file:
        yaml.dump(
            {
                "family": "hold",
                "trajectory": {"type": "hold", "position_W_m": [0, 0, 1], "duration": 5.0},
            },
            file,
        )

    manifest_rows = [
        {
            "scenario_id": "hold_test",
            "family": "hold",
            "scenario_path": "scenarios/hold/hold_test.yaml",
        }
    ]
    pid_configs = {
        "hold": {
            "family": "hold",
            "Kp_pos": [1, 1, 1],
            "Kd_pos": [1, 1, 1],
            "Kp_att": [1, 1, 1],
            "Kd_att": [1, 1, 1],
        }
    }
    pid_source_files = {"hold": str(dataset / "pids" / "pid_hold_v1.yaml")}
    _write_metrics(dataset / "results_transfer" / "hold_test_with_pid_hold", "Time limit reached")

    previous = pd.DataFrame(
        [
            {
                "scenario_id": "hold_test",
                "pid_family": "hold",
                "execution_status": "EXECUTED",
                "status": "EXECUTED",
                "report_provenance": "live",
            }
        ]
    )
    previous_path = dataset / "run_report_classic_transfer.csv"
    previous.to_csv(previous_path, index=False)

    report = refresh_transfer_report(
        manifest_rows,
        str(dataset),
        pid_configs,
        pid_source_files,
        pid_family="hold",
        include_native=True,
        previous_report_path=str(previous_path),
    )

    assert report[0]["execution_status"] == "EXECUTED"
    assert report[0]["report_provenance"] == "live"