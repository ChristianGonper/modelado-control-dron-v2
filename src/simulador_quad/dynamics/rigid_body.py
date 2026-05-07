import numpy as np
from typing import Callable, Tuple
from simulador_quad.core.attitude import normalize_quaternion, quaternion_multiply, body_to_world, world_to_body

def compute_state_derivative(
    position_W_m: np.ndarray,
    velocity_W_m_s: np.ndarray,
    orientation_WB: np.ndarray,
    angular_velocity_B_rad_s: np.ndarray,
    mass_kg: float,
    inertia_B_kg_m2: np.ndarray,
    gravity_m_s2: float,
    force_B_N: np.ndarray,
    torque_B_Nm: np.ndarray,
    wind_W_m_s: np.ndarray = np.zeros(3),
    drag_coeff: np.ndarray = np.zeros(3)
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula la derivada del estado del cuerpo rígido.
    Devuelve (dot_p, dot_v, dot_q, dot_omega).
    """
    # Posición
    dot_p = velocity_W_m_s
    
    # Velocidad
    force_W_N = body_to_world(orientation_WB, force_B_N)
    
    v_rel_W = velocity_W_m_s - wind_W_m_s
    v_rel_B = world_to_body(orientation_WB, v_rel_W)
    drag_B = -drag_coeff * v_rel_B
    drag_W = body_to_world(orientation_WB, drag_B)
    
    gravity_force_W = np.array([0.0, 0.0, -mass_kg * gravity_m_s2])
    total_force_W = force_W_N + drag_W + gravity_force_W
    dot_v = total_force_W / mass_kg
    
    # Actitud
    q_omega = np.array([0.0, angular_velocity_B_rad_s[0], angular_velocity_B_rad_s[1], angular_velocity_B_rad_s[2]])
    dot_q = 0.5 * quaternion_multiply(orientation_WB, q_omega)
    
    # Velocidad angular
    I_inv = np.linalg.inv(inertia_B_kg_m2)
    angular_momentum = inertia_B_kg_m2 @ angular_velocity_B_rad_s
    cross_term = np.cross(angular_velocity_B_rad_s, angular_momentum)
    dot_omega = I_inv @ (torque_B_Nm - cross_term)
    
    return dot_p, dot_v, dot_q, dot_omega

def rk4_step(
    position_W_m: np.ndarray,
    velocity_W_m_s: np.ndarray,
    orientation_WB: np.ndarray,
    angular_velocity_B_rad_s: np.ndarray,
    mass_kg: float,
    inertia_B_kg_m2: np.ndarray,
    gravity_m_s2: float,
    dt_s: float,
    force_B_N: np.ndarray,
    torque_B_Nm: np.ndarray,
    wind_W_m_s: np.ndarray = np.zeros(3),
    drag_coeff: np.ndarray = np.zeros(3)
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Realiza un paso de integración RK4.
    """
    def f(p, v, q, w):
        q_norm = normalize_quaternion(q)
        return compute_state_derivative(
            p, v, q_norm, w, mass_kg, inertia_B_kg_m2, gravity_m_s2, force_B_N, torque_B_Nm, wind_W_m_s, drag_coeff
        )
    
    p0, v0, q0, w0 = position_W_m, velocity_W_m_s, orientation_WB, angular_velocity_B_rad_s
    
    # k1
    dp1, dv1, dq1, dw1 = f(p0, v0, q0, w0)
    
    # k2
    p2 = p0 + 0.5 * dt_s * dp1
    v2 = v0 + 0.5 * dt_s * dv1
    q2 = q0 + 0.5 * dt_s * dq1
    w2 = w0 + 0.5 * dt_s * dw1
    dp2, dv2, dq2, dw2 = f(p2, v2, q2, w2)
    
    # k3
    p3 = p0 + 0.5 * dt_s * dp2
    v3 = v0 + 0.5 * dt_s * dv2
    q3 = q0 + 0.5 * dt_s * dq2
    w3 = w0 + 0.5 * dt_s * dw2
    dp3, dv3, dq3, dw3 = f(p3, v3, q3, w3)
    
    # k4
    p4 = p0 + dt_s * dp3
    v4 = v0 + dt_s * dv3
    q4 = q0 + dt_s * dq3
    w4 = w0 + dt_s * dw3
    dp4, dv4, dq4, dw4 = f(p4, v4, q4, w4)
    
    # Integración
    p_new = p0 + (dt_s / 6.0) * (dp1 + 2*dp2 + 2*dp3 + dp4)
    v_new = v0 + (dt_s / 6.0) * (dv1 + 2*dv2 + 2*dv3 + dv4)
    q_new = q0 + (dt_s / 6.0) * (dq1 + 2*dq2 + 2*dq3 + dq4)
    w_new = w0 + (dt_s / 6.0) * (dw1 + 2*dw2 + 2*dw3 + dw4)
    
    # Normalizar cuaternión
    q_new = normalize_quaternion(q_new)
    
    return p_new, v_new, q_new, w_new
