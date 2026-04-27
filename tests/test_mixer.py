import numpy as np
from simulador_quad.core.contracts import RotorParameters
from simulador_quad.dynamics.mixer import QuadcopterMixer

def create_x_config_rotors():
    # Configuración en X clásica
    # 0 (FR): +x, +y, CCW (s=1)
    # 1 (FL): +x, -y, CW (s=-1)
    # 2 (BR): -x, +y, CW (s=-1)
    # 3 (BL): -x, -y, CCW (s=1)
    L = 0.25
    kf = 1.0
    km = 0.1
    return [
        RotorParameters(np.array([L, L, 0]), 1, kf, km, 100.0, 0.0),    # Front-Right (CCW)
        RotorParameters(np.array([L, -L, 0]), -1, kf, km, 100.0, 0.0),  # Front-Left (CW)
        RotorParameters(np.array([-L, L, 0]), -1, kf, km, 100.0, 0.0),  # Back-Right (CW)
        RotorParameters(np.array([-L, -L, 0]), 1, kf, km, 100.0, 0.0),   # Back-Left (CCW)
    ]

def test_mixer_hover():
    rotors = create_x_config_rotors()
    mixer = QuadcopterMixer(rotors)
    
    # Solo empuje de 40 N
    res = mixer.compute_rotor_commands(thrust_N=40.0, moments_Nm=np.zeros(3))
    omega = res.target_omega_rad_s
    
    # Cada rotor da 10 N -> omega = sqrt(10 / 1.0) = 3.162
    assert np.allclose(omega, np.sqrt(10.0))
    assert np.allclose(res.target_thrust_N, 10.0)
    assert res.degraded_collective_thrust == False

def test_mixer_pitch():
    rotors = create_x_config_rotors()
    mixer = QuadcopterMixer(rotors)
    
    # Empuje 40N, pitch = +1.0 Nm (morro hacia arriba / nose up)
    res = mixer.compute_rotor_commands(thrust_N=40.0, moments_Nm=np.array([0.0, 1.0, 0.0]))
    omega = res.target_omega_rad_s
    
    T_front = 11.0
    T_back = 9.0
    expected_omega = np.array([np.sqrt(T_front), np.sqrt(T_front), np.sqrt(T_back), np.sqrt(T_back)])
    
    assert np.allclose(omega, expected_omega)
    assert res.degraded_collective_thrust == False

def test_mixer_saturation():
    rotors = create_x_config_rotors()
    # Poner límite muy bajo para forzar saturación
    for r in rotors:
        r.omega_max_rad_s = 5.0 # Max thrust = 25N por rotor -> max 100N total
        
    mixer = QuadcopterMixer(rotors)
    
    # Pedir empuje máximo (100) más momento pitch (requeriría que frontales superen 25)
    res = mixer.compute_rotor_commands(thrust_N=100.0, moments_Nm=np.array([0.0, 1.0, 0.0]))
    omega = res.target_omega_rad_s
    
    # La máxima omega debe ser 5.0
    assert np.max(omega) <= 5.0 + 1e-9
    
    # Con tau_y = 1.0, T_front > T_back.
    # T_front saturará a 25. T_back será 23.
    assert np.isclose(omega[0], 5.0)
    assert np.isclose(omega[1], 5.0)
    assert np.isclose(omega[2]**2, 23.0)
    assert np.isclose(omega[3]**2, 23.0)
    
    # Como hubo que bajar el empuje para mantener el momento, debe estar marcado como degradado
    assert res.degraded_collective_thrust == True
