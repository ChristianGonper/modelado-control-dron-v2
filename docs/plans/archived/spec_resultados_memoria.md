# Spec: plantilla de resultados y atlas visual

## Estado

**Implementado como plantilla guiada** (2026-06-26). La campaña experimental y
los CSV consolidados se mantienen como fuente de verdad. El capítulo de
resultados no pretende ser redacción final: queda preparado para que el autor
redacte sobre una estructura profesional con figuras, tablas y comentarios
LaTeX de guía.

- Capítulo: `TFG_Memoria/sections/07_resultados.tex`
- Anejo/atlas: `TFG_Memoria/appendices/a_comandos.tex`
- Figuras: `TFG_Memoria/Figuras/resultados/`
- Generador: `src/simulador_quad/visualization/comparison.py`

## Objetivo

Dejar un capítulo de resultados visualmente sólido y trazable, con alta densidad
curada: siete figuras de cuerpo, tres tablas y un atlas de trayectorias en el
anejo. La redacción final debe distinguir observación, interpretación y
limitación, sin presentar la política neuronal como superior de forma global.

## Figuras del cuerpo

- `res_pid_transfer_matrix`: transferencia cruzada PD en `test`.
- `res_id_rmse_family`: RMSE en familias conocidas; sin panel de éxito.
- `res_ood_rmse_family`: figura principal OOD por familia.
- `res_ood_scenario_matrix`: desglose OOD por escenario y controlador.
- `res_ood_termination_summary`: modos de terminación OOD.
- `res_trajectory_lemniscate_mlp_lstm`: caso visual MLP frente a LSTM.
- `res_protections_ood`: protecciones, clipping y degradación en OOD.

## Atlas del anejo

- `atlas_trayectorias_id`: muestra de `hold`, `circle`, `lissajous` y
  `waypoint`.
- `atlas_trayectorias_ood`: muestra de `lemniscate`, `lissajous` 3D,
  composición y hélice.
- `atlas_trayectoria_helix_3d`: vista 3D de una hélice OOD.

Estas figuras no son evidencia comparativa principal; muestran la variedad de
escenarios y el trabajo realizado.

## Comando de generación

```powershell
uv run simulador-quad plot-comparison results\comparison_all_runs.csv --out TFG_Memoria\Figuras\resultados --formats pdf png
```

## Reglas

- Usar `uv` para toda verificación Python.
- Mantener el cuerpo centrado en cuatro controladores: PD representativo, MLP,
  GRU y LSTM.
- Usar los ocho controladores solo cuando la figura lo justifique, como la
  matriz PD o el material de anejo.
- No ocultar episodios fallidos ni eliminar outliers de OOD.
- No regenerar campañas experimentales salvo inconsistencia objetiva.
- Mantener PDF y PNG para cada figura final.

## Verificación

- `uv run pytest`
- `latexmk -pdf main.tex` desde `TFG_Memoria/`
- Inspección visual de las figuras principales y del atlas.
