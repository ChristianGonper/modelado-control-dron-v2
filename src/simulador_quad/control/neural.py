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
from simulador_quad.control.classic import ClassicCascadeController

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


class NeuralPositionController(Controller):
    """
    Controlador hibrido: la red programa ganancias del lazo externo de posicion
    y el lazo interno de actitud permanece como el clasico.
    """
    def __init__(
        self,
        checkpoint_path: str,
        normalization_path: str,
        architecture: str = "mlp",
        sequence_length: int = 20,
        mass_kg: float = 1.0,
        gravity_m_s2: float = 9.81,
        inertia_B_kg_m2: np.ndarray | None = None,
        base_Kp_pos: np.ndarray | None = None,
        base_Kd_pos: np.ndarray | None = None,
        Kp_att: np.ndarray | None = None,
        Kd_att: np.ndarray | None = None,
        max_body_moments_Nm: np.ndarray | None = None,
        multiplier_clip: np.ndarray | None = None,
    ):
        self.architecture = architecture
        self.sequence_length = sequence_length
        self.base_Kp_pos = np.array(base_Kp_pos if base_Kp_pos is not None else [2.0, 2.0, 5.0], dtype=float)
        self.base_Kd_pos = np.array(base_Kd_pos if base_Kd_pos is not None else [1.0, 1.0, 2.0], dtype=float)
        self.multiplier_clip = np.array(multiplier_clip if multiplier_clip is not None else [0.25, 4.0], dtype=float)
        if self.multiplier_clip.shape != (2,) or self.multiplier_clip[0] <= 0.0 or self.multiplier_clip[1] < self.multiplier_clip[0]:
            raise ValueError("multiplier_clip must be [min_positive, max] with max >= min")

        inertia = np.eye(3) if inertia_B_kg_m2 is None else inertia_B_kg_m2
        self.classic_inner = ClassicCascadeController(
            mass_kg,
            gravity_m_s2,
            inertia,
            Kp_pos=self.base_Kp_pos,
            Kd_pos=self.base_Kd_pos,
            Kp_att=Kp_att,
            Kd_att=Kd_att,
            max_body_moments_Nm=max_body_moments_Nm,
        )

        self.normalizer = Normalizer.load(normalization_path)
        input_dim = len(self.normalizer.mean_x)
        output_dim = 6

        config_path = Path(checkpoint_path).parent.parent / "config.yaml"
        config = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

        if "input_dim" in config and config["input_dim"] != input_dim:
            raise ValueError(f"Input dim mismatch: model config has {config['input_dim']}, but normalizer has {input_dim}")
        if "output_dim" in config and config["output_dim"] != output_dim:
            raise ValueError(f"Output dim mismatch: model config has {config['output_dim']}, expected {output_dim}")

        self.model = build_model(architecture, input_dim, output_dim, config)
        self.model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
        self.model.eval()

        self.window = deque(maxlen=sequence_length)
        self.last_gain_multipliers = np.ones(6)
        self.last_Kp_pos = self.base_Kp_pos.copy()
        self.last_Kd_pos = self.base_Kd_pos.copy()
        self.reset()

    def _predict_gain_multipliers(self, obs_state: VehicleState, reference: TrajectoryReference) -> np.ndarray:
        x = build_feature_vector(
            obs_state.position_W_m,
            obs_state.velocity_W_m_s,
            obs_state.orientation_WB,
            obs_state.angular_velocity_B_rad_s,
            reference.position_W_m,
            reference.velocity_W_m_s,
            reference.acceleration_W_m_s2,
            reference.yaw_rad,
        )
        x_norm = self.normalizer.normalize_x(torch.tensor(x, dtype=torch.float32))

        if self.architecture == "mlp":
            model_input = x_norm.unsqueeze(0)
        else:
            self.window.append(x_norm)
            while len(self.window) < self.sequence_length:
                self.window.appendleft(x_norm)
            model_input = torch.stack(list(self.window)).unsqueeze(0)

        with torch.no_grad():
            y_norm = self.model(model_input).squeeze(0)

        log_multipliers = self.normalizer.denormalize_y(y_norm).numpy()
        multipliers = np.exp(log_multipliers)
        return np.clip(multipliers, self.multiplier_clip[0], self.multiplier_clip[1])

    def compute_control(self, time_s: float, obs_state: VehicleState, reference: TrajectoryReference) -> ControlCommand:
        multipliers = self._predict_gain_multipliers(obs_state, reference)
        kp_pos = self.base_Kp_pos * multipliers[:3]
        kd_pos = self.base_Kd_pos * multipliers[3:6]

        self.last_gain_multipliers = multipliers
        self.last_Kp_pos = kp_pos
        self.last_Kd_pos = kd_pos

        return self.classic_inner.compute_control_with_position_gains(obs_state, reference, kp_pos, kd_pos)

    def reset(self):
        self.window.clear()
        self.last_gain_multipliers = np.ones(6)
        self.last_Kp_pos = self.base_Kp_pos.copy()
        self.last_Kd_pos = self.base_Kd_pos.copy()
