import json
import os

from simulador_quad.visualization.plots import plot_telemetry
from simulador_quad.visualization.three_d import export_trajectory_viewer_html


def test_plot_telemetry_generates_standard_figures(tmp_path):
    telemetry = []
    for idx in range(3):
        t = float(idx)
        telemetry.append(
            {
                "time_s": t,
                "state": {
                    "position_W_m": [t, 0.5 * t, 2.0],
                    "velocity_W_m_s": [1.0, 0.5, 0.0],
                    "orientation_WB": [1.0, 0.0, 0.0, 0.0],
                    "angular_velocity_B_rad_s": [0.0, 0.0, 0.0],
                },
                "observation": {
                    "position_W_m": [t, 0.5 * t, 2.0],
                    "velocity_W_m_s": [1.0, 0.5, 0.0],
                    "orientation_WB": [1.0, 0.0, 0.0, 0.0],
                    "angular_velocity_B_rad_s": [0.0, 0.0, 0.0],
                },
                "reference": {
                    "position_W_m": [t, 0.0, 2.0],
                    "velocity_W_m_s": [1.0, 0.0, 0.0],
                    "acceleration_W_m_s2": [0.0, 0.0, 0.0],
                    "yaw_rad": 0.0,
                },
                "control": {
                    "collective_thrust_N": 9.81,
                    "body_moments_Nm": [0.1, 0.2, 0.0],
                },
                "rotors": {
                    "target_thrust_N": [2.4, 2.4, 2.4, 2.4],
                    "target_omega_rad_s": [100.0, 101.0, 102.0, 103.0],
                    "degraded_collective_thrust": False,
                    "applied_thrust_N": [2.4, 2.4, 2.4, 2.4],
                    "applied_omega_rad_s": [100.0, 101.0, 102.0, 103.0],
                    "applied_torque_Nm": [0.0, 0.0, 0.0, 0.0],
                    "rotor_speed_rpm": [950.0, 960.0, 970.0, 980.0],
                    "saturation_flags": [False, False, False, False],
                },
                "termination_cause": "",
            }
        )

    telemetry_path = tmp_path / "telemetry.json"
    metrics_path = tmp_path / "metrics.json"
    output_dir = tmp_path / "figures"
    telemetry_path.write_text(json.dumps(telemetry), encoding="utf-8")
    metrics_path.write_text(json.dumps({"position_rmse_m": 0.2}), encoding="utf-8")

    generated = plot_telemetry(telemetry_path, output_dir, metrics_path)

    expected_names = {
        "trajectory_xy.png",
        "trajectory_3d_static.png",
        "position_time.png",
        "attitude_time.png",
        "angular_velocity_time.png",
        "tracking_error.png",
        "rotor_speeds.png",
        "control_effort.png",
    }
    assert {os.path.basename(path) for path in generated} == expected_names
    for path in generated:
        assert os.path.getsize(path) > 0

    # Test report profile which generates both PNG and PDF
    output_dir_report = tmp_path / "figures_report"
    generated_report = plot_telemetry(
        telemetry_path, output_dir_report, metrics_path, profile="report", formats=["png", "pdf"]
    )
    expected_report_names = {f"{name[:-4]}.{ext}" for name in expected_names for ext in ["png", "pdf"]}
    assert {os.path.basename(path) for path in generated_report} == expected_report_names
    for path in generated_report:
        assert os.path.getsize(path) > 0

    # B9 without clipped force must not crash
    telemetry_force_only = []
    for sample in telemetry:
        force_sample = dict(sample)
        force_sample["desired_force_W_N"] = [0.1, 0.2, 9.81]
        telemetry_force_only.append(force_sample)

    telemetry_path_force = tmp_path / "telemetry_force_only.json"
    telemetry_path_force.write_text(json.dumps(telemetry_force_only), encoding="utf-8")
    generated_force = plot_telemetry(telemetry_path_force, tmp_path / "figures_force", metrics_path)
    assert "neural_outer_force.png" in {os.path.basename(path) for path in generated_force}

    # B10 with wind only in some samples must not crash
    telemetry_wind_partial = []
    for idx, sample in enumerate(telemetry):
        wind_sample = dict(sample)
        if idx == 1:
            wind_sample["perturbation"] = {"wind_W_m_s": [1.0, 2.0, 0.0]}
        telemetry_wind_partial.append(wind_sample)

    telemetry_path_wind = tmp_path / "telemetry_wind_partial.json"
    telemetry_path_wind.write_text(json.dumps(telemetry_wind_partial), encoding="utf-8")
    generated_wind = plot_telemetry(telemetry_path_wind, tmp_path / "figures_wind", metrics_path)
    assert "perturbation_response.png" in {os.path.basename(path) for path in generated_wind}

    # Full optional telemetry still works
    for sample in telemetry:
        sample["desired_force_W_N"] = [0.1, 0.2, 9.81]
        sample["desired_force_clipped_W_N"] = [0.1, 0.2, 9.5]
        sample["perturbation"] = {"wind_W_m_s": [1.0, 2.0, 0.0]}

    telemetry_path_opt = tmp_path / "telemetry_opt.json"
    telemetry_path_opt.write_text(json.dumps(telemetry), encoding="utf-8")
    generated_opt = plot_telemetry(telemetry_path_opt, tmp_path / "figures_opt", metrics_path)
    generated_names = {os.path.basename(path) for path in generated_opt}
    assert "neural_outer_force.png" in generated_names
    assert "perturbation_response.png" in generated_names


def test_export_trajectory_viewer_html_creates_file(tmp_path):
    telemetry = [
        {
            "time_s": 0.0,
            "state": {"position_W_m": [0.0, 0.0, 0.0]},
            "reference": {"position_W_m": [0.0, 0.0, 0.0]},
        },
        {
            "time_s": 1.0,
            "state": {"position_W_m": [1.0, 1.0, 1.0]},
            "reference": {"position_W_m": [1.0, 1.0, 1.0]},
        },
    ]

    telemetry_path = tmp_path / "telemetry.json"
    output_path = tmp_path / "visualization_3d.html"
    metrics_path = tmp_path / "metrics.json"

    telemetry_path.write_text(json.dumps(telemetry), encoding="utf-8")
    metrics_path.write_text(
        json.dumps(
            {
                "position_rmse_m": 0.0,
                "termination_reason": "Test",
                "duration_s": 1.0,
            }
        ),
        encoding="utf-8",
    )

    path = export_trajectory_viewer_html(telemetry_path, output_path, metrics_path)

    assert os.path.exists(path)
    assert os.path.getsize(path) > 0
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "plotly" in content.lower()
        assert "Visor de Trayectoria 3D" in content
