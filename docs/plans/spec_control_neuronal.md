# Spec: Control Neuronal por Imitacion MLP/GRU/LSTM

## Objective

Implementar una capa de control neuronal entrenada por imitacion a partir del dataset clasico ya generado. Se entrenaran tres arquitecturas comparables: `MLP`, `GRU` y `LSTM`.

El controlador neuronal debe poder sustituir al controlador clasico en bucle cerrado y ejecutarse con cualquier trayectoria soportada por el simulador. No cambia la dinamica, el mixer, los actuadores ni las convenciones ENU/FRD.

La red imita la salida del controlador clasico:

- `collective_thrust_N`
- `body_moments_Nm[3]`

## Dataset And Splits

La division actual `train` / `val` / `test` del dataset clasico se mantiene como evaluacion interpolativa balanceada. Es valida para entrenar y comparar dentro del dominio clasico porque no repite pares exactos `geometry_id + perturbation_id` entre splits y conserva proporcion por familia.

No debe presentarse como una prueba fuerte de generalizacion: las mismas familias, geometrias y perturbaciones aparecen repartidas entre `train`, `val` y `test`.

Uso de splits:

- `train`: ajuste de pesos y calculo de normalizacion.
- `val`: early stopping, seleccion de checkpoint e hiperparametros.
- `test`: metrica final in-distribution.
- `ood`: evaluacion separada con trayectorias no vistas.

La evaluacion OOD queda fuera del manifiesto clasico base. Debe usar escenarios nuevos que no formen parte de `train`, `val` ni `test`. La primera trayectoria OOD recomendada es una trayectoria analitica suave no presente durante entrenamiento, por ejemplo `figure_eight` o `lemniscate`, distinta de `hold`, `circle`, `lissajous` y `waypoint`.

## Training Specification

Usar PyTorch como stack de ML.

El flujo de entrenamiento debe leer `manifest.csv`, cargar los `telemetry.json` de episodios validos y construir muestras supervisadas desde cada `TelemetrySample` exportado.

Entradas por muestra:

- observacion usada por el controlador: posicion ENU, velocidad ENU, orientacion `orientation_WB`, velocidad angular FRD;
- referencia: posicion ENU, velocidad ENU, aceleracion ENU, yaw;
- errores derivados: error de posicion y error de velocidad;
- yaw codificado como `sin(yaw)` y `cos(yaw)`.

Salida objetivo:

- `control.collective_thrust_N`;
- `control.body_moments_Nm`.

Normalizacion:

- calcular estadisticos solo con muestras de `train`;
- guardar `normalization.json`;
- aplicar los mismos estadisticos a `val`, `test`, OOD e inferencia;
- no usar datos de `val`, `test` ni OOD para calcular medias o desviaciones.

Arquitecturas:

- `MLP`: entrada instantanea por muestra, sin memoria temporal.
- `GRU`: ventana secuencial fija de muestras pasadas, con estado recurrente en inferencia.
- `LSTM`: ventana secuencial fija de muestras pasadas, con estado oculto y celda en inferencia.

Defaults iniciales:

- longitud de ventana para GRU/LSTM: `20` muestras;
- si la telemetria esta a `0.1 s`, la ventana representa `2.0 s`;
- loss principal: MSE normalizado sobre las cuatro salidas;
- metrica de seleccion: `val_loss`;
- early stopping activado por `val_loss`.

Metricas supervisadas a reportar:

- MSE normalizado;
- MAE de `collective_thrust_N`;
- MAE y RMSE de `body_moments_Nm`;
- porcentaje de comandos fuera de limites fisicos antes de clipping.

Artefactos esperados por ejecucion:

```text
data/neural_control/<run_id>/
  config.yaml
  normalization.json
  checkpoints/
    mlp_best.pt
    gru_best.pt
    lstm_best.pt
  metrics/
    train_metrics.json
    val_metrics.json
    test_metrics.json
    ood_metrics.json
```

## Simulator Integration

Anadir soporte para controlador neuronal en YAML:

```yaml
controller:
  type: neural
  architecture: mlp
  checkpoint_path: data/neural_control/<run_id>/checkpoints/mlp_best.pt
  normalization_path: data/neural_control/<run_id>/normalization.json
  clip_to_classic_limits: true
```

Valores validos de `architecture`:

- `mlp`
- `gru`
- `lstm`

El controlador neuronal debe implementar el contrato existente:

```python
compute_control(time_s, obs_state, reference) -> ControlCommand
```

Comportamiento en inferencia:

- MLP usa solo la muestra actual.
- GRU y LSTM mantienen estado interno entre llamadas.
- El runner debe llamar a `reset()` si el controlador lo implementa, para limpiar memoria recurrente al inicio de cada simulacion.
- La salida se desnormaliza antes de construir `ControlCommand`.
- Si `clip_to_classic_limits` es `true`, la salida se limita a rangos fisicos compatibles con el controlador clasico:
  - empuje entre `min_thrust` y `max_thrust`;
  - momentos entre `-max_body_moments_Nm` y `+max_body_moments_Nm`.
- Si el checkpoint, normalizador o arquitectura no coinciden, la carga debe fallar pronto con un error claro.

El controlador neuronal debe funcionar con cualquier trayectoria que produzca `TrajectoryReference`, incluidas:

- `hold`;
- `circle`;
- `lissajous`;
- `waypoint`;
- la nueva trayectoria OOD.

## Commands

Entrenamiento:

```powershell
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture mlp --out data\neural_control\mlp_v1
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture gru --out data\neural_control\gru_v1
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture lstm --out data\neural_control\lstm_v1
```

Evaluacion supervisada:

```powershell
uv run python tools\evaluate_neural_controller.py --dataset data\classic_dataset\v1 --run data\neural_control\mlp_v1
```

Evaluacion en bucle cerrado:

```powershell
uv run python tools\run_neural_scenario.py --scenario scenarios\circle_clean.yaml --checkpoint data\neural_control\mlp_v1\checkpoints\mlp_best.pt --no-visualization
```

Regresion:

```powershell
uv run pytest
```

## Project Structure

Ubicaciones esperadas para la implementacion posterior:

```text
src/simulador_quad/control/
  neural.py              -> controlador neuronal compatible con Controller

src/simulador_quad/ml/
  dataset.py             -> carga de manifest, telemetria, features y ventanas
  models.py              -> MLP, GRU, LSTM
  normalization.py       -> estadisticos train-only y transformaciones
  train.py               -> bucle de entrenamiento
  evaluate.py            -> evaluacion supervisada

tools/
  train_neural_controller.py
  evaluate_neural_controller.py
  run_neural_scenario.py

tests/
  test_neural_dataset.py
  test_neural_models.py
  test_neural_controller.py
```

## Testing Strategy

Tests unitarios:

- construccion de features desde una muestra de telemetria;
- normalizacion calculada solo con `train`;
- dataset MLP devuelve muestras independientes;
- dataset GRU/LSTM devuelve ventanas con longitud fija;
- MLP, GRU y LSTM producen tensores de salida `[batch, 4]`;
- desnormalizacion y clipping de comandos;
- `reset()` limpia estado recurrente.

Tests de integracion:

- carga de checkpoint neuronal desde YAML;
- `instantiate_scenario` acepta `controller.type: neural`;
- runner ejecuta un escenario corto con controlador neuronal;
- `hold`, `circle`, `lissajous` y `waypoint` siguen funcionando con controlador clasico;
- escenario OOD se puede ejecutar y queda marcado como OOD en metricas.

Acceptance criteria:

- las tres arquitecturas entrenan sin errores sobre el dataset clasico generado;
- cada entrenamiento escribe checkpoint, config, normalizador y metricas;
- la evaluacion supervisada reporta `train`, `val` y `test` por separado;
- la evaluacion OOD usa escenarios no vistos y no se mezcla con los splits clasicos;
- al menos un escenario por familia puede ejecutarse en bucle cerrado con cada arquitectura;
- la documentacion distingue claramente imitacion supervisada, test in-distribution y test OOD.

## Documentation

Actualizar durante la implementacion:

- `README.md`: estado de la capa neuronal, comandos principales y limites.
- `docs/simulador/arquitectura.md`: nuevo controlador neuronal y contrato comun.
- `docs/simulador/dataset_clasico.md`: uso del dataset clasico como fuente de imitacion y limitacion del split actual.
- documentacion de escenarios si se anade la trayectoria OOD.

## Boundaries

- Always: mantener ENU para mundo y FRD para cuerpo.
- Always: calcular normalizacion solo con `train`.
- Always: guardar configuracion, normalizador, checkpoint y metricas por ejecucion.
- Always: conservar compatibilidad del controlador clasico.
- Ask first: cambiar frecuencia de telemetria, regenerar el dataset clasico o modificar las familias existentes.
- Ask first: cambiar la salida aprendida a velocidades de rotor o aceleraciones deseadas.
- Never: entrenar usando `val`, `test` u OOD para ajustar pesos o normalizacion.
- Never: presentar el test clasico actual como prueba fuerte de generalizacion geometrica.
- Never: cambiar la dinamica fisica, mixer o actuadores para compensar errores del controlador neuronal.

## Success Criteria

La fase queda completa cuando:

1. Existen scripts reproducibles para entrenar MLP, GRU y LSTM.
2. Cada arquitectura puede evaluarse en modo supervisado y en bucle cerrado.
3. El controlador neuronal usa el mismo contrato que el controlador clasico.
4. El dataset conserva splits `train`, `val`, `test` y anade evaluacion OOD separada.
5. La suite `uv run pytest` pasa.
6. La documentacion refleja que el control neuronal esta implementado por imitacion y especifica sus limites.

## Assumptions

- Se usara PyTorch.
- El dataset clasico existente es suficiente para la primera fase.
- Las muestras de entrenamiento salen de la telemetria exportada, no de una simulacion online durante el entrenamiento.
- GRU y LSTM operan con ventanas temporales fijas en entrenamiento y estado recurrente en inferencia.
- La primera version prioriza reproducibilidad y trazabilidad sobre rendimiento maximo.
