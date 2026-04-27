import numpy as np
from typing import List
from simulador_quad.core.contracts import RotorParameters

class QuadcopterMixer:
    """
    Mezclador para cuadricóptero. Convierte comandos (T, tau_x, tau_y, tau_z) 
    en velocidades angulares objetivo (omega) para cada rotor.
    Prioriza actitud frente a empuje colectivo si hay saturación.
    """
    def __init__(self, rotors: List[RotorParameters]):
        self.num_rotors = len(rotors)
        assert self.num_rotors == 4, "QuadcopterMixer requires exactly 4 rotors"
        self.rotors = rotors
        
        # Construir matriz de asignación (Allocation matrix M)
        # T_i = k_f * omega_i^2
        # Q_i = s_i * k_m * omega_i^2
        # F_z = sum(T_i)  (como magnitud de empuje)
        # tau_x = sum(y_i * T_i)
        # tau_y = sum(-x_i * T_i)
        # tau_z = sum(-s_i * k_m/k_f * T_i)
        # 
        # M @ [T_1, T_2, T_3, T_4]^T = [F_z, tau_x, tau_y, tau_z]^T
        
        M = np.zeros((4, 4))
        for i, r in enumerate(rotors):
            x, y, _ = r.position_B_m
            # Columna i:
            M[0, i] = 1.0                           # Empuje colectivo
            M[1, i] = y                             # Momento de alabeo (roll)
            M[2, i] = -x                            # Momento de cabeceo (pitch)
            M[3, i] = -r.turning_direction * (r.k_m / r.k_f) # Momento de guiñada (yaw)
            
        self.M = M
        try:
            self.M_inv = np.linalg.inv(M)
        except np.linalg.LinAlgError:
            raise ValueError("La configuración de rotores no es invertible.")
            
    def compute_rotor_commands(self, thrust_N: float, moments_Nm: np.ndarray) -> np.ndarray:
        """
        Devuelve target_omega_rad_s [4,].
        Prioriza los momentos frente al empuje si hay saturación.
        """
        # Comando deseado
        cmd = np.array([thrust_N, moments_Nm[0], moments_Nm[1], moments_Nm[2]])
        
        # Empujes por rotor requeridos
        T_req = self.M_inv @ cmd
        
        # Límite superior por rotor
        T_max = np.array([r.k_f * r.omega_max_rad_s**2 for r in self.rotors])
        
        # Límite inferior por rotor (no pueden tirar)
        T_min = np.zeros(4)
        
        # Preservar actitud: 
        # T_req = T_req_thrust + T_req_moments
        # T_req_thrust = M_inv @ [thrust, 0, 0, 0]^T
        # T_req_moments = M_inv @ [0, tau_x, tau_y, tau_z]^T
        
        # En la práctica simple, si un rotor excede el límite, desplazamos todos 
        # sumando o restando un offset de empuje para mantener las diferencias (los momentos).
        max_violation = np.max(T_req - T_max)
        min_violation = np.min(T_req - T_min)
        
        if max_violation > 0:
            T_req -= max_violation
        if min_violation < 0:
            T_req -= min_violation
            
        # Saturación estricta al final por seguridad
        T_req = np.clip(T_req, T_min, T_max)
        
        # Convertir a omega
        omega_cmd = np.zeros(4)
        for i, r in enumerate(self.rotors):
            if T_req[i] > 0:
                omega_cmd[i] = np.sqrt(T_req[i] / r.k_f)
                
        return omega_cmd
