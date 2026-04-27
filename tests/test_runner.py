import numpy as np
from simulador_quad.runner import SimulationRunner
from simulador_quad.core.contracts import VehicleParameters, VehicleState, ControlCommand, RotorParameters
from simulador_quad.dynamics.actuators import ActuatorSystem
from simulador_quad.dynamics.mixer import QuadcopterMixer
from simulador_quad.dynamics.perturbations import WindModel, ObservationNoise
from simulador_quad.core.frames import get_level_quaternion

def create_x_config_rotors():
    # Configuración en X clásica (FR, FL, BR, BL)
    L = 0.25
    return [
        RotorParameters(np.array([L, L, 0]), 1, 1.0, 0.1, 100.0, 0.0),
        RotorParameters(np.array([L, -L, 0]), -1, 1.0, 0.1, 100.0, 0.0),
        RotorParameters(np.array([-L, L, 0]), -1, 1.0, 0.1, 100.0, 0.0),
        RotorParameters(np.array([-L, -L, 0]), 1, 1.0, 0.1, 100.0, 0.0),
    ]

def setup_runner(max_dur=1.0, max_sat=1.0):
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
        z_min_m=-1.0,
        max_saturation_duration_s=max_sat
    )

def test_runner_multi_rate():
    runner = setup_runner(max_dur=0.5)
    
    initial_state = VehicleState(
        position_W_m=np.array([0.0, 0.0, 10.0]),
        velocity_W_m_s=np.zeros(3),
        orientation_WB=get_level_quaternion(0.0),
        angular_velocity_B_rad_s=np.zeros(3),
        time_s=0.0
    )
    
    control_calls = []
    
    class DummyTraj:
        def get_reference(self, time_s):
            from simulador_quad.core.contracts import TrajectoryReference
            return TrajectoryReference(np.zeros(3), np.zeros(3), np.zeros(3), 0.0)
            
    traj = DummyTraj()
        
    def dummy_controller(t, obs, ref):
        control_calls.append(t)
        return ControlCommand(collective_thrust_N=9.81, body_moments_Nm=np.zeros(3))
        
    result = runner.run(initial_state, dummy_controller, traj)
    
    # 0.5s duration. Physics dt = 0.01 (50 steps). Control dt = 0.05 (10 steps). Telemetry dt = 0.1 (5 steps)
    assert len(control_calls) == 10
    # Telemetría en 0.0, 0.1, 0.2, 0.3, 0.4. (5 steps)
    assert len(result["telemetry"]) == 5
    assert result["termination_reason"] == "Time limit reached"
    # Verificar que la observación se guardó
    assert np.allclose(result["telemetry"][0].observation.position_W_m, initial_state.position_W_m)

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
    
    class DummyTraj:
        def get_reference(self, time_s):
            from simulador_quad.core.contracts import TrajectoryReference
            return TrajectoryReference(np.zeros(3), np.zeros(3), np.zeros(3), 0.0)
            
    traj = DummyTraj()
        
    def zero_thrust(t, obs, ref):
        return ControlCommand(0.0, np.zeros(3))
        
    result = runner.run(initial_state, zero_thrust, traj)
    assert "Crash: Z_W < z_min_m" in result["termination_reason"]

def test_termination_saturation():
    # max_sat = 0.1s (10 pasos de física)
    runner = setup_runner(max_dur=10.0, max_sat=0.1)
    # Reducir omega_max para que no acelere tanto
    for r in runner.mixer.rotors:
        r.omega_max_rad_s = 10.0 # T_max_total = 400N
    
    runner.max_position_m = 1000.0 
    runner.max_velocity_m_s = 1000.0
    
    initial_state = VehicleState(
        position_W_m=np.array([0.0, 0.0, 10.0]),
        velocity_W_m_s=np.zeros(3),
        orientation_WB=get_level_quaternion(0.0),
        angular_velocity_B_rad_s=np.zeros(3),
        time_s=0.0
    )
    
    class DummyTraj:
        def get_reference(self, time_s):
            from simulador_quad.core.contracts import TrajectoryReference
            return TrajectoryReference(np.zeros(3), np.zeros(3), np.zeros(3), 0.0)
            
    traj = DummyTraj()
        
    def extreme_thrust_controller(t, obs, ref):
        # Pedir empuje imposible (1000N) para forzar degradación
        return ControlCommand(1000.0, np.zeros(3))
        
    result = runner.run(initial_state, extreme_thrust_controller, traj)
    assert "Persistent actuator saturation" in result["termination_reason"]
    # Debería haber terminado alrededor de 0.1s
    assert result["final_state"].time_s < 0.2
