import numpy as np
from simulador_quad.control.contract import Controller
from simulador_quad.core.contracts import VehicleState, TrajectoryReference, ControlCommand
from simulador_quad.core.attitude import world_to_body, quaternion_error, quaternion_to_rotation_matrix

class ClassicCascadeController(Controller):
    def __init__(self, mass_kg: float, gravity_m_s2: float, inertia_B_kg_m2: np.ndarray, max_body_moments_Nm: np.ndarray = None):
        self.mass = mass_kg
        self.gravity = gravity_m_s2
        self.inertia = inertia_B_kg_m2
        
        # Ganancias PID posición (ENU)
        self.Kp_pos = np.array([2.0, 2.0, 5.0])
        self.Kd_pos = np.array([1.0, 1.0, 2.0])
        
        # Ganancias Actitud (Roll, Pitch, Yaw)
        self.Kp_att = np.array([4.0, 4.0, 1.0])
        self.Kd_att = np.array([1.5, 1.5, 0.5])
        
        self.max_thrust = mass_kg * gravity_m_s2 * 2.5
        self.min_thrust = 0.0
        if max_body_moments_Nm is not None:
            self.max_moments_Nm = np.array(max_body_moments_Nm).astype(float)
        else:
            self.max_moments_Nm = np.array([10.0, 10.0, 2.0])
        
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
        
        # Saturar momentos
        tau_B = np.clip(tau_B, -self.max_moments_Nm, self.max_moments_Nm)
        
        return ControlCommand(collective_thrust_N=thrust_N, body_moments_Nm=tau_B)

    def rotation_matrix_to_quaternion(self, R: np.ndarray) -> np.ndarray:
        from scipy.spatial.transform import Rotation
        # SciPy devuelve [x, y, z, w] por defecto. Queremos [w, x, y, z].
        return Rotation.from_matrix(R).as_quat(scalar_first=True)
