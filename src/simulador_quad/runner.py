import numpy as np
from typing import Callable, Optional, Dict, Any, Tuple
from simulador_quad.core.contracts import VehicleState, VehicleParameters, ControlCommand, RotorCommand, RotorAppliedState
from simulador_quad.dynamics.rigid_body import rk4_step
from simulador_quad.dynamics.actuators import ActuatorSystem
from simulador_quad.dynamics.mixer import QuadcopterMixer
from simulador_quad.dynamics.perturbations import compute_linear_drag, WindModel, ObservationNoise

class SimulationRunner:
    def __init__(
        self,
        physics_dt_s: float,
        control_dt_s: float,
        telemetry_dt_s: float,
        vehicle_params: VehicleParameters,
        mixer: QuadcopterMixer,
        actuators: ActuatorSystem,
        wind_model: WindModel,
        observation_noise: ObservationNoise,
        max_duration_s: float = 10.0,
        z_min_m: float = 0.0,
        max_position_m: float = 100.0,
        max_velocity_m_s: float = 50.0,
        max_attitude_angle_rad: float = np.pi/2.5 # ~72 deg
    ):
        self.physics_dt_s = physics_dt_s
        self.control_dt_s = control_dt_s
        self.telemetry_dt_s = telemetry_dt_s
        
        self.vehicle_params = vehicle_params
        self.mixer = mixer
        self.actuators = actuators
        self.wind = wind_model
        self.noise = observation_noise
        
        self.max_duration_s = max_duration_s
        self.z_min_m = z_min_m
        self.max_position_m = max_position_m
        self.max_velocity_m_s = max_velocity_m_s
        self.max_attitude_angle_rad = max_attitude_angle_rad
        
    def _check_termination(self, state: VehicleState) -> Tuple[bool, str]:
        # Valores finitos
        if not (np.all(np.isfinite(state.position_W_m)) and 
                np.all(np.isfinite(state.velocity_W_m_s)) and 
                np.all(np.isfinite(state.orientation_WB)) and 
                np.all(np.isfinite(state.angular_velocity_B_rad_s))):
            return True, "Non-finite values in state"
            
        # Z_W < z_min_m
        if state.position_W_m[2] < self.z_min_m:
            return True, "Crash: Z_W < z_min_m"
            
        # Límites de posición
        if np.any(np.abs(state.position_W_m) > self.max_position_m):
            return True, "Out of position bounds"
            
        # Límites de velocidad
        if np.any(np.abs(state.velocity_W_m_s) > self.max_velocity_m_s):
            return True, "Out of velocity bounds"
            
        # Límite de roll/pitch
        # Extraemos inclinación respecto a Z_W
        from simulador_quad.core.attitude import body_to_world
        z_B_W = body_to_world(state.orientation_WB, np.array([0.0, 0.0, 1.0]))
        # angle to vertical: dot_product = cos(theta)
        # z_B en hover FRD (si FRD es front, right, down) -> Z_B = [0,0,1]
        # en ENU (X_E, Y_N, Z_U), Down is [0,0,-1].
        # Wait, en FRD, Z_B apunta hacia abajo del dron. 
        # Si dron está nivelado, Z_B = [0,0,-1] en mundo ENU.
        cos_theta = np.dot(z_B_W, np.array([0.0, 0.0, -1.0]))
        # cos_theta can be > 1 due to numerical issues
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        tilt_angle = np.arccos(cos_theta)
        
        if tilt_angle > self.max_attitude_angle_rad:
            return True, f"Attitude angle exceeded limit ({tilt_angle:.2f} > {self.max_attitude_angle_rad:.2f})"
            
        # Tiempo máximo
        if state.time_s >= self.max_duration_s:
            return True, "Time limit reached"
            
        return False, ""
        
    def run(self, initial_state: VehicleState, controller_func: Callable) -> Dict[str, Any]:
        """
        Ejecuta la simulación.
        controller_func: (time_s, observation_state) -> ControlCommand
        Devuelve el estado final, la causa de terminación y la telemetría.
        """
        state = VehicleState(
            position_W_m=initial_state.position_W_m.copy(),
            velocity_W_m_s=initial_state.velocity_W_m_s.copy(),
            orientation_WB=initial_state.orientation_WB.copy(),
            angular_velocity_B_rad_s=initial_state.angular_velocity_B_rad_s.copy(),
            time_s=initial_state.time_s
        )
        
        self.actuators.reset(0.0)
        
        telemetry = []
        
        time_s = state.time_s
        last_control_time = time_s - self.control_dt_s - 1e-6
        last_telemetry_time = time_s - self.telemetry_dt_s - 1e-6
        
        current_control = ControlCommand(0.0, np.zeros(3))
        current_target_omega = np.zeros(self.mixer.num_rotors)
        
        termination_reason = ""
        
        # Guardar telemetría inicial
        # ... Para simplificar, la telemetría se guarda al principio del bucle si toca
        
        while True:
            # Comprobar fin
            term, reason = self._check_termination(state)
            if term:
                termination_reason = reason
                break
                
            # 1. Telemetry
            if time_s - last_telemetry_time >= self.telemetry_dt_s - 1e-6:
                telemetry.append({
                    "time_s": time_s,
                    "position_W_m": state.position_W_m.copy(),
                    "velocity_W_m_s": state.velocity_W_m_s.copy(),
                    "orientation_WB": state.orientation_WB.copy(),
                    "angular_velocity_B_rad_s": state.angular_velocity_B_rad_s.copy()
                })
                last_telemetry_time = time_s
                
            # 2. Control (ZOH)
            if time_s - last_control_time >= self.control_dt_s - 1e-6:
                # Observación con ruido
                obs_pos, obs_vel = self.noise.apply_noise(state.position_W_m, state.velocity_W_m_s)
                obs_state = VehicleState(
                    position_W_m=obs_pos,
                    velocity_W_m_s=obs_vel,
                    orientation_WB=state.orientation_WB.copy(),
                    angular_velocity_B_rad_s=state.angular_velocity_B_rad_s.copy(),
                    time_s=time_s
                )
                
                # Ejecutar controlador
                current_control = controller_func(time_s, obs_state)
                
                # Mezclador
                current_target_omega = self.mixer.compute_rotor_commands(
                    current_control.collective_thrust_N, 
                    current_control.body_moments_Nm
                )
                
                last_control_time = time_s
                
            # 3. Física
            # Perturbaciones
            v_wind = self.wind.get_wind(time_s)
            F_drag_W = compute_linear_drag(
                state.velocity_W_m_s, v_wind, state.orientation_WB, 
                self.vehicle_params.linear_drag_coefficient
            )
            
            # Actuadores
            app_omega, app_thrust, app_torque_s, total_torque_B, total_thrust_B = \
                self.actuators.compute_applied_forces(current_target_omega)
                
            # total_thrust_B está en cuerpo, pasarlo a mundo
            from simulador_quad.core.attitude import body_to_world
            total_thrust_W = body_to_world(state.orientation_WB, total_thrust_B)
            
            # Fuerza total externa (el RK4 añade la gravedad internamente)
            force_W = total_thrust_W + F_drag_W
            torque_B = total_torque_B
            
            # RK4 Step
            p_new, v_new, q_new, w_new = rk4_step(
                state.position_W_m, state.velocity_W_m_s, state.orientation_WB, state.angular_velocity_B_rad_s,
                self.vehicle_params.mass_kg, self.vehicle_params.inertia_B_kg_m2, self.vehicle_params.gravity_m_s2,
                self.physics_dt_s, force_W, torque_B
            )
            
            state.position_W_m = p_new
            state.velocity_W_m_s = v_new
            state.orientation_WB = q_new
            state.angular_velocity_B_rad_s = w_new
            
            time_s += self.physics_dt_s
            state.time_s = time_s
            
        return {
            "final_state": state,
            "termination_reason": termination_reason,
            "telemetry": telemetry
        }
