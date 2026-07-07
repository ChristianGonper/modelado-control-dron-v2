import json
import subprocess
import sys
from pathlib import Path


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "simulador_quad.app", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _write_minimal_telemetry(path: Path) -> None:
    telemetry = []
    for idx in range(3):
        telemetry.append(
            {
                "time_s": float(idx),
                "state": {
                    "position_W_m": [float(idx), 0.0, 2.0],
                    "orientation_WB": [1.0, 0.0, 0.0, 0.0],
                    "angular_velocity_B_rad_s": [0.0, 0.0, 0.0],
                },
                "reference": {
                    "position_W_m": [float(idx), 0.0, 2.0],
                },
                "control": {
                    "collective_thrust_N": 9.81,
                    "body_moments_Nm": [0.1, 0.0, 0.0],
                },
                "rotors": {
                    "applied_omega_rad_s": [100.0, 101.0, 102.0, 103.0],
                    "saturation_flags": [False, False, False, False],
                },
            }
        )
    path.write_text(json.dumps(telemetry), encoding="utf-8")


def test_plot_comparison_cli_fails_on_missing_csv(tmp_path):
    missing_csv = tmp_path / "missing.csv"
    result = _run_cli(
        "plot-comparison",
        str(missing_csv),
        "--out",
        str(tmp_path / "figs"),
    )

    assert result.returncode == 1
    assert "not found" in result.stderr.lower()


def test_plot_cli_generates_report_figures(tmp_path):
    telemetry_path = tmp_path / "telemetry.json"
    metrics_path = tmp_path / "metrics.json"
    out_dir = tmp_path / "figures_report"

    _write_minimal_telemetry(telemetry_path)
    metrics_path.write_text(json.dumps({"position_rmse_m": 0.1}), encoding="utf-8")

    result = _run_cli(
        "plot",
        str(telemetry_path),
        "--metrics",
        str(metrics_path),
        "--out",
        str(out_dir),
        "--profile",
        "report",
        "--formats",
        "png",
        "pdf",
        "svg",
    )

    assert result.returncode == 0, result.stderr
    assert (out_dir / "tracking_error.png").exists()
    assert (out_dir / "tracking_error.pdf").exists()
    assert (out_dir / "tracking_error.svg").exists()
