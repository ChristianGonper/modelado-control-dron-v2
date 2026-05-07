import os
import shutil
import pytest
import pandas as pd
from simulador_quad.datasets.classic import (
    get_dataset_manifest_data, write_dataset_files, PROFILES, FAMILIES
)

def test_manifest_v1_content():
    manifest = get_dataset_manifest_data()
    assert len(manifest) == 150
    
    # Check counts per family
    # hold: 6 geometries * 3 profiles = 18
    # circle: 8 geometries * 6 profiles = 48
    # lissajous: 8 geometries * 6 profiles = 48
    # waypoint: 6 geometries * 6 profiles = 36
    # Total: 18 + 48 + 48 + 36 = 150. Correct.
    
    df = pd.DataFrame(manifest)
    counts = df.groupby("family").size()
    assert counts["hold"] == 18
    assert counts["circle"] == 48
    assert counts["lissajous"] == 48
    assert counts["waypoint"] == 36
    
    # Check uniqueness of scenario_id
    assert len(df["scenario_id"].unique()) == 150

def test_determinism():
    m1 = get_dataset_manifest_data()
    m2 = get_dataset_manifest_data()
    assert m1 == m2

def test_write_dataset(tmp_path):
    output_dir = tmp_path / "v1"
    write_dataset_files("v1", str(output_dir))
    
    assert os.path.exists(output_dir / "manifest.csv")
    assert os.path.exists(output_dir / "README.md")
    
    # Check one YAML
    manifest_df = pd.read_csv(output_dir / "manifest.csv")
    first_path = output_dir / manifest_df.iloc[0]["scenario_path"]
    assert os.path.exists(first_path)
    
    # Verify we can load it and it passes validation
    from simulador_quad.scenarios.loader import load_scenario
    config = load_scenario(str(first_path))
    assert config["name"] == manifest_df.iloc[0]["scenario_id"]
    assert config["vehicle"]["rotors"][0]["omega_max_rad_s"] == 1500.0
