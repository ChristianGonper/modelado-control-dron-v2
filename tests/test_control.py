import numpy as np
from simulador_quad.control.classic import ClassicCascadeController
from simulador_quad.core.contracts import VehicleState, TrajectoryReference
from simulador_quad.core.frames import get_level_quaternion

def test_hover_thrust():
    mass = 1.0
    g = 9.81
    inertia = np.eye(3) * 0.01
    ctrl = ClassicCascadeController(mass, g, inertia)
    
    # Estado inicial: hover en el origen
    obs = VehicleState(
        position_W_m=np.zeros(3),
        velocity_W_m_s=np.zeros(3),
        orientation_WB=get_level_quaternion(0.0),
        angular_velocity_B_rad_s=np.zeros(3),
        time_s=0.0
    )
    
    # Referencia: hover en el origen
    ref = TrajectoryReference(
        position_W_m=np.zeros(3),
        velocity_W_m_s=np.zeros(3),
        acceleration_W_m_s2=np.zeros(3),
        yaw_rad=0.0
    )
    
    cmd = ctrl.compute_control(0.0, obs, ref)
    
    # El empuje debe ser igual a mg
    assert np.isclose(cmd.collective_thrust_N, mass * g)
    # Los momentos deben ser cero
    assert np.allclose(cmd.body_moments_Nm, 0.0)

def test_position_error_force_sign():
    mass = 1.0
    g = 9.81
    inertia = np.eye(3) * 0.01
    ctrl = ClassicCascadeController(mass, g, inertia)
    
    # Estado inicial en el origen
    obs = VehicleState(
        position_W_m=np.zeros(3),
        velocity_W_m_s=np.zeros(3),
        orientation_WB=get_level_quaternion(0.0),
        angular_velocity_B_rad_s=np.zeros(3),
        time_s=0.0
    )
    
    # Referencia en X positivo
    ref = TrajectoryReference(
        position_W_m=np.array([1.0, 0.0, 0.0]),
        velocity_W_m_s=np.zeros(3),
        acceleration_W_m_s2=np.zeros(3),
        yaw_rad=0.0
    )
    
    cmd = ctrl.compute_control(0.0, obs, ref)
    
    # Si queremos ir a X=1 (Este), necesitamos una aceleración en X.
    # El controlador calculará a_des_x > 0.
    # F_des_W tendrá componente X positiva.
    # Con Front=Norte (Y) y Right=Este (X), para tener fuerza en X (Este)
    # necesitamos que el dron se incline hacia el Este (Right DOWN).
    # Right DOWN es un roll POSITIVO en FRD.
    # Así que el torque_x (roll) debe ser positivo.
    assert cmd.body_moments_Nm[0] > 0.0
    # No queremos cabeceo (pitch, Y) ni guiñada (yaw, Z)
    assert np.isclose(cmd.body_moments_Nm[1], 0.0)
    assert np.isclose(cmd.body_moments_Nm[2], 0.0)
