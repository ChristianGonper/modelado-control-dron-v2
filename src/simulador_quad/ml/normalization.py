"""
Normalizacion de entradas y salidas para el entrenamiento.
"""

import json
import torch
import numpy as np

class Normalizer:
    """
    Calcula y aplica normalizacion (media/desviacion) a tensores.
    Garantiza que val/test/ood no contaminan los estadisticos.
    """
    def __init__(self, epsilon: float = 1e-8):
        self.mean_x = None
        self.std_x = None
        self.mean_y = None
        self.std_y = None
        self.epsilon = epsilon
        self.feature_names = None
        self.target_names = None
        self.feature_version = None
    
    def fit(self, dataset, feature_names=None, target_names=None, feature_version="v1"):
        """
        Calcula media y desviacion de entradas y salidas.
        Se espera que el dataset sea el split 'train'.
        """
        all_x = []
        all_y = []
        
        # Extraer todos los tensores del dataset
        for i in range(len(dataset)):
            x, y = dataset[i]
            all_x.append(x)
            all_y.append(y)
        
        X = torch.stack(all_x)
        Y = torch.stack(all_y)
        
        # Calcular media y desviacion sobre todas las dimensiones excepto la ultima (features/targets)
        # Esto funciona tanto para [N, D] como para [N, L, D]
        reduction_dims = tuple(range(X.ndim - 1))
        self.mean_x = X.mean(dim=reduction_dims)
        self.std_x = X.std(dim=reduction_dims) + self.epsilon
        
        reduction_dims_y = tuple(range(Y.ndim - 1))
        self.mean_y = Y.mean(dim=reduction_dims_y)
        self.std_y = Y.std(dim=reduction_dims_y) + self.epsilon
        
        self.feature_names = feature_names
        self.target_names = target_names
        self.feature_version = feature_version
    
    def normalize_x(self, x: torch.Tensor) -> torch.Tensor:
        if self.mean_x is None:
            raise ValueError("Normalizer must be fitted before use")
        return (x - self.mean_x) / self.std_x

    def normalize_y(self, y: torch.Tensor) -> torch.Tensor:
        if self.mean_y is None:
            raise ValueError("Normalizer must be fitted before use")
        return (y - self.mean_y) / self.std_y

    def denormalize_y(self, y_norm: torch.Tensor) -> torch.Tensor:
        if self.mean_y is None:
            raise ValueError("Normalizer must be fitted before use")
        return (y_norm * self.std_y) + self.mean_y

    def to(self, device: str):
        """Mueve los estadisticos a CPU/CUDA para usar el normalizador junto al modelo."""
        if self.mean_x is not None:
            self.mean_x = self.mean_x.to(device)
        if self.std_x is not None:
            self.std_x = self.std_x.to(device)
        if self.mean_y is not None:
            self.mean_y = self.mean_y.to(device)
        if self.std_y is not None:
            self.std_y = self.std_y.to(device)
        return self

    def save(self, path: str):
        """Guarda estadisticos en JSON."""
        data = {
            "feature_version": self.feature_version,
            "feature_names": self.feature_names,
            "target_names": self.target_names,
            "epsilon": self.epsilon,
            "mean_x": self.mean_x.tolist(),
            "std_x": self.std_x.tolist(),
            "mean_y": self.mean_y.tolist(),
            "std_y": self.std_y.tolist()
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def load(cls, path: str):
        """Carga estadisticos desde JSON."""
        with open(path, "r") as f:
            data = json.load(f)
        
        norm = cls(epsilon=data["epsilon"])
        norm.feature_version = data["feature_version"]
        norm.feature_names = data["feature_names"]
        norm.target_names = data["target_names"]
        norm.mean_x = torch.tensor(data["mean_x"], dtype=torch.float32)
        norm.std_x = torch.tensor(data["std_x"], dtype=torch.float32)
        norm.mean_y = torch.tensor(data["mean_y"], dtype=torch.float32)
        norm.std_y = torch.tensor(data["std_y"], dtype=torch.float32)
        return norm
