import time
import pytest
from fastapi.testclient import TestClient

from simulador_quad.api.server import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "NeuroFlight"
    assert data["team"] == "AeroLab"
    assert data["status"] in ("ok", "degraded")
    assert data["bundle"]["valid"] is True


def test_api_presets():
    response = client.get("/api/presets?seed=42")
    assert response.status_code == 200
    data = response.json()
    assert "initial_variants" in data
    assert "waypoint_presets" in data
    assert "composite_presets" in data
    assert "circle" in data["initial_variants"]
    assert "waypoint_clean" in data["waypoint_presets"]


def test_api_validate_valid_mission():
    payload = {
        "mode": "simple",
        "family": "circle",
        "params": {
            "center_W_m": [0.0, 0.0, 2.0],
            "radius_m": 1.5,
            "omega_rad_s": 0.6,
            "tilt_deg": 10.0,
            "plane_yaw_deg": 0.0,
            "yaw_mode": "forward",
            "duration": 5.0,
        },
        "wind": {"magnitude_m_s": 0.5, "direction_deg": 45.0},
        "seed": 42,
    }
    response = client.post("/api/mission/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert len(data["errors"]) == 0
    assert data["selected_pid_family"] == "circle"


def test_telemetry_missing_fields_stay_unavailable():
    from simulador_quad.api.server import series_from_samples

    extracted = series_from_samples([
        {"time_s": 0.1, "state": {"velocity_W_m_s": [0.2, 0.0, 0.0]}},
        {"time_s": 0.2, "state": {"position_W_m": [1.0, 2.0, 3.0]}, "reference": {"position_W_m": [1.0, 2.0, 3.0]}},
    ])
    assert extracted["signals"]["pos_x_m"][0] is None
    assert extracted["signals"]["ref_x_m"][0] is None
    assert extracted["signals"]["pos_err_m"][0] is None
    assert extracted["signals"]["wind_x_m_s"][0] is None
    assert extracted["signals"]["thrust_N"][0] is None
    assert extracted["signals"]["vel_x_m_s"][0] == 0.2
    assert extracted["signals"]["pos_err_m"][1] == 0.0


def test_api_validate_invalid_envelope():
    # Radio excesivo (5.0 m) e inclinación fuera de rango (45°)
    payload = {
        "mode": "simple",
        "family": "circle",
        "params": {
            "center_W_m": [0.0, 0.0, 2.0],
            "radius_m": 5.0,
            "omega_rad_s": 1.0,
            "tilt_deg": 45.0,
            "duration": 10.0,
        },
        "wind": {"magnitude_m_s": 2.5, "direction_deg": 0.0}, # viento excesivo
        "seed": 42,
    }
    response = client.post("/api/mission/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["errors"]) >= 3
    err_str = " ".join(data["errors"]).lower()
    assert "radio" in err_str
    assert "viento" in err_str
    assert "inclinación" in err_str or "inclinacion" in err_str


def test_api_preview():
    payload = {
        "mode": "simple",
        "family": "circle",
        "params": {
            "center_W_m": [0.0, 0.0, 2.0],
            "radius_m": 1.5,
            "omega_rad_s": 0.6,
            "duration": 4.0,
        },
        "wind": {"magnitude_m_s": 0.0, "direction_deg": 0.0},
        "seed": 42,
    }
    response = client.post("/api/mission/preview", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["points"]) > 10
    assert len(data["time_series"]) == len(data["points"])
    assert "bounds" in data
    assert data["bounds"]["min_z"] >= 0.5
    assert "accessibility_summary" in data


def test_api_full_simulation_run():
    """Ejecuta una simulación breve de los 4 controladores y verifica resultados y telemetría."""
    payload = {
        "mode": "simple",
        "family": "hold",
        "params": {
            "position_W_m": [0.0, 0.0, 1.5],
            "yaw_rad": 0.0,
            "duration": 1.5, # corta para test rápido
        },
        "wind": {"magnitude_m_s": 0.2, "direction_deg": 0.0},
        "seed": 1042,
    }

    # 1. Lanzar simulación
    run_resp = client.post("/api/simulation/run", json=payload)
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run_id"]
    assert run_id is not None

    # 2. Esperar finalización
    max_wait = 20.0
    start_t = time.time()
    final_status = None

    while time.time() - start_t < max_wait:
        st_resp = client.get(f"/api/simulation/{run_id}/status")
        assert st_resp.status_code == 200
        final_status = st_resp.json()
        if final_status["state"] in ("completed", "partial", "error"):
            break
        time.sleep(0.5)

    assert final_status is not None
    assert final_status["state"] == "completed", f"Simulación no completó: {final_status}"
    for cid in ["classic", "mlp", "gru", "lstm"]:
        assert final_status["controllers"][cid]["status"] == "completed"

    # 3. Consultar resultados
    res_resp = client.get(f"/api/simulation/{run_id}/results")
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert res_data["run_id"] == run_id
    assert len(res_data["summaries"]) == 4
    for cid in ["classic", "mlp", "gru", "lstm"]:
        assert cid in res_data["summaries"]
        summ = res_data["summaries"][cid]
        assert summ["status"] == "completed"
        assert summ["position_mae_m"] is not None
        assert summ["duration_s"] > 0.0

    # 4. Consultar telemetría
    telem_resp = client.get(f"/api/simulation/{run_id}/telemetry/classic")
    assert telem_resp.status_code == 200
    telem_data = telem_resp.json()
    assert "signals" in telem_data
    assert "pos_x_m" in telem_data["signals"]
    assert len(telem_data["time_s"]) > 0
    assert res_data["artifact_identity"]["valid"] is True
    assert any(item.get("sha256") for item in res_data["artifact_identity"]["files"])

    # 5. Exportaciones
    export_json = client.get(f"/api/simulation/{run_id}/export/json")
    assert export_json.status_code == 200
    assert export_json.headers["content-type"] == "application/json"

    export_csv = client.get(f"/api/simulation/{run_id}/export/csv")
    assert export_csv.status_code == 200
    assert "text/csv" in export_csv.headers["content-type"]
