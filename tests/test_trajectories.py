import numpy as np
from simulador_quad.trajectories.analytic import HoldTrajectory, CircleTrajectory, LissajousTrajectory

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
    # sin(pi) = 0, cos(pi) = -1
    # sin(pi/2) = 1, cos(pi/2) = 0
    assert np.allclose(ref1.position_W_m, [0.0, 2.0, 5.0])
    assert np.allclose(ref1.velocity_W_m_s, [-1.0*np.pi, 0.0, 0.0])
