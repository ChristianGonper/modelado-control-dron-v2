# Anexo A10 — Oráculo y campañas

**Fecha:** 2026-06-10 | **Owner:** A10

## Superficie revisada

`tools/generate_outer_force_pid_bank.py`, `generate_outer_force_dataset.py`, `generate_ood_battery.py`, `run_experimental_campaign.py`, `summarize_comparison.py`, `build_comparison_closed_loop.py`, `data/outer_force_pid_bank/v1`, `data/outer_force_dataset/v1`, `data/neural_ood/battery_v1`, `results/comparison_*.csv`, `tests/test_outer_force_generation_integration.py`, `tests/test_campaign_scripts.py`, `tests/test_neural_batch_tools.py`, `tests/test_generate_ood_battery.py`.

## Invariantes y contratos comprobados

- Pipeline outer-force integración (`test_outer_force_generation_pipeline`).
- OOD battery smoke (`test_generate_ood_battery_smoke`).
- Campaign dry-run 11 fases sin error.
- summarize_comparison genera CSV y LaTeX.

## Hallazgos del dominio

| ID | Sev. |
|----|------|
| F-002 | P1 |
| F-014 | P2 |

## Históricos revalidados

- Sin outer_force en data (jun P0): **cerrado localmente**.
- OOD script WIP typo (jun P1): **cerrado** — `generate_ood_battery.py` trackeado.

## No verificable

- Ejecución campaña completa `--rerun` (prohibida en auditoría).

## Zonas sin problemas

- Orquestador documenta fases 1-11 coherentes con README.
- `comparison_summary.csv` agrega neural outer-force test+ood.

## Comandos

| Comando | Resultado |
|---------|-----------|
| `uv run python tools/run_experimental_campaign.py --dry-run` | OK, 11 fases |
| Inspección `comparison_all_runs.csv` | 4 controladores; 249 filas raw |

Controladores presentes: `classic_family_pid` (150), `neural_outer_force_mlp/gru/lstm` (33 c/u). **Ausentes:** `outer_force_oracle`, `classic_transfer_*`, `neural_position_*`.

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A07 | ¿Transfer ejecutado? | No F-005 |
| A09 | ¿Position reports? | No F-004 |
| A12 | ¿comparison_closed_loop_v1? | Ausente |