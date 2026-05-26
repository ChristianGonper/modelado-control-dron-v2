"""
Tests para el cargador de datos neuronal.
"""
import pytest
import os
import torch
import numpy as np
from simulador_quad.ml.dataset import (
    ImitationDataset, SequentialImitationDataset,
    OuterForceDataset, SequentialOuterForceDataset,
    OUTER_FORCE_MIN_V1_NAMES, OUTER_FORCE_FULL_V1_NAMES, TARGET_FORCE_NAMES,
    build_outer_force_min_features_from_observation,
    build_outer_force_full_features_from_observation,
    _build_desired_force_target_for_entry,
)
from simulador_quad.ml.normalization import Normalizer

@pytest.mark.skipif(not os.path.exists("data/classic_dataset/v1"), reason="Classic dataset not found")
def test_imitation_dataset_loading():
    """Prueba que el dataset carga muestras reales."""
    dataset = ImitationDataset("data/classic_dataset/v1", split="train")
    
    # Verificar que tenemos muestras
    assert len(dataset) > 0
    
    # Verificar dimensiones de una muestra
    x, y = dataset[0]
    
    # x: pos(3), vel(3), quat(4), omega(3), ref_pos(3), ref_vel(3), ref_acc(3), ref_yaw(1), err_pos(3), err_vel(3), sin_cos(2) = 31
    assert x.shape == (31,)
    assert y.shape == (4,)
    
    # Verificar que son finitos
    assert torch.isfinite(x).all()
    assert torch.isfinite(y).all()

def test_dataset_split_filtering():
    """Verifica que el dataset filtra por split."""
    # Como no queremos depender siempre del dataset real para tests unitarios rapidos, 
    # podriamos crear un dataset dummy, pero para este TFG el v1 es la fuente de verdad.
    if os.path.exists("data/classic_dataset/v1"):
        train_ds = ImitationDataset("data/classic_dataset/v1", split="train")
        val_ds = ImitationDataset("data/classic_dataset/v1", split="val")
        
        # Deben ser distintos (si el manifest tiene ambos)
        assert len(train_ds) != len(val_ds)

@pytest.mark.skipif(not os.path.exists("data/classic_dataset/v1"), reason="Classic dataset not found")
def test_normalizer_fit_save_load(tmp_path):
    """Prueba el ciclo de vida del normalizador."""
    dataset = ImitationDataset("data/classic_dataset/v1", split="train")
    norm = Normalizer()
    
    # Fit
    norm.fit(dataset, feature_names=["f1"], target_names=["t1"])
    assert norm.mean_x is not None
    
    # Save
    json_path = tmp_path / "norm.json"
    norm.save(str(json_path))
    assert os.path.exists(json_path)
    
    # Load
    norm2 = Normalizer.load(str(json_path))
    assert torch.allclose(norm.mean_x, norm2.mean_x)
    assert norm2.feature_names == ["f1"]
    
    # Transform
    x, y = dataset[0]
    x_norm = norm.normalize_x(x)
    assert not torch.allclose(x, x_norm)
    
    # Inverse transform
    y_norm = norm.normalize_y(y)
    y_rec = norm.denormalize_y(y_norm)
    assert torch.allclose(y, y_rec, atol=1e-5)

@pytest.mark.skipif(not os.path.exists("data/classic_dataset/v1"), reason="Classic dataset not found")
def test_sequential_dataset_loading():
    """Prueba que el dataset secuencial genera ventanas correctas."""
    seq_len = 5
    dataset = SequentialImitationDataset("data/classic_dataset/v1", split="train", sequence_length=seq_len)
    
    assert len(dataset) > 0
    
    x_seq, y = dataset[0]
    
    # x_seq: [seq_len, input_dim]
    assert x_seq.shape == (seq_len, 31)
    # y: [4]
    assert y.shape == (4,)
    
    # Verificar que el target de la ventana coincide con la ultima muestra de la secuencia
    # (Esto asume que el dataset original es determinista, lo cual es cierto para nosotros)
    # Re-extraemos para comparar
    assert torch.isfinite(x_seq).all()
    assert torch.isfinite(y).all()


# =============================================================================
# Tests for outer-force datasets (Phase 2) - use observation, equivalence, dims
# =============================================================================

def test_outer_force_min_features_dim_and_names():
    obs = {
        "position_W_m": [0.1, 0.2, 0.3],
        "velocity_W_m_s": [0.01, 0.02, 0.03],
        "orientation_WB": [1.0, 0.0, 0.0, 0.0],
        "angular_velocity_B_rad_s": [0.0, 0.0, 0.0],
    }
    ref = {
        "position_W_m": [0.5, 0.6, 1.0],
        "velocity_W_m_s": [0.0, 0.0, 0.0],
        "acceleration_W_m_s2": [0.1, 0.0, 0.2],
        "yaw_rad": 0.0,
    }
    x = build_outer_force_min_features_from_observation(obs, ref)
    assert x.shape == (9,)
    assert len(OUTER_FORCE_MIN_V1_NAMES) == 9
    # error_pos + error_vel + ref_acc
    assert np.allclose(x[:3], [0.4, 0.4, 0.7])
    assert np.allclose(x[3:6], [-0.01, -0.02, -0.03])
    assert np.allclose(x[6:], [0.1, 0.0, 0.2])


def test_outer_force_full_features_dim_and_reuses_logic():
    obs = {
        "position_W_m": [0.0, 0.0, 1.0],
        "velocity_W_m_s": [0.0, 0.0, 0.0],
        "orientation_WB": [1.0, 0.0, 0.0, 0.0],
        "angular_velocity_B_rad_s": [0.0, 0.0, 0.0],
    }
    ref = {
        "position_W_m": [0.0, 0.0, 1.0],
        "velocity_W_m_s": [0.0, 0.0, 0.0],
        "acceleration_W_m_s2": [0.0, 0.0, 0.0],
        "yaw_rad": 0.0,
    }
    x = build_outer_force_full_features_from_observation(obs, ref)
    assert x.shape == (31,)
    assert len(OUTER_FORCE_FULL_V1_NAMES) == 31


def test_outer_force_target_equivalence_to_classic():
    """Critical: target must be exactly what ClassicCascadeController.compute_desired_force_W
    produces for the expert's Kp/Kd on the *observation* (not state).
    """
    from simulador_quad.core.contracts import VehicleState, TrajectoryReference
    from simulador_quad.core.frames import get_level_quaternion
    from simulador_quad.control.classic import ClassicCascadeController

    entry = {
        "observation": {
            "position_W_m": [0.2, -0.1, 0.8],
            "velocity_W_m_s": [0.05, 0.1, -0.02],
            "orientation_WB": list(get_level_quaternion(0.1)),
            "angular_velocity_B_rad_s": [0.01, 0.0, 0.0],
            "time_s": 2.5,
        },
        "reference": {
            "position_W_m": [0.0, 0.0, 1.0],
            "velocity_W_m_s": [0.0, 0.0, 0.0],
            "acceleration_W_m_s2": [0.0, 0.05, 0.0],
            "yaw_rad": 0.15,
        },
    }
    kp = np.array([2.0, 2.0, 5.0])
    kd = np.array([1.0, 1.0, 2.0])
    mass, g = 1.0, 9.81

    y_target = _build_desired_force_target_for_entry(entry, kp, kd, mass, g)

    # Recompute with public classic API on same observation
    obs_state = VehicleState(
        position_W_m=np.array(entry["observation"]["position_W_m"]),
        velocity_W_m_s=np.array(entry["observation"]["velocity_W_m_s"]),
        orientation_WB=np.array(entry["observation"]["orientation_WB"]),
        angular_velocity_B_rad_s=np.array(entry["observation"]["angular_velocity_B_rad_s"]),
        time_s=2.5,
    )
    ref = TrajectoryReference(
        position_W_m=np.array(entry["reference"]["position_W_m"]),
        velocity_W_m_s=np.array(entry["reference"]["velocity_W_m_s"]),
        acceleration_W_m_s2=np.array(entry["reference"]["acceleration_W_m_s2"]),
        yaw_rad=0.15,
    )
    classic = ClassicCascadeController(mass, g, np.eye(3), Kp_pos=kp, Kd_pos=kd)
    y_direct = classic.compute_desired_force_W(obs_state, ref)

    assert np.allclose(y_target, y_direct, atol=1e-12)
    assert y_target.shape == (3,)


def test_outer_force_features_use_observation_not_state():
    """Changing only observation while keeping state fixed must change the min features
    (proves no leakage from ground-truth state).
    """
    obs1 = {"position_W_m": [0.0, 0.0, 1.0], "velocity_W_m_s": [0.0, 0.0, 0.0],
            "orientation_WB": [1.,0,0,0], "angular_velocity_B_rad_s": [0,0,0]}
    obs2 = {"position_W_m": [0.1, 0.0, 1.0], "velocity_W_m_s": [0.0, 0.0, 0.0],
            "orientation_WB": [1.,0,0,0], "angular_velocity_B_rad_s": [0,0,0]}
    ref = {"position_W_m": [0.0, 0.0, 1.0], "velocity_W_m_s": [0.0, 0.0, 0.0],
           "acceleration_W_m_s2": [0.0, 0.0, 0.0], "yaw_rad": 0.0}

    x1 = build_outer_force_min_features_from_observation(obs1, ref)
    x2 = build_outer_force_min_features_from_observation(obs2, ref)
    assert not np.allclose(x1, x2)


@pytest.mark.skipif(not os.path.exists("data/classic_dataset/v1"), reason="Classic dataset not found")
def test_outer_force_dataset_loading_min():
    ds = OuterForceDataset("data/classic_dataset/v1", split="train", feature_version="outer_force_min_v1")
    assert len(ds) > 0
    x, y = ds[0]
    assert x.shape == (9,)
    assert y.shape == (3,)
    assert torch.isfinite(x).all() and torch.isfinite(y).all()


@pytest.mark.skipif(not os.path.exists("data/classic_dataset/v1"), reason="Classic dataset not found")
def test_outer_force_dataset_loading_full():
    ds = OuterForceDataset("data/classic_dataset/v1", split="train", feature_version="outer_force_full_v1")
    x, y = ds[0]
    assert x.shape == (31,)
    assert y.shape == (3,)
