"""Load and fingerprint frozen PID configurations for dataset tooling."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import yaml

FROZEN_PID_FAMILIES = ("hold", "circle", "lissajous", "waypoint")

GAIN_KEYS = ("Kp_pos", "Kd_pos", "Kp_att", "Kd_att", "max_body_moments_Nm")


def extract_controller_gains(pid_data: dict[str, Any]) -> dict[str, Any]:
    gains: dict[str, Any] = {}
    for key in GAIN_KEYS:
        if key in pid_data and pid_data[key] is not None:
            gains[key] = pid_data[key]
    return gains


def pid_gains_fingerprint(pid_data: dict[str, Any]) -> str:
    payload = json.dumps(extract_controller_gains(pid_data), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _find_pid_files(pids_dir: str, family: str) -> list[str]:
    matches = []
    for name in os.listdir(pids_dir):
        if name.startswith(f"pid_{family}_") and name.endswith(".yaml"):
            matches.append(os.path.join(pids_dir, name))
    return sorted(matches)


def load_frozen_pid_family(pids_dir: str, family: str) -> tuple[dict[str, Any], str]:
    if family not in FROZEN_PID_FAMILIES:
        raise ValueError(f"Unknown PID family '{family}'. Expected one of {FROZEN_PID_FAMILIES}.")

    if not os.path.isdir(pids_dir):
        raise FileNotFoundError(f"Frozen PID directory not found: {pids_dir}")

    matches = _find_pid_files(pids_dir, family)
    if not matches:
        raise FileNotFoundError(
            f"No frozen PID file found for family '{family}' in {pids_dir}. "
            f"Expected exactly one file matching pid_{family}_*.yaml."
        )
    if len(matches) > 1:
        raise ValueError(
            f"Ambiguous frozen PID for family '{family}' in {pids_dir}: found {len(matches)} files "
            f"({', '.join(os.path.basename(p) for p in matches)}). Expected exactly one."
        )

    pid_path = matches[0]
    with open(pid_path, "r", encoding="utf-8") as file:
        pid_data = yaml.safe_load(file)
    if not isinstance(pid_data, dict):
        raise ValueError(f"Invalid PID YAML at {pid_path}: expected mapping, got {type(pid_data).__name__}.")

    gains = extract_controller_gains(pid_data)
    for key in ("Kp_pos", "Kd_pos", "Kp_att", "Kd_att"):
        if key not in gains:
            raise ValueError(f"Frozen PID at {pid_path} is missing required gain '{key}'.")

    return pid_data, pid_path


def load_all_frozen_pids(
    pids_dir: str,
    required_families: tuple[str, ...] | list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    families = tuple(required_families) if required_families is not None else FROZEN_PID_FAMILIES
    pid_configs: dict[str, dict[str, Any]] = {}
    for family in families:
        pid_data, _ = load_frozen_pid_family(pids_dir, family)
        pid_configs[family] = pid_data
    return pid_configs


def controller_gains_match(
    controller: dict[str, Any],
    pid_data: dict[str, Any],
    transfer_family: str,
) -> bool:
    if controller.get("pid_family") != transfer_family:
        return False
    expected = extract_controller_gains(pid_data)
    for key, value in expected.items():
        if controller.get(key) != value:
            return False
    return True