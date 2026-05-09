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
        
        pos = self.center.copy()
        pos[0] += self.R * np.cos(self.w * t)
        pos[1] += self.R * np.sin(self.w * t)
        
        vel = np.zeros(3)
        vel[0] = -self.R * self.w * np.sin(self.w * t)
        vel[1] = self.R * self.w * np.cos(self.w * t)
        
        acc = np.zeros(3)
        acc[0] = -self.R * self.w**2 * np.cos(self.w * t)
        acc[1] = -self.R * self.w**2 * np.sin(self.w * t)
        
        if self.yaw_mode == "forward":
            yaw = np.arctan2(-vel[0], vel[1])
        else:
            yaw = 0.0
            
        return TrajectoryReference(pos, vel, acc, yaw)

class LissajousTrajectory(Trajectory):
    """
    Trayectoria sinusoidal simple.
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
        
        yaw = 0.0
        
        return TrajectoryReference(pos, vel, acc, yaw)

class LineTrajectory(Trajectory):
    """
    Interpolación entre waypoints usando smoothstep cúbico (C1 continuo).
    Asegura velocidad cero en los waypoints.
    """
    def __init__(self, waypoints: np.ndarray, times: np.ndarray, yaw_rad: float = 0.0):
        self.waypoints = np.array(waypoints).astype(float)
        self.times = np.array(times).astype(float)
        self.yaw = yaw_rad
        
    @property
    def final_time_s(self) -> float:
        return float(self.times[-1])

    @property
    def final_position_W_m(self) -> np.ndarray:
        return self.waypoints[-1].copy()

    def get_reference(self, time_s: float) -> TrajectoryReference:
        if time_s <= self.times[0]:
            return TrajectoryReference(self.waypoints[0].copy(), np.zeros(3), np.zeros(3), self.yaw)
        if time_s >= self.times[-1]:
            return TrajectoryReference(self.waypoints[-1].copy(), np.zeros(3), np.zeros(3), self.yaw)
            
        idx = np.searchsorted(self.times, time_s) - 1
        t0, t1 = self.times[idx], self.times[idx+1]
        p0, p1 = self.waypoints[idx], self.waypoints[idx+1]
        
        dt = t1 - t0
        tau = (time_s - t0) / dt
        
        # Smoothstep cúbico: s(tau) = 3*tau^2 - 2*tau^3
        s = 3*tau**2 - 2*tau**3
        ds = 6*tau - 6*tau**2
        dds = 6 - 12*tau
        
        pos = p0 + s * (p1 - p0)
        vel = (ds / dt) * (p1 - p0)
        acc = (dds / dt**2) * (p1 - p0)
        
        return TrajectoryReference(pos, vel, acc, self.yaw)
