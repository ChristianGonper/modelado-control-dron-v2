import numpy as np
import pytest

from simulador_quad.api.envelope import (
    DATASET_WAYPOINTS_G01_G06,
    is_waypoint_geometry_in_dataset,
    validate_mission_envelope,
    validate_single_segment,
)
from simulador_quad.api.models import (
    CompositeSegmentConfig,
    MissionConfigRequest,
    TrajectoryFamily,
    WindConfig,
)
from simulador_quad.api.pid_selection import compute_segment_length, select_pid_for_mission
from simulador_quad.api.presets import get_waypoint_presets


def test_initial_waypoint_draw_excludes_demanding_helix():
    """La hélice compacta es un ejemplo del catálogo, no una propuesta inicial."""
    from simulador_quad.api.presets import INITIAL_WAYPOINT_PRESET_KEYS, generate_initial_variant

    presets = get_waypoint_presets()
    tight = np.asarray(presets["helix_tight"]["waypoints"], dtype=float)
    allowed = [np.asarray(presets[key]["waypoints"], dtype=float) for key in INITIAL_WAYPOINT_PRESET_KEYS]
    assert "helix_tight" not in INITIAL_WAYPOINT_PRESET_KEYS

    for seed in range(24):
        drawn = np.asarray(generate_initial_variant("waypoint", seed)["waypoints"], dtype=float)
        assert drawn.shape != tight.shape or not np.allclose(drawn, tight)
        assert any(drawn.shape == route.shape and np.allclose(drawn, route) for route in allowed)


def test_helix_tight_preview_reaches_final_waypoint():
    from simulador_quad.api.scenario_builder import compute_preview

    preset = get_waypoint_presets()["helix_tight"]
    mission = _mission("waypoint", {
        "waypoints": preset["waypoints"],
        "max_speed_m_s": preset["max_speed_m_s"],
        "max_acceleration_m_s2": preset["max_acceleration_m_s2"],
        "dwell_time_s": preset["dwell_time_s"],
    })
    preview = compute_preview(mission)
    destination = np.asarray(preset["waypoints"][-1], dtype=float)
    distances = [np.linalg.norm(np.asarray(point) - destination) for point in preview.points]
    assert min(distances) < 1e-3


def test_presets_exclude_train_test_geometries():
    """Ningún preset de waypoint de la aplicación coincide con las geometrías g01-g06."""
    presets = get_waypoint_presets()
    for name, p in presets.items():
        wps = p["waypoints"]
        assert not is_waypoint_geometry_in_dataset(wps), f"Preset '{name}' coincide con g01-g06!"


def test_dataset_geometries_are_detected():
    """Las geometrías g01-g06 del TFG son detectadas como pertenecientes al dataset."""
    for ds_wps in DATASET_WAYPOINTS_G01_G06:
        assert is_waypoint_geometry_in_dataset(ds_wps) is True


def test_envelope_altitude_bounds():
    """La altura debe estar estrictamente entre 0.5 m y 6.0 m."""
    # Válido: 2.0 m
    m_valid = MissionConfigRequest(
        mode="simple",
        family=TrajectoryFamily.HOLD,
        params={"position_W_m": [0.0, 0.0, 2.0]},
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    valid, errors, _, _ = validate_mission_envelope(m_valid)
    assert valid is True
    assert len(errors) == 0

    # Inválido: z = 0.2 m (< 0.5 m)
    m_low = MissionConfigRequest(
        mode="simple",
        family=TrajectoryFamily.HOLD,
        params={"position_W_m": [0.0, 0.0, 0.2]},
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    valid_low, errors_low, _, _ = validate_mission_envelope(m_low)
    assert valid_low is False
    assert any("0.5 a 6.0" in e for e in errors_low)

    # Inválido: z = 7.0 m (> 6.0 m)
    m_high = MissionConfigRequest(
        mode="simple",
        family=TrajectoryFamily.HOLD,
        params={"position_W_m": [0.0, 0.0, 7.0]},
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    valid_high, errors_high, _, _ = validate_mission_envelope(m_high)
    assert valid_high is False
    assert any("0.5 a 6.0" in e for e in errors_high)


def test_envelope_wind_bounds():
    """El viento horizontal no debe superar 1.4 m/s."""
    m_ok = MissionConfigRequest(
        mode="simple",
        family=TrajectoryFamily.HOLD,
        params={"position_W_m": [0.0, 0.0, 1.5]},
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=1.4, direction_deg=90.0),
        seed=42,
    )
    assert validate_mission_envelope(m_ok)[0] is True

    m_excess = MissionConfigRequest(
        mode="simple",
        family=TrajectoryFamily.HOLD,
        params={"position_W_m": [0.0, 0.0, 1.5]},
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=1.5, direction_deg=90.0),
        seed=42,
    )
    valid, errors, _, _ = validate_mission_envelope(m_excess)
    assert valid is False
    assert any("1.4 m/s" in e for e in errors)


def test_envelope_circle_dynamics():
    """Verifica límites de R, R*omega <= 1.5, R*omega^2 <= 1.0 e inclinación <= 30°."""
    # Válido: R=1.5, w=0.6 -> R*w=0.9 <= 1.5, R*w^2=0.54 <= 1.0, tilt=20°
    m_ok = MissionConfigRequest(
        mode="simple",
        family=TrajectoryFamily.CIRCLE,
        params={"center_W_m": [0.0, 0.0, 2.5], "radius_m": 1.5, "omega_rad_s": 0.6, "tilt_deg": 20.0},
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    assert validate_mission_envelope(m_ok)[0] is True

    # R*w > 1.5
    m_fast = MissionConfigRequest(
        mode="simple",
        family=TrajectoryFamily.CIRCLE,
        params={"center_W_m": [0.0, 0.0, 2.5], "radius_m": 2.0, "omega_rad_s": 1.0, "tilt_deg": 0.0},
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    valid_fast, errors_fast, _, _ = validate_mission_envelope(m_fast)
    assert valid_fast is False
    assert any("1.5 m/s" in e for e in errors_fast)

    # Inclinación > 30°
    m_tilt = MissionConfigRequest(
        mode="simple",
        family=TrajectoryFamily.CIRCLE,
        params={"center_W_m": [0.0, 0.0, 2.5], "radius_m": 1.5, "omega_rad_s": 0.5, "tilt_deg": 35.0},
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    valid_tilt, errors_tilt, _, _ = validate_mission_envelope(m_tilt)
    assert valid_tilt is False
    assert any("30°" in e for e in errors_tilt)


def test_envelope_composite_segments_count():
    """Composición debe tener entre 2 y 4 tramos."""
    # 1 tramo es inválido
    m_1 = MissionConfigRequest(
        mode="composite",
        family=TrajectoryFamily.COMPOSITE,
        params={},
        segments=[CompositeSegmentConfig(type="hold", duration=5.0, params={"position_W_m": [0, 0, 2]})],
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    assert validate_mission_envelope(m_1)[0] is False

    # 5 tramos es inválido
    segs_5 = [
        CompositeSegmentConfig(type="hold", duration=2.0, params={"position_W_m": [0, 0, 2]})
        for _ in range(5)
    ]
    m_5 = MissionConfigRequest(
        mode="composite",
        family=TrajectoryFamily.COMPOSITE,
        params={},
        segments=segs_5,
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    assert validate_mission_envelope(m_5)[0] is False

    # 3 tramos válidos
    segs_3 = [
        CompositeSegmentConfig(type="hold", duration=3.0, params={"position_W_m": [0, 0, 2]}),
        CompositeSegmentConfig(type="circle", duration=8.0, params={"center_W_m": [0, 0, 2], "radius_m": 1.5, "omega_rad_s": 0.6}),
        CompositeSegmentConfig(type="hold", duration=3.0, params={"position_W_m": [0, 0, 2]}),
    ]
    m_3 = MissionConfigRequest(
        mode="composite",
        family=TrajectoryFamily.COMPOSITE,
        params={},
        segments=segs_3,
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    assert validate_mission_envelope(m_3)[0] is True


def test_composite_preview_multi_segment():
    """Verifica que compute_preview muestrea todos los tramos y transiciones compuestas."""
    from simulador_quad.api.scenario_builder import compute_preview

    segs = [
        CompositeSegmentConfig(type="circle", duration=5.0, params={"center_W_m": [0, 0, 2], "radius_m": 1.5, "omega_rad_s": 0.6}),
        CompositeSegmentConfig(type="waypoint", duration=8.0, params={"waypoints": [[1.5, 0, 2], [2.5, 1.5, 2.5], [0, 2, 2]]}),
        CompositeSegmentConfig(type="circle", duration=5.0, params={"center_W_m": [0, 2, 2], "radius_m": 1.2, "omega_rad_s": 0.6}),
    ]
    mission = MissionConfigRequest(
        mode="composite",
        family=TrajectoryFamily.COMPOSITE,
        params={},
        segments=segs,
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    prev = compute_preview(mission)
    assert len(prev.points) > 100
    # Comprobar que hay transiciones y que se visitan múltiples tramos
    assert any(prev.is_transition)
    assert len(set(prev.segment_indices)) >= 3


def _mission(family, params, wind=0.0, mode="simple", segments=None):
    return MissionConfigRequest(
        mode=mode,
        family=family,
        params=params,
        segments=segments,
        transition_speed=0.8,
        wind=WindConfig(magnitude_m_s=wind, direction_deg=0.0),
        seed=42,
    )


def test_envelope_rejects_review_extremes():
    """Viento negativo, velocidad nula, Lissajous enorme y duración desmesurada no entran."""
    negative_wind = _mission("hold", {"position_W_m": [0.0, 0.0, 1.5], "duration": 10.0}, wind=-2.0)
    valid_wind, errors_wind, _, _ = validate_mission_envelope(negative_wind)
    assert valid_wind is False
    assert any("viento" in err.lower() for err in errors_wind)

    zero_speed = _mission(
        "waypoint",
        {
            "waypoints": [[0.0, 0.0, 2.0], [2.0, 0.0, 2.0]],
            "max_speed_m_s": 0.0,
            "max_acceleration_m_s2": 0.5,
        },
    )
    valid_speed, errors_speed, _, _ = validate_mission_envelope(zero_speed)
    assert valid_speed is False
    assert any("Velocidad" in err for err in errors_speed)

    huge_lissajous = _mission(
        "lissajous",
        {
            "center_W_m": [0.0, 0.0, 2.5],
            "amplitudes": [100.0, 100.0, 1.0],
            "omegas": [0.5, 0.7, 0.3],
            "duration": 20.0,
        },
    )
    valid_liss, errors_liss, _, _ = validate_mission_envelope(huge_lissajous)
    assert valid_liss is False
    assert any("Amplitud" in err or "extensión" in err or "Velocidad de Lissajous" in err for err in errors_liss)

    endless_circle = _mission(
        "circle",
        {"center_W_m": [0.0, 0.0, 2.0], "radius_m": 1.5, "omega_rad_s": 0.6, "duration": 1_000_000.0},
    )
    valid_dur, errors_dur, _, _ = validate_mission_envelope(endless_circle)
    assert valid_dur is False
    assert any("duración" in err.lower() for err in errors_dur)


def test_presets_stay_inside_envelope():
    from simulador_quad.api.presets import generate_initial_variant, get_composite_presets

    for family in ("hold", "circle", "lissajous", "waypoint", "lemniscate"):
        for seed in (1, 42, 99):
            params = generate_initial_variant(family, seed)
            valid, errors, _, _ = validate_mission_envelope(_mission(family, params))
            assert valid, f"{family} seed {seed}: {errors}"

    for preset in get_composite_presets().values():
        segments = [
            CompositeSegmentConfig(type=seg["type"], duration=seg.get("duration"), params=seg["params"])
            for seg in preset["segments"]
        ]
        mission = _mission("composite", {}, mode="composite", segments=segments)
        mission.family = TrajectoryFamily.COMPOSITE
        valid, errors, _, _ = validate_mission_envelope(mission)
        assert valid, errors


def test_waypoint_preview_uses_nominal_motion_not_fictitious_duration():
    from simulador_quad.api.envelope import estimate_waypoint_motion_s
    from simulador_quad.api.scenario_builder import build_trajectory_config, compute_preview

    params = {
        "waypoints": [[0.0, 0.0, 2.0], [3.0, 0.0, 2.0], [3.0, 3.0, 2.5]],
        "max_speed_m_s": 0.6,
        "max_acceleration_m_s2": 0.5,
        "dwell_time_s": 0.4,
    }
    mission = _mission("waypoint", params)
    preview = compute_preview(mission)
    nominal = estimate_waypoint_motion_s(params)
    legs = len(params["waypoints"]) - 1
    assert preview.total_duration_s + 1e-6 >= min(nominal, 60.0)
    assert preview.total_duration_s <= min(nominal, 60.0) + 0.05 * legs + 1e-6
    for waypoint in params["waypoints"]:
        distances = [np.linalg.norm(np.asarray(point) - np.asarray(waypoint)) for point in preview.points]
        assert min(distances) < 1e-3

    composite = _mission(
        "composite",
        {},
        mode="composite",
        segments=[
            CompositeSegmentConfig(type="circle", duration=5.0, params={"center_W_m": [0, 0, 2], "radius_m": 1.5, "omega_rad_s": 0.6}),
            CompositeSegmentConfig(type="waypoint", duration=8.0, params=params),
            CompositeSegmentConfig(type="hold", duration=3.0, params={"position_W_m": [3.0, 3.0, 2.5]}),
        ],
    )
    composite.family = TrajectoryFamily.COMPOSITE
    config = build_trajectory_config(composite)
    assert "duration" not in config["sequence"][1]
    assert config["sequence"][0]["duration"] == 5.0
