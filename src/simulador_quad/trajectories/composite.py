import numpy as np
from typing import Tuple, Optional, List
from simulador_quad.core.contracts import TrajectoryReference, VehicleState
from simulador_quad.trajectories.contract import Trajectory

class CompositeTrajectory(Trajectory):
    """
    Trayectoria compuesta que combina varias trayectorias en secuencia.
    Permite transiciones automáticas suaves (líneas rectas) entre tramos discontinuos.
    """
    def __init__(
        self, 
        trajectories: List[Trajectory], 
        durations: List[Optional[float]], 
        transition_speed: Optional[float] = None
    ):
        self.trajectories = trajectories
        self.durations = durations
        self.transition_speed = transition_speed
        
        self._last_ref = None
        self.reset()

    def reset(self) -> None:
        self.active_index = 0
        self.current_start_time_s = None
        self.completed = False
        
        self.in_transition = False
        self.transition_trajectory = None
        self.transition_start_time_s = None
        self._last_ref = None
        
        for t in self.trajectories:
            t.reset()

    def get_reference_for_state(self, time_s: float, state: VehicleState) -> TrajectoryReference:
        if self.current_start_time_s is None:
            self.current_start_time_s = time_s

        if self.in_transition:
            local_time = time_s - self.transition_start_time_s
            if hasattr(self.transition_trajectory, "get_reference_for_state"):
                ref = self.transition_trajectory.get_reference_for_state(local_time, state)
            else:
                ref = self.transition_trajectory.get_reference(local_time)
            self._last_ref = ref
            return ref

        if self.active_index >= len(self.trajectories):
            # Si se han completado todas, mantener la última referencia generada
            if self._last_ref is not None:
                return TrajectoryReference(
                    self._last_ref.position_W_m.copy(),
                    np.zeros(3),
                    np.zeros(3),
                    self._last_ref.yaw_rad
                )
            return TrajectoryReference(state.position_W_m.copy(), np.zeros(3), np.zeros(3), 0.0)

        active_traj = self.trajectories[self.active_index]
        local_time = time_s - self.current_start_time_s

        if hasattr(active_traj, "get_reference_for_state"):
            ref = active_traj.get_reference_for_state(local_time, state)
        else:
            ref = active_traj.get_reference(local_time)
            
        self._last_ref = ref
        return ref

    def get_reference(self, time_s: float) -> TrajectoryReference:
        if self.current_start_time_s is None:
            self.current_start_time_s = time_s

        if self.in_transition:
            local_time = time_s - self.transition_start_time_s
            ref = self.transition_trajectory.get_reference(local_time)
            self._last_ref = ref
            return ref

        if self.active_index >= len(self.trajectories):
            if self._last_ref is not None:
                return TrajectoryReference(
                    self._last_ref.position_W_m.copy(),
                    np.zeros(3),
                    np.zeros(3),
                    self._last_ref.yaw_rad
                )
            return TrajectoryReference(np.zeros(3), np.zeros(3), np.zeros(3), 0.0)

        active_traj = self.trajectories[self.active_index]
        local_time = time_s - self.current_start_time_s
        ref = active_traj.get_reference(local_time)
        self._last_ref = ref
        return ref

    def check_completion(self, time_s: float, state: VehicleState, dt_s: float) -> Tuple[bool, str]:
        if self.completed:
            return True, "Composite trajectory completed"

        if self.in_transition:
            local_time = time_s - self.transition_start_time_s
            term, _ = self.transition_trajectory.check_completion(local_time, state, dt_s)
            if term:
                self.in_transition = False
                self.transition_trajectory = None
                self.current_start_time_s = time_s
            return False, ""

        if self.active_index >= len(self.trajectories):
            self.completed = True
            return True, "Composite trajectory completed"

        active_traj = self.trajectories[self.active_index]
        local_time = time_s - self.current_start_time_s

        # Evaluar si la trayectoria actual ha terminado
        sub_completed = False
        duration = self.durations[self.active_index]
        if duration is not None and local_time >= duration:
            sub_completed = True
        elif hasattr(active_traj, "check_completion"):
            term, _ = active_traj.check_completion(local_time, state, dt_s)
            if term:
                sub_completed = True
        elif getattr(active_traj, "completed", False):
            sub_completed = True

        if sub_completed:
            # Proceder a la siguiente trayectoria
            if self.active_index + 1 >= len(self.trajectories):
                self.active_index += 1
                self.completed = True
                return True, "Composite trajectory completed"

            # Preparar la siguiente trayectoria
            next_idx = self.active_index + 1
            next_traj = self.trajectories[next_idx]
            next_traj.reset()

            # Obtener el punto de inicio de la siguiente trayectoria
            if hasattr(next_traj, "get_reference_for_state"):
                ref_next_start = next_traj.get_reference_for_state(0.0, state)
            else:
                ref_next_start = next_traj.get_reference(0.0)

            # Obtener el punto final de la trayectoria actual
            ref_last = self._last_ref
            if ref_last is None:
                if hasattr(active_traj, "get_reference_for_state"):
                    ref_last = active_traj.get_reference_for_state(local_time, state)
                else:
                    ref_last = active_traj.get_reference(local_time)

            dist = np.linalg.norm(ref_last.position_W_m - ref_next_start.position_W_m)

            if self.transition_speed is not None and self.transition_speed > 0.0 and dist > 0.05:
                # Iniciar transición suave (línea recta)
                from simulador_quad.trajectories.analytic import LineTrajectory
                wps = np.array([ref_last.position_W_m, ref_next_start.position_W_m])
                
                self.transition_trajectory = LineTrajectory(
                    waypoints=wps,
                    yaw_rad=ref_next_start.yaw_rad,
                    max_speed_m_s=self.transition_speed,
                    max_acceleration_m_s2=0.5,
                    waypoint_tolerance_m=0.05,
                    waypoint_speed_tolerance_m_s=0.10,
                    dwell_time_s=0.0
                )
                self.in_transition = True
                self.transition_start_time_s = time_s
                self.active_index = next_idx
            else:
                # Cambiar directamente
                self.active_index = next_idx
                self.current_start_time_s = time_s
                
        return False, ""
