from simulador_quad.app import build_execution_metadata
from simulador_quad.runner import SimulationRunner
from simulador_quad.scenarios.loader import instantiate_scenario, load_scenario


def test_execution_metadata_contains_reproducibility_fields():
    scenario_path = "scenarios/hover_clean.yaml"
    config = load_scenario(scenario_path)
    vehicle_params, mixer, actuators, _initial_state, _trajectory, controller, wind, noise = instantiate_scenario(config)

    timing = config["timing"]
    termination = config["termination"]
    runner = SimulationRunner(
        physics_dt_s=timing["physics_dt_s"],
        control_dt_s=timing["control_dt_s"],
        telemetry_dt_s=timing["telemetry_dt_s"],
        vehicle_params=vehicle_params,
        mixer=mixer,
        actuators=actuators,
        wind_model=wind,
        observation_noise=noise,
        max_duration_s=termination["max_duration_s"],
        z_min_m=termination["z_min_m"],
        max_attitude_angle_rad=termination.get("max_attitude_angle_rad", 1.256),
        max_saturation_duration_s=termination.get("max_saturation_duration_s", 1.0),
    )

    metadata = build_execution_metadata(
        config=config,
        scenario_path=scenario_path,
        controller=controller,
        runner=runner,
        visualization=False,
        command="uv run simulador-quad run scenarios/hover_clean.yaml --no-visualization",
    )

    assert metadata["scenario_name"] == "Hover Clean"
    assert metadata["scenario_path"] == scenario_path
    assert metadata["seed"] == 42
    assert metadata["command"].endswith("--no-visualization")
    assert metadata["controller"]["type"] == "classic"
    assert "Kp_pos" in metadata["controller"]["parameters"]
    assert "Kd_pos" in metadata["controller"]["parameters"]
    assert "Kp_att" in metadata["controller"]["parameters"]
    assert "Kd_att" in metadata["controller"]["parameters"]
    assert "max_thrust" in metadata["controller"]["parameters"]
    assert "min_thrust" in metadata["controller"]["parameters"]
    assert "max_moments_Nm" in metadata["controller"]["parameters"]
    assert metadata["python_version"]
    assert metadata["package_version"]
    assert metadata["platform"]
    assert metadata["scenario_file_hash"].startswith("sha256:")
    assert metadata["uv_lock_hash"].startswith("sha256:")
    assert "git_commit" in metadata
    assert "git_dirty" in metadata
    assert metadata["config"] == config
    assert metadata["config_resolved"]["termination_effective"]["max_position_m"] == runner.max_position_m
    assert metadata["config_resolved"]["timing_effective"]["physics_dt_s"] == timing["physics_dt_s"]
