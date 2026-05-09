import numpy as np
from typing import Callable, Optional, Dict, Any, Tuple
from simulador_quad.core.contracts import VehicleState, VehicleParameters, ControlCommand, RotorCommand, RotorAppliedState
from simulador_quad.core.attitude import body_to_world
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
        max_attitude_angle_rad: float = np.pi/2.5, # ~72 deg
        max_saturation_duration_s: float = 1.0
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
        self.max_saturation_duration_s = max_saturation_duration_s
        self.saturation_timer_s = 0.0
        
    def _check_safety_termination(self, state: VehicleState, is_saturated: bool) -> Tuple[bool, str]:
        """
        Comprueba condiciones de seguridad y fallos físicos (crash, límites, NaNs).
        """
        # Acumular saturación
        if is_saturated:
            self.saturation_timer_s += self.physics_dt_s
        else:
            self.saturation_timer_s = 0.0
            
        if self.saturation_timer_s >= self.max_saturation_duration_s:
            return True, "Persistent actuator saturation"

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
        from simulador_quad.core.attitude import body_to_world
        z_B_W = body_to_world(state.orientation_WB, np.array([0.0, 0.0, 1.0]))
        cos_theta = np.dot(z_B_W, np.array([0.0, 0.0, -1.0]))
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        tilt_angle = np.arccos(cos_theta)
        
        if tilt_angle > self.max_attitude_angle_rad:
            return True, f"Attitude angle exceeded limit ({tilt_angle:.2f} > {self.max_attitude_angle_rad:.2f})"
            
        return False, ""

    def _check_goal_termination(self, state: VehicleState, trajectory) -> Tuple[bool, str]:
        """
        Comprueba condiciones de finalización exitosa o por tiempo.
        """
        # Tiempo máximo
        if state.time_s >= self.max_duration_s:
            return True, "Time limit reached"
            
        # Trayectoria completada
        if hasattr(trajectory, "final_time_s") and hasattr(trajectory, "final_position_W_m"):
            # Solo consideramos terminada si el tiempo de referencia ha llegado al final
            if state.time_s >= trajectory.final_time_s:
                # Error de posición y velocidad
                pos_err_m = np.linalg.norm(state.position_W_m - trajectory.final_position_W_m)
                speed_m_s = np.linalg.norm(state.velocity_W_m_s)

                # Umbrales según spec: 0.20 m y 0.30 m/s
                if pos_err_m <= 0.20 and speed_m_s <= 0.30:
                    return True, "Trajectory completed"

        return False, ""

    def _check_trajectory_completion(self, state: VehicleState, trajectory) -> Tuple[bool, str]:
        """
        Mantenido para compatibilidad con tests, delega en _check_goal_termination.
        """
        term, reason = self._check_goal_termination(state, trajectory)
        if reason == "Time limit reached":
            return False, ""
        return term, reason


    def run(self, initial_state: VehicleState, controller_func: Callable, trajectory) -> Dict[str, Any]:
        """
        Ejecuta la simulación.
        controller_func: (time_s, observation_state, reference) -> ControlCommand
        trajectory: objeto con get_reference(time_s)
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
        # Inicialización de objetos de contrato
        current_rotor_cmd = RotorCommand(
            target_thrust_N=np.zeros(self.mixer.num_rotors),
            target_omega_rad_s=np.zeros(self.mixer.num_rotors)
        )
        current_applied = RotorAppliedState(
            applied_omega_rad_s=np.zeros(self.mixer.num_rotors),
            applied_thrust_N=np.zeros(self.mixer.num_rotors),
            applied_torque_Nm=np.zeros(self.mixer.num_rotors),
            rotor_speed_rpm=np.zeros(self.mixer.num_rotors),
            saturation_flags=np.zeros(self.mixer.num_rotors, dtype=bool)
        )
        current_obs = state # Inicialmente coincide
        
        termination_reason = ""
        
        while True:
            # 0. Comprobar seguridad al inicio del bucle (antes de control/actuadores)
            is_saturated = np.any(current_applied.saturation_flags) or current_rotor_cmd.degraded_collective_thrust
            term, reason = self._check_safety_termination(state, is_saturated)
            if term:
                termination_reason = reason
                if telemetry:
                    telemetry[-1].termination_cause = reason
                break

            # Referencia actual
            current_ref = trajectory.get_reference(time_s)

            # 1. Control (ZOH)
            if time_s - last_control_time >= self.control_dt_s - 1e-6:
                # Observación con ruido
                obs_pos, obs_vel = self.noise.apply_noise(state.position_W_m, state.velocity_W_m_s)
                current_obs = VehicleState(
                    position_W_m=obs_pos,
                    velocity_W_m_s=obs_vel,
                    orientation_WB=state.orientation_WB.copy(),
                    angular_velocity_B_rad_s=state.angular_velocity_B_rad_s.copy(),
                    time_s=time_s
                )
                
                # Ejecutar controlador
                current_control = controller_func(time_s, current_obs, current_ref)
                
                # Mezclador
                current_rotor_cmd = self.mixer.compute_rotor_commands(
                    current_control.collective_thrust_N, 
                    current_control.body_moments_Nm
                )
                
                last_control_time = time_s
            
            # 2. Actuadores (calculamos las fuerzas aplicadas con el comando actual)
            current_applied, total_torque_B, total_thrust_B = \
                self.actuators.compute_applied_forces(current_rotor_cmd.target_omega_rad_s)
            
            # 3. Telemetría (guardamos el estado ANTES del paso de física pero CON el comando actual)
            if time_s - last_telemetry_time >= self.telemetry_dt_s - 1e-6:
                from simulador_quad.core.contracts import TelemetrySample
                sample = TelemetrySample(
                    time_s=time_s,
                    state=VehicleState(
                        position_W_m=state.position_W_m.copy(),
                        velocity_W_m_s=state.velocity_W_m_s.copy(),
                        orientation_WB=state.orientation_WB.copy(),
                        angular_velocity_B_rad_s=state.angular_velocity_B_rad_s.copy(),
                        time_s=time_s
                    ),
                    observation=current_obs,
                    reference=current_ref,
                    control_command=ControlCommand(
                        collective_thrust_N=current_control.collective_thrust_N,
                        body_moments_Nm=current_control.body_moments_Nm.copy()
                    ),
                    rotor_command=current_rotor_cmd,
                    rotor_applied=current_applied
                )
                telemetry.append(sample)
                last_telemetry_time = time_s

            # 4. Comprobar finalización por tiempo o llegada (después de registrar telemetría)
            term, reason = self._check_goal_termination(state, trajectory)

            if term:
                termination_reason = reason
                # Actualizar última muestra con la causa
                if telemetry:
                    telemetry[-1].termination_cause = reason
                break

            # 5. Física
            v_wind = self.wind.get_wind(time_s)
            
            p, v, q, w = rk4_step(
                state.position_W_m, state.velocity_W_m_s, state.orientation_WB, state.angular_velocity_B_rad_s,
                self.vehicle_params.mass_kg, self.vehicle_params.inertia_B_kg_m2, self.vehicle_params.gravity_m_s2,
                self.physics_dt_s, total_thrust_B, total_torque_B,
                v_wind, self.vehicle_params.linear_drag_coefficient
            )
            
            state.position_W_m = p
            state.velocity_W_m_s = v
            state.orientation_WB = q
            state.angular_velocity_B_rad_s = w
            
            time_s += self.physics_dt_s
            state.time_s = time_s
            
        return {
            "final_state": state,
            "termination_reason": termination_reason,
            "telemetry": telemetry
        }
