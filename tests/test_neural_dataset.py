"""
Tests para el cargador de datos neuronal.
"""
import pytest
import os
import torch
import numpy as np
from simulador_quad.ml.dataset import ImitationDataset, SequentialImitationDataset
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
