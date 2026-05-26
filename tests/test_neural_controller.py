"""
Tests para el controlador neuronal en bucle cerrado.
"""
import pytest
import os
import yaml
import torch
import numpy as np
from simulador_quad.scenarios.loader import instantiate_scenario
from simulador_quad.runner import SimulationRunner

import json

@pytest.fixture
def dummy_model_dir(tmp_path):
    """Crea un modelo dummy y normalizador para pruebas de bucle cerrado."""
    model_dir = tmp_path / "dummy_model"
    model_dir.mkdir()
    (model_dir / "checkpoints").mkdir()
    
    # Normalizador dummy (31 inputs, 6 outputs for neural_position legacy path)
    norm_data = {
        "mean_x": [0.0] * 31,
        "std_x": [1.0] * 31,
        "mean_y": [0.0] * 6,
        "std_y": [1.0] * 6,
        "feature_names": ["f"] * 31,
        "target_names": ["t"] * 6,
        "feature_version": "v1",
        "epsilon": 1e-8
    }
    with open(model_dir / "normalization.json", "w") as f:
        json.dump(norm_data, f)
        
    # Checkpoint dummy (pesos aleatorios para MLP) - 6 outputs for position gain test
    from simulador_quad.ml.models import MLPControllerNet
    hidden_dim = 16
    model = MLPControllerNet(31, 6, hidden_dim=hidden_dim)
    torch.save(model.state_dict(), model_dir / "checkpoints" / "mlp_best.pt")
    
    # Config dummy
    config = {
        "architecture": "mlp",
        "input_dim": 31,
        "output_dim": 6,
        "hidden_dim": hidden_dim
    }
    with open(model_dir / "config.yaml", "w") as f:
        import yaml
        yaml.dump(config, f)
    
    return model_dir

def test_neural_controller_execution(dummy_model_dir):
    """Verifica que un escenario con controlador neuronal se ejecuta sin errores."""
    checkpoint = dummy_model_dir / "checkpoints" / "mlp_best.pt"
    norm_path = dummy_model_dir / "normalization.json"
    
    # Crear un escenario minimo temporal
    scenario_dict = {
        "name": "neural_test",
        "seed": 42,
        "vehicle": {
            "mass_kg": 1.0,
            "inertia_B_kg_m2": [[0.01, 0, 0], [0, 0.01, 0], [0, 0, 0.02]],
            "linear_drag_coefficient": [0.1, 0.1, 0.1],
            "rotors": [
                {"position_B_m": [0.1, 0.1, 0], "turning_direction": 1, "k_f": 1e-4, "k_m": 1e-6, "omega_max_rad_s": 1000, "time_constant_s": 0.05},
                {"position_B_m": [-0.1, -0.1, 0], "turning_direction": 1, "k_f": 1e-4, "k_m": 1e-6, "omega_max_rad_s": 1000, "time_constant_s": 0.05},
                {"position_B_m": [0.1, -0.1, 0], "turning_direction": -1, "k_f": 1e-4, "k_m": 1e-6, "omega_max_rad_s": 1000, "time_constant_s": 0.05},
                {"position_B_m": [-0.1, 0.1, 0], "turning_direction": -1, "k_f": 1e-4, "k_m": 1e-6, "omega_max_rad_s": 1000, "time_constant_s": 0.05}
            ]
        },
        "initial_state": {
            "position_W_m": [0, 0, 1],
            "velocity_W_m_s": [0, 0, 0],
            "angular_velocity_B_rad_s": [0, 0, 0]
        },
        "trajectory": {
            "type": "hold",
            "position_W_m": [0, 0, 1]
        },
        "controller": {
            "type": "neural_position",
            "architecture": "mlp",
            "checkpoint_path": str(checkpoint),
            "normalization_path": str(norm_path),
            "base_Kp_pos": [2.0, 2.0, 5.0],
            "base_Kd_pos": [1.0, 1.0, 2.0],
        },
        "timing": {
            "physics_dt_s": 0.01,
            "control_dt_s": 0.02,
            "telemetry_dt_s": 0.1
        },
        "termination": {
            "max_duration_s": 0.2,
            "z_min_m": -1.0
        },
        "perturbations": {
            "constant_wind_W_m_s": [0, 0, 0]
        },
        "output": {
            "dir": str(dummy_model_dir / "results"),
            "telemetry_file": "telemetry.json",
            "metrics_file": "metrics.json"
        }
    }
    
    v_params, mixer, actuators, initial_state, trajectory, controller, wind, noise = instantiate_scenario(scenario_dict)
    
    runner = SimulationRunner(
        physics_dt_s=0.01, control_dt_s=0.02, telemetry_dt_s=0.1,
        vehicle_params=v_params, mixer=mixer, actuators=actuators,
        wind_model=wind, observation_noise=noise, max_duration_s=0.2
    )
    
    result = runner.run(initial_state, controller, trajectory)
    
    assert "telemetry" in result
    assert len(result["telemetry"]) > 0
