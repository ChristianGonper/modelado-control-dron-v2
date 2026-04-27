import numpy as np
from simulador_quad.runner import SimulationRunner
from simulador_quad.core.contracts import VehicleParameters, VehicleState, ControlCommand, RotorParameters
from simulador_quad.dynamics.actuators import ActuatorSystem
from simulador_quad.dynamics.mixer import QuadcopterMixer
from simulador_quad.dynamics.perturbations import WindModel, ObservationNoise
from simulador_quad.core.frames import get_level_quaternion

def create_x_config_rotors():
    # Configuración en X clásica
    L = 0.25
    return [
        RotorParameters(np.array([L, L, 0]), -1, 1.0, 0.1, 100.0, 0.0),
        RotorParameters(np.array([L, -L, 0]), 1, 1.0, 0.1, 100.0, 0.0),
        RotorParameters(np.array([-L, L, 0]), 1, 1.0, 0.1, 100.0, 0.0),
        RotorParameters(np.array([-L, -L, 0]), -1, 1.0, 0.1, 100.0, 0.0),
    ]

def setup_runner(max_dur=1.0):
    rotors = create_x_config_rotors()
    v_params = VehicleParameters(
        mass_kg=1.0,
        inertia_B_kg_m2=np.eye(3)*0.01,
        gravity_m_s2=9.81,
        linear_drag_coefficient=np.zeros(3),
        rotors=rotors
    )
    mixer = QuadcopterMixer(rotors)
    actuators = ActuatorSystem(rotors, dt_s=0.01)
    wind = WindModel(np.zeros(3))
    noise = ObservationNoise()
    
    return SimulationRunner(
        physics_dt_s=0.01,
        control_dt_s=0.05,
        telemetry_dt_s=0.1,
        vehicle_params=v_params,
        mixer=mixer,
        actuators=actuators,
        wind_model=wind,
        observation_noise=noise,
        max_duration_s=max_dur,
        z_min_m=-1.0
    )

def test_runner_multi_rate():
    runner = setup_runner(max_dur=0.5)
    
    from simulador_quad.core.frames import get_level_quaternion
    initial_state = VehicleState(
        position_W_m=np.array([0.0, 0.0, 10.0]),
        velocity_W_m_s=np.zeros(3),
        orientation_WB=get_level_quaternion(0.0),
        angular_velocity_B_rad_s=np.zeros(3),
        time_s=0.0
    )
    
    control_calls = []
    
    def dummy_controller(t, obs):
        control_calls.append(t)
        return ControlCommand(collective_thrust_N=9.81, body_moments_Nm=np.zeros(3))
        
    result = runner.run(initial_state, dummy_controller)
    
    # 0.5s duration. Physics dt = 0.01 (50 steps). Control dt = 0.05 (10 steps). Telemetry dt = 0.1 (5 steps)
    assert len(control_calls) == 10
    # Telemetría en 0.0, 0.1, 0.2, 0.3, 0.4. (5 steps)
    assert len(result["telemetry"]) == 5
    assert result["termination_reason"] == "Time limit reached"

def test_termination_z_min():
    runner = setup_runner(max_dur=10.0)
    runner.z_min_m = 0.0
    
    initial_state = VehicleState(
        position_W_m=np.array([0.0, 0.0, 5.0]),
        velocity_W_m_s=np.array([0.0, 0.0, -10.0]), # Cayendo rápido
        orientation_WB=get_level_quaternion(0.0),
        angular_velocity_B_rad_s=np.zeros(3),
        time_s=0.0
    )
    
    def zero_thrust(t, obs):
        return ControlCommand(0.0, np.zeros(3))
        
    result = runner.run(initial_state, zero_thrust)
    assert "Crash: Z_W < z_min_m" in result["termination_reason"]
