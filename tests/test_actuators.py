import numpy as np
from simulador_quad.core.contracts import RotorParameters
from simulador_quad.dynamics.actuators import FirstOrderLagDelay, ActuatorSystem

def test_first_order_lag():
    dt = 0.01
    tau = 0.1
    delay = 0.0
    f = FirstOrderLagDelay(tau, delay, dt)
    f.reset(0.0)
    
    val1 = f.step(1.0)
    val2 = f.step(1.0)
    val3 = f.step(1.0)
    
    # Debe ser monotónico creciente y asintótico a 1.0
    assert val1 > 0.0
    assert val2 > val1
    assert val3 > val2
    assert val3 < 1.0
    
    # Verificar valor concreto con alpha = 1 - exp(-dt/tau)
    alpha = 1.0 - np.exp(-dt / tau)
    expected_val1 = 0.0 + alpha * (1.0 - 0.0)
    assert np.isclose(val1, expected_val1)

def test_pure_delay():
    dt = 0.1
    tau = 0.0
    delay = 0.3 # 3 pasos
    f = FirstOrderLagDelay(tau, delay, dt)
    f.reset(0.0)
    
    assert np.isclose(f.step(1.0), 0.0)
    assert np.isclose(f.step(2.0), 0.0)
    assert np.isclose(f.step(3.0), 0.0)
    assert np.isclose(f.step(4.0), 1.0)
    assert np.isclose(f.step(5.0), 2.0)

def test_actuator_system_forces():
    # Un solo rotor para probar
    # turning_direction = 1 (CCW) -> Reacción CW -> +Z en FRD
    rotor = RotorParameters(
        position_B_m=np.array([1.0, 0.0, 0.0]),
        turning_direction=1,
        k_f=1.0,
        k_m=0.1,
        omega_max_rad_s=10.0,
        time_constant_s=0.0,
        delay_s=0.0
    )
    
    sys = ActuatorSystem([rotor], dt_s=0.1)
    target_omega = np.array([5.0])
    
    res, total_torque, total_thrust = sys.compute_applied_forces(target_omega)
    
    assert np.isclose(res.applied_omega_rad_s[0], 5.0)
    # T = k_f * omega^2 = 1.0 * 25.0 = 25.0
    assert np.isclose(res.applied_thrust_N[0], 25.0)
    # Q = s * k_m * omega^2 = 1 * 0.1 * 25.0 = 2.5
    assert np.isclose(res.applied_torque_Nm[0], 2.5)
    # RPM = 5.0 * 60 / (2*pi) = 300 / 6.28 = 47.74
    assert np.isclose(res.rotor_speed_rpm[0], 5.0 * 60.0 / (2.0 * np.pi))
    assert res.saturation_flags[0] == False
    
    # Thrust en B es [0, 0, -T]
    assert np.allclose(total_thrust, [0.0, 0.0, -25.0])
    
    # Torque:
    # torque_pos = r x F = [1, 0, 0] x [0, 0, -25] = [0, 25, 0]
    # torque_drag = [0, 0, 2.5]
    assert np.allclose(total_torque, [0.0, 25.0, 2.5])

def test_saturation():
    rotor = RotorParameters(
        position_B_m=np.array([0.0, 0.0, 0.0]),
        turning_direction=1,
        k_f=1.0,
        k_m=0.1,
        omega_max_rad_s=10.0,
        time_constant_s=0.0,
        delay_s=0.0
    )
    sys = ActuatorSystem([rotor], dt_s=0.1)
    
    # Pedir omega mayor que max
    target_omega = np.array([20.0])
    res, _, _ = sys.compute_applied_forces(target_omega)
    
    assert np.isclose(res.applied_omega_rad_s[0], 10.0)
    assert res.saturation_flags[0] == True
