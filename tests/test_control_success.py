import pytest

from simulador_quad.metrics.success import (
    evaluate_termination_outcome,
    is_mission_success,
    is_safety_success,
    mission_success_terminations_for_trajectory_type,
    resolve_trajectory_type,
)


@pytest.mark.parametrize(
    ("trajectory_type", "termination_reason", "expected"),
    [
        ("hold", "Time limit reached", True),
        ("circle", "Time limit reached", True),
        ("waypoint", "Trajectory completed", True),
        ("waypoint", "Time limit reached", False),
        ("composite", "Composite trajectory completed", True),
        ("composite", "Time limit reached", False),
        ("composite", "Trajectory completed", False),
        ("hold", "Composite trajectory completed", False),
        ("hold", "Crash: Z_W < z_min_m", False),
    ],
)
def test_is_mission_success_by_trajectory_type(trajectory_type, termination_reason, expected):
    assert is_mission_success(termination_reason, trajectory_type=trajectory_type) is expected


@pytest.mark.parametrize(
    ("termination_reason", "expected"),
    [
        ("Time limit reached", True),
        ("Trajectory completed", True),
        ("Composite trajectory completed", True),
        ("Attitude angle exceeded limit (1.40 > 1.26)", False),
        ("Persistent actuator saturation", False),
        ("Crash: Z_W < z_min_m", False),
        ("Numerical divergence", False),
        ("Unexpected integrator failure", False),
        ("User aborted", False),
    ],
)
def test_is_safety_success(termination_reason, expected):
    assert is_safety_success(termination_reason) is expected


def test_helix_ood_waypoint_time_limit_is_safe_but_not_mission_complete():
    outcome = evaluate_termination_outcome("Time limit reached", trajectory_type="waypoint")
    assert outcome["safety_success"] is True
    assert outcome["mission_success"] is False


def test_resolve_trajectory_type_prefers_explicit_type():
    assert resolve_trajectory_type(trajectory_type="composite", family="waypoint") == "composite"


def test_mission_success_terminations_for_composite():
    assert "Composite trajectory completed" in mission_success_terminations_for_trajectory_type(
        "composite"
    )