# Anexo A09 — Control neuronal cerrado

**Fecha:** 2026-06-10 | **Owner:** A09

## Superficie revisada

`control/neural.py`, `tools/run_neural_scenario.py`, `run_neural_outer_force_dataset.py`, `run_neural_position_dataset.py`, `train_neural_position_controller.py`, `tests/test_neural_controller.py`, `tests/test_neural_outer_force.py`, `tests/test_neural_position_control.py`, `tests/test_neural_batch_tools.py`.

## Invariantes y contratos comprobados

- Rechazo checkpoints legacy 4-out y 6-out position (`test_neural_outer_force.py`).
- Aceptación 3-out válido (`test_neural_outer_force_controller_accepts_valid_3out`).
- Clipping fuerza norm/tilt contadores (`test_neural_outer_force_clip_*`).
- Neural position multiplicadores y clipping (`test_neural_position_control.py`).
- Batch outer-force manifest (`test_run_neural_outer_force_dataset_manifest_and_report`).

## Hallazgos del dominio

| ID | Sev. |
|----|------|
| F-004 | P1 |

## Históricos revalidados

- Sin batch outer-force (jun-02 P1): **cerrado** tooling.
- neural_position obs desalineado: **refutado en código** — usa `obs_state`; falta evidencia (F-004).

## No verificable

- Rendimiento cerrado position sin checkpoints.

## Zonas sin problemas

- `NeuralOuterForceController` integrado en loader/schema tests.
- Equivalencia cuando red predice fuerza experta (`test_neural_outer_force_equivalence_*`).

## Comandos

`uv run pytest tests/test_neural_controller.py tests/test_neural_outer_force.py tests/test_neural_position_control.py tests/test_neural_batch_tools.py -q` → **26 passed**.

`uv run python tools/run_neural_outer_force_dataset.py --help` → OK (inspección CLI).

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A08 | ¿Train/deploy features? | OK outer-force |
| A10 | ¿Reports neural en dataset? | mlp/gru/lstm CSV OOD local |
| A06 | ¿Telemetry desired_force? | Sí |