# Simulador quad 6DOF para TFG

Este repositorio contiene el desarrollo de un simulador 6DOF de cuadricoptero para un Trabajo de Fin de Grado. El objetivo es disponer de un banco de ensayo trazable para comparar un controlador clasico con controladores neuronales entrenados por imitacion.

El estado actual incluye la parte clasica del simulador y un controlador hibrido `neural`: la red predice la fuerza deseada del lazo externo en mundo ENU y el PID clasico conserva el lazo interno de actitud. Se pueden entrenar y ejecutar redes MLP y recurrentes (GRU/LSTM); la MLP es la opcion inicial de menor complejidad.

## Estado actual

Implementado:

- Dinámica de cuerpo rígido 6DOF con mundo ENU y cuerpo FRD.
- Actitud mediante cuaterniones `[w, x, y, z]`.
- Integración RK4 con pasos separados de física, control y telemetría.
- Controlador clasico en cascada y controlador `neural` hibrido: red de fuerza externa `desired_force_W_N[3]` y lazo interno clasico.
- Pipeline de ML con PyTorch: Datasets para MLP y Secuenciales (GRU/LSTM), Normalización determinista, Arquitecturas y Entrenamiento supervisado.
- Mixer de cuadricóptero, actuadores con saturación, retardo puro opcional y lag de primer orden sobre `omega`.
- Drag lineal simplificado, viento constante y ruido gaussiano de observación en posición/velocidad.
- Referencias analíticas (`hold`, `circle`, `lissajous`, `lemniscate`), misión secuencial state-aware con parada en cada punto (`waypoint`), y **trayectorias compuestas** (`composite`) que permiten encadenar secuencias con transiciones lineales automáticas.
- Escenarios YAML, telemetría JSON, métricas JSON con unidades físicas explícitas, figuras PNG/PDF (300 dpi) y visor 3D HTML.
- Postproceso visual con perfiles `diagnostic`/`report`, figuras por episodio (`plot`) y comparativas agregadas de campaña (`plot-comparison`).
- Tooling para generar el dataset `outer_force`, batería OOD (`generate_ood_battery.py`), batch cerrado (`run_neural_outer_force_dataset.py`), sensibilidad neuronal (`run_neural_sensitivity_study.py`, `summarize_neural_sensitivity.py`), tabla comparativa (`build_comparison_closed_loop.py`) y entrenar/evaluar modelos mediante scripts en `tools/`.
- Control neuronal alternativo en el lazo externo de posición (`neural_position`), donde la red predice ganancias variables y el lazo interno clásico estabiliza actitud.

## Comandos minimos

```powershell
uv sync
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures_report --profile report --formats png pdf
uv run simulador-quad plot-comparison results\comparison_all_runs.csv --out results\figures_comparison --formats png pdf
```

Para generar y ejecutar el dataset clasico `v1`:

```powershell
uv run python tools\generate_classic_dataset.py --version v1 --out data\classic_dataset\v1
uv run python tools\run_classic_dataset.py --dataset data\classic_dataset\v1 --no-visualization --workers 4
uv run python tools\summarize_classic_dataset.py --dataset data\classic_dataset\v1
```

Para el controlador `neural` de fuerza externa:

```powershell
# Banco de candidatos de PID externo bajo las condiciones de cada escenario
uv run python tools\generate_outer_force_pid_bank.py --dataset data\classic_dataset\v1 --out data\outer_force_pid_bank\v1 --workers 8

# Dataset con el experto seguro seleccionado y targets de fuerza ENU
uv run python tools\generate_outer_force_dataset.py --source-dataset data\classic_dataset\v1 --pid-bank data\outer_force_pid_bank\v1 --out data\outer_force_dataset\v1

# Entrenamiento inicial recomendado: MLP con features minimas
uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 --architecture mlp --feature-version outer_force_min_v1 --out data\neural_control\outer_force_mlp_min_v1 --device auto

# Evaluacion supervisada in-distribution
uv run python tools\evaluate_neural_controller.py --dataset data\outer_force_dataset\v1 --run data\neural_control\outer_force_mlp_min_v1 --device auto

# Ejecucion en bucle cerrado (escenario OOD)
uv run python tools\run_neural_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --device auto --no-visualization

# Batch cerrado sobre manifest (test u OOD)
uv run python tools\run_neural_outer_force_dataset.py --dataset data\outer_force_dataset\v1 --split test --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --no-visualization

# Bateria OOD local ignorada por git (manifest split=ood)
uv run python tools\generate_ood_battery.py --out data\neural_ood\battery_v1 --overwrite
```

Para ejecutar el estudio de sensibilidad de `outer_force_min_v1` sin sobrescribir
el baseline:

```powershell
uv run python tools\run_neural_sensitivity_study.py --device auto --workers 1
uv run python tools\summarize_neural_sensitivity.py
```

Las variantes se escriben con sufijos propios (`h128`, `L10`, `L40`, semillas)
en `data/`, y los CSV agregados quedan en `results/neural_sensitivity/`.

El banco `outer_force` ejecuta variantes del PID externo para cada escenario fuente, conserva el PID interno y los limites del YAML original, excluye candidatos inseguros y elige el experto por RMSE, esfuerzo dentro del margen del 5% y conservadurismo en empate. La evaluacion supervisada compara fuerzas ENU predichas con `desired_force_W_N` del experto; la calidad de control se compara en bucle cerrado con `position_rmse_m`, errores auxiliares, terminacion, saturacion, degradacion y porcentajes de clipping de fuerza. `run_neural_scenario.py` sustituye el controlador del YAML en memoria sin modificarlo. Los checkpoints legacy de cuatro comandos finales o seis salidas de `neural_position` no son compatibles con `controller.type: neural`.

`data\neural_ood\battery_v1` contiene solo escenarios OOD generados localmente. Regenerarlo es barato y no debe confundirse con evidencia experimental final; la evidencia final requiere ejecutar los escenarios, conservar `metrics.json`/`telemetry.json` y construir las tablas consolidadas mediante `tools/summarize_comparison.py`.

La comparación consolidada distingue completar la misión (`mission_success`) de terminar sin fallo físico (`safety_success`). En trayectorias finitas, alcanzar el límite temporal no cuenta como misión completada.

Para el modo alternativo `neural_position`, que programa multiplicadores de ganancias:

```powershell
uv run python tools\generate_pid_bank.py --dataset data\classic_dataset\v1 --out data\pid_bank\v1
uv run python tools\generate_position_gain_dataset_from_bank.py --source-dataset data\classic_dataset\v1 --pid-bank data\pid_bank\v1 --out data\position_gain_dataset\v1
uv run python tools\run_classic_dataset.py --dataset data\position_gain_dataset\v1 --no-visualization --workers 4
uv run python tools\train_neural_position_controller.py --dataset data\position_gain_dataset\v1 --architecture gru --out data\neural_control\position_gru_v1 --device cuda
uv run python tools\run_neural_position_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\position_gru_v1\checkpoints\gru_best.pt --normalization data\neural_control\position_gru_v1\normalization.json --device cuda
uv run python tools\run_neural_position_dataset.py --dataset data\position_gain_dataset\v1 --split test --checkpoint data\neural_control\position_gru_v1\checkpoints\gru_best.pt --normalization data\neural_control\position_gru_v1\normalization.json --device cuda --no-visualization
```

En `run_neural_position_dataset.py`, omitir `--split` ejecuta todos los escenarios del manifiesto; `--split test` limita la ejecucion al subconjunto de test.

Para ejecutar la campaña experimental completa de forma automatizada y consolidar resultados en tablas comparativas LaTeX:

```powershell
# Ejecutar la campaña completa en modo dry-run para verificar comandos (incluye tune PID base)
uv run python tools\run_experimental_campaign.py --dry-run

# Ejecutar desde cero (sanidad, gen clasico inicial, tune PID base, regen+baseline, bancos neuronales, ...)
uv run python tools\run_experimental_campaign.py --rerun --workers 8 --device cuda

# Tuneo standalone de PIDs base (diagnostica todas, retunea solo las que lo necesiten)
uv run python tools\tune_classic_pid.py --dataset data\classic_dataset\v1 --out data\classic_dataset\v1\pids --workers 8

# Forzar retuneo de todas (cambia la condicion experimental)
uv run python tools\tune_classic_pid.py --dataset data\classic_dataset\v1 --out data\classic_dataset\v1\pids --force --rmse-hold 0.20 --workers 8
```

La campaña (11 fases numeradas tras insercion de tune) no resuelve automáticamente las dependencias al
ejecutar fases aisladas. Usar --phase 1-4 para preparar baseline congelado. La transferencia genera `scenarios_transfer/`,
`results_transfer/` y `run_report_classic_transfer.csv`; el resumen genera
`results\comparison_all_runs.csv` y `results\comparison_summary.csv`, mientras
que las tablas LaTeX se imprimen por salida estándar. Las figuras comparativas
C1–C7 se generan con `plot-comparison` a partir del CSV agregado. La guía de uso
documenta las fases, filtros, criterio de éxito y política de reejecución.

Cambiar umbrales RMSE, presupuesto de candidatos o semilla produce una campaña experimental distinta (quedan registrados en pid_tuning/summary.json y en los YAMLs de PID). Los cuatro conceptos de PID son: inicial (default_initial), base tuneado/congelado (pid_<f>_v1.yaml con source tuned o accepted), banco neural_position (variantes solo externas a partir del base), oraculo outer-force (por escenario, pos-only).

Tras el tuneo se deben regenerar los escenarios con `generate_classic_dataset.py --overwrite`: `run_classic_dataset.py` ejecuta las ganancias embebidas en cada YAML y rechaza escenarios que no coincidan con su PID congelado.

Para paralelizar simulaciones independientes en CPU se puede subir `--workers` en `tune_classic_pid.py`, `generate_outer_force_pid_bank.py`, `run_classic_dataset.py` o `run_neural_position_dataset.py`. El banco outer-force reparte escenarios fuente independientes entre procesos y evalua las cinco variantes de cada escenario en serie. Con una sola GPU, lo normal es entrenar/evaluar con `--device cuda` y mantener `--workers 1` en inferencia CUDA; varios workers CUDA cargan copias independientes del modelo en la misma GPU y pueden competir por memoria.

Para ejecutar otros escenarios:

```powershell
uv run simulador-quad run scenarios\circle_drag.yaml --no-visualization
uv run simulador-quad run scenarios\circle_noisy_wind.yaml --no-visualization
uv run simulador-quad run scenarios\lissajous_clean.yaml --no-visualization
uv run simulador-quad run scenarios\waypoint_clean.yaml --no-visualization
uv run simulador-quad run scenarios\composite_ood.yaml --no-visualization
```

## Mapa documental

- `docs/01_principios_tfg.md`: principios academicos, alcance, trazabilidad y limites del TFG.
- `docs/02_requisitos_ingenieria_simulador.md`: requisitos fisicos y de ingenieria del simulador.
- `docs/03_criterios_ingenieria_software.md`: criterios de software cientifico, pruebas y reproducibilidad.
- `docs/simulador/`: documentacion viva del estado implementado.
- `docs/simulador/trazabilidad.md`: matriz requisito-modelo-codigo-prueba-escenario-metrica.
- `docs/simulador/validacion.md`: clasificacion de escenarios y criterios de aceptacion.
- `docs/simulador/dataset_clasico.md`: generacion, ejecucion y resumen del dataset clasico.
- `docs/simulador/control_neuronal.md`: entrenamiento, evaluacion e inferencia del controlador neuronal por imitacion.
- `docs/plans/archived/`: planes historicos no vigentes; no describen funcionalidad actual.
- `docs/reviews/`: auditorias y revisiones tecnicas.

## Estructura principal

- `src/simulador_quad/`: codigo del paquete Python.
- `tests/`: pruebas unitarias y de integracion ligera.
- `tools/`: scripts de generacion de dataset, ajuste PID, ejecucion masiva y resumen.
- `scenarios/`: escenarios YAML reproducibles.
- `data/classic_dataset/`: ubicacion prevista de datasets clasicos versionados generados localmente.
- `data/outer_force_dataset/`: ubicacion prevista de demostraciones de fuerza externa seleccionadas por escenario.
- `results/`: salidas generadas por ejecuciones.
- `docs/`: documentacion normativa, viva, planes y revisiones.
- `TFG_Memoria/`: memoria LaTeX cerrada del TFG.

## Regla de mantenimiento

Si cambia el comportamiento del simulador, los comandos, escenarios, telemetria, metricas, arquitectura o alcance, deben actualizarse tambien `README.md` y los documentos afectados en `docs/simulador/`.
