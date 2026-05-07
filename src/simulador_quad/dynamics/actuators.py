import numpy as np
from typing import List, Tuple
from simulador_quad.core.contracts import RotorParameters, RotorAppliedState

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
        
        if self.tau > 0.0:
            alpha = 1.0 - np.exp(-self.dt / self.tau)
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
            
    def compute_applied_forces(self, target_omega_rad_s: np.ndarray) -> Tuple[RotorAppliedState, np.ndarray, np.ndarray]:
        """
        Calcula empuje y par aplicado dados los comandos de omega.
        Devuelve (rotor_applied_state, total_torque_B, total_thrust_B)
        """
        applied_omega = np.zeros(self.num_rotors)
        applied_thrust = np.zeros(self.num_rotors)
        applied_torque_scalar = np.zeros(self.num_rotors)
        applied_rpm = np.zeros(self.num_rotors)
        saturation_flags = np.zeros(self.num_rotors, dtype=bool)
        
        total_torque_B = np.zeros(3)
        total_thrust_B = np.zeros(3)
        
        for i, (rotor, f) in enumerate(zip(self.rotors, self.filters)):
            cmd_omega = np.clip(target_omega_rad_s[i], 0.0, rotor.omega_max_rad_s)
            
            # Paso del filtro (lag y retardo)
            curr_omega = f.step(cmd_omega)
            
            # Flags de saturación (si el filtro pide más de lo físicamente posible)
            if curr_omega >= rotor.omega_max_rad_s - 1e-3:
                saturation_flags[i] = True
            
            curr_omega = np.clip(curr_omega, 0.0, rotor.omega_max_rad_s)
            applied_omega[i] = curr_omega
            applied_rpm[i] = curr_omega * 60.0 / (2.0 * np.pi)
            
            T_i = rotor.k_f * curr_omega**2
            applied_thrust[i] = T_i
            
            F_i_B = np.array([0.0, 0.0, -T_i])
            total_thrust_B += F_i_B
            
            torque_pos_B = np.cross(rotor.position_B_m, F_i_B)
            
            Q_i = rotor.turning_direction * rotor.k_m * curr_omega**2
            applied_torque_scalar[i] = Q_i
            
            torque_drag_B = np.array([0.0, 0.0, Q_i])
            
            total_torque_B += torque_pos_B + torque_drag_B
            
        applied_state = RotorAppliedState(
            applied_omega_rad_s=applied_omega,
            applied_thrust_N=applied_thrust,
            applied_torque_Nm=applied_torque_scalar,
            rotor_speed_rpm=applied_rpm,
            saturation_flags=saturation_flags
        )
            
        return applied_state, total_torque_B, total_thrust_B
