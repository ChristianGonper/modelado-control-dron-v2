import numpy as np
from simulador_quad.core.contracts import RotorParameters
from simulador_quad.dynamics.mixer import QuadcopterMixer

def create_x_config_rotors():
    # Configuración en X clásica
    L = 0.25
    return [
        RotorParameters(np.array([L, L, 0]), -1, 1.0, 0.1, 100.0, 0.0),   # Front-Right (CCW)
        RotorParameters(np.array([L, -L, 0]), 1, 1.0, 0.1, 100.0, 0.0),   # Front-Left (CW)
        RotorParameters(np.array([-L, L, 0]), 1, 1.0, 0.1, 100.0, 0.0),   # Back-Right (CW)
        RotorParameters(np.array([-L, -L, 0]), -1, 1.0, 0.1, 100.0, 0.0), # Back-Left (CCW)
    ]

def test_mixer_hover():
    rotors = create_x_config_rotors()
    mixer = QuadcopterMixer(rotors)
    
    # Solo empuje de 40 N
    omega = mixer.compute_rotor_commands(thrust_N=40.0, moments_Nm=np.zeros(3))
    
    # Cada rotor da 10 N -> omega = sqrt(10 / 1.0) = 3.162
    assert np.allclose(omega, np.sqrt(10.0))

def test_mixer_pitch():
    rotors = create_x_config_rotors()
    mixer = QuadcopterMixer(rotors)
    
    # Empuje 40N, pitch = -1.0 Nm (morro hacia arriba)
    omega = mixer.compute_rotor_commands(thrust_N=40.0, moments_Nm=np.array([0.0, -1.0, 0.0]))
    
    # Pitch es tau_y. Los frontales (0 y 1) están en x=L (0.25). Los traseros en x=-L.
    # tau_y = sum(-x_i * T_i) = -0.25*(T0 + T1) + 0.25*(T2 + T3)
    # T0 + T1 + T2 + T3 = 40
    # Queremos tau_y = -1.0
    # Entonces -0.25*(T0+T1) + 0.25*(T2+T3) = -1.0 -> (T0+T1) - (T2+T3) = 4.0
    # Como hay simetría en Y, T0=T1 y T2=T3
    # 2*T0 - 2*T2 = 4 -> T0 - T2 = 2
    # 2*T0 + 2*T2 = 40 -> T0 + T2 = 20
    # Resolviendo: T0 = 11, T2 = 9
    
    T_front = 11.0
    T_back = 9.0
    expected_omega = np.array([np.sqrt(T_front), np.sqrt(T_front), np.sqrt(T_back), np.sqrt(T_back)])
    
    assert np.allclose(omega, expected_omega)

def test_mixer_saturation():
    rotors = create_x_config_rotors()
    # Poner límite muy bajo para forzar saturación
    for r in rotors:
        r.omega_max_rad_s = 5.0 # Max thrust = 25N por rotor -> max 100N total
        
    mixer = QuadcopterMixer(rotors)
    
    # Pedir empuje máximo (100) más momento (requeriría que algunos rotores superen 25)
    omega = mixer.compute_rotor_commands(thrust_N=100.0, moments_Nm=np.array([0.0, -1.0, 0.0]))
    
    # Debe priorizar el momento reduciendo el empuje
    # T0 y T1 requerirían > 25, así que se saturan a 25.
    # T2 y T3 bajan para cumplir la diferencia (momento).
    # La máxima omega debe ser 5.0
    assert np.max(omega) <= 5.0
    # De hecho, los delanteros deberían saturar
    assert np.isclose(omega[0], 5.0)
    assert np.isclose(omega[1], 5.0)
    
    # T0 = T1 = 25. 
    # El offset aplicado baja todos por igual.
    # Originalmente pedíamos T_front = 25+1=26, T_back = 25-1=24
    # Max violation = 26 - 25 = 1
    # T_req -= 1 -> T_front = 25, T_back = 23
    assert np.isclose(omega[2]**2, 23.0)
    assert np.isclose(omega[3]**2, 23.0)
