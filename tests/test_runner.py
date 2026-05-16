import numpy as np
from simulador_quad.runner import SimulationRunner
from simulador_quad.core.contracts import VehicleParameters, VehicleState, ControlCommand, RotorParameters
from simulador_quad.dynamics.actuators import ActuatorSystem
from simulador_quad.dynamics.mixer import QuadcopterMixer
from simulador_quad.dynamics.perturbations import WindModel, ObservationNoise
from simulador_quad.core.frames import get_level_quaternion
from simulador_quad.core.attitude import quaternion_multiply

def create_x_config_rotors(time_constant_s=0.0):
    # Configuración en X clásica (FR, FL, BR, BL)
    L = 0.25
    return [
        RotorParameters(np.array([L, L, 0]), 1, 1.0, 0.1, 100.0, time_constant_s),
        RotorParameters(np.array([L, -L, 0]), -1, 1.0, 0.1, 100.0, time_constant_s),
        RotorParameters(np.array([-L, L, 0]), -1, 1.0, 0.1, 100.0, time_constant_s),
        RotorParameters(np.array([-L, -L, 0]), 1, 1.0, 0.1, 100.0, time_constant_s),
    ]

def setup_runner(max_dur=1.0, max_sat=1.0, physics_dt_s=0.01, control_dt_s=0.05, telemetry_dt_s=0.1, rotor_time_constant_s=0.0):
    rotors = create_x_config_rotors(time_constant_s=rotor_time_constant_s)
    v_params = VehicleParameters(
        mass_kg=1.0,
        inertia_B_kg_m2=np.eye(3)*0.01,
        gravity_m_s2=9.81,
        linear_drag_coefficient=np.zeros(3),
        rotors=rotors
    )
    mixer = QuadcopterMixer(rotors)
    actuators = ActuatorSystem(rotors, dt_s=physics_dt_s)
    wind = WindModel(np.zeros(3))
    noise = ObservationNoise()
    
    return SimulationRunner(
        physics_dt_s=physics_dt_s,
        control_dt_s=control_dt_s,
        telemetry_dt_s=telemetry_dt_s,
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
    
    # 0.5s duration. Physics dt = 0.01 (50 steps). Control dt = 0.05.
    # Con el nuevo runner, se registra la telemetría y el control en t=0.5 antes de terminar.
    # Puntos de control: 0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5 -> 11 puntos
    assert len(control_calls) == 11
    # Telemetría en 0.0, 0.1, 0.2, 0.3, 0.4, 0.5. (6 steps)
    assert len(result["telemetry"]) == 6
    assert result["termination_reason"] == "Time limit reached"
    # Verificar que la observación se guardó
    assert np.allclose(result["telemetry"][0].observation.position_W_m, initial_state.position_W_m)


def test_zoh_keeps_control_command_while_actuators_evolve_at_physics_dt():
    runner = setup_runner(
        max_dur=0.06,
        physics_dt_s=0.01,
        control_dt_s=0.1,
        telemetry_dt_s=0.01,
        rotor_time_constant_s=0.05,
    )

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

    control_calls = []

    def constant_controller(t, obs, ref):
        control_calls.append(t)
        return ControlCommand(collective_thrust_N=100.0, body_moments_Nm=np.zeros(3))

    result = runner.run(initial_state, constant_controller, DummyTraj())
    applied_omega_rad_s = np.array(
        [sample.rotor_applied.applied_omega_rad_s[0] for sample in result["telemetry"]]
    )
    commanded_thrust_N = np.array(
        [sample.control_command.collective_thrust_N for sample in result["telemetry"]]
    )

    assert len(control_calls) == 1
    assert np.allclose(commanded_thrust_N, 100.0)
    assert np.all(np.diff(applied_omega_rad_s) > 0.0)


def test_actuators_start_from_hover_not_zero():
    runner = setup_runner(
        max_dur=0.01,
        physics_dt_s=0.01,
        control_dt_s=0.1,
        telemetry_dt_s=0.01,
        rotor_time_constant_s=0.05,
    )

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

    def hover_controller(t, obs, ref):
        return ControlCommand(collective_thrust_N=9.81, body_moments_Nm=np.zeros(3))

    result = runner.run(initial_state, hover_controller, DummyTraj())
    first = result["telemetry"][0]

    assert np.isclose(np.sum(first.rotor_applied.applied_thrust_N), 9.81)
    assert np.all(first.rotor_applied.applied_omega_rad_s > 0.0)

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


def test_termination_position_velocity_non_finite_and_attitude_limits():
    runner = setup_runner(max_dur=10.0)
    level_orientation = get_level_quaternion(0.0)

    base_state = VehicleState(
        position_W_m=np.array([0.0, 0.0, 10.0]),
        velocity_W_m_s=np.zeros(3),
        orientation_WB=level_orientation,
        angular_velocity_B_rad_s=np.zeros(3),
        time_s=0.0
    )

    out_of_position = VehicleState(
        position_W_m=np.array([runner.max_position_m + 1.0, 0.0, 10.0]),
        velocity_W_m_s=base_state.velocity_W_m_s,
        orientation_WB=base_state.orientation_WB,
        angular_velocity_B_rad_s=base_state.angular_velocity_B_rad_s,
        time_s=0.0
    )
    assert runner._check_safety_termination(out_of_position, False) == (True, "Out of position bounds")

    out_of_velocity = VehicleState(
        position_W_m=base_state.position_W_m,
        velocity_W_m_s=np.array([runner.max_velocity_m_s + 1.0, 0.0, 0.0]),
        orientation_WB=base_state.orientation_WB,
        angular_velocity_B_rad_s=base_state.angular_velocity_B_rad_s,
        time_s=0.0
    )
    assert runner._check_safety_termination(out_of_velocity, False) == (True, "Out of velocity bounds")

    non_finite = VehicleState(
        position_W_m=np.array([0.0, np.nan, 10.0]),
        velocity_W_m_s=base_state.velocity_W_m_s,
        orientation_WB=base_state.orientation_WB,
        angular_velocity_B_rad_s=base_state.angular_velocity_B_rad_s,
        time_s=0.0
    )
    assert runner._check_safety_termination(non_finite, False) == (True, "Non-finite values in state")

    runner.max_attitude_angle_rad = 0.2
    roll_rad = 1.0
    roll_quaternion = np.array([np.cos(roll_rad / 2.0), np.sin(roll_rad / 2.0), 0.0, 0.0])
    tilted_orientation = quaternion_multiply(level_orientation, roll_quaternion)
    tilted = VehicleState(
        position_W_m=base_state.position_W_m,
        velocity_W_m_s=base_state.velocity_W_m_s,
        orientation_WB=tilted_orientation,
        angular_velocity_B_rad_s=base_state.angular_velocity_B_rad_s,
        time_s=0.0
    )
    terminated, reason = runner._check_safety_termination(tilted, False)
    assert terminated
    assert "Attitude angle exceeded limit" in reason

def test_trajectory_completion_termination():
    runner = setup_runner(max_dur=10.0)

    # Trayectoria que termina en t=1.0s nominalmente (para dwell)
    from simulador_quad.trajectories.analytic import LineTrajectory
    pts = np.array([[0,0,10], [1,0,10]])
    traj = LineTrajectory(pts, max_speed_m_s=0.6, max_acceleration_m_s2=0.5, dwell_time_s=0.4)

    # Simular avance de tiempo y estado para que la trayectoria progrese internamente
    # 1. Inicio
    traj.get_reference_for_state(0.0, VehicleState(pts[0], [0,0,0], get_level_quaternion(0.0), [0,0,0], 0.0))
    # 2. Llegada (nominal t_total ~ 2.86s para L=1, v=0.6, a=0.5)
    t_arrival = 1.2 + (1.0 - 0.72)/0.6 + 1.2
    traj.get_reference_for_state(t_arrival, VehicleState(pts[1], [0,0,0], get_level_quaternion(0.0), [0,0,0], t_arrival))
    
    # 3. Dwell (dwell_time=0.40)
    t_done = t_arrival + 0.5
    state = VehicleState(
        position_W_m=np.array([1.05, 0.0, 10.0]), # error 0.05 < 0.20
        velocity_W_m_s=np.array([0.1, 0.0, 0.0]),  # speed 0.1 < 0.20
        orientation_WB=get_level_quaternion(0.0),
        angular_velocity_B_rad_s=np.zeros(3),
        time_s=t_done
    )
    traj.get_reference_for_state(t_done, state)

    term, reason = runner._check_trajectory_completion(state, traj)
    assert term
    assert reason == "Trajectory completed"

    # Estado fuera de tolerancia de posición
    traj.reset()
    traj.get_reference_for_state(0.0, VehicleState(pts[0], [0,0,0], get_level_quaternion(0.0), [0,0,0], 0.0))
    traj.get_reference_for_state(t_arrival, VehicleState(pts[1], [0,0,0], get_level_quaternion(0.0), [0,0,0], t_arrival))
    
    state_far = VehicleState(
        position_W_m=np.array([1.3, 0.0, 10.0]), # error 0.3 > 0.20
        velocity_W_m_s=np.array([0.1, 0.0, 0.0]),
        orientation_WB=get_level_quaternion(0.0),
        angular_velocity_B_rad_s=np.zeros(3),
        time_s=t_done
    )
    traj.get_reference_for_state(t_done, state_far)
    term, reason = runner._check_trajectory_completion(state_far, traj)
    assert not term
