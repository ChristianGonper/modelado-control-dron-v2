"""
Tests para las arquitecturas de red neuronal.
"""
import torch
import pytest
from simulador_quad.ml.models import build_model, MLPControllerNet, GRUControllerNet, LSTMControllerNet

def test_mlp_forward():
    """Verifica el forward de MLP."""
    batch_size = 8
    input_dim = 31
    model = MLPControllerNet(input_dim, output_dim=4)
    
    x = torch.randn(batch_size, input_dim)
    y = model(x)
    
    assert y.shape == (batch_size, 4)

def test_gru_forward():
    """Verifica el forward de GRU."""
    batch_size = 8
    seq_len = 20
    input_dim = 31
    model = GRUControllerNet(input_dim, output_dim=4)
    
    x = torch.randn(batch_size, seq_len, input_dim)
    y = model(x)
    
    assert y.shape == (batch_size, 4)

def test_lstm_forward():
    """Verifica el forward de LSTM."""
    batch_size = 8
    seq_len = 20
    input_dim = 31
    model = LSTMControllerNet(input_dim, output_dim=4)
    
    x = torch.randn(batch_size, seq_len, input_dim)
    y = model(x)
    
    assert y.shape == (batch_size, 4)

def test_model_factory():
    """Verifica que la factory construye los modelos correctos."""
    mlp = build_model("mlp", 31)
    assert isinstance(mlp, MLPControllerNet)
    
    gru = build_model("gru", 31)
    assert isinstance(gru, GRUControllerNet)
    
    lstm = build_model("lstm", 31)
    assert isinstance(lstm, LSTMControllerNet)
    
    with pytest.raises(ValueError):
        build_model("unknown", 31)
