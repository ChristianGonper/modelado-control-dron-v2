from abc import ABC, abstractmethod
from simulador_quad.core.contracts import VehicleState, TrajectoryReference, ControlCommand

class Controller(ABC):
    @abstractmethod
    def compute_control(self, time_s: float, obs_state: VehicleState, reference: TrajectoryReference) -> ControlCommand:
        pass
