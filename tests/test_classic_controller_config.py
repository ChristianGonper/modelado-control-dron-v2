import numpy as np
import pytest
from simulador_quad.control.classic import ClassicCascadeController
from simulador_quad.scenarios.loader import instantiate_scenario
from simulador_quad.scenarios.schema import validate_scenario_config

def test_controller_explicit_gains():
    mass = 1.0
    g = 9.81
    inertia = np.eye(3)
    
    # Defaults
    ctrl_def = ClassicCascadeController(mass, g, inertia)
    assert np.allclose(ctrl_def.Kp_pos, [2.0, 2.0, 5.0])
    
    # Explicit
    kp_pos = np.array([10.0, 10.0, 20.0])
    ctrl_exp = ClassicCascadeController(mass, g, inertia, Kp_pos=kp_pos)
    assert np.allclose(ctrl_exp.Kp_pos, kp_pos)
    assert np.allclose(ctrl_exp.Kd_pos, [1.0, 1.0, 2.0]) # Still default

def test_scenario_loader_with_gains():
    config = {
        "seed": 42,
        "vehicle": {
            "mass_kg": 1.0,
            "gravity_m_s2": 9.81,
            "inertia_B_kg_m2": [[0.1, 0, 0], [0, 0.1, 0], [0, 0, 0.2]],
            "linear_drag_coefficient": [0.1, 0.1, 0.05],
            "rotors": [
                {"position_B_m": [0.1, 0.1, 0], "turning_direction": 1, "k_f": 1e-5, "k_m": 1e-7, "omega_max_rad_s": 1000, "time_constant_s": 0.01},
                {"position_B_m": [-0.1, 0.1, 0], "turning_direction": -1, "k_f": 1e-5, "k_m": 1e-7, "omega_max_rad_s": 1000, "time_constant_s": 0.01},
                {"position_B_m": [-0.1, -0.1, 0], "turning_direction": 1, "k_f": 1e-5, "k_m": 1e-7, "omega_max_rad_s": 1000, "time_constant_s": 0.01},
                {"position_B_m": [0.1, -0.1, 0], "turning_direction": -1, "k_f": 1e-5, "k_m": 1e-7, "omega_max_rad_s": 1000, "time_constant_s": 0.01},
            ]
        },
        "timing": {
            "physics_dt_s": 0.01,
            "control_dt_s": 0.01,
            "telemetry_dt_s": 0.1
        },
        "termination": {
            "max_duration_s": 10.0
        },
        "initial_state": {
            "position_W_m": [0, 0, 0],
            "velocity_W_m_s": [0, 0, 0],
            "angular_velocity_B_rad_s": [0, 0, 0],
            "yaw_rad": 0.0
        },
        "trajectory": {
            "type": "hold",
            "position_W_m": [0, 0, 2]
        },
        "controller": {
            "type": "classic",
            "Kp_pos": [5.0, 5.0, 10.0],
            "Kd_pos": [2.0, 2.0, 4.0]
        },
        "perturbations": {
            "constant_wind_W_m_s": [0, 0, 0]
        }
    }
    
    validate_scenario_config(config)
    v_params, mixer, actuators, initial_state, trajectory, controller, wind, noise = instantiate_scenario(config)
    
    assert isinstance(controller, ClassicCascadeController)
    assert np.allclose(controller.Kp_pos, [5.0, 5.0, 10.0])
    assert np.allclose(controller.Kd_pos, [2.0, 2.0, 4.0])
    assert np.allclose(controller.Kp_att, [4.0, 4.0, 1.0]) # Default

def test_invalid_gains_fail_validation():
    config = {
        "controller": {
            "type": "classic",
            "Kp_pos": [5.0, -1.0, 10.0]
        }
    }
    # We need a full config for validate_scenario_config, so let's mock it or use a helper
    # But for unit test of _validate_controller specifically:
    from simulador_quad.scenarios.schema import _validate_controller
    with pytest.raises(ValueError, match="controller.Kp_pos"):
        _validate_controller(config)
