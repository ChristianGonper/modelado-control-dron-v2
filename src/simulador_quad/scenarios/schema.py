# Esquema básico para la validación (opcional) o estructura de datos de escenarios
from dataclasses import dataclass
from typing import Dict, Any, List
import numpy as np

@dataclass
class ScenarioConfig:
    name: str
    vehicle: Dict[str, Any]
    initial_state: Dict[str, Any]
    trajectory: Dict[str, Any]
    controller: Dict[str, Any]
    perturbations: Dict[str, Any]
    timing: Dict[str, Any]
    termination: Dict[str, Any]
    output: Dict[str, Any]
    seed: int = 42
