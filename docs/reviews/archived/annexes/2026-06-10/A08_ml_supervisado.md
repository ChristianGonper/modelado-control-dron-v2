# Anexo A08 — ML supervisado

**Fecha:** 2026-06-10 | **Owner:** A08

## Superficie revisada

`src/simulador_quad/ml/` (dataset, models, normalization), `tools/train_neural_controller.py`, `evaluate_neural_controller.py`, `data/neural_control/outer_force_*_min_v1/`, `tests/test_neural_dataset.py`, `tests/test_neural_models.py`, `tests/test_neural_training.py`, `tests/test_neural_imports.py`.

## Invariantes y contratos comprobados

- Features outer_force_min (9) y full (31) (`test_neural_dataset.py`).
- Normalizer fit solo train; save/load (`test_normalizer_fit_save_load`).
- Targets fuerza ENU equivalencia clásico (`test_outer_force_target_equivalence_to_classic`).
- Features desde observation (`test_outer_force_features_use_observation_not_state`).
- Factory MLP/GRU/LSTM (`test_neural_models.py`).

## Hallazgos del dominio

| ID | Sev. |
|----|------|
| F-012 | P2 |

## Históricos revalidados

- Leakage observation/state outer-force (jun-02 position): **refutado para outer-force**; position sin dataset (F-004).

## No verificable

- Varianza entre semillas sin re-entrenar.

## Zonas sin problemas

- Checkpoints locales `output_dim: 3`, `feature_version: outer_force_min_v1`.
- Métricas supervisadas `*_force_metrics.json` presentes en mlp_min_v1.

## Comandos

`uv run pytest tests/test_neural_dataset.py tests/test_neural_models.py tests/test_neural_training.py tests/test_neural_imports.py -q` → **19 passed**.

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A09 | ¿Inferencia usa mismas features? | Sí outer-force |
| A10 | ¿Dataset outer_force generado? | Local sí |
| A12 | ¿Checkpoints versionados? | No Git F-001 |