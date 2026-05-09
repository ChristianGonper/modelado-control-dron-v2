"""
Controlador neuronal para integracion en el simulador.
"""

import torch
import numpy as np
import yaml
from pathlib import Path
from collections import deque
from simulador_quad.control.contract import Controller
from simulador_quad.core.contracts import ControlCommand, VehicleState, TrajectoryReference
from simulador_quad.ml.models import build_model
from simulador_quad.ml.normalization import Normalizer
from simulador_quad.ml.dataset import build_feature_vector

class NeuralController(Controller):
    """
    Implementa el contrato de Controller usando una red neuronal entrenada.
    """
    def __init__(self, 
                 checkpoint_path: str, 
                 normalization_path: str, 
                 architecture: str = "mlp", 
                 sequence_length: int = 20,
                 clip_to_classic_limits: bool = True,
                 mass_kg: float = 1.0,
                 gravity_m_s2: float = 9.81,
                 max_moments_Nm: np.ndarray = np.array([10.0, 10.0, 2.0])):
        self.architecture = architecture
        self.sequence_length = sequence_length
        self.clip_to_classic_limits = clip_to_classic_limits
        self.mass = mass_kg
        self.g = gravity_m_s2
        self.max_moments = max_moments_Nm
        
        # Cargar normalizador
        self.normalizer = Normalizer.load(normalization_path)
        
        # Cargar modelo
        # Deducir input_dim del normalizador cargado
        input_dim = len(self.normalizer.mean_x)
        output_dim = 4
        
        # Podriamos intentar cargar hidden_dim del config.yaml si esta al lado del checkpoint
        config_path = Path(checkpoint_path).parent.parent / "config.yaml"
        config = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        
        # Validacion de consistencia
        if "input_dim" in config and config["input_dim"] != input_dim:
            raise ValueError(f"Input dim mismatch: model config has {config['input_dim']}, but normalizer has {input_dim}")

        self.model = build_model(architecture, input_dim, output_dim, config)
        self.model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
        self.model.eval()
        
        # Estado recurrente para GRU/LSTM
        self.window = deque(maxlen=sequence_length)
        self.reset()
    
    def compute_control(self, time_s: float, obs_state: VehicleState, reference: TrajectoryReference) -> ControlCommand:
        """Ejecuta inferencia y devuelve comando de control."""
        # 1. Construir features
        x = build_feature_vector(
            obs_state.position_W_m,
            obs_state.velocity_W_m_s,
            obs_state.orientation_WB,
            obs_state.angular_velocity_B_rad_s,
            reference.position_W_m,
            reference.velocity_W_m_s,
            reference.acceleration_W_m_s2,
            reference.yaw_rad
        )
        
        # 2. Normalizar
        x_norm = self.normalizer.normalize_x(torch.tensor(x, dtype=torch.float32))
        
        # 3. Preparar entrada segun arquitectura
        if self.architecture == "mlp":
            model_input = x_norm.unsqueeze(0) # [1, input_dim]
        else:
            self.window.append(x_norm)
            # Si no tenemos suficiente historia, rellenamos con la primera muestra
            while len(self.window) < self.sequence_length:
                self.window.appendleft(x_norm)
            
            model_input = torch.stack(list(self.window)).unsqueeze(0) # [1, seq_len, input_dim]
        
        # 4. Inferencia
        with torch.no_grad():
            y_norm = self.model(model_input).squeeze(0) # [4]
        
        # 5. Desnormalizar
        y = self.normalizer.denormalize_y(y_norm).numpy()
        
        thrust = float(y[0])
        moments = y[1:4]
        
        # 6. Clipping (opcional)
        if self.clip_to_classic_limits:
            # Limites compatibles con el controlador clasico efectivo
            max_thrust = self.mass * self.g * 2.5
            thrust = np.clip(thrust, 0.0, max_thrust)
            moments = np.clip(moments, -self.max_moments, self.max_moments)
            
        return ControlCommand(thrust, moments)

    def reset(self):
        """Limpia estado interno (importante para GRU/LSTM)."""
        self.window.clear()
