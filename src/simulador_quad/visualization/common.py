from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np


def load_json(path: str | os.PathLike[str] | None) -> Any:
    """
    Load JSON data from a file.
    Returns None if the path is None or the file does not exist.
    """
    if path is None:
        return None
    p = Path(path)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    return False


def as_array(
    samples: list[dict[str, Any]],
    section: str,
    field: str | None = None,
    default: Any = np.nan,
) -> np.ndarray | None:
    """
    Extract a nested or top-level field from a list of telemetry samples as a NumPy array.

    When ``default`` is ``None`` and every sample lacks the field, returns ``None`` instead
    of an array filled with NaN. Partially missing vector fields are padded with NaN so
    mixed optional telemetry (e.g. wind only in some samples) can be plotted safely.
    """
    data: list[Any] = []
    for sample in samples:
        if field is None:
            val = sample.get(section, default)
        else:
            sec = sample.get(section)
            if not isinstance(sec, dict):
                val = default
            else:
                val = sec.get(field, default)
        data.append(val)

    if default is None and all(_is_missing_value(val) for val in data):
        return None

    fill_value = default if default is not None else np.nan
    reference = next((val for val in data if not _is_missing_value(val)), None)
    if reference is None:
        return None

    if isinstance(reference, (list, tuple, np.ndarray)):
        width = len(reference)
        cleaned = []
        for val in data:
            if _is_missing_value(val):
                cleaned.append([fill_value] * width)
            else:
                cleaned.append(val)
        return np.array(cleaned, dtype=float)

    cleaned = [fill_value if _is_missing_value(val) else val for val in data]
    return np.array(cleaned, dtype=float)
