"""
Tests basicos de importacion para el modulo neuronal.
"""
import torch
import pytest

def test_torch_available():
    """Verifica que torch esta instalado y es funcional."""
    x = torch.ones(3)
    assert x.sum() == 3.0

def test_ml_imports():
    """Verifica que los modulos del paquete ml son importables."""
    from simulador_quad.ml.dataset import ImitationDataset
    from simulador_quad.ml.models import MLPControllerNet, build_model
    from simulador_quad.ml.normalization import Normalizer
    from simulador_quad.ml.train import train_model
    from simulador_quad.ml.evaluate import evaluate_model
    
    assert True

def test_neural_control_import():
    """Verifica que el controlador neuronal es importable."""
    from simulador_quad.control.neural import NeuralController
    assert True
