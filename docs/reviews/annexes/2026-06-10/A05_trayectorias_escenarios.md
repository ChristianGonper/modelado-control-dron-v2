# Anexo A05 — Trayectorias y escenarios

**Fecha:** 2026-06-10 | **Owner:** A05

## Superficie revisada

`trajectories/` (analytic, composite, contract), `scenarios/*.yaml`, `scenarios/loader.py`, `scenarios/schema.py`, `tests/test_trajectories.py`, `tests/test_scenarios.py`, `tests/test_composite_trajectory.py`, `data/neural_ood/battery_v1/scenarios/`.

## Invariantes y contratos comprobados

- Trayectorias analíticas hold/circle/lissajous/lemniscate (`test_trajectories.py`).
- Validación física YAML (`test_scenarios.py` — 18 tests collect).
- Composite con/sin transición (`test_composite_trajectory.py`).
- `composite_ood` alineación inicial documentada en `validacion.md:54`.

## Hallazgos del dominio

| ID | Sev. |
|----|------|
| F-017 | P2 |
| F-021 | P3 |

## Históricos revalidados

- composite_ood estado inicial (jun-02): **cerrado** en validacion.md.

## No verificable

- Comportamiento cerrado composite OOD masivo (evidencia parcial en comparison_summary).

## Zonas sin problemas

- Escenarios oficiales dataset `max_attitude_angle_rad: 1.256` coherente.
- Loader rechaza masa/inercia/rotores inválidos.

## Comandos

`uv run pytest tests/test_trajectories.py tests/test_scenarios.py tests/test_composite_trajectory.py -q` → **29 passed** (18+7+4 collect).

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A06 | ¿Terminación trajectory-aware? | Sí (`test_runner.py`) |
| A10 | ¿OOD battery schema válido? | Sí; manifest split=ood |
| A03 | ¿Referencias físicamente consistentes? | Sí salvo F-021 transición |