# Anexo A06 — Ejecución, telemetría y métricas

**Fecha:** 2026-06-10 | **Owner:** A06

## Superficie revisada

`app.py`, `runner.py`, `telemetry/export.py`, `metrics/report.py`, `visualization/`, `tests/test_runner.py`, `tests/test_metrics.py`, `tests/test_telemetry_desired_force.py`, `tests/test_app_metadata.py`, `tests/test_visualization.py`.

## Invariantes y contratos comprobados

- Multi-rate y ZOH (`test_runner.py`).
- Terminaciones múltiples (altura, actitud, saturación, no finitos).
- Telemetría `desired_force_W_N` y viento (`test_telemetry_desired_force.py`).
- Metadata reproducibilidad campos (`test_app_metadata.py`).

## Hallazgos del dominio

| ID | Sev. |
|----|------|
| F-011 | P2 |

## Históricos revalidados

- Telemetría sin desired_force (mayo P2): **cerrado**.

## No verificable

- Presencia metadata en 100% telemetrías locales (muestra parcial).

## Zonas sin problemas

- Export JSON telemetría/métricas finitos en regresión corta.
- Figuras PNG y HTML 3D generables.

## Comandos

`uv run pytest tests/test_runner.py tests/test_metrics.py tests/test_telemetry_desired_force.py tests/test_app_metadata.py tests/test_visualization.py -q` → **19 passed**.

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A09 | ¿Outer-force escribe desired_force? | Sí |
| A01 | ¿Metadata commit en runs? | Diseño sí; evidencia F-003 |
| A13 | ¿guia_uso advierte heuristic? | Sí :163-164 |