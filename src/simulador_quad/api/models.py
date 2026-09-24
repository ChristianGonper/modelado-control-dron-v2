"""
Pydantic schemas and contracts for the NeuroFlight API.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TrajectoryFamily(str, Enum):
    HOLD = "hold"
    CIRCLE = "circle"
    LISSAJOUS = "lissajous"
    WAYPOINT = "waypoint"
    LEMNISCATE = "lemniscate"
    COMPOSITE = "composite"


class WindConfig(BaseModel):
    magnitude_m_s: float = Field(0.0, description="Velocidad horizontal del viento en m/s (máx 1.4)")
    direction_deg: float = Field(0.0, description="Dirección del viento en grados (0° = hacia +X Este)")


class CompositeSegmentConfig(BaseModel):
    type: str = Field(..., description="Tipo de tramo: hold, circle, lissajous, waypoint, lemniscate")
    duration: Optional[float] = Field(None, gt=0.0, description="Duración en segundos (obligatorio para continuos)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parámetros específicos del tramo")


class MissionConfigRequest(BaseModel):
    mode: str = Field("simple", description="'simple' para familia única, 'composite' para tramos")
    family: TrajectoryFamily = Field(TrajectoryFamily.CIRCLE, description="Familia de trayectoria")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parámetros de la trayectoria simple")
    segments: Optional[List[CompositeSegmentConfig]] = Field(None, description="Tramos de la misión compuesta (2 a 4)")
    transition_speed: float = Field(0.8, gt=0.0, le=2.0, description="Velocidad de transición entre tramos (m/s)")
    wind: WindConfig = Field(default_factory=WindConfig, description="Perturbación de viento horizontal")
    seed: int = Field(42, description="Semilla determinista")


class ValidationResponse(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    initial_position: List[float] = Field(default_factory=lambda: [0.0, 0.0, 1.5])
    selected_pid_family: Optional[str] = None
    selected_pid_explanation: Optional[str] = None


class PathPoint(BaseModel):
    t: float
    x: float
    y: float
    z: float
    is_transition: bool = False
    segment_index: int = 0


class PreviewResponse(BaseModel):
    points: List[List[float]] = Field(description="Muestras 3D [x, y, z]")
    time_series: List[float] = Field(description="Tiempos t correspondientes")
    is_transition: List[bool] = Field(description="Indicador de tramo de transición automática")
    segment_indices: List[int] = Field(description="Índice de tramo al que pertenece cada muestra")
    initial_position: List[float]
    bounds: Dict[str, float]
    total_duration_s: float
    accessibility_summary: str
    selected_pid_family: str
    selected_pid_explanation: str


class ControllerProgress(BaseModel):
    status: str = Field("pending", description="pending, running, completed, error, cancelled")
    progress_pct: float = 0.0
    error_message: Optional[str] = None
    termination_reason: Optional[str] = None
    duration_s: Optional[float] = None
    position_mae_m: Optional[float] = None
    position_max_err_m: Optional[float] = None


class RunStatusResponse(BaseModel):
    run_id: str
    state: str = Field(..., description="idle, preparing, running, completed, partial, interrupted, error")
    progress_pct: float = 0.0
    controllers: Dict[str, ControllerProgress]
    created_at: str


class ControllerSummary(BaseModel):
    controller_id: str
    name: str
    family: str
    status: str
    termination_reason: str
    duration_s: float
    position_mae_m: Optional[float] = None
    position_max_err_m: Optional[float] = None
    sample_count: int = 0
    is_interrupted: bool = False


class RunResultsResponse(BaseModel):
    run_id: str
    timestamp: str
    mission_mode: str
    mission_family: str
    selected_pid: str
    selected_pid_explanation: str
    effective_config: Dict[str, Any]
    seed: int
    summaries: Dict[str, ControllerSummary]
    nominal_path: List[List[float]]
    runs_trajectory: Dict[str, List[Dict[str, Any]]]
    is_partial: bool
    artifact_identity: Dict[str, Any] = Field(
        default_factory=dict,
        description="Versión del paquete y hashes SHA-256 de los artefactos usados",
    )


class TelemetrySeriesResponse(BaseModel):
    run_id: str
    controller_id: str
    time_s: List[float]
    signals: Dict[str, List[Optional[float]]]
    units: Dict[str, str]
    groups: Dict[str, str]
