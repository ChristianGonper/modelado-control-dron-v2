from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _load_json(path: str | os.PathLike[str]) -> Any:
    with open(path, "r") as f:
        return json.load(f)


def _as_array(samples: list[dict[str, Any]], section: str, field: str) -> np.ndarray:
    return np.array([sample[section][field] for sample in samples], dtype=float)


def _save(fig: plt.Figure, output_dir: Path, filename: str) -> str:
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
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(reference_W_m[:, 0], reference_W_m[:, 1], "--", label="Referencia")
    ax.plot(position_W_m[:, 0], position_W_m[:, 1], label="Estado")
    ax.scatter(position_W_m[0, 0], position_W_m[0, 1], s=30, label="Inicio")
    ax.scatter(position_W_m[-1, 0], position_W_m[-1, 1], s=30, label="Fin")
    ax.set_title("Trayectoria en plano XY mundo")
    ax.set_xlabel("X_W Este [m]")
    ax.set_ylabel("Y_W Norte [m]")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    ax.legend()
    if metrics:
        rmse = metrics.get("position_rmse_m")
        if rmse is not None:
            ax.text(
                0.02,
                0.98,
                f"RMSE posicion: {rmse:.3f} m",
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
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    labels = ("X_W Este [m]", "Y_W Norte [m]", "Z_W arriba [m]")
    for idx, ax in enumerate(axes):
        ax.plot(time_s, reference_W_m[:, idx], "--", label="Referencia")
        ax.plot(time_s, position_W_m[:, idx], label="Estado")
        ax.set_ylabel(labels[idx])
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best")
    axes[-1].set_xlabel("Tiempo [s]")
    fig.suptitle("Posicion frente a referencia")
    return _save(fig, output_dir, "position_time.png")


def _plot_tracking_error(output_dir: Path, time_s: np.ndarray, position_error_m: np.ndarray) -> str:
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(time_s, position_error_m)
    ax.set_title("Error de seguimiento de posicion")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("||p_ref - p|| [m]")
    ax.grid(True, alpha=0.3)
    return _save(fig, output_dir, "tracking_error.png")


def _plot_rotor_speeds(output_dir: Path, time_s: np.ndarray, applied_omega_rad_s: np.ndarray) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    for rotor_idx in range(applied_omega_rad_s.shape[1]):
        ax.plot(time_s, applied_omega_rad_s[:, rotor_idx], label=f"Rotor {rotor_idx + 1}")
    ax.set_title("Velocidades de rotor aplicadas")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Omega [rad/s]")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", ncols=2)
    return _save(fig, output_dir, "rotor_speeds.png")


def _plot_control_effort(
    output_dir: Path,
    time_s: np.ndarray,
    collective_thrust_N: np.ndarray,
    body_moments_Nm: np.ndarray,
) -> str:
    effort = np.abs(collective_thrust_N) + np.linalg.norm(body_moments_Nm, axis=1)
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    axes[0].plot(time_s, collective_thrust_N)
    axes[0].set_ylabel("T [N]")
    axes[0].set_title("Comando de control")
    axes[1].plot(time_s, body_moments_Nm[:, 0], label="tau_x")
    axes[1].plot(time_s, body_moments_Nm[:, 1], label="tau_y")
    axes[1].plot(time_s, body_moments_Nm[:, 2], label="tau_z")
    axes[1].set_ylabel("Momentos [Nm]")
    axes[1].legend(loc="best")
    axes[2].plot(time_s, effort)
    axes[2].set_ylabel("|T| + ||tau||")
    axes[2].set_xlabel("Tiempo [s]")
    for ax in axes:
        ax.grid(True, alpha=0.3)
    return _save(fig, output_dir, "control_effort.png")


def plot_telemetry(
    telemetry_path: str | os.PathLike[str],
    output_dir: str | os.PathLike[str],
    metrics_path: str | os.PathLike[str] | None = None,
) -> list[str]:
    """Create standard PNG figures from exported simulator telemetry."""
    telemetry = _load_json(telemetry_path)
    if not telemetry:
        raise ValueError("Telemetry file does not contain samples.")

    metrics = _load_json(metrics_path) if metrics_path else None
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    time_s = np.array([sample["time_s"] for sample in telemetry], dtype=float)
    position_W_m = _as_array(telemetry, "state", "position_W_m")
    reference_W_m = _as_array(telemetry, "reference", "position_W_m")
    collective_thrust_N = np.array(
        [sample["control"]["collective_thrust_N"] for sample in telemetry], dtype=float
    )
    body_moments_Nm = _as_array(telemetry, "control", "body_moments_Nm")
    applied_omega_rad_s = _as_array(telemetry, "rotors", "applied_omega_rad_s")
    position_error_m = np.linalg.norm(reference_W_m - position_W_m, axis=1)

    return [
        _plot_trajectory_xy(output, position_W_m, reference_W_m, metrics),
        _plot_position_time(output, time_s, position_W_m, reference_W_m),
        _plot_tracking_error(output, time_s, position_error_m),
        _plot_rotor_speeds(output, time_s, applied_omega_rad_s),
        _plot_control_effort(output, time_s, collective_thrust_N, body_moments_Nm),
    ]
