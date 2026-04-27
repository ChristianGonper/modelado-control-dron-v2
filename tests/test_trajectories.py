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
        [1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0]
    ])
    times = np.array([0.0, 1.0, 2.0])
    traj = LineTrajectory(pts, times, yaw_rad=0.0)
    
    # t = 0.5 (medio camino entre p0 y p1)
    # tau = 0.5 -> s = 0.5 (posición mitad), ds/dtau = 1.5
    ref = traj.get_reference(0.5)
    assert np.allclose(ref.position_W_m, [0.5, 0.0, 0.0])
    assert np.allclose(ref.velocity_W_m_s, [1.5, 0.0, 0.0])
    
    # t = 1.5 (medio camino entre p1 y p2)
    ref2 = traj.get_reference(1.5)
    assert np.allclose(ref2.position_W_m, [1.0, 0.5, 0.0])
    assert np.allclose(ref2.velocity_W_m_s, [0.0, 1.5, 0.0])
    
    # Fuera de límites
    ref3 = traj.get_reference(-1.0)
    assert np.allclose(ref3.position_W_m, [0.0, 0.0, 0.0])
    
    ref4 = traj.get_reference(10.0)
    assert np.allclose(ref4.position_W_m, [1.0, 1.0, 0.0])
