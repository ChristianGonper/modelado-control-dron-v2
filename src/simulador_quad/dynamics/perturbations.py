import numpy as np
from typing import Tuple
from simulador_quad.core.attitude import world_to_body, body_to_world

def compute_linear_drag(
    velocity_W_m_s: np.ndarray,
    wind_velocity_W_m_s: np.ndarray,
    orientation_WB: np.ndarray,
    linear_drag_coefficient: np.ndarray
) -> np.ndarray:
    """
    Calcula la fuerza de drag lineal en el sistema del mundo (ENU).
    linear_drag_coefficient puede ser un escalar o un vector [3,] en cuerpo (FRD).
    """
    v_rel_W = velocity_W_m_s - wind_velocity_W_m_s
    v_rel_B = world_to_body(orientation_WB, v_rel_W)
    
    F_drag_B = -linear_drag_coefficient * v_rel_B
    F_drag_W = body_to_world(orientation_WB, F_drag_B)
    
    return F_drag_W

class WindModel:
    def __init__(self, constant_wind_W_m_s: np.ndarray):
        self.constant_wind = constant_wind_W_m_s
        
    def get_wind(self, time_s: float) -> np.ndarray:
        # Viento constante por ahora
        return self.constant_wind

class ObservationNoise:
    def __init__(
        self, 
        pos_std_m: float = 0.0, 
        vel_std_m_s: float = 0.0, 
        seed: int = 42
    ):
        self.pos_std = pos_std_m
        self.vel_std = vel_std_m_s
        self.rng = np.random.default_rng(seed)
        
    def apply_noise(
        self, 
        position_W_m: np.ndarray, 
        velocity_W_m_s: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Añade ruido gaussiano a las observaciones de posición y velocidad.
        """
        pos_noise = self.rng.normal(0.0, self.pos_std, size=3)
        vel_noise = self.rng.normal(0.0, self.vel_std, size=3)
        
        return position_W_m + pos_noise, velocity_W_m_s + vel_noise
