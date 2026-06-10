# Anexo A04 — Actuadores, mixer y control clásico

**Fecha:** 2026-06-10 | **Owner:** A04

## Superficie revisada

`dynamics/actuators.py`, `mixer.py`, `control/classic.py`, `control/contract.py`, `scenarios/schema.py` (gains), `tests/test_actuators.py`, `tests/test_mixer.py`, `tests/test_control.py`, `tests/test_classic_controller_config.py`.

## Invariantes y contratos comprobados

- Actuadores: lag, delay, saturación (`test_actuators.py`).
- Mixer hover y saturación (`test_mixer.py`).
- PID en cascada; ganancias YAML (`test_classic_controller_config.py`).
- `compute_control_from_desired_force_W` equivalencia outer-force (`test_control.py`).

## Hallazgos del dominio

Ninguno propietario.

## Históricos revalidados

- Ganancias no en YAML (mayo): **cerrado**.

## No verificable

- Rendimiento PID transferido sin `results_transfer/` (dominio A07/A10).

## Zonas sin problemas

- Contrato `Controller` respetado por clásico y neuronal.
- Saturación y degradación reportadas en métricas.

## Comandos

`uv run pytest tests/test_actuators.py tests/test_mixer.py tests/test_control.py tests/test_classic_controller_config.py -q` → **13 passed**.

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A03 | ¿Signo empuje mixer→rigid_body? | Coherente |
| A07 | ¿PIDs congelados en dataset? | Sí en classic v1 |
| A09 | ¿PID interno fijo en outer-force? | Sí (`NeuralOuterForceController`) |