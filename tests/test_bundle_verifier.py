import json
from pathlib import Path

import pytest

from simulador_quad.api.bundle_verifier import BundleVerifier


def test_bundle_verifier_ok():
    verifier = BundleVerifier()
    res = verifier.verify()
    assert res["valid"] is True, f"Bundle validation failed: {res}"
    assert res["status"] == "ok"
    assert res["files_checked"] == 13
    assert len(res["missing_files"]) == 0
    assert len(res["hash_mismatches"]) == 0


def test_bundle_verifier_get_paths():
    verifier = BundleVerifier()
    for fam in ["hold", "circle", "lissajous", "waypoint", "lemniscate"]:
        pid_path = verifier.get_pid_path(fam)
        assert pid_path.exists()

    for arch in ["mlp", "gru", "lstm"]:
        ckpt, norm, cfg = verifier.get_neural_paths(arch)
        assert ckpt.exists()
        assert norm.exists()
        assert cfg.exists()


def test_empty_manifest_is_invalid(tmp_path: Path):
    manifest = tmp_path / "bundle_manifest.json"
    manifest.write_text(json.dumps({"bundle_version": "1.0.0", "files": []}), encoding="utf-8")
    status = BundleVerifier(tmp_path).verify()
    assert status["valid"] is False
    assert status["files_checked"] == 0
    assert status["missing_files"]


def test_loader_does_not_fall_back_to_regenerated_tree(tmp_path: Path):
    manifest = tmp_path / "bundle_manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    verifier = BundleVerifier(tmp_path)
    with pytest.raises(FileNotFoundError) as exc:
        verifier.get_pid_path("hold")
    message = str(exc.value)
    assert "regenerada no sustituye" in message
    assert "data/regenerated" not in message or "no sustituye" in message


def test_artifact_identity_records_hashes():
    identity = BundleVerifier().artifact_identity()
    assert identity["valid"] is True
    assert identity["files"]
    assert all(entry.get("sha256") for entry in identity["files"])
