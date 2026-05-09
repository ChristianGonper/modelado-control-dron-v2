"""
Arquitecturas de red (MLP, GRU, LSTM) para control.
"""

import torch
import torch.nn as nn

class MLPControllerNet(nn.Module):
    """Multi-Layer Perceptron para control instantaneo."""
    def __init__(self, input_dim: int, output_dim: int = 4, hidden_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
    
    def forward(self, x):
        # x shape: [batch, input_dim]
        return self.net(x)

class GRUControllerNet(nn.Module):
    """Gated Recurrent Unit para control secuencial."""
    def __init__(self, input_dim: int, output_dim: int = 4, hidden_dim: int = 64, num_layers: int = 1):
        super().__init__()
        self.gru = nn.GRU(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
    
    def forward(self, x):
        # x shape: [batch, seq_len, input_dim]
        out, _ = self.gru(x)
        # Tomamos el ultimo estado de la secuencia: [batch, hidden_dim]
        out = out[:, -1, :]
        return self.fc(out)

class LSTMControllerNet(nn.Module):
    """Long Short-Term Memory para control secuencial."""
    def __init__(self, input_dim: int, output_dim: int = 4, hidden_dim: int = 64, num_layers: int = 1):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
    
    def forward(self, x):
        # x shape: [batch, seq_len, input_dim]
        out, _ = self.lstm(x)
        # Tomamos el ultimo estado de la secuencia: [batch, hidden_dim]
        out = out[:, -1, :]
        return self.fc(out)

def build_model(architecture: str, input_dim: int, output_dim: int = 4, config: dict = None):
    """Factory para construir modelos."""
    config = config or {}
    hidden_dim = config.get("hidden_dim", 64)
    num_layers = config.get("num_layers", 1)
    
    if architecture == "mlp":
        return MLPControllerNet(input_dim, output_dim, hidden_dim)
    elif architecture == "gru":
        return GRUControllerNet(input_dim, output_dim, hidden_dim, num_layers)
    elif architecture == "lstm":
        return LSTMControllerNet(input_dim, output_dim, hidden_dim, num_layers)
    else:
        raise ValueError(f"Unknown architecture: {architecture}")
