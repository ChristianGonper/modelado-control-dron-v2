import numpy as np
from simulador_quad.control.contract import Controller
from simulador_quad.core.contracts import VehicleState, TrajectoryReference, ControlCommand
from simulador_quad.core.attitude import world_to_body, quaternion_error, quaternion_to_rotation_matrix

class ClassicCascadeController(Controller):
    def __init__(self, mass_kg: float, gravity_m_s2: float, inertia_B_kg_m2: np.ndarray):
        self.mass = mass_kg
        self.gravity = gravity_m_s2
        self.inertia = inertia_B_kg_m2
        
        # Ganancias PID posición (ENU)
        self.Kp_pos = np.array([2.0, 2.0, 5.0])
        self.Kd_pos = np.array([1.5, 1.5, 3.0])
        
        # Ganancias PID actitud (FRD)
        self.Kp_att = np.array([50.0, 50.0, 10.0])
        self.Kd_att = np.array([10.0, 10.0, 5.0])
        
        self.max_thrust = mass_kg * gravity_m_s2 * 2.0
        self.min_thrust = 0.0
        
    def compute_control(self, time_s: float, obs_state: VehicleState, reference: TrajectoryReference) -> ControlCommand:
        # 1. Bucle externo: Posición -> Fuerza deseada en ENU
        pos_err = reference.position_W_m - obs_state.position_W_m
        vel_err = reference.velocity_W_m_s - obs_state.velocity_W_m_s
        
        # Aceleración deseada (PD) + feedforward
        a_des = self.Kp_pos * pos_err + self.Kd_pos * vel_err + reference.acceleration_W_m_s2
        
        # Fuerza deseada (sumando gravedad para contrarrestar)
        g_vec = np.array([0.0, 0.0, -self.gravity])
        F_des_W = self.mass * (a_des - g_vec)
        
        # 2. Convertir fuerza a empuje y actitud deseada
        # Empuje es la proyección de F_des_W sobre el eje Z_B.
        # Pero simplificamos calculando la actitud deseada a partir de F_des_W
        
        # El empuje total requerido (saturado)
        thrust_N = np.linalg.norm(F_des_W)
        thrust_N = np.clip(thrust_N, self.min_thrust, self.max_thrust)
        
        # Z_B deseado es -F_des_W normalizado (porque los rotores empujan hacia -Z_B)
        # Wait, en FRD, Z_B es "abajo". El empuje va hacia -Z_B.
        # Por tanto, la fuerza producida por el dron es en la dirección -Z_B.
        # Así que F_des_W debe estar alineado con -Z_B_W.
        # -> Z_B_W = -F_des_W / ||F_des_W||
        if thrust_N > 1e-3:
            z_B_des = -F_des_W / np.linalg.norm(F_des_W)
        else:
            z_B_des = np.array([0.0, 0.0, 1.0]) # Default a -z_B_W = -1 ?
            # Si z_B es down, hover significa z_B_W = [0,0,-1]
            z_B_des = np.array([0.0, 0.0, -1.0])
            
        # Para X_B_des e Y_B_des usamos el yaw de referencia
        # Rotación inicial de Yaw alrededor de Z_W
        yaw_rad = reference.yaw_rad
        # Con yaw=0, el frente (X_B) apunta al Norte (Y_W)
        x_C = np.array([-np.sin(yaw_rad), np.cos(yaw_rad), 0.0])
        
        # Y_B_des es Z_B_des x x_C
        y_B_des = np.cross(z_B_des, x_C)
        if np.linalg.norm(y_B_des) < 1e-3:
            # Singularidad
            y_B_des = np.array([0.0, 1.0, 0.0])
        else:
            y_B_des = y_B_des / np.linalg.norm(y_B_des)
            
        # Recalcular X_B_des para que sea ortonormal
        x_B_des = np.cross(y_B_des, z_B_des)
        
        R_des = np.column_stack((x_B_des, y_B_des, z_B_des))
        
        # Convertir R_des a cuaternión q_des
        q_des = self.rotation_matrix_to_quaternion(R_des)
        
        # 3. Bucle interno: Actitud -> Momentos (FRD)
        q_err = quaternion_error(q_des, obs_state.orientation_WB)
        # q_err = [w, x, y, z]. La parte vectorial (x,y,z) aproxima el error angular / 2
        # Asumimos que w > 0 para tomar el camino corto
        if q_err[0] < 0:
            q_err = -q_err
            
        angle_err = 2.0 * q_err[1:]
        
        # PD de actitud
        # reference angular velocity = 0 para simplificar
        w_des = np.zeros(3)
        w_err = w_des - obs_state.angular_velocity_B_rad_s
        
        tau_B = self.Kp_att * angle_err + self.Kd_att * w_err
        
        # feedforward de giroscopio: w x (I w)
        gyro_ff = np.cross(obs_state.angular_velocity_B_rad_s, self.inertia @ obs_state.angular_velocity_B_rad_s)
        
        tau_B += gyro_ff
        
        return ControlCommand(collective_thrust_N=thrust_N, body_moments_Nm=tau_B)

    def rotation_matrix_to_quaternion(self, R: np.ndarray) -> np.ndarray:
        m00, m01, m02 = R[0,0], R[0,1], R[0,2]
        m10, m11, m12 = R[1,0], R[1,1], R[1,2]
        m20, m21, m22 = R[2,0], R[2,1], R[2,2]
        
        tr = m00 + m11 + m22
        if tr > 0:
            S = np.sqrt(tr + 1.0) * 2
            qw = 0.25 * S
            qx = (m21 - m12) / S
            qy = (m02 - m20) / S
            qz = (m10 - m01) / S
        elif (m00 > m11) and (m00 > m22):
            S = np.sqrt(1.0 + m00 - m11 - m22) * 2
            qw = (m21 - m12) / S
            qx = 0.25 * S
            qy = (m01 + m10) / S
            qz = (m02 + m20) / S
        elif m11 > m22:
            S = np.sqrt(1.0 + m11 - m00 - m22) * 2
            qw = (m02 - m20) / S
            qx = (m01 + m10) / S
            qy = 0.25 * S
            qz = (m12 + m21) / S
        else:
            S = np.sqrt(1.0 + m22 - m00 - m11) * 2
            qw = (m10 - m01) / S
            qx = (m02 + m20) / S
            qy = (m12 + m21) / S
            qz = 0.25 * S
            
        return np.array([qw, qx, qy, qz])
