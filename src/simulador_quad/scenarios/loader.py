import yaml
import numpy as np
from typing import Dict, Any, Tuple
from simulador_quad.core.contracts import VehicleParameters, RotorParameters, VehicleState
from simulador_quad.dynamics.actuators import ActuatorSystem
from simulador_quad.dynamics.mixer import QuadcopterMixer
from simulador_quad.dynamics.perturbations import WindModel, ObservationNoise
from simulador_quad.trajectories.analytic import HoldTrajectory, CircleTrajectory, LissajousTrajectory, LineTrajectory
from simulador_quad.control.classic import ClassicCascadeController
from simulador_quad.core.frames import get_level_quaternion

def load_scenario(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def instantiate_scenario(config: Dict[str, Any]) -> Tuple[Any, Any, Any, Any, Any, Any, Any]:
    seed = config.get('seed', 42)
    
    # 1. Vehicle
    v_cfg = config['vehicle']
    rotors = []
    for r in v_cfg['rotors']:
        rotors.append(RotorParameters(
            position_B_m=np.array(r['position_B_m']).astype(float),
            turning_direction=r['turning_direction'],
            k_f=float(r['k_f']),
            k_m=float(r['k_m']),
            omega_max_rad_s=float(r['omega_max_rad_s']),
            time_constant_s=float(r['time_constant_s']),
            delay_s=float(r.get('delay_s', 0.0))
        ))
        
    v_params = VehicleParameters(
        mass_kg=float(v_cfg['mass_kg']),
        inertia_B_kg_m2=np.array(v_cfg['inertia_B_kg_m2']).astype(float),
        gravity_m_s2=float(v_cfg.get('gravity_m_s2', 9.81)),
        linear_drag_coefficient=np.array(v_cfg['linear_drag_coefficient']).astype(float),
        rotors=rotors
    )
    
    mixer = QuadcopterMixer(rotors)
    actuators = ActuatorSystem(rotors, dt_s=float(config['timing']['physics_dt_s']))
    
    # 2. Initial State
    is_cfg = config['initial_state']
    # Si orientation_WB es nulo, usamos get_level_quaternion
    if is_cfg.get('orientation_WB') is None:
        q0 = get_level_quaternion(float(is_cfg.get('yaw_rad', 0.0)))
    else:
        q0 = np.array(is_cfg['orientation_WB']).astype(float)
        
    initial_state = VehicleState(
        position_W_m=np.array(is_cfg['position_W_m']).astype(float),
        velocity_W_m_s=np.array(is_cfg['velocity_W_m_s']).astype(float),
        orientation_WB=q0,
        angular_velocity_B_rad_s=np.array(is_cfg['angular_velocity_B_rad_s']).astype(float),
        time_s=0.0
    )
    
    # 3. Trajectory
    t_cfg = config['trajectory']
    t_type = t_cfg['type']
    if t_type == 'hold':
        trajectory = HoldTrajectory(np.array(t_cfg['position_W_m']).astype(float), float(t_cfg.get('yaw_rad', 0.0)))
    elif t_type == 'circle':
        trajectory = CircleTrajectory(
            np.array(t_cfg['center_W_m']).astype(float), float(t_cfg['radius_m']), float(t_cfg['omega_rad_s']), t_cfg.get('yaw_mode', 'forward')
        )
    elif t_type == 'lissajous':
        trajectory = LissajousTrajectory(
            np.array(t_cfg['center_W_m']).astype(float), np.array(t_cfg['amplitudes']).astype(float), np.array(t_cfg['omegas']).astype(float)
        )
    elif t_type == 'line' or t_type == 'waypoint':
        trajectory = LineTrajectory(
            np.array(t_cfg['waypoints']).astype(float), np.array(t_cfg['times']).astype(float), float(t_cfg.get('yaw_rad', 0.0))
        )
    else:
        raise ValueError(f"Unknown trajectory type: {t_type}")
        
    # 4. Controller
    c_cfg = config['controller']
    if c_cfg['type'] == 'classic':
        max_moments = c_cfg.get('max_body_moments_Nm')
        controller = ClassicCascadeController(
            v_params.mass_kg, v_params.gravity_m_s2, v_params.inertia_B_kg_m2,
            max_body_moments_Nm=max_moments
        )
    else:
        raise ValueError(f"Unknown controller type: {c_cfg['type']}")
        
    # 5. Perturbations
    p_cfg = config['perturbations']
    wind = WindModel(np.array(p_cfg['constant_wind_W_m_s']).astype(float))
    noise = ObservationNoise(
        pos_std_m=float(p_cfg.get('pos_std_m', 0.0)),
        vel_std_m_s=float(p_cfg.get('vel_std_m_s', 0.0)),
        seed=seed
    )
    
    return v_params, mixer, actuators, initial_state, trajectory, controller, wind, noise
