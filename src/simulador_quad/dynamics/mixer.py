import numpy as np
from typing import List
from simulador_quad.core.contracts import RotorParameters, RotorCommand

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
        # F_thrust_B = [0, 0, -sum(T_i)]
        # tau_x = sum(-y_i * T_i)
        # tau_y = sum(x_i * T_i)
        # tau_z = sum(s_i * (k_m/k_f) * T_i)
        # 
        # M @ [T_1, T_2, T_3, T_4]^T = [F_thrust_mag, tau_x, tau_y, tau_z]^T
        
        M = np.zeros((4, 4))
        for i, r in enumerate(rotors):
            x, y, _ = r.position_B_m
            # Columna i:
            M[0, i] = 1.0                                   # Empuje colectivo (magnitud)
            M[1, i] = -y                                    # Momento de alabeo (roll): tau_x = -y*T
            M[2, i] = x                                     # Momento de cabeceo (pitch): tau_y = x*T
            M[3, i] = r.turning_direction * (r.k_m / r.k_f) # Momento de guiñada (yaw): tau_z = s*(km/kf)*T
            
        self.M = M
        try:
            self.M_inv = np.linalg.inv(M)
        except np.linalg.LinAlgError:
            raise ValueError("La configuración de rotores no es invertible.")
            
    def compute_rotor_commands(self, thrust_N: float, moments_Nm: np.ndarray) -> RotorCommand:
        """
        Devuelve RotorCommand con target_thrust_N y target_omega_rad_s.
        Prioriza los momentos frente al empuje si hay saturación.
        """
        # ... (lógica de cálculo igual hasta T_req)
        T_min = np.zeros(4)
        T_max = np.array([r.k_f * r.omega_max_rad_s**2 for r in self.rotors])
        
        # Priorizar momentos frente al empuje
        T_moment_part = self.M_inv @ np.array([0.0, moments_Nm[0], moments_Nm[1], moments_Nm[2]])
        T_thrust_part_req = self.M_inv @ np.array([thrust_N, 0.0, 0.0, 0.0])
        
        delta_min = np.max(T_min - T_thrust_part_req - T_moment_part)
        delta_max = np.min(T_max - T_thrust_part_req - T_moment_part)
        
        degraded = False
        if delta_max >= delta_min:
            delta = np.clip(0.0, delta_min, delta_max)
            if delta < -1e-6 or delta > 1e-6:
                degraded = True
            T_req = T_thrust_part_req + delta + T_moment_part
        else:
            degraded = True
            T_target_thrust = (T_min + T_max) / 2.0
            k = 1.0
            for i in range(4):
                if T_moment_part[i] > 1e-9:
                    k = min(k, (T_max[i] - T_target_thrust[i]) / T_moment_part[i])
                elif T_moment_part[i] < -1e-9:
                    k = min(k, (T_min[i] - T_target_thrust[i]) / T_moment_part[i])
            T_req = T_target_thrust + k * T_moment_part
        
        T_req = np.clip(T_req, T_min, T_max)
        
        omega_cmd = np.zeros(4)
        for i, r in enumerate(self.rotors):
            if T_req[i] > 0:
                omega_cmd[i] = np.sqrt(T_req[i] / r.k_f)
                
        return RotorCommand(
            target_thrust_N=T_req,
            target_omega_rad_s=omega_cmd,
            degraded_collective_thrust=degraded
        )
