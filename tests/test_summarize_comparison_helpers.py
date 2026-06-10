import sys
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.summarize_comparison import build_run_record, resolve_classic_pid_family


def test_build_run_record_exports_physical_control_magnitudes():
    record = build_run_record(
        scenario_id="s1",
        family="hold",
        split="test",
        controller="classic_pid_hold",
        metrics={
            "position_rmse_m": 0.1,
            "collective_thrust_mean_N": 9.8,
            "body_moment_norm_mean_Nm": 0.4,
            "termination_reason": "Time limit reached",
        },
    )

    assert record["collective_thrust_mean_N"] == 9.8
    assert record["body_moment_norm_mean_Nm"] == 0.4


def test_resolve_classic_pid_family_from_manifest_pid_family():
    row = pd.Series({"pid_family": "circle", "family": "lemniscate"})
    family = resolve_classic_pid_family(row, {}, "/tmp/classic", "/tmp/ood")
    assert family == "circle"


def test_resolve_classic_pid_family_from_scenario_yaml(tmp_path):
    classic_dir = tmp_path / "classic"
    ood_dir = tmp_path / "ood"
    (classic_dir / "pids").mkdir(parents=True)
    (ood_dir / "scenarios").mkdir(parents=True)

    gains = {
        "Kp_pos": [2.5, 2.5, 6.0],
        "Kd_pos": [1.2, 1.2, 2.5],
        "Kp_att": [4.0, 4.0, 1.0],
        "Kd_att": [1.5, 1.5, 0.5],
    }
    with open(classic_dir / "pids" / "pid_hold_v1.yaml", "w", encoding="utf-8") as handle:
        yaml.safe_dump(gains, handle)

    scenario_path = ood_dir / "scenarios" / "lemniscate_demo.yaml"
    scenario_path.write_text(
        yaml.safe_dump({"controller": {"type": "classic", **gains}}),
        encoding="utf-8",
    )

    row = pd.Series(
        {
            "family": "lemniscate",
            "scenario_path": "scenarios/lemniscate_demo.yaml",
        }
    )
    metrics = {
        "position_rmse_m": 0.2,
        "termination_reason": "Time limit reached",
    }

    assert resolve_classic_pid_family(row, metrics, str(classic_dir), str(ood_dir)) == "hold"