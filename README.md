# Simulador quad 6DOF para TFG

Este repositorio contiene el desarrollo de un simulador 6DOF de cuadricoptero para un Trabajo de Fin de Grado. El objetivo academico es disponer de un banco de ensayo trazable para comparar un controlador clasico con, en una fase posterior, un controlador neuronal entrenado por imitacion.

El estado actual incluye la parte clásica del simulador y el **Pipeline de Control Neuronal por Imitación**, permitiendo entrenar y ejecutar redes MLP y recurrentes (GRU/LSTM) para el control del cuadricóptero.

## Estado actual

Implementado:

- Dinámica de cuerpo rígido 6DOF con mundo ENU y cuerpo FRD.
- Actitud mediante cuaterniones `[w, x, y, z]`.
- Integración RK4 con pasos separados de física, control y telemetría.
- Controlador clásico en cascada y **Controlador Neuronal en bucle cerrado**.
- Pipeline de ML con PyTorch: Datasets para MLP y Secuenciales (GRU/LSTM), Normalización determinista, Arquitecturas y Entrenamiento supervisado.
- Mixer de cuadricóptero, actuadores con saturación, retardo puro opcional y lag de primer orden sobre `omega`.
- Drag lineal simplificado, viento constante y ruido gaussiano de observación en posición/velocidad.
- Referencias analíticas (`hold`, `circle`, `lissajous`, `lemniscate`) y misión secuencial state-aware con parada en cada punto (`waypoint`).
- Escenarios YAML, telemetría JSON, métricas JSON con unidades físicas explícitas, figuras PNG y visor 3D HTML.
- Generación de dataset experto y entrenamiento/evaluación de modelos mediante scripts en `tools/`.
- Control neuronal alternativo en el lazo externo de posición (`neural_position`), donde la red predice ganancias variables y el lazo interno clásico estabiliza actitud.

Fuera de alcance actual:

- Aerodinámica formal más allá del drag lineal.
- Modelo de batería, sensores realistas, estimador onboard, contacto con suelo o validación con datos reales.

## Comandos minimos

```powershell
uv sync
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
```

Para generar y ejecutar el dataset clasico `v1`:

```powershell
uv run python tools\generate_classic_dataset.py --version v1 --out data\classic_dataset\v1
uv run python tools\run_classic_dataset.py --dataset data\classic_dataset\v1 --no-visualization --workers 4
uv run python tools\summarize_classic_dataset.py --dataset data\classic_dataset\v1
```

Para el pipeline neuronal (ML):

```powershell
# Entrenamiento (ejemplo GRU)
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture gru --out data\neural_control\gru_v1 --device cuda

# Evaluacion supervisada in-distribution
uv run python tools\evaluate_neural_controller.py --dataset data\classic_dataset\v1 --run data\neural_control\gru_v1

# Evaluacion supervisada OOD sobre un dataset ya generado
uv run python tools\evaluate_neural_controller.py --dataset data\classic_dataset\v1 --run data\neural_control\gru_v1 --ood-dataset data\neural_ood\lemniscate_v1

# Ejecucion en bucle cerrado (escenario OOD)
uv run python tools\run_neural_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\gru_v1\checkpoints\gru_best.pt --normalization data\neural_control\gru_v1\normalization.json --device cuda
```

La evaluacion supervisada mide fidelidad de imitacion: compara los comandos de la red con los comandos del PID del dataset. La metrica principal para comparar calidad de control es `position_rmse_m` en ejecuciones de bucle cerrado, acompanada de `position_mae_m`, `position_max_err_m`, terminacion y saturacion. La evaluacion OOD supervisada espera un directorio con `manifest.csv` y `telemetry.json` ya generados; no ejecuta por si sola el escenario OOD. Para evaluar en bucle cerrado se usa `run_neural_scenario.py`, que sustituye el controlador del YAML en memoria sin modificar el escenario base. Si no se indica `--architecture`, los scripts de inferencia la leen desde el `config.yaml` del entrenamiento. `--device auto` usa CUDA cuando PyTorch la detecta; `--device cuda` falla de forma explicita si el entorno no tiene GPU disponible.

Para el controlador neuronal de lazo externo:

```powershell
uv run python tools\generate_pid_bank.py --dataset data\classic_dataset\v1 --out data\pid_bank\v1
uv run python tools\generate_position_gain_dataset_from_bank.py --source-dataset data\classic_dataset\v1 --pid-bank data\pid_bank\v1 --out data\position_gain_dataset\v1
uv run python tools\run_classic_dataset.py --dataset data\position_gain_dataset\v1 --no-visualization --workers 4
uv run python tools\train_neural_position_controller.py --dataset data\position_gain_dataset\v1 --architecture gru --out data\neural_control\position_gru_v1 --device cuda
uv run python tools\run_neural_position_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\position_gru_v1\checkpoints\gru_best.pt --normalization data\neural_control\position_gru_v1\normalization.json --device cuda
uv run python tools\run_neural_position_dataset.py --dataset data\position_gain_dataset\v1 --split test --checkpoint data\neural_control\position_gru_v1\checkpoints\gru_best.pt --normalization data\neural_control\position_gru_v1\normalization.json --device cuda --no-visualization
```

Para paralelizar simulaciones independientes en CPU se puede subir `--workers` en `run_classic_dataset.py` o `run_neural_position_dataset.py`. Con una sola GPU, lo normal es entrenar/evaluar con `--device cuda` y mantener `--workers 1` en inferencia CUDA; varios workers CUDA cargan copias independientes del modelo en la misma GPU y pueden competir por memoria.

Para ejecutar otros escenarios:

```powershell
uv run simulador-quad run scenarios\circle_drag.yaml --no-visualization
uv run simulador-quad run scenarios\circle_noisy_wind.yaml --no-visualization
uv run simulador-quad run scenarios\lissajous_clean.yaml --no-visualization
uv run simulador-quad run scenarios\waypoint_clean.yaml --no-visualization
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
- `docs/plans/`: specs vigentes de saneamiento y trabajo futuro inmediato.
- `docs/plans/archived/`: planes historicos no vigentes.
- `docs/reviews/`: auditorias y revisiones tecnicas.

## Estructura principal

- `src/simulador_quad/`: codigo del paquete Python.
- `tests/`: pruebas unitarias y de integracion ligera.
- `tools/`: scripts de generacion de dataset, ajuste PID, ejecucion masiva y resumen.
- `scenarios/`: escenarios YAML reproducibles.
- `data/classic_dataset/`: ubicacion prevista de datasets clasicos versionados generados localmente.
- `results/`: salidas generadas por ejecuciones.
- `docs/`: documentacion normativa, viva, planes y revisiones.

## Regla de mantenimiento

Si cambia el comportamiento del simulador, los comandos, escenarios, telemetria, metricas, arquitectura o alcance, deben actualizarse tambien `README.md` y los documentos afectados en `docs/simulador/`.
