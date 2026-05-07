from __future__ import annotations

import json
import os
from typing import Any

import numpy as np


def load_json(path: str | os.PathLike[str]) -> Any:
    """Load JSON data from a file."""
    with open(path, "r") as f:
        return json.load(f)


def as_array(samples: list[dict[str, Any]], section: str, field: str) -> np.ndarray:
    """
    Extract a nested field from a list of telemetry samples as a NumPy array.
    
    Args:
        samples: List of telemetry dictionaries.
        section: First-level key (e.g., 'state', 'control').
        field: Second-level key (e.g., 'position_W_m').
        
    Returns:
        np.ndarray: Extracted data as a float array.
    """
    return np.array([sample[section][field] for sample in samples], dtype=float)
