import numpy as np

def normalize_quaternion(q: np.ndarray) -> np.ndarray:
    """Normaliza un cuaternión [w, x, y, z]."""
    norm = np.linalg.norm(q)
    if norm < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0])
    return q / norm

def quaternion_multiply(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Producto de cuaterniones q1 * q2."""
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    ])

def quaternion_conjugate(q: np.ndarray) -> np.ndarray:
    """Conjugado de un cuaternión."""
    return np.array([q[0], -q[1], -q[2], -q[3]])

def quaternion_to_rotation_matrix(q: np.ndarray) -> np.ndarray:
    """Convierte un cuaternión a matriz de rotación."""
    w, x, y, z = normalize_quaternion(q)
    return np.array([
        [1 - 2*(y**2 + z**2), 2*(x*y - w*z),     2*(x*z + w*y)],
        [2*(x*y + w*z),     1 - 2*(x**2 + z**2), 2*(y*z - w*x)],
        [2*(x*z - w*y),     2*(y*z + w*x),     1 - 2*(x**2 + y**2)]
    ])

def rotate_vector(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rota un vector v usando el cuaternión q. Equivalente a R(q) * v."""
    q_v = np.array([0.0, v[0], v[1], v[2]])
    q_out = quaternion_multiply(quaternion_multiply(q, q_v), quaternion_conjugate(q))
    return q_out[1:]

def body_to_world(q_WB: np.ndarray, v_B: np.ndarray) -> np.ndarray:
    """Rota un vector del sistema de cuerpo al sistema de mundo."""
    return rotate_vector(q_WB, v_B)

def world_to_body(q_WB: np.ndarray, v_W: np.ndarray) -> np.ndarray:
    """Rota un vector del sistema de mundo al sistema de cuerpo."""
    q_BW = quaternion_conjugate(q_WB)
    return rotate_vector(q_BW, v_W)

def quaternion_error(q_des: np.ndarray, q_act: np.ndarray) -> np.ndarray:
    """
    Calcula el error de actitud para el controlador clásico.
    q_err = q_act^-1 * q_des
    """
    q_act_inv = quaternion_conjugate(q_act)  # Asumiendo unitario
    return quaternion_multiply(q_act_inv, q_des)
