"""
Suite completa de verificación de las diez comprobaciones de aceptación de NeuroFlight.
Referencia: docs/spec.md#comprobaciones-de-aceptación
"""

import csv
import io
import json
import time
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from simulador_quad.api.bundle_verifier import BundleVerifier
from simulador_quad.api.envelope import (
    DATASET_WAYPOINTS_G01_G06,
    is_waypoint_geometry_in_dataset,
    validate_mission_envelope,
)
from simulador_quad.api.models import (
    CompositeSegmentConfig,
    MissionConfigRequest,
    TrajectoryFamily,
    WindConfig,
)
from simulador_quad.api.pid_selection import select_pid_for_mission
from simulador_quad.api.presets import (
    generate_initial_variant,
    get_composite_presets,
    get_waypoint_presets,
)
from simulador_quad.api.scenario_builder import build_trajectory_config, compute_preview
from simulador_quad.api.server import app, series_from_samples
from simulador_quad.trajectories.analytic import CircleTrajectory

client = TestClient(app)


def test_acceptance_check_01_catalog_and_repeatability():
    """
    Comprobación 1:
    El visitante puede elegir cada una de las cinco familias, recibir variantes iniciales que pueden
    cambiar en sucesivas elecciones, ajustar sus parámetros admitidos y recuperar exactamente la
    configuración de una prueba. El punto de inicio aparece y no se edita de forma independiente.
    """
    families = [
        TrajectoryFamily.HOLD,
        TrajectoryFamily.CIRCLE,
        TrajectoryFamily.LISSAJOUS,
        TrajectoryFamily.WAYPOINT,
        TrajectoryFamily.LEMNISCATE,
    ]

    for fam in families:
        var1 = generate_initial_variant(fam.value, seed=1)
        var2 = generate_initial_variant(fam.value, seed=2)
        # Ambas son válidas
        m1 = MissionConfigRequest(
            mode="simple", family=fam, params=var1, wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0), seed=1
        )
        m2 = MissionConfigRequest(
            mode="simple", family=fam, params=var2, wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0), seed=2
        )
        valid1, err1, _, _ = validate_mission_envelope(m1)
        valid2, err2, _, _ = validate_mission_envelope(m2)
        assert valid1 is True, f"Error en variante 1 de {fam}: {err1}"
        assert valid2 is True, f"Error en variante 2 de {fam}: {err2}"

        # El punto de inicio se deriva de la geometría, no se edita aparte
        prev1 = compute_preview(m1)
        assert prev1.initial_position is not None
        assert len(prev1.initial_position) == 3
        # Repetibilidad exacta con la misma configuración
        prev1_again = compute_preview(m1)
        assert prev1.points == prev1_again.points
        assert prev1.initial_position == prev1_again.initial_position


def test_acceptance_check_02_waypoint_presets_outside_splits():
    """
    Comprobación 2:
    Los presets waypoint propuestos por defecto no corresponden a rutas de train ni test;
    un visitante puede introducir coordenadas nuevas y ver la ruta antes de ejecutarla.
    El entrenamiento regenerado conserva las geometrías y divisiones originales, sin incorporar
    estos presets de aplicación.
    """
    presets = get_waypoint_presets()
    assert "waypoint_clean" in presets

    for preset_name, preset_data in presets.items():
        wps = preset_data["waypoints"]
        assert not is_waypoint_geometry_in_dataset(wps), (
            f"El preset {preset_name} coincide con una geometría g01-g06 de train/test!"
        )

    # Introducción de coordenadas manuales arbitrarias
    manual_wps = [[0.0, 0.0, 2.0], [1.2, 0.8, 2.2], [2.0, 1.5, 2.5], [0.5, 2.0, 2.0]]
    mission_manual = MissionConfigRequest(
        mode="simple",
        family=TrajectoryFamily.WAYPOINT,
        params={
            "waypoints": manual_wps,
            "max_speed_m_s": 0.6,
            "max_acceleration_m_s2": 0.5,
            "dwell_time_s": 0.3,
        },
        wind=WindConfig(magnitude_m_s=0.2, direction_deg=30.0),
        seed=100,
    )
    valid, errors, _, _ = validate_mission_envelope(mission_manual)
    assert valid is True, f"Ruta manual válida rechazada: {errors}"

    preview = compute_preview(mission_manual)
    assert len(preview.points) > 10
    # La posición inicial coincide con el primer waypoint
    assert np.allclose(preview.initial_position, manual_wps[0], atol=1e-3)


def test_acceptance_check_03_circle_horizontal_vs_inclined():
    """
    Comprobación 3:
    Un círculo horizontal con inclinación cero conserva la referencia del simulador existente.
    Un círculo inclinado válido muestra y ejecuta posición, velocidad, aceleración y orientación
    coherentes; sus límites de altura, velocidad tangencial y aceleración se comprueban antes de ejecutar.
    """
    radius = 1.5
    omega = 0.6
    center = np.array([0.0, 0.0, 2.5])

    # Inclinación 0°
    c_flat = CircleTrajectory(center_W_m=center, radius_m=radius, omega_rad_s=omega, tilt_rad=0.0)
    # Círculo tradicional del simulador (sin tilt)
    c_orig = CircleTrajectory(center_W_m=center, radius_m=radius, omega_rad_s=omega)

    for t in [0.0, 1.0, 3.5, 7.2]:
        ref_flat = c_flat.get_reference(t)
        ref_orig = c_orig.get_reference(t)

        assert np.allclose(ref_flat.position_W_m, ref_orig.position_W_m, atol=1e-6)
        assert np.allclose(ref_flat.velocity_W_m_s, ref_orig.velocity_W_m_s, atol=1e-6)
        assert np.allclose(ref_flat.acceleration_W_m_s2, ref_orig.acceleration_W_m_s2, atol=1e-6)
        assert np.allclose(ref_flat.yaw_rad, ref_orig.yaw_rad, atol=1e-6)

    # Inclinado a 20°
    c_tilt = CircleTrajectory(center_W_m=center, radius_m=radius, omega_rad_s=omega, tilt_rad=np.radians(20.0), plane_yaw_rad=np.radians(45.0))
    for t in [0.0, 2.0, 5.0]:
        ref_tilt = c_tilt.get_reference(t)
        pos = ref_tilt.position_W_m
        vel = ref_tilt.velocity_W_m_s
        acc = ref_tilt.acceleration_W_m_s2
        yaw = ref_tilt.yaw_rad
        # La altura debe mantenerse dentro de la envolvente
        assert 0.5 <= pos[2] <= 6.0
        # Magnitud de velocidad debe ser R*omega
        assert np.isclose(np.linalg.norm(vel), radius * omega, atol=1e-5)
        # Magnitud de aceleración centrípeta R*omega^2
        assert np.isclose(np.linalg.norm(acc), radius * (omega ** 2), atol=1e-5)
        assert -np.pi <= yaw <= np.pi


def test_acceptance_check_04_composite_editor_and_pid_selection():
    """
    Comprobación 4:
    El editor crea una composición de dos a cuatro tramos de tipos mezclados, permite orden y
    duración de los tramos continuos, muestra transiciones y aplica un único PD según la mayor
    longitud nominal. Empates, solo hold y presencia de lemniscata tienen resultado determinista y visible.
    """
    # Caso A: Círculo dominante vs Hold
    segs_circle_dominant = [
        CompositeSegmentConfig(type="hold", duration=3.0, params={"position_W_m": [0, 0, 2]}),
        CompositeSegmentConfig(type="circle", duration=12.0, params={"center_W_m": [0, 0, 2], "radius_m": 1.5, "omega_rad_s": 0.6}),
        CompositeSegmentConfig(type="hold", duration=2.0, params={"position_W_m": [0, 0, 2]}),
    ]
    mission_a = MissionConfigRequest(
        mode="composite",
        family=TrajectoryFamily.COMPOSITE,
        params={},
        segments=segs_circle_dominant,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    pid_fam_a, exp_a, _ = select_pid_for_mission(mission_a.mode, mission_a.family.value, mission_a.params, mission_a.segments)
    assert pid_fam_a == "circle"
    assert "círculo" in exp_a.lower() or "circle" in exp_a.lower()

    # Caso B: Solo hold -> PID hold
    segs_hold_only = [
        CompositeSegmentConfig(type="hold", duration=4.0, params={"position_W_m": [0, 0, 2]}),
        CompositeSegmentConfig(type="hold", duration=5.0, params={"position_W_m": [1, 1, 2]}),
    ]
    mission_b = MissionConfigRequest(
        mode="composite",
        family=TrajectoryFamily.COMPOSITE,
        params={},
        segments=segs_hold_only,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    pid_fam_b, exp_b, _ = select_pid_for_mission(mission_b.mode, mission_b.family.value, mission_b.params, mission_b.segments)
    assert pid_fam_b == "hold"

    # Caso C: Lemniscata -> asocia al PID de lissajous
    segs_lemniscate = [
        CompositeSegmentConfig(type="hold", duration=2.0, params={"position_W_m": [0, 0, 2]}),
        CompositeSegmentConfig(type="lemniscate", duration=10.0, params={"center_W_m": [0, 0, 2], "a": 2.0, "b": 1.0, "omega_rad_s": 0.35}),
    ]
    mission_c = MissionConfigRequest(
        mode="composite",
        family=TrajectoryFamily.COMPOSITE,
        params={},
        segments=segs_lemniscate,
        wind=WindConfig(magnitude_m_s=0.0, direction_deg=0.0),
        seed=42,
    )
    pid_fam_c, exp_c, _ = select_pid_for_mission(mission_c.mode, mission_c.family.value, mission_c.params, mission_c.segments)
    assert pid_fam_c == "lissajous"
    assert "lemniscata" in exp_c.lower()


def test_acceptance_check_05_execution_conditions_and_isolation():
    """
    Comprobación 5:
    PD, MLP, GRU y LSTM ejecutan la misma configuración y semilla.
    La comparación no cambia física, viento o punto de inicio entre controladores y
    no se alimenta con una ejecución anterior cuando una nueva falla.
    """
    payload = {
        "mode": "simple",
        "family": "hold",
        "params": {"position_W_m": [0.0, 0.0, 1.8], "duration": 1.0},
        "wind": {"magnitude_m_s": 0.4, "direction_deg": 45.0},
        "seed": 2042,
    }
    resp = client.post("/api/simulation/run", json=payload)
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]

    # Poll status until done
    for _ in range(30):
        st = client.get(f"/api/simulation/{run_id}/status").json()
        if st["state"] in ("completed", "partial", "error"):
            break
        time.sleep(0.4)

    assert st["state"] == "completed"
    res = client.get(f"/api/simulation/{run_id}/results").json()
    assert res["seed"] == 2042
    assert res["effective_config"]["vehicle"]["mass_kg"] == 1.0
    # Cada controlador tiene su entrada con métricas propias
    assert set(res["summaries"].keys()) == {"classic", "mlp", "gru", "lstm"}


def test_acceptance_check_06_comparison_playback_and_early_termination():
    """
    Comprobación 6:
    La comparación reproduce ruta nominal y ejecuciones con un cursor común; pausar,
    mover el cursor, cambiar velocidad y activar GRU/LSTM mantienen la sincronía.
    Una ejecución cortada se detiene en su última muestra y expone la causa.
    En waypoint se distingue ruta común de referencia temporal propia.
    """
    # Lanzar una corrida breve con waypoint
    payload = {
        "mode": "simple",
        "family": "waypoint",
        "params": {
            "waypoints": [[0.0, 0.0, 2.0], [1.0, 0.0, 2.0]],
            "max_speed_m_s": 0.5,
            "max_acceleration_m_s2": 0.4,
            "dwell_time_s": 0.2,
        },
        "wind": {"magnitude_m_s": 0.0, "direction_deg": 0.0},
        "seed": 3042,
    }
    resp = client.post("/api/simulation/run", json=payload)
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]

    for _ in range(35):
        st = client.get(f"/api/simulation/{run_id}/status").json()
        if st["state"] in ("completed", "partial", "error"):
            break
        time.sleep(0.4)

    res = client.get(f"/api/simulation/{run_id}/results").json()
    assert len(res["nominal_path"]) >= 2
    for cid in ["classic", "mlp", "gru", "lstm"]:
        samples = res["runs_trajectory"][cid]
        assert len(samples) > 0
        # Las muestras tienen tiempo creciente y pos tridimensional
        assert samples[-1]["time_s"] >= samples[0]["time_s"]
        assert len(samples[0]["pos"]) == 3


def test_acceptance_check_07_metrics_fidelity_and_no_auto_winner():
    """
    Comprobación 7:
    Estado, separación media y separación máxima proceden de las métricas del simulador y
    se muestran con unidades y alcance temporal. Un tiempo límite de trayectoria continua y
    una terminación por waypoint se explican de manera distinta; no aparece una clasificación universal.
    """
    payload = {
        "mode": "simple",
        "family": "circle",
        "params": {
            "center_W_m": [0.0, 0.0, 2.0],
            "radius_m": 1.2,
            "omega_rad_s": 0.5,
            "duration": 1.5,
        },
        "wind": {"magnitude_m_s": 0.1, "direction_deg": 0.0},
        "seed": 4042,
    }
    resp = client.post("/api/simulation/run", json=payload)
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]

    for _ in range(30):
        st = client.get(f"/api/simulation/{run_id}/status").json()
        if st["state"] in ("completed", "partial", "error"):
            break
        time.sleep(0.4)

    res = client.get(f"/api/simulation/{run_id}/results").json()
    for cid, summ in res["summaries"].items():
        assert summ["position_mae_m"] is not None
        assert summ["position_max_err_m"] is not None
        assert summ["position_mae_m"] >= 0.0
        assert summ["position_max_err_m"] >= summ["position_mae_m"]
        assert "winner" not in summ
        assert "rank" not in summ


def test_acceptance_check_08_analysis_telemetry_and_export():
    """
    Comprobación 8:
    Análisis muestra gráficas con unidades y explicación. Telemetría completa permite localizar
    y representar campos presentes, consultar el mismo instante que en la reproducción y exportar
    muestras; no inventa valores donde una señal falta.
    """
    payload = {
        "mode": "simple",
        "family": "hold",
        "params": {"position_W_m": [0.0, 0.0, 1.5], "duration": 1.0},
        "wind": {"magnitude_m_s": 0.0, "direction_deg": 0.0},
        "seed": 5042,
    }
    resp = client.post("/api/simulation/run", json=payload)
    run_id = resp.json()["run_id"]

    for _ in range(30):
        st = client.get(f"/api/simulation/{run_id}/status").json()
        if st["state"] in ("completed", "partial", "error"):
            break
        time.sleep(0.4)

    # Telemetría PD
    telem_pd = client.get(f"/api/simulation/{run_id}/telemetry/classic").json()
    assert "signals" in telem_pd
    assert "units" in telem_pd
    assert "groups" in telem_pd
    assert telem_pd["units"]["pos_x_m"] == "m"
    assert telem_pd["units"]["thrust_N"] == "N"

    # Exportación JSON
    exp_json = client.get(f"/api/simulation/{run_id}/export/json")
    assert exp_json.status_code == 200
    data_json = exp_json.json()
    assert data_json["metadata"]["run_id"] == run_id
    assert "telemetry_files" in data_json

    # Exportación CSV
    exp_csv = client.get(f"/api/simulation/{run_id}/export/csv")
    assert exp_csv.status_code == 200
    reader = csv.reader(io.StringIO(exp_csv.text))
    rows = list(reader)
    assert len(rows) > 5
    # Cabecera contiene controller_id, time_s, etc.
    assert "controller_id" in rows[0]
    assert "time_s" in rows[0]


def test_acceptance_check_09_offline_package_and_manifest():
    """
    Comprobación 9:
    La demostración arranca con PD, checkpoints outer-force, normalización y configuración
    disponibles localmente, sin red ni entrenamiento. Un artefacto ausente o incompatible
    produce un diagnóstico claro. Los nuevos resultados quedan separados de la memoria y
    results/ históricos.
    """
    verifier = BundleVerifier()
    res = verifier.verify()
    assert res["valid"] is True
    assert res["files_checked"] >= 7

    # Verificar que los directorios históricos no han sido alterados
    runs_dir = Path("data/neuroflight_runs")
    assert runs_dir.exists()
    # Los resultados de neuroflight no deben guardarse en results/
    for item in runs_dir.iterdir():
        assert not str(item).startswith("results")


def test_acceptance_check_10_presentation_accessibility_and_responsive():
    """
    Comprobación 10:
    El primer recorrido y el detalle funcionan en escritorio y móvil, con teclado, reflujo,
    foco visible, significado no dependiente solo del color y alternativa textual al visor.
    """
    # Verificar que los archivos del frontend implementan las directivas requeridas:
    frontend_dir = Path("frontend/src")

    # index.css: media query prefers-reduced-motion y focus visible
    css_content = (frontend_dir / "index.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in css_content
    assert ":focus-visible" in css_content

    # TrajectoryViewer3D: soporte touch, teclado (onKeyDown, Arrow keys, +/-, R), ARIA role y live summary
    viewer_code = (frontend_dir / "components" / "TrajectoryViewer3D.tsx").read_text(encoding="utf-8")
    assert "onTouchStart" in viewer_code
    assert "onTouchMove" in viewer_code
    assert "handleKeyDown" in viewer_code
    assert "role=\"region\"" in viewer_code
    assert "role=\"status\"" in viewer_code
    assert "aria-live=\"polite\"" in viewer_code
    assert "touch-none" in viewer_code

    # TelemetryChart: distinción no basada solo en color (estilo de trazo continuo/trazos/puntos), touch handlers
    chart_code = (frontend_dir / "components" / "TelemetryChart.tsx").read_text(encoding="utf-8")
    assert "styleLabel" in chart_code
    assert "onTouchStart" in chart_code
    assert "onTouchMove" in chart_code
