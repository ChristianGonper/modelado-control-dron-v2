import numpy as np
import pytest
from copy import deepcopy

from simulador_quad.trajectories.analytic import HoldTrajectory, CircleTrajectory, LineTrajectory
from simulador_quad.trajectories.composite import CompositeTrajectory
from simulador_quad.core.contracts import VehicleState
from simulador_quad.core.frames import get_level_quaternion
from simulador_quad.scenarios.schema import validate_scenario_config
from simulador_quad.scenarios.loader import instantiate_trajectory

def get_dummy_state(t: float, pos=None, vel=None) -> VehicleState:
    return VehicleState(
        position_W_m=np.array(pos if pos is not None else [0, 0, 0]).astype(float),
        velocity_W_m_s=np.array(vel if vel is not None else [0, 0, 0]).astype(float),
        orientation_WB=get_level_quaternion(0.0),
        angular_velocity_B_rad_s=np.zeros(3),
        time_s=t
    )

def test_composite_no_transition():
    # Dos holds de 5 segundos cada uno:
    # 1. hold en [0, 0, 1]
    # 2. hold en [2, 2, 2]
    hold1 = HoldTrajectory(np.array([0.0, 0.0, 1.0]))
    hold2 = HoldTrajectory(np.array([2.0, 2.0, 2.0]))
    
    # Sin transición (transition_speed=None)
    comp = CompositeTrajectory([hold1, hold2], [5.0, 5.0], transition_speed=None)
    
    # t = 0
    ref = comp.get_reference_for_state(0.0, get_dummy_state(0.0, pos=[0, 0, 1]))
    assert np.allclose(ref.position_W_m, [0, 0, 1])
    assert comp.active_index == 0
    
    # t = 4.0 (todavía en el primer tramo)
    ref = comp.get_reference_for_state(4.0, get_dummy_state(4.0, pos=[0, 0, 1]))
    assert np.allclose(ref.position_W_m, [0, 0, 1])
    assert comp.active_index == 0
    
    # Evaluar completitud a t = 4.0: no debería avanzar
    term, _ = comp.check_completion(4.0, get_dummy_state(4.0, pos=[0, 0, 1]), 0.01)
    assert not term
    assert comp.active_index == 0
    
    # Evaluar completitud a t = 5.1 (pasó los 5.0s del primer tramo)
    term, _ = comp.check_completion(5.1, get_dummy_state(5.1, pos=[0, 0, 1]), 0.01)
    assert not term
    assert comp.active_index == 1 # Cambia al segundo tramo!
    
    # Obtener referencia a t = 5.2 (tiempo local del segundo tramo es 5.2 - 5.1 = 0.1s)
    ref = comp.get_reference_for_state(5.2, get_dummy_state(5.2, pos=[0, 0, 1]))
    assert np.allclose(ref.position_W_m, [2, 2, 2])
    
    # Evaluar completitud a t = 10.0 (segundo tramo completado: 5.1 + 5.0 = 10.1s)
    term, _ = comp.check_completion(10.0, get_dummy_state(10.0), 0.01)
    assert not term # Aún no pasa el tiempo
    
    term, _ = comp.check_completion(10.2, get_dummy_state(10.2), 0.01)
    assert term # Completada toda la trayectoria!

def test_composite_with_transition():
    # Dos holds de 5 segundos cada uno:
    # 1. hold en [0, 0, 1]
    # 2. hold en [2, 0, 1] (distancia de 2 metros)
    hold1 = HoldTrajectory(np.array([0.0, 0.0, 1.0]))
    hold2 = HoldTrajectory(np.array([2.0, 0.0, 1.0]))
    
    # Con transición a 1.0 m/s. Tiempo estimado del tramo de transición con max_speed=1.0, max_acc=0.5:
    # L = 2.0. 2 * d_acc = 2 * (0.5 * 1.0 * 2^2) = 1.0 < 2.0 (trapezoidal)
    # t_acc = 1.0 / 0.5 = 2.0s
    # d_acc = 0.5 * 0.5 * 4 = 1.0m
    # Como 2*d_acc = 2.0 = L, es un perfil triangular límite o trapezoidal con t_const = 0.
    # t_total = 2.0 + 2.0 = 4.0s.
    comp = CompositeTrajectory([hold1, hold2], [5.0, 5.0], transition_speed=1.0)
    
    # Iniciar
    comp.get_reference_for_state(0.0, get_dummy_state(0.0, pos=[0, 0, 1]))
    
    # Forzar final de la primera trayectoria evaluando a t = 5.1s
    term, _ = comp.check_completion(5.1, get_dummy_state(5.1, pos=[0, 0, 1]), 0.01)
    assert not term
    assert comp.in_transition == True
    assert comp.active_index == 1 # Apunta a la siguiente trayectoria
    
    # t_local_transition = t - 5.1
    # Obtener referencias durante la transición
    # A t = 5.1s (inicio de transición)
    ref = comp.get_reference_for_state(5.1, get_dummy_state(5.1, pos=[0, 0, 1]))
    assert np.allclose(ref.position_W_m, [0, 0, 1])
    
    # Simulamos que el dron se mueve de acuerdo a la referencia
    # A t = 7.1s (mitad de la transición: t_local_transition = 2.0s, debería haber recorrido 1.0m)
    ref = comp.get_reference_for_state(7.1, get_dummy_state(7.1, pos=[1.0, 0, 1]))
    assert np.allclose(ref.position_W_m, [1.0, 0, 1])
    
    # A t = 9.1s (fin nominal de transición)
    ref = comp.get_reference_for_state(9.1, get_dummy_state(9.1, pos=[2.0, 0, 1]))
    assert np.allclose(ref.position_W_m, [2.0, 0, 1])
    
    # Evaluar completitud a t = 9.1s (aún no se ha evaluado el estado de HOLD)
    term, _ = comp.check_completion(9.1, get_dummy_state(9.1, pos=[2.0, 0, 1], vel=[0,0,0]), 0.01)
    assert not term
    assert comp.in_transition == True
    
    # Avanzar un paso para evaluar HOLD (t = 9.11s)
    ref = comp.get_reference_for_state(9.11, get_dummy_state(9.11, pos=[2.0, 0, 1]))
    term, _ = comp.check_completion(9.11, get_dummy_state(9.11, pos=[2.0, 0, 1], vel=[0,0,0]), 0.01)
    assert not term
    assert comp.in_transition == False # Ya terminó la transición!
    assert comp.current_start_time_s == 9.11
    
    # A t = 10.11 (tiempo local del segundo hold es 1.0s)
    ref = comp.get_reference_for_state(10.11, get_dummy_state(10.11, pos=[2, 0, 1]))
    assert np.allclose(ref.position_W_m, [2, 0, 1])
    
    # Evaluar completitud a t = 14.12 (duración 5s de hold2 cumplida: 9.11 + 5.0 = 14.11s)
    term, _ = comp.check_completion(14.12, get_dummy_state(14.12, pos=[2, 0, 1]), 0.01)
    assert term # Trayectoria completa!

def test_validation_schema_composite():
    # Config base válida
    valid_cfg = {
        "trajectory": {
            "type": "composite",
            "transition_speed": 0.5,
            "sequence": [
                {
                    "type": "hold",
                    "position_W_m": [0.0, 0.0, 1.0],
                    "duration": 3.0,
                    "yaw_rad": 0.0
                },
                {
                    "type": "circle",
                    "center_W_m": [1.0, 1.0, 1.0],
                    "radius_m": 1.5,
                    "omega_rad_s": 0.5,
                    "duration": 10.0,
                    "yaw_mode": "forward"
                },
                {
                    "type": "waypoint",
                    "waypoints": [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]],
                    "max_speed_m_s": 0.6,
                    "max_acceleration_m_s2": 0.5
                }
            ]
        }
    }
    
    # Construir un dummy config de escenario completo para validar
    dummy_scenario = {
        "name": "Test Composite Scenario",
        "seed": 42,
        "vehicle": {
            "mass_kg": 1.0,
            "gravity_m_s2": 9.81,
            "inertia_B_kg_m2": [[0.05, 0, 0], [0, 0.05, 0], [0, 0, 0.1]],
            "linear_drag_coefficient": [0.1, 0.1, 0.1],
            "rotors": [
                {"position_B_m": [0.17, 0.17, 0], "turning_direction": -1, "k_f": 1.0e-4, "k_m": 1.0e-6, "omega_max_rad_s": 1000, "time_constant_s": 0.0},
                {"position_B_m": [0.17, -0.17, 0], "turning_direction": 1, "k_f": 1.0e-4, "k_m": 1.0e-6, "omega_max_rad_s": 1000, "time_constant_s": 0.0},
                {"position_B_m": [-0.17, 0.17, 0], "turning_direction": 1, "k_f": 1.0e-4, "k_m": 1.0e-6, "omega_max_rad_s": 1000, "time_constant_s": 0.0},
                {"position_B_m": [-0.17, -0.17, 0], "turning_direction": -1, "k_f": 1.0e-4, "k_m": 1.0e-6, "omega_max_rad_s": 1000, "time_constant_s": 0.0}
            ]
        },
        "initial_state": {
            "position_W_m": [0, 0, 0],
            "velocity_W_m_s": [0, 0, 0],
            "angular_velocity_B_rad_s": [0, 0, 0],
            "orientation_WB": None
        },
        "timing": {
            "physics_dt_s": 0.01,
            "control_dt_s": 0.02,
            "telemetry_dt_s": 0.1
        },
        "termination": {
            "max_duration_s": 40.0,
            "z_min_m": -0.1
        },
        "controller": {
            "type": "classic"
        },
        "perturbations": {
            "constant_wind_W_m_s": [0, 0, 0],
            "pos_std_m": 0.0,
            "vel_std_m_s": 0.0
        },
        "trajectory": valid_cfg["trajectory"]
    }
    
    # Debería validar sin problemas
    validate_scenario_config(dummy_scenario)
    
    # 1. Probar fallo si falta 'duration' en una trayectoria analítica dentro del composite
    invalid_cfg_1 = deepcopy(dummy_scenario)
    del invalid_cfg_1["trajectory"]["sequence"][1]["duration"] # Eliminar duration del circle
    with pytest.raises(ValueError, match="must specify 'duration' inside a composite trajectory"):
        validate_scenario_config(invalid_cfg_1)
        
    # 2. Probar fallo si el tipo de sub-trayectoria no es válido
    invalid_cfg_2 = deepcopy(dummy_scenario)
    invalid_cfg_2["trajectory"]["sequence"][0]["type"] = "invalid_type"
    with pytest.raises(ValueError, match="one of"):
        validate_scenario_config(invalid_cfg_2)

    # 3. Probar fallo si se especifica un duration negativo o inválido en un waypoint
    invalid_cfg_3 = deepcopy(dummy_scenario)
    invalid_cfg_3["trajectory"]["sequence"][2]["duration"] = -5.0
    with pytest.raises(ValueError, match="expected positive seconds value"):
        validate_scenario_config(invalid_cfg_3)

    # 4. Probar fallo si se especifica un duration negativo en un circle
    invalid_cfg_4 = deepcopy(dummy_scenario)
    invalid_cfg_4["trajectory"]["sequence"][1]["duration"] = 0.0
    with pytest.raises(ValueError, match="expected positive seconds value"):
        validate_scenario_config(invalid_cfg_4)

    # 5. Probar fallo si se especifica duration en trayectoria top-level
    invalid_cfg_5 = deepcopy(dummy_scenario)
    invalid_cfg_5["trajectory"] = {
        "type": "circle",
        "center_W_m": [0.0, 0.0, 1.0],
        "radius_m": 2.0,
        "omega_rad_s": 0.5,
        "duration": 10.0
    }
    with pytest.raises(ValueError, match="only allowed for sub-trajectories inside a composite trajectory"):
        validate_scenario_config(invalid_cfg_5)

def test_instantiate_composite():
    cfg = {
        "type": "composite",
        "transition_speed": 0.6,
        "sequence": [
            {
                "type": "hold",
                "position_W_m": [0.0, 0.0, 1.0],
                "duration": 3.0
            },
            {
                "type": "circle",
                "center_W_m": [0.0, 0.0, 1.0],
                "radius_m": 2.0,
                "omega_rad_s": 0.5,
                "duration": 5.0
            }
        ]
    }
    
    comp = instantiate_trajectory(cfg)
    assert isinstance(comp, CompositeTrajectory)
    assert len(comp.trajectories) == 2
    assert isinstance(comp.trajectories[0], HoldTrajectory)
    assert isinstance(comp.trajectories[1], CircleTrajectory)
    assert comp.durations == [3.0, 5.0]
    assert comp.transition_speed == 0.6
