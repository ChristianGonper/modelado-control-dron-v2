# Anexo A12 — Evidencia local

**Fecha:** 2026-06-10 | **Owner:** A12

## Superficie revisada (selectiva)

`data/classic_dataset/v1/` (manifest, summary, sample metrics), `data/outer_force_pid_bank/v1/`, `data/outer_force_dataset/v1/`, `data/neural_control/outer_force_*_min_v1/`, `data/neural_ood/battery_v1/`, `results/comparison_all_runs.csv`, `results/comparison_summary.csv`. Sin telemetrías masivas muestra a muestra.

## Inventario resumido

| Ruta | Contenido | En Git |
|------|-----------|--------|
| `data/classic_dataset/v1` | 150 episodios, PIDs, results | No (*) |
| `data/outer_force_pid_bank/v1` | Banco PID externo | No |
| `data/outer_force_dataset/v1` | Manifest experto | No |
| `data/neural_control/outer_force_*_min_v1` | Checkpoints 3-out MLP/GRU/LSTM | No |
| `data/position_gain_dataset` | — | **Ausente** |
| `data/neural_ood/battery_v1` | Escenarios OOD + reports neural | No |
| `results/comparison_*.csv` | Agregados parciales | No |
| `results/comparison_closed_loop_v1.csv` | — | **Ausente** |

## Hallazgos del dominio

| ID | Sev. |
|----|------|
| F-001 | P1 |
| F-003 | P1 |

## Históricos revalidados

- Sin outer_force (jun P0): **refutado** inspección local.
- Legacy 4-out en neural_control: **no presente** en outer_force_*_min_v1 (output_dim 3).

## No verificable

- Integridad hashes de todos los checkpoints sin script dedicado.

## Zonas sin problemas

- `summary.csv` clásico: 150 VALID.
- Reports OOD neural mlp/gru/lstm en battery_v1.

## Comandos

Inspección filesystem + lectura `metrics.json` muestra (hold_g01_P0_nominal_s1042).

Metadata muestra: `git_commit: 0cee096…`, `git_dirty: true` (F-003).

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A01 | ¿Política gitignore? | F-001 |
| A10 | ¿Suficiente para comparativa? | No F-002 |
| A14 | ¿Memoria puede citar? | Solo con manifiesto/commit |