import numpy as np
from simulador_quad.trajectories.analytic import HoldTrajectory, CircleTrajectory, LissajousTrajectory, LineTrajectory

def test_hold_trajectory():
    pos = np.array([1.0, 2.0, 3.0])
    yaw = 0.5
    traj = HoldTrajectory(pos, yaw)
    
    ref = traj.get_reference(10.0)
    
    assert np.allclose(ref.position_W_m, pos)
    assert np.allclose(ref.velocity_W_m_s, 0.0)
    assert np.allclose(ref.acceleration_W_m_s2, 0.0)
    assert ref.yaw_rad == yaw

def test_circle_trajectory():
    center = np.array([0.0, 0.0, 5.0])
    R = 2.0
    w = np.pi / 2.0 # 90 deg/s
    traj = CircleTrajectory(center, R, w, yaw_mode="forward")
    
    # t = 0
    ref0 = traj.get_reference(0.0)
    assert np.allclose(ref0.position_W_m, [2.0, 0.0, 5.0])
    assert np.allclose(ref0.velocity_W_m_s, [0.0, R*w, 0.0]) # en y
    assert np.allclose(ref0.acceleration_W_m_s2, [-R*w**2, 0.0, 0.0]) # en -x
    
    # t = 1.0 (90 grados)
    ref1 = traj.get_reference(1.0)
    assert np.allclose(ref1.position_W_m, [0.0, 2.0, 5.0])
    assert np.allclose(ref1.velocity_W_m_s, [-R*w, 0.0, 0.0]) # en -x
    
def test_lissajous_trajectory():
    center = np.array([0.0, 0.0, 5.0])
    A = np.array([1.0, 2.0, 0.0])
    w = np.array([np.pi, np.pi/2, 0.0])
    traj = LissajousTrajectory(center, A, w)
    
    # t = 1.0
    ref1 = traj.get_reference(1.0)
    assert np.allclose(ref1.position_W_m, [0.0, 2.0, 5.0])
    assert np.allclose(ref1.velocity_W_m_s, [-1.0*np.pi, 0.0, 0.0])

def test_line_trajectory():
    pts = np.array([
        [0.0, 0.0, 0.0],
        [2.0, 0.0, 0.0]
    ])
    # max_speed=0.6, max_acc=0.5
    # t_acc = 0.6 / 0.5 = 1.2s
    # d_acc = 0.5 * 0.5 * 1.2^2 = 0.36m
    # 2*d_acc = 0.72 < 2.0 -> Perfil trapezoidal
    # d_const = 2.0 - 0.72 = 1.28m
    # t_const = 1.28 / 0.6 = 2.133s
    # t_total = 1.2 + 2.133 + 1.2 = 4.533s
    
    traj = LineTrajectory(pts, max_speed_m_s=0.6, max_acceleration_m_s2=0.5, dwell_time_s=1.0)
    
    from simulador_quad.core.contracts import VehicleState
    from simulador_quad.core.frames import get_level_quaternion
    
    def get_state(t, pos=None, vel=None):
        return VehicleState(
            position_W_m=np.array(pos if pos is not None else [0,0,0]).astype(float),
            velocity_W_m_s=np.array(vel if vel is not None else [0,0,0]).astype(float),
            orientation_WB=get_level_quaternion(0.0),
            angular_velocity_B_rad_s=np.zeros(3),
            time_s=t
        )

    # Inicio
    ref0 = traj.get_reference_for_state(0.0, get_state(0.0))
    assert np.allclose(ref0.position_W_m, [0,0,0])
    assert traj.phase.value == "MOVE_TO_WAYPOINT"

    # t = 1.2s (final de aceleración)
    ref1 = traj.get_reference_for_state(1.2, get_state(1.2))
    assert np.allclose(ref1.position_W_m, [0.36, 0.0, 0.0])
    assert np.allclose(ref1.velocity_W_m_s, [0.6, 0.0, 0.0])
    
    # t = 4.533333333s (llegada nominal)
    t_total = 1.2 + 1.28 / 0.6 + 1.2
    ref2 = traj.get_reference_for_state(t_total, get_state(t_total))
    assert np.allclose(ref2.position_W_m, [2.0, 0.0, 0.0], atol=1e-5)
    assert np.allclose(ref2.velocity_W_m_s, [0.0, 0.0, 0.0], atol=1e-5)
    # Debería haber cambiado a HOLD_AT_WAYPOINT en la siguiente llamada o al final de esta
    assert traj.phase.value == "HOLD_AT_WAYPOINT"
    
    # Simular dwell: estar fuera de tolerancia
    # Seguimos en HOLD_AT_WAYPOINT, dwell no acumula
    ref3 = traj.get_reference_for_state(t_total + 0.5, get_state(t_total + 0.5, pos=[1.5, 0, 0]))
    assert traj.dwell_timer_s == 0.0
    
    # Simular dwell: estar dentro de tolerancia
    ref4 = traj.get_reference_for_state(t_total + 1.0, get_state(t_total + 1.0, pos=[2.0, 0, 0], vel=[0,0,0]))
    assert traj.dwell_timer_s > 0.0
    
    # Esperar a completar dwell (1.0s)
    ref5 = traj.get_reference_for_state(t_total + 2.0, get_state(t_total + 2.0, pos=[2.0, 0, 0], vel=[0,0,0]))
    assert traj.completed == True
    
    term, reason = traj.check_completion(t_total + 2.0, get_state(t_total + 2.0), 0.01)
    assert term == True
    assert reason == "Trajectory completed"

def test_line_trajectory_triangular():
    pts = np.array([[0,0,0], [0.5, 0, 0]])
    # L = 0.5. 2*d_acc = 0.72 > 0.5 -> Perfil triangular
    # t_acc_tri = sqrt(0.5 / 0.5) = 1.0s
    # t_total = 2.0s
    # v_peak = 0.5 * 1.0 = 0.5 m/s
    traj = LineTrajectory(pts, max_speed_m_s=0.6, max_acceleration_m_s2=0.5)
    
    from simulador_quad.core.contracts import VehicleState
    from simulador_quad.core.frames import get_level_quaternion
    
    def get_state(t):
        return VehicleState([0,0,0], [0,0,0], get_level_quaternion(0.0), [0,0,0], t)
        
    ref0 = traj.get_reference_for_state(0.0, get_state(0.0))
    # t = 1.0s (pico)
    ref1 = traj.get_reference_for_state(1.0, get_state(1.0))
    assert np.allclose(ref1.position_W_m, [0.25, 0.0, 0.0])
    assert np.allclose(ref1.velocity_W_m_s, [0.5, 0.0, 0.0])
    
    # t = 2.0s (final)
    ref2 = traj.get_reference_for_state(2.0, get_state(2.0))
    assert np.allclose(ref2.position_W_m, [0.5, 0.0, 0.0])
    assert np.allclose(ref2.velocity_W_m_s, [0.0, 0.0, 0.0])
