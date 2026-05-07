from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from simulador_quad.scenarios.loader import instantiate_scenario, load_scenario
from simulador_quad.scenarios.schema import validate_scenario_config


SCENARIOS_DIR = Path("scenarios")


def _valid_config() -> dict:
    return load_scenario(str(SCENARIOS_DIR / "hover_clean.yaml"))


def _expect_invalid(config: dict, field: str) -> None:
    with pytest.raises(ValueError, match=field):
        validate_scenario_config(config)


def test_official_scenarios_pass_physical_validation():
    scenario_paths = sorted(SCENARIOS_DIR.glob("*.yaml"))
    assert scenario_paths

    for scenario_path in scenario_paths:
        config = load_scenario(str(scenario_path))
        instantiate_scenario(config)


def test_invalid_vehicle_mass_fails_early():
    config = _valid_config()
    config["vehicle"]["mass_kg"] = -1.0

    _expect_invalid(config, "vehicle.mass_kg")


def test_invalid_inertia_matrix_fails_early():
    config = _valid_config()
    config["vehicle"]["inertia_B_kg_m2"] = [[0.05, 0.01, 0], [0, 0.05, 0], [0, 0, 0.1]]

    _expect_invalid(config, "vehicle.inertia_B_kg_m2")


def test_non_positive_definite_inertia_fails_early():
    config = _valid_config()
    config["vehicle"]["inertia_B_kg_m2"] = [[0.05, 0, 0], [0, -0.05, 0], [0, 0, 0.1]]

    _expect_invalid(config, "vehicle.inertia_B_kg_m2")


def test_negative_drag_coefficient_fails_early():
    config = _valid_config()
    config["vehicle"]["linear_drag_coefficient"] = [0.0, -0.1, 0.0]

    _expect_invalid(config, "vehicle.linear_drag_coefficient")


def test_invalid_rotor_count_fails_early():
    config = _valid_config()
    config["vehicle"]["rotors"] = config["vehicle"]["rotors"][:3]

    _expect_invalid(config, "vehicle.rotors")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("position_B_m", [0.17, 0.17]),
        ("turning_direction", 0),
        ("k_f", 0.0),
        ("k_m", -1.0e-6),
        ("omega_max_rad_s", 0.0),
        ("time_constant_s", -0.01),
        ("delay_s", -0.01),
    ],
)
def test_invalid_rotor_fields_fail_early(field, value):
    config = _valid_config()
    config["vehicle"]["rotors"][0][field] = value

    _expect_invalid(config, f"vehicle.rotors\\[0\\].{field}")


@pytest.mark.parametrize("field", ["physics_dt_s", "control_dt_s", "telemetry_dt_s"])
def test_invalid_timing_fails_early(field):
    config = _valid_config()
    config["timing"][field] = 0.0

    _expect_invalid(config, f"timing.{field}")


def test_invalid_orientation_quaternion_fails_early():
    config = _valid_config()
    config["initial_state"]["orientation_WB"] = [1.0, 1.0, 0.0, 0.0]

    _expect_invalid(config, "initial_state.orientation_WB")


def test_null_orientation_remains_valid():
    config = deepcopy(_valid_config())
    config["initial_state"]["orientation_WB"] = None

    validate_scenario_config(config)
