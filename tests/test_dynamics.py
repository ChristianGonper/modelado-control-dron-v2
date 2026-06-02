import numpy as np
from simulador_quad.dynamics.rigid_body import rk4_step
from simulador_quad.core.frames import get_level_quaternion

def test_free_fall():
    mass = 1.0
    inertia = np.eye(3)
    gravity = 9.81
    dt = 0.1
    
    p0 = np.zeros(3)
    v0 = np.zeros(3)
    q0 = np.array([1.0, 0.0, 0.0, 0.0])
    w0 = np.zeros(3)
    
    force_W = np.zeros(3)
    torque_B = np.zeros(3)
    
    p1, v1, q1, w1 = rk4_step(p0, v0, q0, w0, mass, inertia, gravity, dt, force_W, torque_B)
    
    # v = gt, p = 1/2 g t^2 (hacia abajo, o sea Z negativo)
    assert np.isclose(v1[2], -gravity * dt)
    assert np.isclose(p1[2], -0.5 * gravity * dt**2)
    assert np.allclose(q1, q0)
    assert np.allclose(w1, w0)

def test_hover_level_frd_thrust_sign():
    """Hover with thrust along -Z_B (FRD); wrong sign (+Z_B) accelerates downward."""
    mass = 1.0
    inertia = np.eye(3)
    gravity = 9.81
    dt = 0.1

    p0 = np.zeros(3)
    v0 = np.zeros(3)
    q0 = get_level_quaternion(0.0)
    w0 = np.zeros(3)

    force_hover_B_N = np.array([0.0, 0.0, -mass * gravity])
    torque_B_Nm = np.zeros(3)

    p1, v1, _, _ = rk4_step(p0, v0, q0, w0, mass, inertia, gravity, dt, force_hover_B_N, torque_B_Nm)
    assert np.allclose(v1, v0, atol=1e-9)
    assert np.allclose(p1, p0, atol=1e-9)

    force_wrong_B_N = np.array([0.0, 0.0, mass * gravity])
    _, v_bad, _, _ = rk4_step(p0, v0, q0, w0, mass, inertia, gravity, dt, force_wrong_B_N, torque_B_Nm)
    assert v_bad[2] < -0.5 * gravity * dt


def test_ideal_hover():
    mass = 1.0
    inertia = np.eye(3)
    gravity = 9.81
    dt = 0.1
    
    p0 = np.zeros(3)
    v0 = np.zeros(3)
    q0 = np.array([1.0, 0.0, 0.0, 0.0])
    w0 = np.zeros(3)
    
    # Fuerza de empuje igual a la gravedad hacia arriba (en el mundo ENU)
    force_W = np.array([0.0, 0.0, mass * gravity])
    torque_B = np.zeros(3)
    
    p1, v1, q1, w1 = rk4_step(p0, v0, q0, w0, mass, inertia, gravity, dt, force_W, torque_B)
    
    assert np.allclose(v1, v0)
    assert np.allclose(p1, p0)
    assert np.allclose(q1, q0)
    assert np.allclose(w1, w0)

def test_orientation_conservation():
    mass = 1.0
    inertia = np.eye(3)
    gravity = 0.0
    dt = 1.0
    
    p0 = np.zeros(3)
    v0 = np.zeros(3)
    # Una orientación cualquiera
    q0 = np.array([0.5, 0.5, 0.5, 0.5])
    w0 = np.zeros(3)
    
    force_W = np.zeros(3)
    torque_B = np.zeros(3)
    
    p1, v1, q1, w1 = rk4_step(p0, v0, q0, w0, mass, inertia, gravity, dt, force_W, torque_B)
    
    assert np.allclose(q1, q0)
    assert np.allclose(w1, w0)

def test_rk4_simple_rotation():
    mass = 1.0
    inertia = np.eye(3)
    gravity = 0.0
    dt = 0.1
    
    p0 = np.zeros(3)
    v0 = np.zeros(3)
    q0 = np.array([1.0, 0.0, 0.0, 0.0])
    # Velocidad angular constante en X
    w0 = np.array([1.0, 0.0, 0.0])
    
    force_W = np.zeros(3)
    torque_B = np.zeros(3) # Sin torque, omega se mantiene constante (inercia diagonal)
    
    p1, v1, q1, w1 = rk4_step(p0, v0, q0, w0, mass, inertia, gravity, dt, force_W, torque_B)
    
    # Para omega = [1, 0, 0], el cuaternión en el tiempo dt será:
    # q(t) = [cos(w*t/2), sin(w*t/2), 0, 0]
    expected_q = np.array([np.cos(dt/2), np.sin(dt/2), 0.0, 0.0])
    
    assert np.allclose(w1, w0)
    assert np.allclose(q1, expected_q)


def test_rk4_preserves_quaternion_norm_over_long_run():
    mass_kg = 1.0
    inertia_B_kg_m2 = np.diag([0.02, 0.03, 0.04])
    gravity_m_s2 = 0.0
    dt_s = 0.01

    position_W_m = np.zeros(3)
    velocity_W_m_s = np.zeros(3)
    orientation_WB = get_level_quaternion(0.4)
    angular_velocity_B_rad_s = np.array([0.3, -0.2, 0.1])
    force_B_N = np.zeros(3)
    torque_B_Nm = np.zeros(3)

    for _ in range(1000):
        position_W_m, velocity_W_m_s, orientation_WB, angular_velocity_B_rad_s = rk4_step(
            position_W_m,
            velocity_W_m_s,
            orientation_WB,
            angular_velocity_B_rad_s,
            mass_kg,
            inertia_B_kg_m2,
            gravity_m_s2,
            dt_s,
            force_B_N,
            torque_B_Nm,
        )

    assert np.isclose(np.linalg.norm(orientation_WB), 1.0, atol=1e-12)
