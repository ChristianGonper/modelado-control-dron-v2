from dataclasses import dataclass
from typing import List, Optional
import numpy as np

@dataclass
class VehicleState:
    position_W_m: np.ndarray  # [3,] ENU
    velocity_W_m_s: np.ndarray  # [3,] ENU
    orientation_WB: np.ndarray  # [4,] Cuaternión [w, x, y, z]
    angular_velocity_B_rad_s: np.ndarray  # [3,] FRD
    time_s: float

@dataclass
class RotorParameters:
    position_B_m: np.ndarray  # [3,] FRD
    turning_direction: int  # 1 o -1
    k_f: float  # N / (rad/s)^2
    k_m: float  # N*m / (rad/s)^2
    omega_max_rad_s: float
    time_constant_s: float
    delay_s: float = 0.0

@dataclass
class VehicleParameters:
    mass_kg: float
    inertia_B_kg_m2: np.ndarray  # [3, 3] matriz de inercia FRD
    gravity_m_s2: float
    linear_drag_coefficient: np.ndarray  # [3,] FRD o escalar
    rotors: List[RotorParameters]

@dataclass
class TrajectoryReference:
    position_W_m: np.ndarray  # [3,] ENU
    velocity_W_m_s: np.ndarray  # [3,] ENU
    acceleration_W_m_s2: np.ndarray  # [3,] ENU
    yaw_rad: float

@dataclass
class ControlCommand:
    collective_thrust_N: float
    body_moments_Nm: np.ndarray  # [3,] FRD

@dataclass
class RotorCommand:
    target_thrust_N: np.ndarray  # [num_rotors,]
    target_omega_rad_s: np.ndarray  # [num_rotors,]
    degraded_collective_thrust: bool = False

@dataclass
class RotorAppliedState:
    applied_omega_rad_s: np.ndarray  # [num_rotors,]
    applied_thrust_N: np.ndarray  # [num_rotors,]
    applied_torque_Nm: np.ndarray  # [num_rotors,] (reacción aerodinámica)
    rotor_speed_rpm: np.ndarray  # [num_rotors,]
    saturation_flags: np.ndarray  # [num_rotors,] boolean
    
@dataclass
class TelemetrySample:
    time_s: float
    state: VehicleState
    observation: VehicleState  # Estado tal cual lo vio el controlador (con ruido/retraso si aplica)
    reference: TrajectoryReference
    control_command: ControlCommand
    rotor_command: RotorCommand
    rotor_applied: RotorAppliedState
    termination_cause: str = ""
    desired_force_W_N: Optional[np.ndarray] = None
    desired_force_clipped_W_N: Optional[np.ndarray] = None
    wind_W_m_s: Optional[np.ndarray] = None
