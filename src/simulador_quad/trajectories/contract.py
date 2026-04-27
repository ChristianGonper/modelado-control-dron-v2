from abc import ABC, abstractmethod
from simulador_quad.core.contracts import TrajectoryReference

class Trajectory(ABC):
    @abstractmethod
    def get_reference(self, time_s: float) -> TrajectoryReference:
        pass
