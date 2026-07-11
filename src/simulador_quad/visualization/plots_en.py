from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .common import as_array, load_json
from .style import use_style, COLORS
from .export import save_figure


def _plot_trajectory_xy(
    output_dir: Path,
    position_W_m: np.ndarray,
    reference_W_m: np.ndarray,
    metrics: dict[str, Any] | None,
    profile: str,
    formats: list[str],
) -> list[str]:
    """B1: Plot the 2D trajectory in the horizontal World (XY) plane."""
    fig, ax = plt.subplots()

    # Plot ENU: X is East, Y is North
    ax.plot(reference_W_m[:, 0], reference_W_m[:, 1], "--", color=COLORS["reference"], label="Reference")
    ax.plot(position_W_m[:, 0], position_W_m[:, 1], color=COLORS["real"], label="State")

    # Start and end markers
    ax.scatter(position_W_m[0, 0], position_W_m[0, 1], color=COLORS["start"], s=45, label="Start", zorder=5)
    ax.scatter(position_W_m[-1, 0], position_W_m[-1, 1], color=COLORS["failure"], s=45, label="End", zorder=5)

    if profile != "report":
        ax.set_title("Horizontal Plane Trajectory (World)")

    ax.set_xlabel("X_W East [m]")
    ax.set_ylabel("Y_W North [m]")
    ax.axis("equal")
    ax.legend(loc="best")

    # Metric overlay only in diagnostic
    if profile != "report" and metrics:
        rmse = metrics.get("position_rmse_m")
        if rmse is not None:
            ax.text(
                0.02,
                0.98,
                f"Position RMSE: {rmse:.3f} m",
                transform=ax.transAxes,
                va="top",
                bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
            )

    return save_figure(fig, output_dir, "trajectory_xy", formats)


def _plot_trajectory_3d_static(
    output_dir: Path,
    position_W_m: np.ndarray,
    reference_W_m: np.ndarray,
    profile: str,
    formats: list[str],
) -> list[str]:
    """B2: Static 3D trajectory plot in World frame."""
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    ax.plot(reference_W_m[:, 0], reference_W_m[:, 1], reference_W_m[:, 2], "--", color=COLORS["reference"], label="Reference")
    ax.plot(position_W_m[:, 0], position_W_m[:, 1], position_W_m[:, 2], color=COLORS["real"], label="State")

    ax.scatter(position_W_m[0, 0], position_W_m[0, 1], position_W_m[0, 2], color=COLORS["start"], s=30, label="Start", zorder=5)
    ax.scatter(position_W_m[-1, 0], position_W_m[-1, 1], position_W_m[-1, 2], color=COLORS["failure"], s=30, label="End", zorder=5)

    if profile != "report":
        ax.set_title("Static 3D Trajectory")

    ax.set_xlabel("X_W East [m]")
    ax.set_ylabel("Y_W North [m]")
    ax.set_zlabel("Z_W Up [m]")
    ax.legend(loc="best")

    # Equal scaling for physical correctness
    max_range = np.array([
        position_W_m[:, 0].max() - position_W_m[:, 0].min(),
        position_W_m[:, 1].max() - position_W_m[:, 1].min(),
        position_W_m[:, 2].max() - position_W_m[:, 2].min()
    ]).max() / 2.0

    mid_x = (position_W_m[:, 0].max() + position_W_m[:, 0].min()) * 0.5
    mid_y = (position_W_m[:, 1].max() + position_W_m[:, 1].min()) * 0.5
    mid_z = (position_W_m[:, 2].max() + position_W_m[:, 2].min()) * 0.5

    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

    return save_figure(fig, output_dir, "trajectory_3d_static", formats)


def _plot_position_time(
    output_dir: Path,
    time_s: np.ndarray,
    position_W_m: np.ndarray,
    reference_W_m: np.ndarray,
    profile: str,
    formats: list[str],
) -> list[str]:
    """B3: Plot X, Y, Z positions over time compared to references."""
    fig, axes = plt.subplots(3, 1, sharex=True)
    labels = ("X_W East [m]", "Y_W North [m]", "Z_W Up [m]")

    for idx, ax in enumerate(axes):
        ax.plot(time_s, reference_W_m[:, idx], "--", color=COLORS["reference"], label="Reference")
        ax.plot(time_s, position_W_m[:, idx], color=COLORS["real"], label="State")
        ax.set_ylabel(labels[idx])

    axes[-1].set_xlabel("Time [s]")
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", ncol=2)
    if profile != "report":
        fig.suptitle("Position Evolution vs Reference (World)")

    return save_figure(fig, output_dir, "position_time", formats)


def _plot_tracking_error(
    output_dir: Path,
    time_s: np.ndarray,
    position_error_m: np.ndarray,
    profile: str,
    formats: list[str],
) -> list[str]:
    """B4: Plot the Euclidean position tracking error over time."""
    fig, ax = plt.subplots()
    ax.plot(time_s, position_error_m, color=COLORS["failure"], label="L2 Error")

    if profile != "report":
        ax.set_title("Position Tracking Error")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("L2 Error: ||p_ref - p|| [m]")
    ax.legend(loc="best")

    return save_figure(fig, output_dir, "tracking_error", formats)


def _plot_attitude_time(
    output_dir: Path,
    time_s: np.ndarray,
    orientation_WB: np.ndarray,
    profile: str,
    formats: list[str],
) -> list[str]:
    """B5: Plot Roll, Pitch, and Yaw angles over time."""
    from simulador_quad.core.attitude import quaternion_to_euler_enu_frd

    # Convert q_WB to aircraft angles consistent with the simulator ENU/FRD convention.
    euler_angles_deg = np.array([
        quaternion_to_euler_enu_frd(q) for q in orientation_WB
    ]) * 180.0 / np.pi

    roll_deg = euler_angles_deg[:, 0]
    pitch_deg = euler_angles_deg[:, 1]
    yaw_deg = euler_angles_deg[:, 2]

    fig, axes = plt.subplots(3, 1, sharex=True)

    axes[0].plot(time_s, roll_deg, color=COLORS["real"], label="Roll")
    axes[0].set_ylabel(r"Roll $\phi$ [deg]")

    axes[1].plot(time_s, pitch_deg, color=COLORS["mlp"], label="Pitch")
    axes[1].set_ylabel(r"Pitch $\theta$ [deg]")

    axes[2].plot(time_s, yaw_deg, color=COLORS["gru"], label="Yaw")
    axes[2].set_ylabel(r"Yaw $\psi$ [deg]")
    axes[2].set_xlabel("Time [s]")

    for ax in axes:
        ax.legend(loc="best")

    if profile != "report":
        fig.suptitle("Vehicle Attitude (ENU/FRD)")

    return save_figure(fig, output_dir, "attitude_time", formats)


def _plot_angular_velocity_time(
    output_dir: Path,
    time_s: np.ndarray,
    angular_velocity_B_rad_s: np.ndarray,
    profile: str,
    formats: list[str],
) -> list[str]:
    """B6: Plot the body angular velocities (p, q, r) over time."""
    fig, axes = plt.subplots(3, 1, sharex=True)

    axes[0].plot(time_s, angular_velocity_B_rad_s[:, 0], color=COLORS["real"], label="p (Roll rate)")
    axes[0].set_ylabel(r"$p$ [rad/s]")

    axes[1].plot(time_s, angular_velocity_B_rad_s[:, 1], color=COLORS["mlp"], label="q (Pitch rate)")
    axes[1].set_ylabel(r"$q$ [rad/s]")

    axes[2].plot(time_s, angular_velocity_B_rad_s[:, 2], color=COLORS["gru"], label="r (Yaw rate)")
    axes[2].set_ylabel(r"$r$ [rad/s]")
    axes[2].set_xlabel("Time [s]")

    for ax in axes:
        ax.legend(loc="best")

    if profile != "report":
        fig.suptitle("Absolute Vehicle Angular Velocity (Body)")

    return save_figure(fig, output_dir, "angular_velocity_time", formats)


def _plot_control_effort(
    output_dir: Path,
    time_s: np.ndarray,
    collective_thrust_N: np.ndarray,
    body_moments_Nm: np.ndarray,
    profile: str,
    formats: list[str],
) -> list[str]:
    """B7: Plot control signals (collective thrust and moments)."""
    fig, axes = plt.subplots(2, 1, sharex=True)

    # Collective Thrust
    axes[0].plot(time_s, collective_thrust_N, color=COLORS["real"], label="Thrust")
    axes[0].set_ylabel("Thrust T [N]")
    axes[0].legend(loc="best")

    # Body Moments
    axes[1].plot(time_s, body_moments_Nm[:, 0], label=r"$\tau_x$ (Roll)", color=COLORS["real"])
    axes[1].plot(time_s, body_moments_Nm[:, 1], label=r"$\tau_y$ (Pitch)", color=COLORS["mlp"])
    axes[1].plot(time_s, body_moments_Nm[:, 2], label=r"$\tau_z$ (Yaw)", color=COLORS["gru"])
    axes[1].set_ylabel(r"Moments $\tau$ [Nm]")
    axes[1].set_xlabel("Time [s]")
    axes[1].legend(loc="best", ncol=3)

    if profile != "report":
        fig.suptitle("Control Effort: Collective Thrust and Moments")

    return save_figure(fig, output_dir, "control_effort", formats)


def _plot_rotor_speeds(
    output_dir: Path,
    time_s: np.ndarray,
    applied_omega_rad_s: np.ndarray,
    saturation_flags: np.ndarray | None,
    profile: str,
    formats: list[str],
) -> list[str]:
    """B8: Plot rotor angular speeds, highlighting saturation in red."""
    fig, ax = plt.subplots()

    colors = [COLORS["real"], COLORS["mlp"], COLORS["gru"], COLORS["lstm"]]
    for rotor_idx in range(applied_omega_rad_s.shape[1]):
        ax.plot(
            time_s,
            applied_omega_rad_s[:, rotor_idx],
            label=f"Rotor {rotor_idx + 1}",
            color=colors[rotor_idx % len(colors)]
        )

    # Highlight saturation intervals in red
    if saturation_flags is not None:
        any_saturated = np.any(saturation_flags, axis=1)
        # Find contiguous saturated regions
        in_sat = False
        start_t = 0.0
        for i, sat in enumerate(any_saturated):
            t = time_s[i]
            if sat and not in_sat:
                in_sat = True
                start_t = t
            elif not sat and in_sat:
                in_sat = False
                ax.axvspan(start_t, t, color=COLORS["failure"], alpha=0.15, label="Saturation" if "Saturation" not in ax.get_legend_handles_labels()[1] else "")
        if in_sat:  # Close final interval
            ax.axvspan(start_t, time_s[-1], color=COLORS["failure"], alpha=0.15, label="Saturation" if "Saturation" not in ax.get_legend_handles_labels()[1] else "")

    if profile != "report":
        ax.set_title("Rotor Angular Speeds")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel(r"Angular Speed $\omega$ [rad/s]")
    ax.legend(loc="best", ncol=2)

    return save_figure(fig, output_dir, "rotor_speeds", formats)


def _plot_neural_outer_force(
    output_dir: Path,
    time_s: np.ndarray,
    desired_force_W_N: np.ndarray,
    desired_force_clipped_W_N: np.ndarray | None,
    profile: str,
    formats: list[str],
) -> list[str]:
    """B9: Plot requested external force components vs clipped force."""
    fig, axes = plt.subplots(3, 1, sharex=True)
    labels = ("Fx [N]", "Fy [N]", "Fz [N]")

    for idx, ax in enumerate(axes):
        ax.plot(time_s, desired_force_W_N[:, idx], "--", color=COLORS["reference"], label="Requested")
        if desired_force_clipped_W_N is not None:
            ax.plot(time_s, desired_force_clipped_W_N[:, idx], color=COLORS["real"], label="Applied (Clipped)")
        ax.set_ylabel(labels[idx])
        ax.legend(loc="best")

    axes[-1].set_xlabel("Time [s]")
    if profile != "report":
        fig.suptitle("Neural External Force (Requested vs Clipped)")

    return save_figure(fig, output_dir, "neural_outer_force", formats)


def _plot_perturbation_response(
    output_dir: Path,
    time_s: np.ndarray,
    wind_W_m_s: np.ndarray,
    position_error_m: np.ndarray,
    profile: str,
    formats: list[str],
) -> list[str]:
    """B10: Plot external perturbations (wind) vs tracking error response."""
    fig, axes = plt.subplots(2, 1, sharex=True)

    # Wind velocity components
    axes[0].plot(time_s, wind_W_m_s[:, 0], label="Wx (East)", color=COLORS["real"])
    axes[0].plot(time_s, wind_W_m_s[:, 1], label="Wy (North)", color=COLORS["mlp"])
    axes[0].plot(time_s, wind_W_m_s[:, 2], label="Wz (Up)", color=COLORS["gru"])
    axes[0].set_ylabel("Wind W_W [m/s]")
    axes[0].legend(loc="best")

    # L2 Error response
    axes[1].plot(time_s, position_error_m, color=COLORS["failure"], label="L2 Error")
    axes[1].set_ylabel("Position Error [m]")
    axes[1].set_xlabel("Time [s]")
    axes[1].legend(loc="best")

    if profile != "report":
        fig.suptitle("Drone Response to Wind Perturbations")

    return save_figure(fig, output_dir, "perturbation_response", formats)


def plot_telemetry(
    telemetry_path: str | os.PathLike[str],
    output_dir: str | os.PathLike[str],
    metrics_path: str | os.PathLike[str] | None = None,
    profile: str = "diagnostic",
    formats: list[str] | None = None,
) -> list[str]:
    """
    Create a set of standard scientific plots from simulator telemetry (English version).
    """
    if formats is None:
        formats = ["png"]

    telemetry = load_json(telemetry_path)
    if not telemetry:
        raise ValueError("Telemetry file does not contain samples.")

    metrics = load_json(metrics_path) if metrics_path else None
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # Apply style profile context
    with use_style(profile):
        # Data extraction
        time_s = np.array([sample["time_s"] for sample in telemetry], dtype=float)
        position_W_m = as_array(telemetry, "state", "position_W_m")
        reference_W_m = as_array(telemetry, "reference", "position_W_m")

        collective_thrust_N = as_array(telemetry, "control", "collective_thrust_N")
        body_moments_Nm = as_array(telemetry, "control", "body_moments_Nm")
        applied_omega_rad_s = as_array(telemetry, "rotors", "applied_omega_rad_s")

        orientation_WB = as_array(telemetry, "state", "orientation_WB")
        angular_velocity_B_rad_s = as_array(telemetry, "state", "angular_velocity_B_rad_s")

        # Saturation flags (can be boolean array)
        saturation_flags_raw = [
            sample.get("rotors", {}).get("saturation_flags") for sample in telemetry
        ]
        if any(f is not None for f in saturation_flags_raw):
            # Fill None or invalid elements with zeros
            cleaned_flags = []
            for f in saturation_flags_raw:
                if f is None or len(f) != 4:
                    cleaned_flags.append([False, False, False, False])
                else:
                    cleaned_flags.append(f)
            saturation_flags = np.array(cleaned_flags, dtype=bool)
        else:
            saturation_flags = None

        # Optional neural forces
        desired_force_W_N = as_array(telemetry, "desired_force_W_N", default=None)
        desired_force_clipped_W_N = as_array(telemetry, "desired_force_clipped_W_N", default=None)

        # Wind perturbation
        wind_W_m_s = as_array(telemetry, "perturbation", "wind_W_m_s", default=None)

        # Derived metrics
        position_error_m = np.linalg.norm(reference_W_m - position_W_m, axis=1)

        # Generate and save core plots (B1, B3, B4, B5, B6, B7, B8)
        generated = []
        generated.extend(_plot_trajectory_xy(output, position_W_m, reference_W_m, metrics, profile, formats))
        generated.extend(_plot_trajectory_3d_static(output, position_W_m, reference_W_m, profile, formats))
        generated.extend(_plot_position_time(output, time_s, position_W_m, reference_W_m, profile, formats))
        generated.extend(_plot_tracking_error(output, time_s, position_error_m, profile, formats))
        generated.extend(_plot_attitude_time(output, time_s, orientation_WB, profile, formats))
        generated.extend(_plot_angular_velocity_time(output, time_s, angular_velocity_B_rad_s, profile, formats))
        generated.extend(_plot_control_effort(output, time_s, collective_thrust_N, body_moments_Nm, profile, formats))
        generated.extend(_plot_rotor_speeds(output, time_s, applied_omega_rad_s, saturation_flags, profile, formats))

        # B9: Neural force plot (only generated if desired force is present in telemetry)
        if desired_force_W_N is not None and not np.all(np.isnan(desired_force_W_N)):
            desired_force_W_N[np.isnan(desired_force_W_N)] = 0.0
            if desired_force_clipped_W_N is not None:
                desired_force_clipped_W_N[np.isnan(desired_force_clipped_W_N)] = 0.0
            generated.extend(_plot_neural_outer_force(output, time_s, desired_force_W_N, desired_force_clipped_W_N, profile, formats))

        # B10: Wind response plot (only if wind is present)
        if wind_W_m_s is not None and not np.all(np.isnan(wind_W_m_s)):
            wind_W_m_s[np.isnan(wind_W_m_s)] = 0.0
            generated.extend(_plot_perturbation_response(output, time_s, wind_W_m_s, position_error_m, profile, formats))

    return generated
