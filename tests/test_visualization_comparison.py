import os
from pathlib import Path

import pandas as pd
import pytest

from simulador_quad.visualization.comparison import plot_comparison


def test_plot_comparison_missing_csv_raises(tmp_path):
    missing_csv = tmp_path / "does_not_exist.csv"
    with pytest.raises(FileNotFoundError):
        plot_comparison(missing_csv, tmp_path / "figs")


def test_plot_comparison_empty_csv_raises(tmp_path):
    empty_csv = tmp_path / "empty.csv"
    pd.DataFrame().to_csv(empty_csv, index=False)
    with pytest.raises(ValueError, match="empty"):
        plot_comparison(empty_csv, tmp_path / "figs")


def _record(**overrides):
    base = {
        "position_rmse_m": 0.1,
        "position_max_err_m": 0.2,
        "collective_thrust_mean_N": 9.8,
        "body_moment_norm_mean_Nm": 0.4,
        "saturation_percentage": 1.5,
        "force_norm_clip_percentage": 2.0,
        "force_tilt_clip_percentage": 0.5,
        "degradation_percentage": 0.0,
        "mission_success": 1.0,
        "success": 1.0,
        "termination_reason": "Trajectory completed",
    }
    base.update(overrides)
    return base


def _build_comparison_records():
    records = []
    for family in ["hold", "circle", "lissajous", "waypoint"]:
        for controller in [
            f"classic_pid_{family}",
            "classic_pid_representative",
            "neural_outer_force_mlp",
            "neural_outer_force_gru",
            "neural_outer_force_lstm",
        ]:
            records.append(
                _record(
                    scenario_id=f"scen_{family}_{controller}",
                    family=family,
                    split="test",
                    controller=controller,
                    position_rmse_m=0.05 + 0.02 * len(controller),
                    collective_thrust_mean_N=9.5 + 0.1 * len(controller),
                    body_moment_norm_mean_Nm=0.3 + 0.05 * len(controller),
                )
            )

    for family in ["lemniscate", "lissajous", "composite", "waypoint"]:
        for controller in [
            "classic_pid_representative",
            "neural_outer_force_mlp",
            "neural_outer_force_gru",
            "neural_outer_force_lstm",
        ]:
            records.append(
                _record(
                    scenario_id=f"scen_ood_{family}_{controller}",
                    family=family,
                    split="ood",
                    controller=controller,
                    position_rmse_m=0.5 + 0.1 * len(controller),
                    collective_thrust_mean_N=10.5 + 0.1 * len(controller),
                    body_moment_norm_mean_Nm=0.8 + 0.05 * len(controller),
                    saturation_percentage=4.0,
                    mission_success=0.0 if family == "lemniscate" else 1.0,
                    success=0.0,
                    termination_reason="Persistent actuator saturation" if family == "lemniscate" else "Trajectory completed",
                )
            )

    for family in ["hold", "circle"]:
        records.append(
            _record(
                scenario_id=f"scen_trans_{family}",
                family=family,
                split="test",
                controller="classic_pid_hold",
                position_rmse_m=0.25,
                collective_thrust_mean_N=10.2,
                body_moment_norm_mean_Nm=0.55,
            )
        )

    return records


def test_plot_comparison_generates_all_figures(tmp_path):
    csv_path = tmp_path / "comparison_all_runs.csv"
    pd.DataFrame(_build_comparison_records()).to_csv(csv_path, index=False)

    out_dir = tmp_path / "figures_comp"
    result = plot_comparison(csv_path, out_dir, formats=["png", "pdf"])

    expected_bases = {
        "res_id_rmse_family",
        "res_ood_rmse_family",
        "res_pid_transfer_matrix",
        "res_ood_scenario_matrix",
        "res_ood_termination_summary",
        "res_protections_ood",
    }

    actual_files = os.listdir(out_dir)
    for base in expected_bases:
        assert f"{base}.png" in actual_files
        assert f"{base}.pdf" in actual_files
        assert os.path.getsize(out_dir / f"{base}.png") > 0
        assert os.path.getsize(out_dir / f"{base}.pdf") > 0

    generated = set(result.generated)
    assert expected_bases.issubset(generated)
    assert len(result.paths) == len(generated) * 2


def test_plot_comparison_reports_skipped_c3_without_ood(tmp_path):
    records = [
        _record(
            scenario_id="hold_native",
            family="hold",
            split="test",
            controller="classic_pid_hold",
        )
    ]
    csv_path = tmp_path / "test_only.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False)

    result = plot_comparison(csv_path, tmp_path / "figs", formats=["png"])

    assert "res_ood_rmse_family" not in result.generated
    skipped_ids = {figure_id for figure_id, _ in result.skipped}
    assert "res_ood_rmse_family" in skipped_ids


def test_plot_comparison_includes_transfer_pid_runs_in_c1(tmp_path):
    records = [
        _record(
            scenario_id="hold_native",
            family="hold",
            split="test",
            controller="classic_pid_hold",
            position_rmse_m=0.05,
        ),
        _record(
            scenario_id="circle_with_hold_pid",
            family="circle",
            split="test",
            controller="classic_pid_hold",
            position_rmse_m=0.18,
        ),
    ]
    csv_path = tmp_path / "transfer_identity.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False)

    result = plot_comparison(csv_path, tmp_path / "figs", formats=["png"])
    assert "res_pid_transfer_matrix" in result.generated


def test_plot_comparison_c4_ignores_non_test_splits(tmp_path):
    records = [
        _record(
            scenario_id="hold_test",
            family="circle",
            split="test",
            controller="classic_pid_hold",
            position_rmse_m=0.20,
        ),
        _record(
            scenario_id="hold_train",
            family="circle",
            split="train",
            controller="classic_pid_hold",
            position_rmse_m=9.99,
        ),
    ]
    csv_path = tmp_path / "c4_split_filter.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False)

    result = plot_comparison(csv_path, tmp_path / "figs", formats=["png"])
    assert "res_pid_transfer_matrix" in result.generated


def test_plot_comparison_skips_c5_without_physical_columns(tmp_path):
    records = [
        {
            "scenario_id": "a",
            "family": "hold",
            "split": "test",
            "controller": "classic_pid_hold",
            "position_rmse_m": 0.1,
            "saturation_percentage": 0.0,
            "success": 1.0,
        }
    ]
    csv_path = tmp_path / "missing_physical_cols.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False)

    result = plot_comparison(csv_path, tmp_path / "figs", formats=["png"])
    assert "res_protections_ood" not in result.generated


def test_plot_comparison_drops_ambiguous_classic_family_pid_rows(tmp_path):
    records = [
        _record(
            scenario_id="legacy_family_pid",
            family="circle",
            split="test",
            controller="classic_family_pid",
            position_rmse_m=0.99,
        ),
        _record(
            scenario_id="native_hold",
            family="hold",
            split="test",
            controller="classic_pid_hold",
            position_rmse_m=0.05,
        ),
    ]
    csv_path = tmp_path / "legacy_family_pid.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False)

    result = plot_comparison(csv_path, tmp_path / "figs", formats=["png"])

    assert result.warnings
    assert "classic_family_pid" in result.warnings[0]
    assert result.generated


def test_plot_comparison_c5_uses_only_test_split(tmp_path):
    records = [
        _record(
            scenario_id="train_only",
            family="hold",
            split="train",
            controller="classic_pid_hold",
            position_rmse_m=9.99,
            collective_thrust_mean_N=99.0,
            body_moment_norm_mean_Nm=9.0,
        ),
        _record(
            scenario_id="test_only",
            family="hold",
            split="test",
            controller="classic_pid_hold",
            position_rmse_m=0.1,
            collective_thrust_mean_N=9.8,
            body_moment_norm_mean_Nm=0.4,
        ),
    ]
    csv_path = tmp_path / "c5_test_only.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False)

    result = plot_comparison(csv_path, tmp_path / "figs", formats=["png"])
    assert result.generated


def test_plot_comparison_normalizes_legacy_transfer_labels(tmp_path):
    records = [
        _record(
            scenario_id="legacy_transfer",
            family="circle",
            split="test",
            controller="classic_transfer_hold",
            position_rmse_m=0.22,
        )
    ]
    csv_path = tmp_path / "legacy_transfer.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False)

    result = plot_comparison(csv_path, tmp_path / "figs", formats=["png"])
    assert "res_pid_transfer_matrix" in result.generated


def test_plot_comparison_generates_trajectory_with_fixture_telemetry(tmp_path):
    fixtures_dir = Path(__file__).resolve().parent / "fixtures"
    csv_path = tmp_path / "comparison_all_runs.csv"
    pd.DataFrame(_build_comparison_records()).to_csv(csv_path, index=False)
    out_dir = tmp_path / "figs_traj"
    result = plot_comparison(
        csv_path,
        out_dir,
        formats=["png"],
        trajectory_telemetry=[
            ("MLP", fixtures_dir / "trajectory_representative_mlp.json"),
            ("LSTM", fixtures_dir / "trajectory_representative_lstm.json"),
        ],
    )
    assert "res_trajectory_lemniscate_mlp_lstm" in result.generated
    assert (out_dir / "res_trajectory_lemniscate_mlp_lstm.png").exists()


def test_plot_comparison_skips_trajectory_when_telemetry_missing(tmp_path):
    csv_path = tmp_path / "comparison_all_runs.csv"
    pd.DataFrame(_build_comparison_records()).to_csv(csv_path, index=False)
    result = plot_comparison(
        csv_path,
        tmp_path / "figs_missing_traj",
        formats=["png"],
        trajectory_telemetry=[("MLP", tmp_path / "missing.json")],
    )
    assert "res_trajectory_lemniscate_mlp_lstm" not in result.generated
    skipped = dict(result.skipped)
    assert "res_trajectory_lemniscate_mlp_lstm" in skipped
    assert "telemetría ausente" in skipped["res_trajectory_lemniscate_mlp_lstm"]


def test_plot_comparison_prefers_mission_success_and_warns_on_legacy_success(tmp_path):
    records = [
        _record(
            scenario_id="legacy_success_only",
            family="hold",
            split="test",
            controller="classic_pid_representative",
            mission_success=0.0,
            success=1.0,
        )
    ]
    records[0].pop("mission_success")
    csv_path = tmp_path / "legacy_success.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False)
    result = plot_comparison(csv_path, tmp_path / "figs_legacy", formats=["png"])
    assert result.generated
