# Anexo A07 — Dataset clásico y PID

**Fecha:** 2026-06-10 | **Owner:** A07

## Superficie revisada

`datasets/classic.py`, `tools/generate_classic_dataset.py`, `run_classic_dataset.py`, `summarize_classic_dataset.py`, `tune_classic_pid.py`, `run_classic_transfer_dataset.py`, `data/classic_dataset/v1/`, `tests/test_classic_*`.

## Invariantes y contratos comprobados

- Manifest 150 episodios (`summary.csv` 151 líneas con header).
- PIDs congelados `pids/pid_<family>_v1.yaml`.
- Tuneo progresivo y filtros duros (`test_classic_pid_tuning.py` — 12 tests).
- Rechazo escenarios stale PID (`test_classic_dataset_scripts.py`).

## Hallazgos del dominio

| ID | Sev. |
|----|------|
| F-005 | P1 |

## Históricos revalidados

- Ganancias YAML: **cerrado**.
- Dataset clásico ausente (mayo): **cerrado localmente**.

## No verificable

- Calidad tuneo todas las familias sin revisar `pid_tuning/summary.json` completo.

## Zonas sin problemas

- Splits train/val/test en manifest.
- `run_report.csv` y `summary.csv` coherentes.

## Comandos

`uv run pytest tests/test_classic_dataset_generation.py tests/test_classic_dataset_scripts.py tests/test_classic_pid_selection.py tests/test_classic_pid_tuning.py -q` → **26 passed**.

Inspección: `data/classic_dataset/v1/summary.csv` — 150 episodios VALID.

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A10 | ¿Transfer en comparativa? | Ausente F-005 |
| A08 | ¿Fuente outer-force? | classic v1 usado |
| A01 | ¿Commit metadata? | F-003 |