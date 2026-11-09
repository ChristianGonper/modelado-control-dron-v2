# Control neuronal por imitación

En la comparación principal del TFG, `controller.type: "neural"` usa una red para calcular la fuerza del lazo de posición. La estabilización de actitud sigue a cargo del controlador clásico.

## Qué aprende la red

En el modo `neural`, una red calcula la fuerza que el cuadricóptero necesita para seguir la trayectoria. El resto del control convierte esa fuerza en órdenes para el vehículo:

```text
observación + referencia
        |
        v
MLP / GRU / LSTM -> desired_force_W_N[3]
        |
        v
límites de fuerza e inclinación
        |
        v
conversión clásica fuerza-actitud + PID clásico de actitud
        |
        v
collective_thrust_N + body_moments_Nm
```

La salida contiene los tres componentes de la fuerza deseada, expresados en newtons en el marco del mundo ENU:

- `force_x_W_N`
- `force_y_W_N`
- `force_z_W_N`

El lazo interno no se aprende: utiliza las ganancias y límites del controlador clásico para convertir la fuerza y la orientación de referencia en empuje colectivo y momentos en el marco del cuerpo FRD. Así, la red participa en el control de posición y el controlador clásico mantiene la estabilización de actitud.

## Entradas y salida de entrenamiento

La comparación principal usa `outer_force_min_v1` en MLP, GRU y LSTM. Sus nueve entradas se calculan a partir de la observación disponible para el controlador, no directamente del estado verdadero:

- error de posición ENU `[3]`;
- error de velocidad ENU `[3]`;
- aceleración de referencia ENU `[3]`.

`outer_force_full_v1` tiene 31 entradas e incorpora estado observado, referencia, errores y representación continua del yaw. Esta variante está implementada, pero queda fuera del alcance experimental principal por ahora.

La salida objetivo, `desired_force_W_v1`, se obtiene con el método `compute_desired_force_W(...)` del controlador clásico, usando la observación y las ganancias del experto seleccionado. La normalización de entradas y salidas se ajusta únicamente con el conjunto de entrenamiento (`train`).

## Preparar las demostraciones

El conjunto de datos clásico aporta escenarios, divisiones y condiciones; para entrenar la red se prepara después un conjunto específico de fuerza exterior. El proceso selecciona un experto PD para cada escenario:

1. Para cada fila del `manifest.csv` clásico, se ejecutan variantes del controlador externo con `tools\generate_outer_force_pid_bank.py`.
2. Se mantienen sin cambios el PID interno (`Kp_att`, `Kd_att`), los limites, la trayectoria, las perturbaciones, la semilla y los parametros del vehiculo del YAML fuente.
3. Se excluyen las variantes que no superan `passes_hard_filters`.
4. Se elige un experto por escenario: se busca el menor `position_rmse_m`; entre candidatos a menos del 5 % del mejor error se prefiere el de menor esfuerzo y, en caso de empate, la variante más conservadora.
5. Se copia la telemetría del experto elegido y se escriben sus ganancias `Kp_pos` y `Kd_pos` en el YAML de salida.

Si ningún candidato supera los filtros de seguridad, la generación falla: no se crea una demostración válida para ese escenario.

```powershell
uv run python tools\generate_outer_force_pid_bank.py --dataset data\classic_dataset\v1 --out data\outer_force_pid_bank\v1 --workers 8
uv run python tools\generate_outer_force_dataset.py --source-dataset data\classic_dataset\v1 --pid-bank data\outer_force_pid_bank\v1 --out data\outer_force_dataset\v1
```

## Entrenamiento y evaluación

Los siguientes comandos entrenan y evalúan una MLP. Requieren haber generado antes el conjunto de fuerza exterior:

```powershell
uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 --architecture mlp --feature-version outer_force_min_v1 --out data\neural_control\outer_force_mlp_min_v1 --device auto
uv run python tools\evaluate_neural_controller.py --dataset data\outer_force_dataset\v1 --run data\neural_control\outer_force_mlp_min_v1 --device auto
```

El script también soporta `gru` y `lstm`, que forman parte de la comparación principal con control de fuerza. El entrenamiento produce `config.yaml`, `normalization.json` y checkpoints. La evaluación outer-force escribe métricas de error de fuerza por split bajo `metrics/*_force_metrics.json`.

Estas métricas miden cuánto se parece la fuerza predicha a la del experto. Para evaluar el seguimiento de la trayectoria hay que ejecutar el controlador en bucle cerrado:

```powershell
uv run python tools\run_neural_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --device auto --no-visualization
uv run python tools\run_neural_outer_force_dataset.py --dataset data\outer_force_dataset\v1 --split test --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --device auto --no-visualization --limit 2
```

Para probar el seguimiento fuera de distribución, puedes generar una batería de escenarios y ejecutarla en bucle cerrado. `data/neural_ood/battery_v1` es un directorio local con escenarios YAML; no contiene telemetría de expertos:

```powershell
uv run python tools\generate_ood_battery.py --out data\neural_ood\battery_v1 --overwrite
uv run python tools\run_neural_outer_force_dataset.py --dataset data\neural_ood\battery_v1 --split ood --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --no-visualization
```

### Sensibilidad a los hiperparámetros

El estudio de sensibilidad de `outer_force_min_v1` se ejecuta sobre artefactos
ya generados y no sobrescribe los resultados base. Las variantes usan sufijos en
los directorios de resultado y sus informes de batch se guardan en
`data/neural_ablation/reports/`.

```powershell
uv run python tools\run_neural_sensitivity_study.py --device auto --workers 1
uv run python tools\summarize_neural_sensitivity.py
```

El resumen se guarda en `results/neural_sensitivity/`. El informe técnico
`docs/reviews/archived/annexes/estudio_sensibilidad_neuronal_outer_force_2026-06-25.md` documenta
la campaña ejecutada para `hidden_dim=128`, ventanas `L=10/40` y semillas
adicionales.

### Evaluación supervisada fuera de distribución

La batería `battery_v1` contiene escenarios, pero no las demostraciones de fuerza necesarias para evaluar la imitación. Para una evaluación supervisada OOD se necesita un conjunto con telemetría de expertos compatible y un manifiesto con `split=ood`. El banco de expertos debe corresponder a esos mismos escenarios: el banco generado para el conjunto de entrenamiento no se puede reutilizar automáticamente para escenarios OOD distintos.

Una vez preparado ese conjunto, el evaluador acepta su ruta mediante `--ood-dataset` y selecciona las filas marcadas como `ood`. Sin esos datos no debe interpretarse la batería de escenarios como una evaluación supervisada. La evaluación en bucle cerrado descrita antes sí puede ejecutarse con la batería de escenarios.

Al presentar los resultados en bucle cerrado, incluye el error de posición (`position_rmse_m`, `position_mae_m` y `position_max_err_m`), la causa de terminación, la saturación y la degradación. Las métricas `force_norm_clip_percentage` y `force_tilt_clip_percentage` indican cuándo actúan los límites de fuerza. La telemetría distingue `desired_force_W_N` —salida de la red antes de los límites— de `desired_force_clipped_W_N`, la fuerza enviada al lazo interno; también registra el viento cuando corresponde.

Para preparar una comparación reproducible, genera la batería, ejecuta las simulaciones y construye las tablas con una misma versión del código. `battery_v1` por sí sola es una lista de escenarios, no un resultado experimental.

## Configuración y protecciones

Un escenario `neural` debe indicar el checkpoint, la normalización, la versión de las entradas y el límite de inclinación. Por ejemplo:

```yaml
controller:
  type: "neural"
  architecture: "mlp"
  checkpoint_path: "data/neural_control/outer_force_mlp_min_v1/checkpoints/mlp_best.pt"
  normalization_path: "data/neural_control/outer_force_mlp_min_v1/normalization.json"
  feature_version: "outer_force_min_v1"
  clip_to_classic_limits: true
  max_desired_tilt_rad: 0.52
  Kp_att: [4.0, 4.0, 1.0]
  Kd_att: [1.5, 1.5, 0.5]
  max_body_moments_Nm: [10.0, 10.0, 2.0]
  device: "auto"
```

Con `clip_to_classic_limits: true`, el controlador limita la norma de la fuerza a `mass_kg * gravity_m_s2 * 2.5`, restringe la inclinación solicitada a `max_desired_tilt_rad` y mantiene una componente ascendente mínima antes del PID interno. El script `run_neural_scenario.py` usa `0.52 rad` si ese límite no figura en la configuración del entrenamiento.

Los checkpoints incompatibles con la arquitectura y las entradas de fuerza exterior se rechazan al cargarse. Por tanto, los modelos anteriores no deben reutilizarse como outer-force sin regenerar dataset y entrenar de nuevo.

## Arquitecturas comparadas

La comparación principal incluye MLP, GRU y LSTM con las entradas de fuerza exterior seleccionadas para el TFG. La MLP sirve como referencia de menor complejidad; GRU y LSTM incorporan una ventana temporal y memoria recurrente. Para compararlas, se utilizan métricas supervisadas y simulaciones en bucle cerrado bajo las mismas condiciones `test` y OOD. La variante de 31 entradas `outer_force_full_v1` no forma parte de esa comparación.

## Alcance

La [memoria del TFG](../../site/assets/reports/TFG_Memoria_es.pdf) recoge los resultados académicos. Para probar NeuroFlight, el repositorio también incluye un paquete de modelos regenerados: consulta su [guía](../neuroflight.md). Una ejecución nueva debe identificarse por separado y compararse bajo condiciones equivalentes.
