import numpy as np
from simulador_quad.control.contract import Controller
from simulador_quad.core.contracts import VehicleState, TrajectoryReference, ControlCommand
from simulador_quad.core.attitude import world_to_body, quaternion_error, rotation_matrix_to_quaternion

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
        
    def compute_control(self, time_s: float, obs_state: VehicleState, reference: TrajectoryReference) -> ControlCommand:
        # Bucle externo
        pos_err = reference.position_W_m - obs_state.position_W_m
        vel_err = reference.velocity_W_m_s - obs_state.velocity_W_m_s
        
        a_des = self.Kp_pos * pos_err + self.Kd_pos * vel_err + reference.acceleration_W_m_s2
        
        g_vec = np.array([0.0, 0.0, -self.gravity])
        F_des_W = self.mass * (a_des - g_vec)
        
        # Empuje total requerido
        thrust_N = np.linalg.norm(F_des_W)
        thrust_N = np.clip(thrust_N, self.min_thrust, self.max_thrust)
        
        if thrust_N > 1e-3:
            z_B_des = -F_des_W / np.linalg.norm(F_des_W)
        else:
            z_B_des = np.array([0.0, 0.0, -1.0])
            
        # Yaw de referencia
        yaw_rad = reference.yaw_rad
        x_C = np.array([-np.sin(yaw_rad), np.cos(yaw_rad), 0.0])
        
        y_B_des = np.cross(z_B_des, x_C)
        if np.linalg.norm(y_B_des) < 1e-3:
            y_B_des = np.array([0.0, 1.0, 0.0])
        else:
            y_B_des = y_B_des / np.linalg.norm(y_B_des)
            
        x_B_des = np.cross(y_B_des, z_B_des)
        
        R_des = np.column_stack((x_B_des, y_B_des, z_B_des))
        
        q_des = rotation_matrix_to_quaternion(R_des)
        
        # Bucle interno: Actitud -> Momentos
        q_err = quaternion_error(q_des, obs_state.orientation_WB)
        
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
        tau_B = np.clip(tau_B, -self.max_moments_Nm, self.max_moments_Nm)
        
        return ControlCommand(collective_thrust_N=thrust_N, body_moments_Nm=tau_B)
