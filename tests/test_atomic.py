import os
import shutil
import pytest
from pathlib import Path
from simulador_quad.core.fs import atomic_write_directory

def test_atomic_write_directory_success(tmp_path):
    target = tmp_path / "target_dir"

    def write_ok(temp_dir):
        (temp_dir / "file1.txt").write_text("hello")
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "file2.txt").write_text("world")

    atomic_write_directory(str(target), write_ok, overwrite=False)

    assert target.exists()
    assert (target / "file1.txt").read_text() == "hello"
    assert (target / "subdir" / "file2.txt").read_text() == "world"

def test_atomic_write_directory_exists_no_overwrite(tmp_path):
    target = tmp_path / "target_dir"
    target.mkdir()
    (target / "existing.txt").write_text("prior")

    def write_ok(temp_dir):
        (temp_dir / "new.txt").write_text("new")

    with pytest.raises(FileExistsError):
        atomic_write_directory(str(target), write_ok, overwrite=False)

    assert (target / "existing.txt").read_text() == "prior"
    assert not (target / "new.txt").exists()

def test_atomic_write_directory_overwrite(tmp_path):
    target = tmp_path / "target_dir"
    target.mkdir()
    (target / "existing.txt").write_text("prior")
    (target / "residual_dir").mkdir()
    (target / "residual_dir" / "residual.txt").write_text("residual")

    def write_ok(temp_dir):
        (temp_dir / "new.txt").write_text("new")

    atomic_write_directory(str(target), write_ok, overwrite=True)

    assert target.exists()
    assert (target / "new.txt").read_text() == "new"
    assert not (target / "existing.txt").exists()
    assert not (target / "residual_dir").exists()

def test_atomic_write_directory_failure_rollback(tmp_path):
    target = tmp_path / "target_dir"
    target.mkdir()
    (target / "existing.txt").write_text("prior")

    def write_fail(temp_dir):
        (temp_dir / "new.txt").write_text("new")
        raise RuntimeError("simulated write error")

    with pytest.raises(RuntimeError, match="simulated write error"):
        atomic_write_directory(str(target), write_fail, overwrite=True)

    assert target.exists()
    assert (target / "existing.txt").read_text() == "prior"
    assert not (target / "new.txt").exists()


def test_atomic_write_directory_backup_cleanup_failure_is_nonfatal(tmp_path, monkeypatch):
    target = tmp_path / "target_dir"
    target.mkdir()
    (target / "existing.txt").write_text("prior")

    original_rmtree = shutil.rmtree

    def flaky_rmtree(path, *args, **kwargs):
        if Path(path).name.startswith(".tmp_old_"):
            raise OSError("simulated backup cleanup failure")
        return original_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(shutil, "rmtree", flaky_rmtree)

    def write_ok(temp_dir):
        (temp_dir / "new.txt").write_text("new")

    with pytest.warns(RuntimeWarning, match="failed to remove backup"):
        atomic_write_directory(str(target), write_ok, overwrite=True)

    assert (target / "new.txt").read_text() == "new"
    assert not (target / "existing.txt").exists()
    backup_dirs = [p for p in tmp_path.iterdir() if p.name.startswith(".tmp_old_")]
    assert len(backup_dirs) == 1
