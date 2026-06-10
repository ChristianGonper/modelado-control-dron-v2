import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from tools.summarize_comparison import build_record, coverage_group_for_split


def test_build_record_marks_composite_completed_as_mission_success():
    record = build_record(
        scenario_id="composite_aggressive_transitions",
        family="composite",
        split="ood",
        controller="neural_outer_force_mlp",
        metrics={
            "termination_reason": "Composite trajectory completed",
            "position_rmse_m": 0.4,
            "position_max_err_m": 0.8,
            "saturation_percentage": 0.0,
            "degradation_percentage": 0.0,
        },
        trajectory_type="composite",
    )
    assert record["mission_success"] is True
    assert record["safety_success"] is True
    assert record["success"] == 1.0
    assert record["coverage_group"] == "comparable"


def test_build_record_waypoint_time_limit_is_not_mission_success():
    record = build_record(
        scenario_id="helix_ascending_fast",
        family="waypoint",
        split="ood",
        controller="classic_pid_representative",
        metrics={
            "termination_reason": "Time limit reached",
            "position_rmse_m": 0.5,
            "position_max_err_m": 1.0,
            "saturation_percentage": 0.0,
            "degradation_percentage": 0.0,
        },
        trajectory_type="waypoint",
    )
    assert record["mission_success"] is False
    assert record["safety_success"] is True


def test_coverage_group_marks_train_as_partial():
    assert coverage_group_for_split("train") == "baseline_partial"
    assert coverage_group_for_split("test") == "comparable"