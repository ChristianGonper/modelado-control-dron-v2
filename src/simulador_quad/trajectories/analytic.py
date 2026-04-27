import numpy as np
from simulador_quad.core.contracts import TrajectoryReference
from simulador_quad.trajectories.contract import Trajectory

class HoldTrajectory(Trajectory):
    def __init__(self, position_W_m: np.ndarray, yaw_rad: float = 0.0):
        self.pos = position_W_m.copy()
        self.yaw = yaw_rad
        
    def get_reference(self, time_s: float) -> TrajectoryReference:
        return TrajectoryReference(
            position_W_m=self.pos.copy(),
            velocity_W_m_s=np.zeros(3),
            acceleration_W_m_s2=np.zeros(3),
            yaw_rad=self.yaw
        )

class CircleTrajectory(Trajectory):
    """
    Círculo en el plano XY (ENU) centrado en 'center_W_m'.
    x(t) = cx + R * cos(omega * t)
    y(t) = cy + R * sin(omega * t)
    z(t) = cz
    """
    def __init__(self, center_W_m: np.ndarray, radius_m: float, omega_rad_s: float, yaw_mode: str = "forward"):
        self.center = center_W_m.copy()
        self.R = radius_m
        self.w = omega_rad_s
        self.yaw_mode = yaw_mode # "forward" o "center"
        
    def get_reference(self, time_s: float) -> TrajectoryReference:
        t = time_s
        
        # Posición
        pos = self.center.copy()
        pos[0] += self.R * np.cos(self.w * t)
        pos[1] += self.R * np.sin(self.w * t)
        
        # Velocidad
        vel = np.zeros(3)
        vel[0] = -self.R * self.w * np.sin(self.w * t)
        vel[1] = self.R * self.w * np.cos(self.w * t)
        
        # Aceleración
        acc = np.zeros(3)
        acc[0] = -self.R * self.w**2 * np.cos(self.w * t)
        acc[1] = -self.R * self.w**2 * np.sin(self.w * t)
        
        # Yaw
        if self.yaw_mode == "forward":
            yaw = np.arctan2(-vel[0], vel[1])
        else:
            yaw = 0.0
            
        return TrajectoryReference(pos, vel, acc, yaw)

class LissajousTrajectory(Trajectory):
    """
    Trayectoria senoidal simple.
    x(t) = cx + A_x * sin(w_x * t)
    y(t) = cy + A_y * sin(w_y * t)
    z(t) = cz + A_z * sin(w_z * t)
    """
    def __init__(self, center_W_m: np.ndarray, amplitudes: np.ndarray, omegas: np.ndarray):
        self.c = center_W_m.copy()
        self.A = amplitudes.copy()
        self.w = omegas.copy()
        
    def get_reference(self, time_s: float) -> TrajectoryReference:
        t = time_s
        
        pos = self.c + self.A * np.sin(self.w * t)
        vel = self.A * self.w * np.cos(self.w * t)
        acc = -self.A * self.w**2 * np.sin(self.w * t)
        
        # Yaw constante 0.0 por simplicidad en Lissajous
        yaw = 0.0
        
        return TrajectoryReference(pos, vel, acc, yaw)
