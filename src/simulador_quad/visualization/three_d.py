from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import plotly.graph_objects as go


def _load_json(path: str | os.PathLike[str]) -> Any:
    with open(path, "r") as f:
        return json.load(f)


def _as_array(samples: list[dict[str, Any]], section: str, field: str) -> np.ndarray:
    return np.array([sample[section][field] for sample in samples], dtype=float)


def export_trajectory_viewer_html(
    telemetry_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    metrics_path: str | os.PathLike[str] | None = None,
) -> str:
    """
    Generate an interactive 3D HTML visualization of the quadcopter trajectory.
    """
    telemetry = _load_json(telemetry_path)
    if not telemetry:
        raise ValueError("Telemetry file is empty or invalid.")

    metrics = _load_json(metrics_path) if metrics_path else {}
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Extract data
    pos_actual = _as_array(telemetry, "state", "position_W_m")
    pos_ref = _as_array(telemetry, "reference", "position_W_m")

    fig = go.Figure()

    # Reference trajectory
    fig.add_trace(
        go.Scatter3d(
            x=pos_ref[:, 0],
            y=pos_ref[:, 1],
            z=pos_ref[:, 2],
            mode="lines",
            name="Referencia",
            line=dict(color="blue", width=2, dash="dash"),
        )
    )

    # Actual trajectory
    fig.add_trace(
        go.Scatter3d(
            x=pos_actual[:, 0],
            y=pos_actual[:, 1],
            z=pos_actual[:, 2],
            mode="lines",
            name="Trayectoria Real",
            line=dict(color="red", width=4),
        )
    )

    # Start and End points
    fig.add_trace(
        go.Scatter3d(
            x=[pos_actual[0, 0]],
            y=[pos_actual[0, 1]],
            z=[pos_actual[0, 2]],
            mode="markers",
            name="Inicio",
            marker=dict(size=6, color="green", symbol="diamond"),
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[pos_actual[-1, 0]],
            y=[pos_actual[-1, 1]],
            z=[pos_actual[-1, 2]],
            mode="markers",
            name="Fin",
            marker=dict(size=6, color="black", symbol="square"),
        )
    )

    # Axis labels and layout
    # In ENU: X=East, Y=North, Z=Up
    scenario_name = metrics.get("metadata", {}).get("scenario_name")
    display_name = scenario_name if scenario_name else Path(telemetry_path).stem
    
    fig.update_layout(
        title=f"Visor de Trayectoria 3D - {display_name}",
        scene=dict(
            xaxis_title="X Mundo [Este, m]",
            yaxis_title="Y Mundo [Norte, m]",
            zaxis_title="Z Mundo [Arriba, m]",
            aspectmode="data",  # Scale axes equally
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    # Basic metrics summary in annotation if available
    summary_text = ""
    if metrics:
        rmse = metrics.get("position_rmse_m")
        term = metrics.get("termination_reason", "Desconocido")
        duration = metrics.get("duration_s", 0.0)
        summary_text = (
            f"<b>Resumen de Simulacion</b><br>"
            f"Terminacion: {term}<br>"
            f"Duracion: {duration:.2f} s<br>"
        )
        if rmse is not None:
            summary_text += f"RMSE Posicion: {rmse:.4f} m"

    if summary_text:
        fig.add_annotation(
            text=summary_text,
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.98,
            y=0.02,
            align="right",
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="gray",
            borderwidth=1,
        )

    fig.write_html(str(output))
    return str(output)
