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
            M[1, i] = -y                            # Momento de alabeo (roll)
            M[2, i] = x                             # Momento de cabeceo (pitch)
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
        
        # Priorizar momentos frente al empuje
        # T_req = T_thrust_part + T_moment_part
        T_moment_part = self.M_inv @ np.array([0.0, moments_Nm[0], moments_Nm[1], moments_Nm[2]])
        
        # Cada rotor i debe cumplir: 0 <= T_thrust_i + T_moment_part_i <= T_max_i
        # Como T_thrust_i = thrust_N / 4 (para un quad simétrico), buscamos el mejor thrust_N
        # Pero para ser más generales (no asumir simetría perfecta en M_inv):
        # T_thrust_part = self.M_inv @ [thrust_N, 0, 0, 0]^T
        
        # Simplificación robusta: Calculamos los márgenes permitidos para el componente de empuje colectivo
        # en cada rotor una vez restado el componente de momento.
        T_thrust_part_req = self.M_inv @ np.array([thrust_N, 0.0, 0.0, 0.0])
        
        # Ajustamos T_thrust_part_req para que T_req esté en [T_min, T_max]
        # Para cada rotor i: T_min_i - T_moment_part_i <= T_thrust_part_i <= T_max_i - T_moment_part_i
        T_thrust_min_allowed = T_min - T_moment_part
        T_thrust_max_allowed = T_max - T_moment_part
        
        # Si T_thrust_max_allowed < T_thrust_min_allowed para algún rotor, los momentos son físicamente
        # imposibles de alcanzar con esos límites. En ese caso, saturamos momentos.
        if np.any(T_thrust_max_allowed < T_thrust_min_allowed):
            # Escalar momentos hacia abajo para que quepan (provisional)
            # Por ahora, simplemente clipamos T_req al final.
            pass
            
        # Clipamos la parte de empuje rotor a rotor
        T_thrust_part_actual = np.clip(T_thrust_part_req, T_thrust_min_allowed, T_thrust_max_allowed)
        
        T_req = T_thrust_part_actual + T_moment_part
        
        # Saturación estricta final por errores numéricos
        T_req = np.clip(T_req, T_min, T_max)
        
        # Convertir a omega
        omega_cmd = np.zeros(4)
        for i, r in enumerate(self.rotors):
            if T_req[i] > 0:
                omega_cmd[i] = np.sqrt(T_req[i] / r.k_f)
                
        return omega_cmd
