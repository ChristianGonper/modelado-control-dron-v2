"""
Script to package the minimal demonstration bundle for NeuroFlight.
Collects:
- 4 frozen PIDs (hold, circle, lissajous, waypoint)
- 3 outer-force neural checkpoints (MLP, GRU, LSTM) with config.yaml and normalization.json
- Generates bundle_manifest.json with SHA-256 hashes.
"""

import hashlib
import json
import os
import shutil
from pathlib import Path


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def package_bundle(
    source_root: Path = Path("data/regenerated_2026-09-23"),
    target_root: Path = Path("data/neuroflight_bundle"),
) -> Path:
    target_root.mkdir(parents=True, exist_ok=True)

    manifest_entries = []

    # 1. Frozen PIDs
    pid_src_dir = source_root / "classic_dataset" / "v1" / "pids"
    pid_dst_dir = target_root / "pids"
    pid_dst_dir.mkdir(parents=True, exist_ok=True)

    pids = [
        "pid_hold_v1.yaml",
        "pid_circle_v1.yaml",
        "pid_lissajous_v1.yaml",
        "pid_waypoint_v1.yaml",
    ]
    for pid_name in pids:
        src = pid_src_dir / pid_name
        dst = pid_dst_dir / pid_name
        if not src.exists():
            raise FileNotFoundError(f"Source PID file not found: {src}")
        shutil.copy2(src, dst)
        rel_path = str(dst.relative_to(target_root)).replace("\\", "/")
        manifest_entries.append({
            "rel_path": rel_path,
            "type": "frozen_pid",
            "bytes": dst.stat().st_size,
            "sha256": file_sha256(dst),
        })

    # 2. Outer-Force Neural Checkpoints
    models = [
        ("outer_force_mlp_min_v1", "mlp_best.pt"),
        ("outer_force_gru_min_v1", "gru_best.pt"),
        ("outer_force_lstm_min_v1", "lstm_best.pt"),
    ]
    for model_name, ckpt_name in models:
        src_model_dir = source_root / "neural_control" / model_name
        dst_model_dir = target_root / "neural_control" / model_name
        (dst_model_dir / "checkpoints").mkdir(parents=True, exist_ok=True)

        files_to_copy = [
            (src_model_dir / "checkpoints" / ckpt_name, dst_model_dir / "checkpoints" / ckpt_name, "checkpoint"),
            (src_model_dir / "config.yaml", dst_model_dir / "config.yaml", "model_config"),
            (src_model_dir / "normalization.json", dst_model_dir / "normalization.json", "normalization"),
        ]

        for src_f, dst_f, file_type in files_to_copy:
            if not src_f.exists():
                raise FileNotFoundError(f"Source file not found: {src_f}")
            shutil.copy2(src_f, dst_f)
            rel_path = str(dst_f.relative_to(target_root)).replace("\\", "/")
            manifest_entries.append({
                "rel_path": rel_path,
                "model": model_name,
                "type": file_type,
                "bytes": dst_f.stat().st_size,
                "sha256": file_sha256(dst_f),
            })

    # 3. Write manifest
    bundle_manifest = {
        "bundle_version": "1.0.0",
        "description": "NeuroFlight demo bundle containing 4 frozen classic PIDs and 3 outer-force neural checkpoints",
        "files": manifest_entries,
    }

    manifest_path = target_root / "bundle_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(bundle_manifest, f, indent=2)

    total_bytes = sum(entry["bytes"] for entry in manifest_entries)
    print(f"Packaged {len(manifest_entries)} bundle files into {target_root} (Total: {total_bytes / 1024:.1f} KB)")
    return manifest_path


if __name__ == "__main__":
    package_bundle()
