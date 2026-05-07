import numpy as np
from simulador_quad.core.attitude import (
    normalize_quaternion,
    body_to_world,
    world_to_body,
    quaternion_to_rotation_matrix
)

def test_quaternion_normalization():
    q = np.array([2.0, 0.0, 0.0, 0.0])
    q_norm = normalize_quaternion(q)
    assert np.isclose(np.linalg.norm(q_norm), 1.0)
    assert np.allclose(q_norm, [1.0, 0.0, 0.0, 0.0])
    
    q_zero = np.array([0.0, 0.0, 0.0, 0.0])
    q_zero_norm = normalize_quaternion(q_zero)
    assert np.isclose(np.linalg.norm(q_zero_norm), 1.0)

def test_identity_rotation():
    q_id = np.array([1.0, 0.0, 0.0, 0.0])
    v = np.array([1.0, 2.0, 3.0])
    
    v_W = body_to_world(q_id, v)
    assert np.allclose(v_W, v)
    
    v_B = world_to_body(q_id, v)
    assert np.allclose(v_B, v)

def test_thrust_sign_enu_frd():
    from simulador_quad.core.frames import get_level_quaternion
    # Con actitud nivelada (FRD a ENU)
    q_level = get_level_quaternion(yaw_rad=0.0)
    
    # Empuje en cuerpo (FRD): rotores empujan Z negativo (hacia arriba del dron)
    T = 15.0 # N
    F_thrust_B = np.array([0.0, 0.0, -T])
    
    F_thrust_W = body_to_world(q_level, F_thrust_B)
    
    # En ENU, Z es arriba. La fuerza debe ser positiva en Z.
    assert F_thrust_W[2] > 0
    assert np.isclose(F_thrust_W[2], T)


def test_level_enu_frd_axes_yaw_zero():
    from simulador_quad.core.frames import get_level_quaternion

    q_level = get_level_quaternion(yaw_rad=0.0)

    x_front_B = np.array([1.0, 0.0, 0.0])
    y_right_B = np.array([0.0, 1.0, 0.0])
    z_down_B = np.array([0.0, 0.0, 1.0])

    assert np.allclose(body_to_world(q_level, x_front_B), [0.0, 1.0, 0.0])
    assert np.allclose(body_to_world(q_level, y_right_B), [1.0, 0.0, 0.0])
    assert np.allclose(body_to_world(q_level, z_down_B), [0.0, 0.0, -1.0])

