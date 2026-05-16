import numpy as np
from simulador_quad.control.contract import Controller
from simulador_quad.core.contracts import VehicleState, TrajectoryReference, ControlCommand
from simulador_quad.core.attitude import quaternion_error, rotation_matrix_to_quaternion

class ClassicCascadeController(Controller):
    def __init__(self, mass_kg: float, gravity_m_s2: float, inertia_B_kg_m2: np.ndarray, 
                 Kp_pos: np.ndarray = None, Kd_pos: np.ndarray = None,
                 Kp_att: np.ndarray = None, Kd_att: np.ndarray = None,
                 max_body_moments_Nm: np.ndarray = None):
        self.mass = mass_kg
        self.gravity = gravity_m_s2
        self.inertia = inertia_B_kg_m2
        
        # Ganancias posición
        self.Kp_pos = np.array(Kp_pos) if Kp_pos is not None else np.array([2.0, 2.0, 5.0])
        self.Kd_pos = np.array(Kd_pos) if Kd_pos is not None else np.array([1.0, 1.0, 2.0])
        
        # Ganancias actitud
        self.Kp_att = np.array(Kp_att) if Kp_att is not None else np.array([4.0, 4.0, 1.0])
        self.Kd_att = np.array(Kd_att) if Kd_att is not None else np.array([1.5, 1.5, 0.5])
        
        self.max_thrust = mass_kg * gravity_m_s2 * 2.5
        self.min_thrust = 0.0
        if max_body_moments_Nm is not None:
            self.max_moments_Nm = np.array(max_body_moments_Nm).astype(float)
        else:
            self.max_moments_Nm = np.array([10.0, 10.0, 2.0])

    def compute_desired_force_W(
        self,
        obs_state: VehicleState,
        reference: TrajectoryReference,
        Kp_pos: np.ndarray | None = None,
        Kd_pos: np.ndarray | None = None,
    ) -> np.ndarray:
        """Lazo externo de posicion: estado/referencia -> fuerza deseada ENU."""
        kp_pos = self.Kp_pos if Kp_pos is None else np.array(Kp_pos, dtype=float)
        kd_pos = self.Kd_pos if Kd_pos is None else np.array(Kd_pos, dtype=float)

        pos_err = reference.position_W_m - obs_state.position_W_m
        vel_err = reference.velocity_W_m_s - obs_state.velocity_W_m_s

        a_des = kp_pos * pos_err + kd_pos * vel_err + reference.acceleration_W_m_s2
        g_vec = np.array([0.0, 0.0, -self.gravity])
        return self.mass * (a_des - g_vec)

    def desired_force_to_attitude(self, desired_force_W: np.ndarray, yaw_rad: float) -> tuple[float, np.ndarray]:
        """Convierte fuerza deseada ENU y yaw en empuje colectivo y actitud deseada."""
        # Empuje total requerido
        thrust_N = np.linalg.norm(desired_force_W)
        thrust_N = np.clip(thrust_N, self.min_thrust, self.max_thrust)

        if thrust_N > 1e-3:
            z_B_des = -desired_force_W / np.linalg.norm(desired_force_W)
        else:
            z_B_des = np.array([0.0, 0.0, -1.0])

        x_C = np.array([-np.sin(yaw_rad), np.cos(yaw_rad), 0.0])

        y_B_des = np.cross(z_B_des, x_C)
        if np.linalg.norm(y_B_des) < 1e-3:
            y_B_des = np.array([0.0, 1.0, 0.0])
        else:
            y_B_des = y_B_des / np.linalg.norm(y_B_des)

        x_B_des = np.cross(y_B_des, z_B_des)
        R_des = np.column_stack((x_B_des, y_B_des, z_B_des))

        return float(thrust_N), rotation_matrix_to_quaternion(R_des)

    def compute_attitude_moments(self, obs_state: VehicleState, desired_orientation_WB: np.ndarray) -> np.ndarray:
        """Lazo interno clasico: actitud deseada -> momentos de cuerpo FRD."""
        q_err = quaternion_error(desired_orientation_WB, obs_state.orientation_WB)

        if q_err[0] < 0:
            q_err = -q_err

        angle_err = 2.0 * q_err[1:]

        # PD de actitud
        w_des = np.zeros(3)
        w_err = w_des - obs_state.angular_velocity_B_rad_s

        tau_B = self.Kp_att * angle_err + self.Kd_att * w_err

        gyro_ff = np.cross(obs_state.angular_velocity_B_rad_s, self.inertia @ obs_state.angular_velocity_B_rad_s)

        tau_B += gyro_ff

        # Saturar momentos
        return np.clip(tau_B, -self.max_moments_Nm, self.max_moments_Nm)

    def compute_control_with_position_gains(
        self,
        obs_state: VehicleState,
        reference: TrajectoryReference,
        Kp_pos: np.ndarray,
        Kd_pos: np.ndarray,
    ) -> ControlCommand:
        desired_force_W = self.compute_desired_force_W(obs_state, reference, Kp_pos=Kp_pos, Kd_pos=Kd_pos)
        thrust_N, q_des = self.desired_force_to_attitude(desired_force_W, reference.yaw_rad)
        tau_B = self.compute_attitude_moments(obs_state, q_des)
        return ControlCommand(collective_thrust_N=thrust_N, body_moments_Nm=tau_B)

    def compute_control(self, time_s: float, obs_state: VehicleState, reference: TrajectoryReference) -> ControlCommand:
        return self.compute_control_with_position_gains(obs_state, reference, self.Kp_pos, self.Kd_pos)
