from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from simulador_quad.app import run_simulation
from simulador_quad.scenarios.loader import load_scenario


def _write_temp_scenario(tmp_path: Path, source_path: str, max_duration_s: float) -> Path:
    config = deepcopy(load_scenario(source_path))
    output_dir = tmp_path / "output"

    config["termination"]["max_duration_s"] = max_duration_s
    config["output"]["dir"] = str(output_dir)
    config["output"]["telemetry_file"] = "telemetry.json"
    config["output"]["metrics_file"] = "metrics.json"

    scenario_path = tmp_path / Path(source_path).name
    scenario_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return scenario_path


def _assert_json_finite(value: Any) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            _assert_json_finite(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_json_finite(nested)
    elif isinstance(value, (int, float)):
        assert np.isfinite(value)


def test_short_hover_scenario_exports_finite_json_with_expected_schema(tmp_path):
    scenario_path = _write_temp_scenario(tmp_path, "scenarios/hover_clean.yaml", max_duration_s=1.0)

    run_simulation(
        str(scenario_path),
        visualization=False,
        command=f"uv run simulador-quad run {scenario_path} --no-visualization",
    )

    telemetry_path = tmp_path / "output" / "telemetry.json"
    metrics_path = tmp_path / "output" / "metrics.json"
    assert telemetry_path.exists()
    assert metrics_path.exists()

    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    assert telemetry
    required_sample_sections = {"time_s", "state", "observation", "reference", "control", "rotors", "termination_cause"}
    assert required_sample_sections.issubset(telemetry[0])
    assert {"position_W_m", "velocity_W_m_s", "orientation_WB", "angular_velocity_B_rad_s"}.issubset(
        telemetry[0]["state"]
    )
    assert {"collective_thrust_N", "body_moments_Nm"}.issubset(telemetry[0]["control"])
    assert {"target_omega_rad_s", "applied_omega_rad_s", "saturation_flags"}.issubset(telemetry[0]["rotors"])

    required_metrics = {
        "position_rmse_m",
        "position_mae_m",
        "position_max_err_m",
        "collective_thrust_mean_N",
        "body_moment_norm_mean_Nm",
        "saturation_percentage",
        "degradation_percentage",
        "termination_reason",
        "duration_s",
        "metadata",
    }
    assert required_metrics.issubset(metrics)
    assert metrics["termination_reason"] == "Time limit reached"
    assert metrics["position_rmse_m"] < 1.0
    assert metrics["saturation_percentage"] == 0.0
    assert metrics["degradation_percentage"] == 0.0
    assert metrics["metadata"]["controller"]["type"] == "classic"

    _assert_json_finite(telemetry)
    _assert_json_finite(metrics)
