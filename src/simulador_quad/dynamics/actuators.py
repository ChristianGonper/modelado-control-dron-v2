import numpy as np
from typing import List, Tuple
from simulador_quad.core.contracts import RotorParameters

class FirstOrderLagDelay:
    def __init__(self, time_constant_s: float, delay_s: float, dt_s: float):
        self.tau = time_constant_s
        self.delay = delay_s
        self.dt = dt_s
        self.delay_steps = max(0, int(round(delay_s / dt_s)))
        self.buffer = []
        self.state = 0.0
        
    def reset(self, initial_value: float):
        self.state = initial_value
        self.buffer = [initial_value] * self.delay_steps
        
    def step(self, target: float) -> float:
        self.buffer.append(target)
        delayed_target = self.buffer.pop(0)
        
        if self.tau > 1e-6:
            alpha = self.dt / (self.tau + self.dt)
            self.state = self.state + alpha * (delayed_target - self.state)
        else:
            self.state = delayed_target
            
        return self.state

class ActuatorSystem:
    def __init__(self, rotors: List[RotorParameters], dt_s: float):
        self.rotors = rotors
        self.dt = dt_s
        self.num_rotors = len(rotors)
        self.filters = [FirstOrderLagDelay(r.time_constant_s, r.delay_s, dt_s) for r in rotors]
        self.reset(0.0)
        
    def reset(self, initial_omega: float):
        for f in self.filters:
            f.reset(initial_omega)
            
    def compute_applied_forces(self, target_omega_rad_s: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Calcula empuje y par aplicado dados los comandos de omega.
        Devuelve (applied_omega, applied_thrust, applied_torque_scalar, applied_torque_vector_B)
        """
        applied_omega = np.zeros(self.num_rotors)
        applied_thrust = np.zeros(self.num_rotors)
        applied_torque_scalar = np.zeros(self.num_rotors)
        
        # El par vector_B es el torque neto que ejercen todos los rotores juntos
        total_torque_B = np.zeros(3)
        total_thrust_B = np.zeros(3)
        
        for i, (rotor, f) in enumerate(zip(self.rotors, self.filters)):
            # Saturar target opcionalmente antes del filtro, o después.
            # Lo haremos después de saturar target en mixer, pero saturamos aplicado por seguridad.
            cmd_omega = np.clip(target_omega_rad_s[i], 0.0, rotor.omega_max_rad_s)
            
            # Paso del filtro
            curr_omega = f.step(cmd_omega)
            
            # Saturar el estado por seguridad
            curr_omega = np.clip(curr_omega, 0.0, rotor.omega_max_rad_s)
            applied_omega[i] = curr_omega
            
            # T = k_f * omega^2
            T_i = rotor.k_f * curr_omega**2
            applied_thrust[i] = T_i
            
            # Fuerza en B (apunta hacia -Z en FRD, o "arriba" del dron)
            F_i_B = np.array([0.0, 0.0, -T_i])
            total_thrust_B += F_i_B
            
            # Torque por empuje desplazado (r x F)
            torque_pos_B = np.cross(rotor.position_B_m, F_i_B)
            
            # Torque por resistencia aerodinámica del rotor (Q = s * k_m * omega^2)
            # El rotor gira en dirección rotor.turning_direction (1 = CW, -1 = CCW)
            # El torque sobre el dron es opuesto a la dirección de giro
            Q_i = rotor.turning_direction * rotor.k_m * curr_omega**2
            applied_torque_scalar[i] = Q_i
            
            # Como los rotores giran alrededor del eje Z (en cuerpo),
            # El vector de torque de resistencia (drag torque) es en Z.
            # Ojo: si turning_direction es CW (1, o sea que gira en Z positivo FRD),
            # el torque sobre el dron es CCW (-Z).
            # F_z = k_f * w^2. Tau_z = turning_dir * k_m * w^2.
            # M[3, i] = turning_dir * (k_m / k_f)
            # Si turning_dir = 1 (CW), reacción es CCW (Positivo en Z_B si Z_B es Down)
            torque_drag_B = np.array([0.0, 0.0, rotor.turning_direction * rotor.k_m * curr_omega**2])
            
            total_torque_B += torque_pos_B + torque_drag_B
            
        return applied_omega, applied_thrust, applied_torque_scalar, total_torque_B, total_thrust_B
