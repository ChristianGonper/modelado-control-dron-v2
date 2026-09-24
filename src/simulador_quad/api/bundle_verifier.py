"""
Verification and discovery of the NeuroFlight demo bundle.
Validates the presence, size, and SHA-256 hashes of:
- 4 frozen classic PIDs
- 3 outer-force neural checkpoints (MLP, GRU, LSTM)
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


DEFAULT_BUNDLE_DIR = Path("data/neuroflight_bundle")

# Archivos que el paquete de demostración debe declarar y verificar.
REQUIRED_BUNDLE_FILES = [
    "pids/pid_hold_v1.yaml",
    "pids/pid_circle_v1.yaml",
    "pids/pid_lissajous_v1.yaml",
    "pids/pid_waypoint_v1.yaml",
    "neural_control/outer_force_mlp_min_v1/checkpoints/mlp_best.pt",
    "neural_control/outer_force_mlp_min_v1/normalization.json",
    "neural_control/outer_force_mlp_min_v1/config.yaml",
    "neural_control/outer_force_gru_min_v1/checkpoints/gru_best.pt",
    "neural_control/outer_force_gru_min_v1/normalization.json",
    "neural_control/outer_force_gru_min_v1/config.yaml",
    "neural_control/outer_force_lstm_min_v1/checkpoints/lstm_best.pt",
    "neural_control/outer_force_lstm_min_v1/normalization.json",
    "neural_control/outer_force_lstm_min_v1/config.yaml",
]


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class BundleVerifier:
    def __init__(self, bundle_dir: Path = DEFAULT_BUNDLE_DIR):
        self.bundle_dir = bundle_dir.resolve()
        self.manifest_path = self.bundle_dir / "bundle_manifest.json"
        self._cached_status: Optional[Dict[str, Any]] = None

    def verify(self) -> Dict[str, Any]:
        """
        Verifies the integrity of the bundle against bundle_manifest.json.
        Returns a detailed status dictionary.
        """
        if not self.manifest_path.exists():
            return {
                "status": "missing",
                "valid": False,
                "error": f"Manifest not found at {self.manifest_path}",
                "bundle_dir": str(self.bundle_dir),
                "files_checked": 0,
                "missing_files": [],
                "hash_mismatches": [],
            }

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as exc:
            return {
                "status": "corrupt",
                "valid": False,
                "error": f"Failed to parse manifest: {exc}",
                "bundle_dir": str(self.bundle_dir),
                "files_checked": 0,
                "missing_files": [],
                "hash_mismatches": [],
            }

        declared = manifest.get("files")
        if not isinstance(declared, list) or len(declared) == 0:
            return {
                "status": "missing",
                "valid": False,
                "error": "El manifiesto no declara archivos. El paquete de demostración no está instalado.",
                "bundle_dir": str(self.bundle_dir),
                "files_checked": 0,
                "missing_files": list(REQUIRED_BUNDLE_FILES),
                "hash_mismatches": [],
            }

        files_checked = 0
        missing_files = []
        hash_mismatches = []
        declared_paths = set()

        for entry in declared:
            rel_path = entry.get("rel_path")
            expected_sha = entry.get("sha256")
            expected_bytes = entry.get("bytes")
            if not rel_path:
                hash_mismatches.append({"path": "", "reason": "Entrada de manifiesto sin rel_path"})
                continue
            declared_paths.add(rel_path.replace("\\", "/"))

            full_path = self.bundle_dir / rel_path
            files_checked += 1

            if not full_path.exists():
                missing_files.append(rel_path)
                continue

            if expected_bytes is not None and full_path.stat().st_size != expected_bytes:
                hash_mismatches.append({
                    "path": rel_path,
                    "reason": f"Size mismatch: expected {expected_bytes}, got {full_path.stat().st_size}",
                })
                continue

            if expected_sha is not None:
                actual_sha = compute_sha256(full_path)
                if actual_sha != expected_sha:
                    hash_mismatches.append({
                        "path": rel_path,
                        "reason": f"SHA256 mismatch: expected {expected_sha[:10]}..., got {actual_sha[:10]}...",
                    })

        for required in REQUIRED_BUNDLE_FILES:
            if required not in declared_paths and required not in missing_files:
                missing_files.append(required)

        valid = (len(missing_files) == 0 and len(hash_mismatches) == 0 and files_checked > 0)
        status = {
            "status": "ok" if valid else ("degraded" if files_checked and len(missing_files) < files_checked else "missing"),
            "valid": valid,
            "bundle_version": manifest.get("bundle_version", "1.0.0"),
            "bundle_dir": str(self.bundle_dir),
            "files_checked": files_checked,
            "missing_files": missing_files,
            "hash_mismatches": hash_mismatches,
        }
        self._cached_status = status
        return status

    def artifact_identity(self) -> Dict[str, Any]:
        """Hashes y versión del paquete verificado, para guardarlos con cada corrida."""
        status = self.verify()
        files: list = []
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                for entry in manifest.get("files") or []:
                    files.append({
                        "rel_path": entry.get("rel_path"),
                        "sha256": entry.get("sha256"),
                        "bytes": entry.get("bytes"),
                        "type": entry.get("type"),
                    })
            except Exception:
                files = []
        return {
            "bundle_version": status.get("bundle_version"),
            "bundle_dir": status.get("bundle_dir"),
            "valid": bool(status.get("valid")),
            "files": files,
        }

    def _require_verified_file(self, relative: str) -> Path:
        status = self._cached_status if self._cached_status is not None else self.verify()
        if not status.get("valid"):
            detail = status.get("error") or (
                f"faltan {status.get('missing_files') or []} "
                f"y hay {len(status.get('hash_mismatches') or [])} hash distinto"
            )
            raise FileNotFoundError(
                "El paquete de NeuroFlight en "
                f"{self.bundle_dir} no superó la verificación ({detail}). "
                "Instálelo con tools/package_demo_artifacts.py. "
                "La carpeta regenerada no sustituye al paquete."
            )
        path = self.bundle_dir / relative
        if not path.exists():
            raise FileNotFoundError(f"Archivo del paquete no encontrado tras la verificación: {path}")
        return path

    def get_pid_path(self, family: str) -> Path:
        """Returns path to the frozen PID for the given family."""
        family_clean = family.lower()
        if family_clean == "line":
            family_clean = "waypoint"
        elif family_clean == "lemniscate":
            family_clean = "lissajous"

        filename = f"pid_{family_clean}_v1.yaml"
        return self._require_verified_file(f"pids/{filename}")

    def get_neural_paths(self, architecture: str) -> Tuple[Path, Path, Path]:
        """
        Returns (checkpoint_path, normalization_path, config_path) for outer_force architecture.
        architecture in ['mlp', 'gru', 'lstm'].
        """
        arch_clean = architecture.lower()
        model_name = f"outer_force_{arch_clean}_min_v1"
        ckpt_name = f"{arch_clean}_best.pt"

        ckpt = self._require_verified_file(f"neural_control/{model_name}/checkpoints/{ckpt_name}")
        norm = self._require_verified_file(f"neural_control/{model_name}/normalization.json")
        cfg = self._require_verified_file(f"neural_control/{model_name}/config.yaml")
        return ckpt, norm, cfg
