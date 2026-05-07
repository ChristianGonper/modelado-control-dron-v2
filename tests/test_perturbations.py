import numpy as np
from simulador_quad.dynamics.perturbations import compute_linear_drag, ObservationNoise
from simulador_quad.core.frames import get_level_quaternion

def test_linear_drag():
    q_id = np.array([1.0, 0.0, 0.0, 0.0])
    drag_coeff = np.array([0.1, 0.1, 0.2])
    
    # 1. Sin velocidad relativa
    v = np.array([5.0, 0.0, 0.0])
    v_wind = np.array([5.0, 0.0, 0.0])
    F_drag = compute_linear_drag(v, v_wind, q_id, drag_coeff)
    assert np.allclose(F_drag, 0.0)
    
    # 2. Viento nulo, el dron se mueve en X
    v = np.array([10.0, 0.0, 0.0])
    v_wind = np.array([0.0, 0.0, 0.0])
    F_drag = compute_linear_drag(v, v_wind, q_id, drag_coeff)
    # F_drag_B = -D * v_rel_B = -[0.1, 0.1, 0.2] * [10, 0, 0] = [-1, 0, 0]
    # En mundo, igual porque q es identidad. Ojo, q identidad mapea ejes directamente.
    assert np.allclose(F_drag, [-1.0, 0.0, 0.0])
    # El drag se opone a la velocidad
    assert np.dot(F_drag, v) < 0

def test_observation_noise_reproducibility():
    noise1 = ObservationNoise(pos_std_m=0.1, vel_std_m_s=0.2, seed=123)
    noise2 = ObservationNoise(pos_std_m=0.1, vel_std_m_s=0.2, seed=123)
    
    p0 = np.zeros(3)
    v0 = np.zeros(3)
    
    p1_noisy, v1_noisy = noise1.apply_noise(p0, v0)
    p2_noisy, v2_noisy = noise2.apply_noise(p0, v0)
    
    assert np.allclose(p1_noisy, p2_noisy)
    assert np.allclose(v1_noisy, v2_noisy)
    
    # Comprobar que no es exactamente cero (aunque con semilla 123 es muy poco probable)
    assert not np.allclose(p1_noisy, p0)


def test_linear_drag_is_dissipative_with_yawed_level_orientation():
    orientation_WB = get_level_quaternion(yaw_rad=np.pi / 2.0)
    velocity_W_m_s = np.array([3.0, -4.0, 0.5])
    wind_velocity_W_m_s = np.array([-1.0, 0.5, 0.0])
    drag_coeff = np.array([0.2, 0.1, 0.05])

    force_drag_W_N = compute_linear_drag(
        velocity_W_m_s,
        wind_velocity_W_m_s,
        orientation_WB,
        drag_coeff,
    )

    relative_velocity_W_m_s = velocity_W_m_s - wind_velocity_W_m_s
    assert np.dot(force_drag_W_N, relative_velocity_W_m_s) < 0.0
