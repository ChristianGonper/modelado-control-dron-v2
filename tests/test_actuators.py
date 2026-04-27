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
    
    app_omega, app_thrust, app_torque_s, total_torque, total_thrust = sys.compute_applied_forces(target_omega)
    
    assert np.isclose(app_omega[0], 5.0)
    # T = k_f * omega^2
    assert np.isclose(app_thrust[0], 25.0)
    # Q = turning_direction * k_m * omega^2
    assert np.isclose(app_torque_s[0], 2.5)
    
    # Thrust en B es [0, 0, -T]
    assert np.allclose(total_thrust, [0.0, 0.0, -25.0])
    
    # Torque:
    # torque_pos = r x F = [1, 0, 0] x [0, 0, -25] = [0, 25, 0]
    # torque_drag = [0, 0, -1 * 0.1 * 25] = [0, 0, -2.5]
    assert np.allclose(total_torque, [0.0, 25.0, -2.5])

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
    app_omega, _, _, _, _ = sys.compute_applied_forces(target_omega)
    
    assert np.isclose(app_omega[0], 10.0)
