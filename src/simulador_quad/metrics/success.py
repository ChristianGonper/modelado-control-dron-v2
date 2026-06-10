"""Termination success contracts derived from trajectory type."""
from __future__ import annotations

from typing import Any, Mapping

FAMILY_DEFAULT_TRAJECTORY_TYPE: dict[str, str] = {
    "hold": "hold",
    "circle": "circle",
    "lissajous": "lissajous",
    "waypoint": "waypoint",
    "lemniscate": "lemniscate",
    "composite": "composite",
}

MISSION_SUCCESS_TERMINATIONS: dict[str, tuple[str, ...]] = {
    "hold": ("Time limit reached",),
    "circle": ("Time limit reached",),
    "lissajous": ("Time limit reached",),
    "lemniscate": ("Time limit reached",),
    "waypoint": ("Trajectory completed",),
    "line": ("Trajectory completed",),
    "composite": ("Composite trajectory completed",),
}

SAFETY_SUCCESS_TERMINATIONS: tuple[str, ...] = (
    "Time limit reached",
    "Trajectory completed",
    "Composite trajectory completed",
)

PRESERVED_TRANSFER_EXECUTION_STATUSES: tuple[str, ...] = ("EXECUTED", "SKIPPED")


def trajectory_type_from_config(config: Mapping[str, Any] | None) -> str | None:
    if not isinstance(config, Mapping):
        return None
    trajectory = config.get("trajectory")
    if not isinstance(trajectory, Mapping):
        return None
    trajectory_type = trajectory.get("type")
    return trajectory_type if isinstance(trajectory_type, str) else None


def resolve_trajectory_type(
    *,
    trajectory_type: str | None = None,
    family: str | None = None,
) -> str:
    if trajectory_type:
        return trajectory_type
    if family:
        return FAMILY_DEFAULT_TRAJECTORY_TYPE.get(family, family)
    return "hold"


def mission_success_terminations_for_trajectory_type(trajectory_type: str) -> tuple[str, ...]:
    return MISSION_SUCCESS_TERMINATIONS.get(trajectory_type, ("Time limit reached",))


def is_safety_success(termination_reason: str | None) -> bool:
    if not termination_reason:
        return False
    return termination_reason in SAFETY_SUCCESS_TERMINATIONS


def is_preserved_transfer_execution_status(
    execution_status: str | None,
    *,
    report_provenance: str | None = None,
) -> bool:
    if not execution_status:
        return False
    if execution_status.startswith("FAILED:"):
        return True
    if execution_status == "SKIPPED":
        return True
    if execution_status == "EXECUTED" and report_provenance == "live":
        return True
    return False


def is_mission_success(
    termination_reason: str | None,
    *,
    trajectory_type: str | None = None,
    family: str | None = None,
) -> bool:
    if not termination_reason:
        return False
    resolved_type = resolve_trajectory_type(trajectory_type=trajectory_type, family=family)
    return termination_reason in mission_success_terminations_for_trajectory_type(resolved_type)


def is_control_success(
    termination_reason: str | None,
    *,
    trajectory_type: str | None = None,
    family: str | None = None,
) -> bool:
    """Backward-compatible alias for mission success."""
    return is_mission_success(
        termination_reason,
        trajectory_type=trajectory_type,
        family=family,
    )


def evaluate_termination_outcome(
    termination_reason: str | None,
    *,
    trajectory_type: str | None = None,
    family: str | None = None,
) -> dict[str, bool]:
    return {
        "mission_success": is_mission_success(
            termination_reason,
            trajectory_type=trajectory_type,
            family=family,
        ),
        "safety_success": is_safety_success(termination_reason),
    }