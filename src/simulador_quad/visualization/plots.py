from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .common import as_array, load_json


def _save(fig: plt.Figure, output_dir: Path, filename: str) -> str:
    """Save the figure to the output directory with consistent formatting."""
    path = output_dir / filename
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def _plot_trajectory_xy(
    output_dir: Path,
    position_W_m: np.ndarray,
    reference_W_m: np.ndarray,
    metrics: dict[str, Any] | None,
) -> str:
    """
    Plot the 2D trajectory in the horizontal World (XY) plane.
    
    Args:
        output_dir: Directory to save the plot.
        position_W_m: Actual trajectory (N x 3) in World frame [m].
        reference_W_m: Reference trajectory (N x 3) in World frame [m].
        metrics: Dictionary containing simulation metrics (optional).
    """
    fig, ax = plt.subplots(figsize=(7, 6))
    
    # Plot ENU: X is East, Y is North
    ax.plot(reference_W_m[:, 0], reference_W_m[:, 1], "--", color="gray", label="Referencia")
    ax.plot(position_W_m[:, 0], position_W_m[:, 1], color="tab:blue", label="Estado")
    
    # Start and end markers
    ax.scatter(position_W_m[0, 0], position_W_m[0, 1], color="tab:green", s=40, label="Inicio", zorder=5)
    ax.scatter(position_W_m[-1, 0], position_W_m[-1, 1], color="tab:red", s=40, label="Fin", zorder=5)
    
    ax.set_title("Trayectoria en Plano Horizontal (Mundo)")
    ax.set_xlabel("X_W Este [m]")
    ax.set_ylabel("Y_W Norte [m]")
    ax.axis("equal")
    ax.grid(True, alpha=0.3, linestyle=":")
    ax.legend(loc="upper right")
    
    if metrics:
        rmse = metrics.get("position_rmse_m")
        if rmse is not None:
            ax.text(
                0.02,
                0.98,
                f"RMSE Posición: {rmse:.3f} m",
                transform=ax.transAxes,
                va="top",
                bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
            )
            
    return _save(fig, output_dir, "trajectory_xy.png")


def _plot_position_time(
    output_dir: Path,
    time_s: np.ndarray,
    position_W_m: np.ndarray,
    reference_W_m: np.ndarray,
) -> str:
    """
    Plot X, Y, Z positions over time compared to references.
    
    Args:
        output_dir: Directory to save the plot.
        time_s: Time vector [s].
        position_W_m: Actual position in World frame [m].
        reference_W_m: Reference position in World frame [m].
    """
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    labels = ("X_W Este [m]", "Y_W Norte [m]", "Z_W Arriba [m]")
    
    for idx, ax in enumerate(axes):
        ax.plot(time_s, reference_W_m[:, idx], "--", color="gray", label="Referencia")
        ax.plot(time_s, position_W_m[:, idx], color="tab:blue", label="Estado")
        ax.set_ylabel(labels[idx])
        ax.grid(True, alpha=0.3, linestyle=":")
        ax.legend(loc="best")
        
    axes[-1].set_xlabel("Tiempo [s]")
    fig.suptitle("Evolución de la Posición frente a Referencia (Mundo)")
    return _save(fig, output_dir, "position_time.png")


def _plot_tracking_error(output_dir: Path, time_s: np.ndarray, position_error_m: np.ndarray) -> str:
    """Plot the Euclidean position tracking error over time."""
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(time_s, position_error_m, color="tab:red")
    
    ax.set_title("Error de Seguimiento de Posición")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Error L2: ||p_ref - p|| [m]")
    ax.grid(True, alpha=0.3, linestyle=":")
    
    return _save(fig, output_dir, "tracking_error.png")


def _plot_rotor_speeds(output_dir: Path, time_s: np.ndarray, applied_omega_rad_s: np.ndarray) -> str:
    """Plot the angular speeds of the four rotors."""
    fig, ax = plt.subplots(figsize=(9, 5))
    
    colors = ["tab:blue", "tab:orange", "tab:green", "tab:red"]
    for rotor_idx in range(applied_omega_rad_s.shape[1]):
        ax.plot(
            time_s, 
            applied_omega_rad_s[:, rotor_idx], 
            label=f"Rotor {rotor_idx + 1}", 
            color=colors[rotor_idx % len(colors)]
        )
        
    ax.set_title("Velocidades Angulares de los Rotores")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel(r"Velocidad Angular $\omega$ [rad/s]")
    ax.grid(True, alpha=0.3, linestyle=":")
    ax.legend(loc="best", ncol=2)
    
    return _save(fig, output_dir, "rotor_speeds.png")


def _plot_attitude_time(
    output_dir: Path,
    time_s: np.ndarray,
    orientation_WB: np.ndarray,
) -> str:
    """
    Plot Roll, Pitch, and Yaw angles over time.
    
    Args:
        output_dir: Directory to save the plot.
        time_s: Time vector [s].
        orientation_WB: Actual q_WB orientation quaternion [w, x, y, z].
    """
    from simulador_quad.core.attitude import quaternion_to_euler_enu_frd
    
    # Convert q_WB to aircraft angles consistent with the simulator ENU/FRD convention.
    euler_angles_deg = np.array([
        quaternion_to_euler_enu_frd(q) for q in orientation_WB
    ]) * 180.0 / np.pi
    
    roll_deg = euler_angles_deg[:, 0]
    pitch_deg = euler_angles_deg[:, 1]
    yaw_deg = euler_angles_deg[:, 2]
    
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    
    axes[0].plot(time_s, roll_deg, color="tab:blue", label="Roll")
    axes[0].set_ylabel(r"Roll $\phi$ [deg]")
    axes[0].set_title("Actitud del Vehículo (ENU/FRD)")
    
    axes[1].plot(time_s, pitch_deg, color="tab:orange", label="Pitch")
    axes[1].set_ylabel(r"Pitch $\theta$ [deg]")
    
    axes[2].plot(time_s, yaw_deg, color="tab:green", label="Yaw")
    axes[2].set_ylabel(r"Yaw $\psi$ [deg]")
    axes[2].set_xlabel("Tiempo [s]")
    
    for ax in axes:
        ax.grid(True, alpha=0.3, linestyle=":")
        ax.legend(loc="best")
        
    return _save(fig, output_dir, "attitude_time.png")


def _plot_angular_velocity_time(
    output_dir: Path,
    time_s: np.ndarray,
    angular_velocity_B_rad_s: np.ndarray,
) -> str:
    """
    Plot the body angular velocities (p, q, r) over time.
    
    Args:
        output_dir: Directory to save the plot.
        time_s: Time vector [s].
        angular_velocity_B_rad_s: Angular velocity in Body frame [rad/s].
    """
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    
    axes[0].plot(time_s, angular_velocity_B_rad_s[:, 0], color="tab:blue", label="p (Roll rate)")
    axes[0].set_ylabel(r"$p$ [rad/s]")
    axes[0].set_title("Velocidad Angular Absoluta del Vehículo (Cuerpo)")
    
    axes[1].plot(time_s, angular_velocity_B_rad_s[:, 1], color="tab:orange", label="q (Pitch rate)")
    axes[1].set_ylabel(r"$q$ [rad/s]")
    
    axes[2].plot(time_s, angular_velocity_B_rad_s[:, 2], color="tab:green", label="r (Yaw rate)")
    axes[2].set_ylabel(r"$r$ [rad/s]")
    axes[2].set_xlabel("Tiempo [s]")
    
    for ax in axes:
        ax.grid(True, alpha=0.3, linestyle=":")
        ax.legend(loc="best")
        
    return _save(fig, output_dir, "angular_velocity_time.png")


def _plot_control_effort(
    output_dir: Path,
    time_s: np.ndarray,
    collective_thrust_N: np.ndarray,
    body_moments_Nm: np.ndarray,
) -> str:
    """
    Plot the control signals: collective thrust and body moments.
    
    Args:
        output_dir: Directory to save the plot.
        time_s: Time vector [s].
        collective_thrust_N: Total thrust command in Body frame [N].
        body_moments_Nm: Moments (tau_x, tau_y, tau_z) in Body frame [Nm].
    """
    
    fig, axes = plt.subplots(2, 1, figsize=(9, 8), sharex=True)
    
    # Collective Thrust
    axes[0].plot(time_s, collective_thrust_N, color="tab:blue")
    axes[0].set_ylabel(r"Empuje $T$ [N]")
    axes[0].set_title("Esfuerzo de Control: Empuje Colectivo y Momentos")
    
    # Body Moments
    axes[1].plot(time_s, body_moments_Nm[:, 0], label=r"$\tau_x$ (Roll)", alpha=0.8)
    axes[1].plot(time_s, body_moments_Nm[:, 1], label=r"$\tau_y$ (Pitch)", alpha=0.8)
    axes[1].plot(time_s, body_moments_Nm[:, 2], label=r"$\tau_z$ (Yaw)", alpha=0.8)
    axes[1].set_ylabel(r"Momentos $\tau$ [Nm]")
    axes[1].legend(loc="best", ncol=3)

    for ax in axes:
        ax.grid(True, alpha=0.3, linestyle=":")
        
    return _save(fig, output_dir, "control_effort.png")


def plot_telemetry(
    telemetry_path: str | os.PathLike[str],
    output_dir: str | os.PathLike[str],
    metrics_path: str | os.PathLike[str] | None = None,
) -> list[str]:
    """
    Create a set of standard scientific plots from simulator telemetry.
    
    Args:
        telemetry_path: Path to the telemetry JSON file.
        output_dir: Path to the directory where plots will be saved.
        metrics_path: Optional path to the metrics JSON file for extra info.
        
    Returns:
        list[str]: List of absolute paths to the generated figures.
    """
    telemetry = load_json(telemetry_path)
    if not telemetry:
        raise ValueError("Telemetry file does not contain samples.")

    metrics = load_json(metrics_path) if metrics_path else None
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # Data extraction
    time_s = np.array([sample["time_s"] for sample in telemetry], dtype=float)
    position_W_m = as_array(telemetry, "state", "position_W_m")
    reference_W_m = as_array(telemetry, "reference", "position_W_m")
    
    collective_thrust_N = np.array(
        [sample["control"]["collective_thrust_N"] for sample in telemetry], dtype=float
    )
    body_moments_Nm = as_array(telemetry, "control", "body_moments_Nm")
    applied_omega_rad_s = as_array(telemetry, "rotors", "applied_omega_rad_s")
    
    orientation_WB = as_array(telemetry, "state", "orientation_WB")
    angular_velocity_B_rad_s = as_array(telemetry, "state", "angular_velocity_B_rad_s")
    
    # Derived metrics
    position_error_m = np.linalg.norm(reference_W_m - position_W_m, axis=1)

    # Generate and save all plots
    return [
        _plot_trajectory_xy(output, position_W_m, reference_W_m, metrics),
        _plot_position_time(output, time_s, position_W_m, reference_W_m),
        _plot_attitude_time(output, time_s, orientation_WB),
        _plot_angular_velocity_time(output, time_s, angular_velocity_B_rad_s),
        _plot_tracking_error(output, time_s, position_error_m),
        _plot_rotor_speeds(output, time_s, applied_omega_rad_s),
        _plot_control_effort(output, time_s, collective_thrust_N, body_moments_Nm),
    ]
