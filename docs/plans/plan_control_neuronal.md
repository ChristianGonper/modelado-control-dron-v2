# Plan: Implementacion de Control Neuronal por Imitacion

## Summary

Implementar la fase definida en `docs/plans/spec_control_neuronal.md`: entrenamiento supervisado por imitacion con PyTorch, tres arquitecturas (`MLP`, `GRU`, `LSTM`), evaluacion supervisada, carga del controlador neuronal en escenarios YAML y ejecucion en bucle cerrado sobre trayectorias existentes y OOD.

La implementacion debe ser incremental. Primero se construye el pipeline offline de datos y modelos; despues se integra el controlador neuronal en el simulador; finalmente se anade evaluacion OOD y documentacion.

Queda fuera de este plan cambiar dinamica 6DOF, mixer, actuadores, PID clasico, splits existentes del dataset clasico o la frecuencia de telemetria.

## Implementation Order

### 1. Dependencia ML y estructura base

Objetivo: preparar el modulo neuronal sin tocar comportamiento clasico.

Cambios:

- Anadir PyTorch a dependencias del proyecto usando `uv`.
- Crear paquete `src/simulador_quad/ml/`.
- Crear modulos base:
  - `dataset.py`;
  - `normalization.py`;
  - `models.py`;
  - `train.py`;
  - `evaluate.py`.
- Crear `src/simulador_quad/control/neural.py`.
- Mantener imports perezosos o localizados si ayudan a que el simulador clasico siga arrancando sin coste innecesario.

Verificacion:

```powershell
uv run pytest
```

Acceptance:

- El proyecto instala y resuelve dependencias con `uv`.
- Los tests existentes siguen pasando.
- No cambia ningun escenario clasico.

### 2. Carga de telemetria y construccion de features

Objetivo: convertir `telemetry.json` en muestras supervisadas reproducibles.

Cambios:

- Implementar lectura de `manifest.csv` desde un dataset clasico.
- Filtrar episodios por `split` y por existencia de `result_dir/telemetry.json`.
- Extraer de cada muestra:
  - observacion: posicion, velocidad, orientacion, velocidad angular;
  - referencia: posicion, velocidad, aceleracion, yaw;
  - errores: referencia menos observacion para posicion y velocidad;
  - `sin(yaw)` y `cos(yaw)`.
- Extraer objetivo:
  - `collective_thrust_N`;
  - `body_moments_Nm[3]`.
- Definir nombres de features y targets en constantes versionadas para evitar cambios silenciosos.
- Rechazar muestras con valores no finitos.

Verificacion:

```powershell
uv run pytest tests\test_neural_dataset.py
```

Acceptance:

- El loader produce arrays finitos `X` e `Y`.
- `Y` tiene dimension final `4`.
- La construccion de features es determinista.
- El loader puede leer al menos un episodio real del dataset `data/classic_dataset/v1` si existe.

### 3. Normalizacion train-only

Objetivo: garantizar que `val`, `test` y OOD no contaminan estadisticos.

Cambios:

- Implementar calculo de media y desviacion para entradas y salidas solo con muestras `train`.
- Guardar y cargar `normalization.json`.
- Aplicar transformacion e inversa de transformacion.
- Proteger desviaciones casi cero con epsilon fijo.
- Incluir en el JSON:
  - version de features;
  - nombres de features;
  - nombres de targets;
  - medias y desviaciones;
  - epsilon.

Verificacion:

```powershell
uv run pytest tests\test_neural_dataset.py
```

Acceptance:

- Los estadisticos se calculan solo desde split `train`.
- `normalization.json` permite reproducir transformaciones.
- La desnormalizacion recupera targets en unidades fisicas dentro de tolerancia numerica.

### 4. Datasets para MLP, GRU y LSTM

Objetivo: entregar datos en el formato correcto para cada arquitectura.

Cambios:

- Implementar dataset instantaneo para `MLP`.
- Implementar dataset secuencial para `GRU` y `LSTM` con ventana fija `sequence_length=20`.
- Las ventanas no deben cruzar limites de episodio.
- El target de una ventana recurrente sera el comando de la ultima muestra de la ventana.
- Permitir configurar `sequence_length`, manteniendo `20` como default.

Verificacion:

```powershell
uv run pytest tests\test_neural_dataset.py
```

Acceptance:

- MLP devuelve `x.shape == [input_dim]`, `y.shape == [4]`.
- GRU/LSTM devuelven `x.shape == [sequence_length, input_dim]`, `y.shape == [4]`.
- No se mezclan muestras de episodios distintos en una misma ventana.

### 5. Modelos MLP, GRU y LSTM

Objetivo: definir arquitecturas comparables y simples.

Cambios:

- Implementar `MLPControllerNet`.
- Implementar `GRUControllerNet`.
- Implementar `LSTMControllerNet`.
- Crear factory `build_model(architecture, input_dim, output_dim, config)`.
- Defaults iniciales:
  - `output_dim = 4`;
  - MLP con 2-3 capas ocultas y activacion ReLU;
  - GRU/LSTM con `batch_first=True`;
  - salida lineal sin activacion final.
- Guardar hiperparametros necesarios en `config.yaml` para reconstruir cada modelo.

Verificacion:

```powershell
uv run pytest tests\test_neural_models.py
```

Acceptance:

- Las tres arquitecturas aceptan tensores batch.
- Las tres devuelven salida `[batch, 4]`.
- La factory falla con error claro para arquitecturas desconocidas.

### 6. Entrenamiento supervisado

Objetivo: entrenar una arquitectura y escribir artefactos reproducibles.

Nuevo script:

```powershell
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture mlp --out data\neural_control\mlp_v1
```

Cambios:

- Implementar bucle de entrenamiento en `src/simulador_quad/ml/train.py`.
- Usar `train` para pesos y `val` para early stopping.
- Loss principal: MSE sobre salidas normalizadas.
- Guardar:
  - `config.yaml`;
  - `normalization.json`;
  - `checkpoints/<architecture>_best.pt`;
  - `metrics/train_metrics.json`;
  - `metrics/val_metrics.json`.
- Registrar semilla, arquitectura, dimensiones, hiperparametros, dataset path y numero de muestras.
- Soportar flags minimos:
  - `--dataset`;
  - `--architecture`;
  - `--out`;
  - `--epochs`;
  - `--batch-size`;
  - `--seed`;
  - `--sequence-length`.

Verificacion:

```powershell
uv run pytest tests\test_neural_training.py
```

Acceptance:

- Un entrenamiento corto sobre dataset temporal genera checkpoint y metricas.
- Early stopping guarda el mejor modelo por `val_loss`.
- El comando falla pronto si faltan telemetrias o no hay muestras suficientes.

### 7. Evaluacion supervisada in-distribution

Objetivo: medir una ejecucion entrenada sobre `train`, `val` y `test`.

Nuevo script:

```powershell
uv run python tools\evaluate_neural_controller.py --dataset data\classic_dataset\v1 --run data\neural_control\mlp_v1
```

Cambios:

- Cargar `config.yaml`, `normalization.json` y checkpoint.
- Evaluar splits `train`, `val` y `test`.
- Reportar:
  - MSE normalizado;
  - MAE empuje;
  - MAE/RMSE momentos;
  - porcentaje de comandos fuera de limites antes de clipping, si hay limites configurados.
- Escribir metricas por split bajo `metrics/`.

Verificacion:

```powershell
uv run pytest tests\test_neural_evaluation.py
```

Acceptance:

- La evaluacion no recalcula normalizacion.
- `test_metrics.json` se escribe de forma reproducible.
- El reporte separa claramente `train`, `val` y `test`.

### 8. Controlador neuronal en bucle cerrado

Objetivo: cargar un checkpoint desde YAML y sustituir el controlador clasico.

Cambios:

- Implementar `NeuralController` en `src/simulador_quad/control/neural.py`.
- Implementar `compute_control(time_s, obs_state, reference)`.
- Implementar `reset()` para limpiar estado recurrente.
- Reutilizar exactamente la misma construccion de features y normalizacion que entrenamiento.
- Desnormalizar salida a unidades fisicas.
- Aplicar clipping si `clip_to_classic_limits: true`.
- Extender `schema.py` para validar `controller.type: neural`.
- Extender `loader.py` para instanciar controlador neuronal.
- Extender `SimulationRunner.run` para llamar `controller.reset()` si existe al inicio de cada simulacion.
- Extender metadata para registrar arquitectura, checkpoint y normalizador.

YAML objetivo:

```yaml
controller:
  type: neural
  architecture: mlp
  checkpoint_path: data/neural_control/mlp_v1/checkpoints/mlp_best.pt
  normalization_path: data/neural_control/mlp_v1/normalization.json
  clip_to_classic_limits: true
```

Verificacion:

```powershell
uv run pytest tests\test_neural_controller.py tests\test_scenarios.py tests\test_runner.py
```

Acceptance:

- `instantiate_scenario` acepta controlador neuronal.
- MLP, GRU y LSTM producen `ControlCommand` finito.
- GRU/LSTM limpian memoria con `reset()`.
- Los escenarios con controlador clasico siguen funcionando igual.

### 9. Script de ejecucion neuronal en escenarios

Objetivo: ejecutar un checkpoint neuronal sobre cualquier escenario existente sin editar manualmente el YAML original.

Nuevo script:

```powershell
uv run python tools\run_neural_scenario.py --scenario scenarios\circle_clean.yaml --checkpoint data\neural_control\mlp_v1\checkpoints\mlp_best.pt --normalization data\neural_control\mlp_v1\normalization.json --architecture mlp --no-visualization
```

Comportamiento:

- Cargar escenario base.
- Reemplazar en memoria `controller` por `type: neural`.
- Mantener trayectoria, vehiculo, perturbaciones, timing y termination del escenario.
- Permitir `--out` para redirigir resultados.
- Ejecutar `run_simulation`.

Verificacion:

```powershell
uv run pytest tests\test_neural_cli.py
```

Acceptance:

- El script no modifica el YAML base.
- Genera `telemetry.json` y `metrics.json`.
- El metadata identifica que el controlador ejecutado fue neuronal.

### 10. Trayectoria y evaluacion OOD

Objetivo: medir generalizacion en una trayectoria no vista por entrenamiento.

Cambios:

- Anadir una trayectoria analitica nueva, preferiblemente `figure_eight` o `lemniscate`.
- Crear escenario OOD oficial, por ejemplo `scenarios/neural_ood_figure_eight.yaml`.
- Asegurar que la trayectoria OOD produce `TrajectoryReference` con posicion, velocidad, aceleracion y yaw finitos.
- Anadir evaluacion OOD al script de evaluacion o un comando especifico que escriba `metrics/ood_metrics.json`.
- Documentar que OOD no pertenece al split clasico.

Verificacion:

```powershell
uv run pytest tests\test_trajectories.py tests\test_neural_evaluation.py
uv run simulador-quad run scenarios\neural_ood_figure_eight.yaml --no-visualization
```

Acceptance:

- La nueva trayectoria no rompe las existentes.
- El escenario OOD se ejecuta con controlador clasico.
- La evaluacion neuronal OOD queda separada de `train`, `val` y `test`.

### 11. Documentacion final

Objetivo: dejar el estado implementado trazable.

Cambios:

- Actualizar `README.md` con comandos neuronales reales.
- Actualizar `docs/simulador/arquitectura.md` con el contrato comun de controladores.
- Actualizar `docs/simulador/dataset_clasico.md` con uso como dataset de imitacion y limitacion de splits.
- Actualizar documentacion de escenarios si se anade una trayectoria OOD.
- Mantener `docs/plans/spec_control_neuronal.md` como fuente de intencion y este plan como guia de ejecucion.

Verificacion:

```powershell
uv run pytest
```

Acceptance:

- La documentacion no afirma que el split clasico mida generalizacion fuerte.
- Los comandos documentados existen y son ejecutables.
- Queda clara la diferencia entre evaluacion supervisada, bucle cerrado y OOD.

## Tests

Crear o ampliar:

- `tests/test_neural_dataset.py`
  - lectura de telemetria;
  - features y targets;
  - normalizacion train-only;
  - ventanas recurrentes sin cruce de episodio.

- `tests/test_neural_models.py`
  - forward de MLP/GRU/LSTM;
  - dimensiones de salida;
  - factory de modelos.

- `tests/test_neural_training.py`
  - entrenamiento corto en dataset temporal;
  - escritura de checkpoint, config, normalizador y metricas.

- `tests/test_neural_evaluation.py`
  - evaluacion sin recalcular normalizacion;
  - metricas por split.

- `tests/test_neural_controller.py`
  - carga de checkpoint;
  - `compute_control`;
  - clipping;
  - `reset()` recurrente.

- `tests/test_neural_cli.py`
  - scripts CLI sobre dataset/escenario temporal minimo.

Comando final:

```powershell
uv run pytest
```

## Implementation Boundaries

- Always: usar `uv`; mantener ENU/FRD; calcular normalizacion solo con `train`; guardar artefactos reproducibles; mantener compatibilidad del controlador clasico.
- Always: separar metricas supervisadas de metricas en bucle cerrado.
- Always: tratar OOD como evaluacion separada, no como parte de `test`.
- Ask first: regenerar el dataset clasico; cambiar frecuencia de telemetria; cambiar salida aprendida; modificar PID o dinamica para ayudar al modelo.
- Never: usar `val`, `test` u OOD para ajustar pesos o normalizacion.
- Never: presentar el test in-distribution como prueba fuerte de generalizacion.
- Never: editar escenarios base desde scripts de ejecucion neuronal.

## Suggested Task Breakdown

1. Anadir PyTorch, estructura `ml/` y tests de import basicos.
2. Implementar loader de telemetria, features y targets.
3. Implementar normalizacion train-only y datasets MLP/recurrentes.
4. Implementar modelos MLP, GRU y LSTM con factory.
5. Implementar entrenamiento y script `train_neural_controller.py`.
6. Implementar evaluacion supervisada y script `evaluate_neural_controller.py`.
7. Implementar `NeuralController`, validacion YAML, loader y reset en runner.
8. Implementar script `run_neural_scenario.py`.
9. Anadir trayectoria/escenario OOD y metricas OOD.
10. Actualizar README y docs.
11. Ejecutar `uv run pytest` y una prueba manual corta por arquitectura.

## Manual Smoke Tests

Despues de tener datos clasicos ejecutados:

```powershell
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture mlp --out data\neural_control\mlp_smoke --epochs 2
uv run python tools\evaluate_neural_controller.py --dataset data\classic_dataset\v1 --run data\neural_control\mlp_smoke
uv run python tools\run_neural_scenario.py --scenario scenarios\hover_clean.yaml --checkpoint data\neural_control\mlp_smoke\checkpoints\mlp_best.pt --normalization data\neural_control\mlp_smoke\normalization.json --architecture mlp --no-visualization
```

El smoke test no valida calidad final del modelo; solo confirma que entrenamiento, evaluacion e inferencia en bucle cerrado estan conectados.
