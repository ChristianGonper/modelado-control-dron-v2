import numpy as np
from simulador_quad.dynamics.rigid_body import rk4_step

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
