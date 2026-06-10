"""Smoke tests for tools/generate_ood_battery.py."""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

from simulador_quad.datasets.classic import INITIAL_PIDS


def test_generate_ood_battery_help():
    result = subprocess.run(
        [sys.executable, "tools/generate_ood_battery.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--out" in result.stdout
    assert "--pid-source-dataset" in result.stdout


def _write_frozen_pids(pid_root: Path) -> Path:
    pids_dir = pid_root / "pids"
    pids_dir.mkdir(parents=True, exist_ok=True)
    for family, gains in INITIAL_PIDS.items():
        payload = {"pid_id": f"pid_{family}_v1", "family": family, "version": "v1", **gains}
        with open(pids_dir / f"pid_{family}_v1.yaml", "w", encoding="utf-8") as file:
            yaml.dump(payload, file)
    return pid_root


def test_generate_ood_battery_smoke(tmp_path):
    pid_root = _write_frozen_pids(tmp_path / "classic_source")
    out = tmp_path / "battery"
    result = subprocess.run(
        [
            sys.executable,
            "tools/generate_ood_battery.py",
            "--out",
            str(out),
            "--pid-source-dataset",
            str(pid_root),
            "--scenario-id",
            "lemniscate_3d_heavy_wind",
            "--overwrite",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    manifest = pd.read_csv(out / "manifest.csv")
    assert (manifest["split"] == "ood").all()
    assert len(manifest) == 1
    sc_path = out / "scenarios" / "lemniscate" / "lemniscate_3d_heavy_wind.yaml"
    assert sc_path.exists()

    row = manifest.iloc[0]
    with open(sc_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    assert cfg["output"]["dir"] == "results/lemniscate_3d_heavy_wind"
    assert row["result_dir"].replace("\\", "/") == "results/lemniscate_3d_heavy_wind"


def test_generate_ood_battery_requires_frozen_pids(tmp_path):
    out = tmp_path / "battery"
    result = subprocess.run(
        [
            sys.executable,
            "tools/generate_ood_battery.py",
            "--out",
            str(out),
            "--pid-source-dataset",
            str(tmp_path / "missing_source"),
            "--overwrite",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Frozen PID" in result.stderr or "not found" in result.stderr.lower()


def test_generate_ood_battery_rejects_nonempty_without_overwrite(tmp_path):
    out = tmp_path / "battery"
    out.mkdir()
    (out / "placeholder.txt").write_text("x", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "tools/generate_ood_battery.py",
            "--out",
            str(out),
            "--scenario-id",
            "lemniscate_3d_heavy_wind",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "overwrite" in (result.stderr + result.stdout).lower()