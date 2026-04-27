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
        "position_time.png",
        "tracking_error.png",
        "rotor_speeds.png",
        "control_effort.png",
    }
    assert {os.path.basename(path) for path in generated} == expected_names
    for path in generated:
        assert os.path.getsize(path) > 0


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
