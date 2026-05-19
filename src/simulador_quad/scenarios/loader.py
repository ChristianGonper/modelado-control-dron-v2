import yaml
import numpy as np
from typing import Dict, Any, Tuple
from simulador_quad.core.contracts import VehicleParameters, RotorParameters, VehicleState
from simulador_quad.dynamics.actuators import ActuatorSystem
from simulador_quad.dynamics.mixer import QuadcopterMixer
from simulador_quad.dynamics.perturbations import WindModel, ObservationNoise
from simulador_quad.trajectories.analytic import HoldTrajectory, CircleTrajectory, LissajousTrajectory, LineTrajectory, LemniscateTrajectory
from simulador_quad.control.classic import ClassicCascadeController
from simulador_quad.core.frames import get_level_quaternion
from simulador_quad.scenarios.schema import validate_scenario_config

def load_scenario(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    validate_scenario_config(config)
    return config

def instantiate_trajectory(t_cfg: Dict[str, Any]) -> Any:
    t_type = t_cfg['type']
    if t_type == 'hold':
        return HoldTrajectory(np.array(t_cfg['position_W_m']).astype(float), float(t_cfg.get('yaw_rad', 0.0)))
    elif t_type == 'circle':
        return CircleTrajectory(
            np.array(t_cfg['center_W_m']).astype(float), float(t_cfg['radius_m']), float(t_cfg['omega_rad_s']), t_cfg.get('yaw_mode', 'forward')
        )
    elif t_type == 'lissajous':
        return LissajousTrajectory(
            np.array(t_cfg['center_W_m']).astype(float), np.array(t_cfg['amplitudes']).astype(float), np.array(t_cfg['omegas']).astype(float)
        )
    elif t_type == 'line' or t_type == 'waypoint':
        return LineTrajectory(
            waypoints=np.array(t_cfg['waypoints']).astype(float),
            times=np.array(t_cfg['times']).astype(float) if 'times' in t_cfg else None,
            yaw_rad=float(t_cfg.get('yaw_rad', 0.0)),
            max_speed_m_s=float(t_cfg.get('max_speed_m_s', 0.6)),
            max_acceleration_m_s2=float(t_cfg.get('max_acceleration_m_s2', 0.5)),
            waypoint_tolerance_m=float(t_cfg.get('waypoint_tolerance_m', 0.20)),
            waypoint_speed_tolerance_m_s=float(t_cfg.get('waypoint_speed_tolerance_m_s', 0.20)),
            dwell_time_s=float(t_cfg.get('dwell_time_s', 0.40))
        )
    elif t_type == 'lemniscate':
        return LemniscateTrajectory(
            center_W_m=np.array(t_cfg['center_W_m']).astype(float),
            a=float(t_cfg['a']),
            b=float(t_cfg['b']),
            omega_rad_s=float(t_cfg['omega_rad_s']),
            z_amp=float(t_cfg.get('z_amp', 0.0)),
            z_omega_rad_s=float(t_cfg.get('z_omega_rad_s', 0.0)),
            yaw_mode=t_cfg.get('yaw_mode', 'forward'),
            warmup_s=float(t_cfg.get('warmup_s', 3.0))
        )
    else:
        raise ValueError(f"Unknown trajectory type: {t_type}")

def instantiate_scenario(config: Dict[str, Any]) -> Tuple[Any, Any, Any, Any, Any, Any, Any]:
    validate_scenario_config(config)
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
    trajectory = instantiate_trajectory(config['trajectory'])

    # 4. Controller
    c_cfg = config['controller']
    if c_cfg['type'] == 'classic':
        max_moments = c_cfg.get('max_body_moments_Nm')
        kp_pos = c_cfg.get('Kp_pos')
        kd_pos = c_cfg.get('Kd_pos')
        kp_att = c_cfg.get('Kp_att')
        kd_att = c_cfg.get('Kd_att')

        controller = ClassicCascadeController(
            v_params.mass_kg, v_params.gravity_m_s2, v_params.inertia_B_kg_m2,
            Kp_pos=kp_pos, Kd_pos=kd_pos, Kp_att=kp_att, Kd_att=kd_att,
            max_body_moments_Nm=max_moments
        )
    elif c_cfg['type'] == 'neural':
        from simulador_quad.control.neural import NeuralController
        max_moments = c_cfg.get('max_body_moments_Nm')
        if max_moments is not None:
            max_moments = np.array(max_moments).astype(float)
            
        controller = NeuralController(
            checkpoint_path=c_cfg['checkpoint_path'],
            normalization_path=c_cfg['normalization_path'],
            architecture=c_cfg.get('architecture', 'mlp'),
            sequence_length=c_cfg.get('sequence_length', 20),
            clip_to_classic_limits=c_cfg.get('clip_to_classic_limits', True),
            mass_kg=v_params.mass_kg,
            gravity_m_s2=v_params.gravity_m_s2,
            max_moments_Nm=max_moments if max_moments is not None else np.array([10.0, 10.0, 2.0]),
            device=c_cfg.get('device', 'auto'),
        )
    elif c_cfg['type'] == 'neural_position':
        from simulador_quad.control.neural import NeuralPositionController
        max_moments = c_cfg.get('max_body_moments_Nm')
        if max_moments is not None:
            max_moments = np.array(max_moments).astype(float)

        controller = NeuralPositionController(
            checkpoint_path=c_cfg['checkpoint_path'],
            normalization_path=c_cfg['normalization_path'],
            architecture=c_cfg.get('architecture', 'mlp'),
            sequence_length=c_cfg.get('sequence_length', 20),
            mass_kg=v_params.mass_kg,
            gravity_m_s2=v_params.gravity_m_s2,
            inertia_B_kg_m2=v_params.inertia_B_kg_m2,
            base_Kp_pos=np.array(c_cfg.get('base_Kp_pos', [2.0, 2.0, 5.0])).astype(float),
            base_Kd_pos=np.array(c_cfg.get('base_Kd_pos', [1.0, 1.0, 2.0])).astype(float),
            Kp_att=np.array(c_cfg.get('Kp_att', [4.0, 4.0, 1.0])).astype(float),
            Kd_att=np.array(c_cfg.get('Kd_att', [1.5, 1.5, 0.5])).astype(float),
            max_body_moments_Nm=max_moments if max_moments is not None else np.array([10.0, 10.0, 2.0]),
            multiplier_clip=np.array(c_cfg.get('multiplier_clip', [0.25, 4.0])).astype(float),
            device=c_cfg.get('device', 'auto'),
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
