from __future__ import annotations

from typing import Any, Mapping

import numpy as np


def _invalid(field: str, expected: str, value: Any) -> ValueError:
    return ValueError(f"Invalid {field}: expected {expected}, got {value!r}")


def _require_mapping(config: Mapping[str, Any], field: str) -> Mapping[str, Any]:
    value = config.get(field)
    if not isinstance(value, Mapping):
        raise _invalid(field, "mapping", value)
    return value


def _require_sequence(config: Mapping[str, Any], field: str) -> list[Any]:
    value = config.get(field)
    if not isinstance(value, list):
        raise _invalid(field, "list", value)
    return value


def _as_array(field: str, value: Any, shape: tuple[int, ...] | None = None) -> np.ndarray:
    try:
        array = np.array(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise _invalid(field, "finite numeric value", value) from exc

    if shape is not None and array.shape != shape:
        raise _invalid(field, f"shape {shape}", value)
    if not np.all(np.isfinite(array)):
        raise _invalid(field, "finite numeric value", value)
    return array


def _positive(field: str, value: Any, unit: str = "value") -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise _invalid(field, f"positive {unit}", value) from exc
    if not np.isfinite(number) or number <= 0.0:
        raise _invalid(field, f"positive {unit}", value)
    return number


def _non_negative(field: str, value: Any, unit: str = "value") -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise _invalid(field, f"non-negative {unit}", value) from exc
    if not np.isfinite(number) or number < 0.0:
        raise _invalid(field, f"non-negative {unit}", value)
    return number


def _validate_vehicle(config: Mapping[str, Any]) -> None:
    vehicle = _require_mapping(config, "vehicle")

    _positive("vehicle.mass_kg", vehicle.get("mass_kg"), "kg value")
    _positive("vehicle.gravity_m_s2", vehicle.get("gravity_m_s2", 9.81), "m/s^2 value")

    inertia = _as_array("vehicle.inertia_B_kg_m2", vehicle.get("inertia_B_kg_m2"), (3, 3))
    if not np.allclose(inertia, inertia.T, atol=1e-9):
        raise _invalid("vehicle.inertia_B_kg_m2", "symmetric 3x3 matrix", vehicle.get("inertia_B_kg_m2"))
    try:
        eigenvalues = np.linalg.eigvalsh(inertia)
    except np.linalg.LinAlgError as exc:
        raise _invalid("vehicle.inertia_B_kg_m2", "positive definite 3x3 matrix", vehicle.get("inertia_B_kg_m2")) from exc
    if np.any(eigenvalues <= 0.0):
        raise _invalid("vehicle.inertia_B_kg_m2", "positive definite 3x3 matrix", vehicle.get("inertia_B_kg_m2"))

    drag = _as_array("vehicle.linear_drag_coefficient", vehicle.get("linear_drag_coefficient"))
    if drag.shape not in ((), (3,)):
        raise _invalid("vehicle.linear_drag_coefficient", "scalar or shape (3,)", vehicle.get("linear_drag_coefficient"))
    if np.any(drag < 0.0):
        raise _invalid("vehicle.linear_drag_coefficient", "non-negative scalar or vector", vehicle.get("linear_drag_coefficient"))

    rotors = _require_sequence(vehicle, "rotors")
    if len(rotors) != 4:
        raise _invalid("vehicle.rotors", "list with 4 rotors", rotors)

    for idx, rotor in enumerate(rotors):
        field = f"vehicle.rotors[{idx}]"
        if not isinstance(rotor, Mapping):
            raise _invalid(field, "mapping", rotor)
        _as_array(f"{field}.position_B_m", rotor.get("position_B_m"), (3,))
        if rotor.get("turning_direction") not in (-1, 1):
            raise _invalid(f"{field}.turning_direction", "-1 or 1", rotor.get("turning_direction"))
        _positive(f"{field}.k_f", rotor.get("k_f"), "N/(rad/s)^2 value")
        _non_negative(f"{field}.k_m", rotor.get("k_m"), "N*m/(rad/s)^2 value")
        _positive(f"{field}.omega_max_rad_s", rotor.get("omega_max_rad_s"), "rad/s value")
        _non_negative(f"{field}.time_constant_s", rotor.get("time_constant_s"), "s value")
        _non_negative(f"{field}.delay_s", rotor.get("delay_s", 0.0), "s value")


def _validate_timing(config: Mapping[str, Any]) -> None:
    timing = _require_mapping(config, "timing")
    for field in ("physics_dt_s", "control_dt_s", "telemetry_dt_s"):
        _positive(f"timing.{field}", timing.get(field), "s value")

    termination = _require_mapping(config, "termination")
    _positive("termination.max_duration_s", termination.get("max_duration_s"), "s value")
    for field in ("max_attitude_angle_rad", "max_saturation_duration_s", "max_position_m", "max_speed_m_s"):
        if field in termination:
            _positive(f"termination.{field}", termination.get(field), "value")
    if "z_min_m" in termination:
        _as_array("termination.z_min_m", termination.get("z_min_m"))


def _validate_initial_state(config: Mapping[str, Any]) -> None:
    initial_state = _require_mapping(config, "initial_state")
    _as_array("initial_state.position_W_m", initial_state.get("position_W_m"), (3,))
    _as_array("initial_state.velocity_W_m_s", initial_state.get("velocity_W_m_s"), (3,))
    _as_array("initial_state.angular_velocity_B_rad_s", initial_state.get("angular_velocity_B_rad_s"), (3,))

    orientation = initial_state.get("orientation_WB")
    if orientation is None:
        return

    q = _as_array("initial_state.orientation_WB", orientation, (4,))
    norm = float(np.linalg.norm(q))
    if norm <= 0.0 or not np.isclose(norm, 1.0, atol=1e-3):
        raise _invalid("initial_state.orientation_WB", "unit quaternion [w, x, y, z] or null", orientation)


def _validate_controller(config: Mapping[str, Any]) -> None:
    controller = _require_mapping(config, "controller")
    if controller.get("type") == "classic":
        for field in ("Kp_pos", "Kd_pos", "Kp_att", "Kd_att"):
            if field in controller:
                _as_array(f"controller.{field}", controller.get(field), (3,))
                if np.any(_as_array(f"controller.{field}", controller.get(field)) < 0.0):
                    raise _invalid(f"controller.{field}", "non-negative vector", controller.get(field))
        if "max_body_moments_Nm" in controller:
            _as_array("controller.max_body_moments_Nm", controller.get("max_body_moments_Nm"), (3,))
            if np.any(_as_array("controller.max_body_moments_Nm", controller.get("max_body_moments_Nm")) < 0.0):
                raise _invalid("controller.max_body_moments_Nm", "non-negative vector", controller.get("max_body_moments_Nm"))


def validate_scenario_config(config: Mapping[str, Any]) -> None:
    """Validate the physical fields that can invalidate a simulation result."""
    if not isinstance(config, Mapping):
        raise _invalid("scenario", "mapping", config)

    _validate_vehicle(config)
    _validate_timing(config)
    _validate_initial_state(config)
    _validate_controller(config)
