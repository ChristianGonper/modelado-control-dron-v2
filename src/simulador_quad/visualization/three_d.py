from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import plotly.graph_objects as go

from .common import as_array, load_json


def export_trajectory_viewer_html(
    telemetry_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    metrics_path: str | os.PathLike[str] | None = None,
) -> str:
    """
    Generate an interactive 3D HTML visualization of the quadcopter trajectory.
    
    The visualization uses ENU (East-North-Up) coordinates for the World frame.
    
    Args:
        telemetry_path: Path to the telemetry JSON file.
        output_path: Path where the HTML file will be saved.
        metrics_path: Optional path to metrics JSON for summary information.
        
    Returns:
        str: Absolute path to the generated HTML file.
    """
    telemetry = load_json(telemetry_path)
    if not telemetry:
        raise ValueError("Telemetry file is empty or invalid.")

    metrics = load_json(metrics_path) if metrics_path else {}
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Extract data
    position_W_m = as_array(telemetry, "state", "position_W_m")
    reference_W_m = as_array(telemetry, "reference", "position_W_m")

    fig = go.Figure()

    # Reference trajectory
    fig.add_trace(
        go.Scatter3d(
            x=reference_W_m[:, 0],
            y=reference_W_m[:, 1],
            z=reference_W_m[:, 2],
            mode="lines",
            name="Referencia",
            line=dict(color="blue", width=2, dash="dash"),
        )
    )

    # Actual trajectory
    fig.add_trace(
        go.Scatter3d(
            x=position_W_m[:, 0],
            y=position_W_m[:, 1],
            z=position_W_m[:, 2],
            mode="lines",
            name="Trayectoria Real",
            line=dict(color="red", width=4),
        )
    )

    # Start and End points for visual reference
    fig.add_trace(
        go.Scatter3d(
            x=[position_W_m[0, 0]],
            y=[position_W_m[0, 1]],
            z=[position_W_m[0, 2]],
            mode="markers",
            name="Inicio",
            marker=dict(size=6, color="green", symbol="diamond"),
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[position_W_m[-1, 0]],
            y=[position_W_m[-1, 1]],
            z=[position_W_m[-1, 2]],
            mode="markers",
            name="Fin",
            marker=dict(size=6, color="black", symbol="square"),
        )
    )

    # Axis labels and layout (Standard ENU: X=East, Y=North, Z=Up)
    scenario_name = metrics.get("metadata", {}).get("scenario_name")
    display_name = scenario_name if scenario_name else Path(telemetry_path).stem
    
    fig.update_layout(
        title=f"Visor de Trayectoria 3D - {display_name}",
        scene=dict(
            xaxis_title="X Mundo [Este, m]",
            yaxis_title="Y Mundo [Norte, m]",
            zaxis_title="Z Mundo [Arriba, m]",
            aspectmode="data",  # Scale axes equally for physical realism
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    # Simulation summary annotation
    summary_text = ""
    if metrics:
        rmse = metrics.get("position_rmse_m")
        term = metrics.get("termination_reason", "Desconocido")
        duration = metrics.get("duration_s", 0.0)
        
        summary_text = (
            f"<b>Resumen de Simulación</b><br>"
            f"Terminación: {term}<br>"
            f"Duración: {duration:.2f} s<br>"
        )
        if rmse is not None:
            summary_text += f"RMSE Posición: {rmse:.4f} m"

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
