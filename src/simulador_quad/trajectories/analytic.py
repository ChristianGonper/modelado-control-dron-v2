import numpy as np
from enum import Enum
from typing import Tuple, Optional
from simulador_quad.core.contracts import TrajectoryReference, VehicleState
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

class WaypointPhase(Enum):
    MOVE_TO_WAYPOINT = "MOVE_TO_WAYPOINT"
    HOLD_AT_WAYPOINT = "HOLD_AT_WAYPOINT"

def compute_trapezoidal_profile(t: float, L: float, v_max: float, a_max: float) -> Tuple[float, float, float]:
    """
    Genera un perfil trapezoidal (o triangular) de 1D para recorrer L metros.
    Empieza y termina con velocidad cero.
    Retorna (s, s_dot, s_ddot).
    """
    if L <= 0:
        return 0.0, 0.0, 0.0
        
    # Tiempo para alcanzar v_max
    t_acc = v_max / a_max
    # Distancia recorrida en t_acc
    d_acc = 0.5 * a_max * t_acc**2
    
    if 2 * d_acc <= L:
        # Perfil trapezoidal
        d_const = L - 2 * d_acc
        t_const = d_const / v_max
        t_total = 2 * t_acc + t_const
        
        if t <= 0:
            return 0.0, 0.0, 0.0
        elif t <= t_acc:
            return 0.5 * a_max * t**2, a_max * t, a_max
        elif t <= t_acc + t_const:
            t_rel = t - t_acc
            return d_acc + v_max * t_rel, v_max, 0.0
        elif t <= t_total:
            t_rel = t - (t_acc + t_const)
            return L - d_acc + v_max * t_rel - 0.5 * a_max * t_rel**2, v_max - a_max * t_rel, -a_max
        else:
            return L, 0.0, 0.0
    else:
        # Perfil triangular (no se alcanza v_max)
        t_acc_tri = np.sqrt(L / a_max)
        v_peak = a_max * t_acc_tri
        t_total = 2 * t_acc_tri
        
        if t <= 0:
            return 0.0, 0.0, 0.0
        elif t <= t_acc_tri:
            return 0.5 * a_max * t**2, a_max * t, a_max
        elif t <= t_total:
            t_rel = t - t_acc_tri
            return 0.5 * L + v_peak * t_rel - 0.5 * a_max * t_rel**2, v_peak - a_max * t_rel, -a_max
        else:
            return L, 0.0, 0.0

class LineTrajectory(Trajectory):
    """
    Trayectoria de puntos con parada controlada en cada waypoint.
    Sustituye a la interpolación temporal por una guía state-aware.
    """
    def __init__(
        self, 
        waypoints: np.ndarray, 
        times: Optional[np.ndarray] = None, 
        yaw_rad: float = 0.0,
        max_speed_m_s: float = 0.6,
        max_acceleration_m_s2: float = 0.5,
        waypoint_tolerance_m: float = 0.20,
        waypoint_speed_tolerance_m_s: float = 0.20,
        dwell_time_s: float = 0.40
    ):
        self.waypoints = np.array(waypoints).astype(float)
        self.times = times # Deprecated, kept for compatibility
        self.yaw = yaw_rad
        
        self.max_speed = max_speed_m_s
        self.max_acc = max_acceleration_m_s2
        self.tol_pos = waypoint_tolerance_m
        self.tol_vel = waypoint_speed_tolerance_m_s
        self.dwell_time = dwell_time_s
        
        self.reset()

    def reset(self) -> None:
        self.active_target_index = 1
        self.phase = WaypointPhase.MOVE_TO_WAYPOINT
        self.phase_time_s = 0.0
        self.dwell_timer_s = 0.0
        self.completed = False
        
        if hasattr(self, "_last_time_s"):
            delattr(self, "_last_time_s")

        if len(self.waypoints) <= 1:
            self.active_target_index = 0
            self.phase = WaypointPhase.HOLD_AT_WAYPOINT

    def get_reference_for_state(self, time_s: float, state: VehicleState) -> TrajectoryReference:
        if not hasattr(self, "_last_time_s"):
            self._last_time_s = time_s
        
        dt = time_s - self._last_time_s
        self._last_time_s = time_s
        
        if dt > 0:
            self.phase_time_s += dt
            if self.phase == WaypointPhase.HOLD_AT_WAYPOINT:
                # Comprobar si estamos dentro de tolerancia para acumular dwell
                p_target = self.waypoints[self.active_target_index]
                pos_err = np.linalg.norm(state.position_W_m - p_target)
                speed = np.linalg.norm(state.velocity_W_m_s)
                
                if pos_err <= self.tol_pos and speed <= self.tol_vel:
                    self.dwell_timer_s += dt
                else:
                    self.dwell_timer_s = 0.0
                
                # Cambio de segmento
                if self.dwell_timer_s >= self.dwell_time:
                    if self.active_target_index < len(self.waypoints) - 1:
                        self.active_target_index += 1
                        self.phase = WaypointPhase.MOVE_TO_WAYPOINT
                        self.phase_time_s = 0.0
                        self.dwell_timer_s = 0.0
                    else:
                        self.completed = True

        # Generar referencia según fase
        if self.phase == WaypointPhase.MOVE_TO_WAYPOINT:
            p0 = self.waypoints[self.active_target_index - 1]
            p1 = self.waypoints[self.active_target_index]
            d = p1 - p0
            L = np.linalg.norm(d)
            
            if L < 1e-6:
                s, s_dot, s_ddot = 0.0, 0.0, 0.0
            else:
                u = d / L
                s, s_dot, s_ddot = compute_trapezoidal_profile(self.phase_time_s, L, self.max_speed, self.max_acc)
            
            pos = p0 + s * (u if L > 1e-6 else np.zeros(3))
            vel = s_dot * (u if L > 1e-6 else np.zeros(3))
            acc = s_ddot * (u if L > 1e-6 else np.zeros(3))
            
            # Si el perfil ha terminado, pasamos a HOLD_AT_WAYPOINT
            # pero la referencia se queda en p1
            # Calculamos t_total para saber si ha terminado
            t_acc = self.max_speed / self.max_acc
            d_acc = 0.5 * self.max_acc * t_acc**2
            if 2 * d_acc <= L:
                t_total = 2 * t_acc + (L - 2 * d_acc) / self.max_speed
            else:
                t_total = 2 * np.sqrt(L / self.max_acc)
            
            if self.phase_time_s >= t_total:
                self.phase = WaypointPhase.HOLD_AT_WAYPOINT
                self.phase_time_s = 0.0
                
            return TrajectoryReference(pos, vel, acc, self.yaw)
            
        else: # HOLD_AT_WAYPOINT
            p_target = self.waypoints[self.active_target_index]
            return TrajectoryReference(p_target.copy(), np.zeros(3), np.zeros(3), self.yaw)

    def get_reference(self, time_s: float) -> TrajectoryReference:
        """Fallback legacy que no usa el estado. Solo para compatibilidad."""
        # Para inicialización (t=0), devolvemos siempre el punto de partida (primer waypoint)
        if time_s <= 1e-6 and self.active_target_index <= 1 and self.phase == WaypointPhase.MOVE_TO_WAYPOINT:
            return TrajectoryReference(self.waypoints[0].copy(), np.zeros(3), np.zeros(3), self.yaw)
            
        # En otros casos, devolvemos el waypoint objetivo actual
        p_target = self.waypoints[min(self.active_target_index, len(self.waypoints)-1)]
        return TrajectoryReference(p_target.copy(), np.zeros(3), np.zeros(3), self.yaw)

    def check_completion(self, time_s: float, state: VehicleState, dt_s: float) -> Tuple[bool, str]:
        if self.completed:
            return True, "Trajectory completed"
        return False, ""

class LemniscateTrajectory(Trajectory):
    """
    Trayectoria en forma de ocho (Lemniscata de Gerono) en el plano XY.
    x(t) = cx + a * sin(w * t)
    y(t) = cy + b * sin(2 * w * t)
    z(t) = cz
    """
    def __init__(self, center_W_m: np.ndarray, a: float, b: float, omega_rad_s: float, yaw_mode: str = "forward"):
        self.center = center_W_m.copy()
        self.a = a
        self.b = b
        self.w = omega_rad_s
        self.yaw_mode = yaw_mode
        
    def get_reference(self, time_s: float) -> TrajectoryReference:
        t = time_s
        
        pos = self.center.copy()
        pos[0] += self.a * np.sin(self.w * t)
        pos[1] += self.b * np.sin(2 * self.w * t)
        
        vel = np.zeros(3)
        vel[0] = self.a * self.w * np.cos(self.w * t)
        vel[1] = 2 * self.b * self.w * np.cos(2 * self.w * t)
        
        acc = np.zeros(3)
        acc[0] = -self.a * self.w**2 * np.sin(self.w * t)
        acc[1] = -4 * self.b * self.w**2 * np.sin(2 * self.w * t)
        
        if self.yaw_mode == "forward":
            yaw = np.arctan2(vel[1], vel[0]) # Apuntar hacia donde se mueve
        else:
            yaw = 0.0
            
        return TrajectoryReference(pos, vel, acc, yaw)
