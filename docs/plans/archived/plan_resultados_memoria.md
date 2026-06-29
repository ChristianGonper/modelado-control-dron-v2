# Plan: resultados y atlas visual de memoria

## Estado

Plan ejecutado como plantilla guiada. El usuario redactará la versión final del
capítulo sobre la estructura, figuras, tablas y comentarios LaTeX generados.

## Tareas completadas

- [x] Auditar y corregir la batería OOD helicoidal con `max_duration_s=60`.
- [x] Consolidar `results/comparison_all_runs.csv`,
  `comparison_all_runs_full.csv`, `comparison_summary.csv` y
  `evidence_manifest.csv`.
- [x] Sustituir el contrato visual antiguo (`mem_*`, `c1--c7`) por figuras
  finales `res_*` y atlas `atlas_*`.
- [x] Generar figuras de cuerpo:
  - `res_pid_transfer_matrix`
  - `res_id_rmse_family`
  - `res_ood_rmse_family`
  - `res_ood_scenario_matrix`
  - `res_ood_termination_summary`
  - `res_trajectory_lemniscate_mlp_lstm`
  - `res_protections_ood`
- [x] Generar atlas del anejo:
  - `atlas_trayectorias_id`
  - `atlas_trayectorias_ood`
  - `atlas_trayectoria_helix_3d`
- [x] Convertir `TFG_Memoria/sections/07_resultados.tex` en plantilla guiada
  compilable.
- [x] Actualizar `TFG_Memoria/appendices/a_comandos.tex` como trazabilidad y
  atlas experimental.
- [x] Sincronizar `TFG_Memoria/docs/plan_figuras_diagramas.md`.
- [x] Actualizar tests de visualización al nuevo contrato de figuras.

## Pendiente editorial

- [ ] Redactar manualmente el texto final de resultados a partir de los
  comentarios LaTeX.
- [ ] Revisar después `TFG_Memoria/sections/08_discusion.tex` para alinearla con
  la redacción final del capítulo.

## Verificación esperada

```powershell
uv run simulador-quad plot-comparison results\comparison_all_runs.csv --out TFG_Memoria\Figuras\resultados --formats pdf png
uv run pytest
cd TFG_Memoria
latexmk -pdf main.tex
```
