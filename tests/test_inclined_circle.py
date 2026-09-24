import numpy as np
import pytest
from simulador_quad.trajectories.analytic import CircleTrajectory
from simulador_quad.scenarios.loader import instantiate_trajectory
from simulador_quad.scenarios.schema import validate_scenario_config


def test_horizontal_circle_identity():
    """tilt=0 exactly matches default horizontal behavior."""
    center = np.array([1.0, 2.0, 3.0])
    radius = 1.5
    omega = 0.8

    c_default = CircleTrajectory(center, radius, omega, yaw_mode="forward")
    c_tilt_zero = CircleTrajectory(center, radius, omega, yaw_mode="forward", tilt_rad=0.0, plane_yaw_rad=0.0)

    for t in [0.0, 0.5, 1.25, 2.5, 5.0, 10.0]:
        ref1 = c_default.get_reference(t)
        ref2 = c_tilt_zero.get_reference(t)

        np.testing.assert_array_equal(ref1.position_W_m, ref2.position_W_m)
        np.testing.assert_array_equal(ref1.velocity_W_m_s, ref2.velocity_W_m_s)
        np.testing.assert_array_equal(ref1.acceleration_W_m_s2, ref2.acceleration_W_m_s2)
        assert np.isclose(ref1.yaw_rad, ref2.yaw_rad)


def test_inclined_circle_geometry_and_derivatives():
    """Inclined circle maintains circular geometry, normal planarity, and analytic derivatives."""
    center = np.array([0.0, 0.0, 2.5])
    radius = 2.0
    omega = 0.5
    tilt_rad = np.deg2rad(20.0)
    plane_yaw_rad = np.deg2rad(45.0)

    traj = CircleTrajectory(center, radius, omega, yaw_mode="forward", tilt_rad=tilt_rad, plane_yaw_rad=plane_yaw_rad)

    dt = 1e-5
    for t in np.linspace(0, 12, 25):
        ref = traj.get_reference(t)

        # 1. Radius constraint
        dist_from_center = np.linalg.norm(ref.position_W_m - center)
        assert np.isclose(dist_from_center, radius, atol=1e-7)

        # 2. Velocity magnitude
        vel_mag = np.linalg.norm(ref.velocity_W_m_s)
        assert np.isclose(vel_mag, radius * omega, atol=1e-7)

        # 3. Tangent orthogonality: pos_offset . vel == 0
        pos_offset = ref.position_W_m - center
        assert np.isclose(np.dot(pos_offset, ref.velocity_W_m_s), 0.0, atol=1e-7)

        # 4. Centripetal acceleration: acc . pos_offset == - (radius * omega)^2
        assert np.isclose(np.dot(ref.acceleration_W_m_s2, pos_offset), -(radius * omega)**2, atol=1e-6)

        # 5. Numerical derivative check for velocity
        ref_next = traj.get_reference(t + dt)
        num_vel = (ref_next.position_W_m - ref.position_W_m) / dt
        np.testing.assert_allclose(ref.velocity_W_m_s, num_vel, rtol=1e-4, atol=1e-4)

        # 6. Numerical derivative check for acceleration
        num_acc = (ref_next.velocity_W_m_s - ref.velocity_W_m_s) / dt
        np.testing.assert_allclose(ref.acceleration_W_m_s2, num_acc, rtol=1e-4, atol=1e-4)


def test_inclined_circle_loader_and_schema():
    """Loader correctly parses tilt_deg and plane_yaw_deg."""
    cfg = {
        "type": "circle",
        "center_W_m": [0.0, 0.0, 2.0],
        "radius_m": 1.5,
        "omega_rad_s": 0.6,
        "tilt_deg": 15.0,
        "plane_yaw_deg": 30.0,
        "yaw_mode": "forward"
    }
    traj = instantiate_trajectory(cfg)
    assert isinstance(traj, CircleTrajectory)
    assert np.isclose(traj.tilt_rad, np.deg2rad(15.0))
    assert np.isclose(traj.plane_yaw_rad, np.deg2rad(30.0))

    ref = traj.get_reference(0.0)
    assert np.all(np.isfinite(ref.position_W_m))
    assert np.all(np.isfinite(ref.velocity_W_m_s))
    assert np.all(np.isfinite(ref.acceleration_W_m_s2))
