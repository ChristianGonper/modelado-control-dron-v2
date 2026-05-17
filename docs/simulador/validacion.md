# Validacion de escenarios y resultados

Este documento define como usar los escenarios actuales como evidencia experimental del simulador. No sustituye a los YAML ni a las metricas exportadas: fija el papel de cada escenario, los criterios iniciales de aceptacion y las evidencias minimas que deben conservarse para la memoria del TFG.

La validacion clasica y la neuronal deben separarse. Los escenarios oficiales clasicos siguen siendo la referencia de sanidad fisica y trazabilidad. El controlador neuronal se evalua en dos niveles: error supervisado sobre telemetria exportada y ejecucion en bucle cerrado dentro del simulador.

## Comandos oficiales

Ejecutar desde la raiz del repositorio:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
uv run simulador-quad run scenarios\circle_drag.yaml --no-visualization
uv run simulador-quad run scenarios\circle_noisy_wind.yaml --no-visualization
uv run simulador-quad run scenarios\lissajous_clean.yaml --no-visualization
uv run simulador-quad run scenarios\waypoint_clean.yaml --no-visualization
```

Para generar figuras despues de una ejecucion:

```powershell
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
```

Para el dataset clasico versionado:

```powershell
uv run python tools\generate_classic_dataset.py --version v1 --out data\classic_dataset\v1
uv run python tools\run_classic_dataset.py --dataset data\classic_dataset\v1 --no-visualization --workers 4
uv run python tools\summarize_classic_dataset.py --dataset data\classic_dataset\v1
```

Para entrenamiento y evaluacion neuronal:

```powershell
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture gru --out data\neural_control\gru_v1
uv run python tools\evaluate_neural_controller.py --dataset data\classic_dataset\v1 --run data\neural_control\gru_v1
uv run python tools\run_neural_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\gru_v1\checkpoints\gru_best.pt --normalization data\neural_control\gru_v1\normalization.json --architecture gru --no-visualization
```

Para evaluacion OOD supervisada:

```powershell
uv run python tools\evaluate_neural_controller.py --dataset data\classic_dataset\v1 --run data\neural_control\gru_v1 --ood-dataset data\neural_ood\lemniscate_v1
```

El directorio OOD debe contener `manifest.csv` y telemetria ya generada. Este comando no ejecuta el escenario OOD; solo evalua un dataset OOD existente.

## Criterios generales

Un escenario se considera valido como evidencia de la version clasica si cumple:

- El YAML usado esta versionado en `scenarios/`.
- La ejecucion termina por la causa esperada.
- `metrics.json` y `telemetry.json` se generan desde ese YAML.
- No aparecen valores no finitos en estado, comandos, rotores o metricas.
- Las saturaciones y degradaciones se reportan, no se ocultan.
- Las figuras se generan desde la telemetria exportada, no desde datos editados manualmente.

Los umbrales numericos de RMSE y error maximo son iniciales. Deben revisarse cuando cambie el modelo fisico, el controlador o la lista de escenarios oficiales.

## Escenarios oficiales

| Escenario | Tipo | Objetivo | Perturbaciones | Semilla | Criterio inicial de exito |
| --- | --- | --- | --- | --- | --- |
| `scenarios/hover_clean.yaml` | Nominal | Verificar despegue corto y mantenimiento de hover con referencia fija. | Sin viento, sin ruido, sin drag. | `42` | `termination_reason == "Time limit reached"`, `saturation_percentage == 0`, `degradation_percentage == 0`, `position_rmse_m <= 0.40`. |
| `scenarios/circle_drag.yaml` | Nominal con disipacion | Verificar seguimiento circular con drag lineal activo. | Drag lineal `[0.1, 0.1, 0.05]`, sin viento ni ruido. | `42` | `termination_reason == "Time limit reached"`, `saturation_percentage == 0`, `degradation_percentage <= 1`, `position_rmse_m <= 0.45`. |
| `scenarios/circle_noisy_wind.yaml` | Robustez | Verificar seguimiento circular con viento constante, ruido de observacion, retardo y lag. | Viento `[2, 1, 0]`, ruido pos/vel, drag, retardo y lag. | `123` | `termination_reason == "Time limit reached"`, `saturation_percentage == 0`, `degradation_percentage <= 5`, `position_rmse_m <= 0.60`. |
| `scenarios/lissajous_clean.yaml` | Nominal dinamico | Verificar seguimiento suave 3D sin perturbaciones externas. | Sin viento, sin ruido, sin drag. | `42` | `termination_reason == "Time limit reached"`, `saturation_percentage == 0`, `degradation_percentage <= 1`, `position_rmse_m <= 0.70`. |
| `scenarios/waypoint_clean.yaml` | Demostración de trayectoria con paradas | Verificar llegada secuencial a puntos con frenado y asentamiento en cada waypoint. | Sin viento, sin ruido, sin drag. | `42` | `termination_reason == "Trajectory completed"`, sin fallo por actitud/no finitos/saturación persistente, `position_rmse_m <= 0.40`. |
| `scenarios/neural_ood_lemniscate.yaml` | OOD / generalizacion | Verificar una trayectoria analitica no incluida en el dataset clasico base. | Viento bajo y ruido bajo. | `1234` | Con controlador clasico debe ejecutarse sin fallo fisico. Con controlador neuronal, usar como evidencia OOD en bucle cerrado y reportar terminacion, RMSE, saturacion y degradacion sin mezclarlo con `test`. |

## Resultados historicos

Los directorios actuales en `results/` son utiles para inspeccion y comparacion durante desarrollo, pero no deben tratarse como evidencia final de memoria sin regenerarlos desde los YAML actuales.

Motivos:

- Los artefactos generados antes de la metadata fuerte no registraban commit, estado del arbol, comando exacto ni hash de `uv.lock`.
- Algunos resultados pueden proceder de versiones anteriores de escenarios o codigo.
- Por ejemplo, la duración registrada en resultados históricos puede no coincidir con el YAML actual (especialmente en trayectorias finitas como `waypoint`).

Para usar un resultado en memoria:

1. Ejecutar el YAML oficial desde el estado de codigo que se quiere defender.
2. Guardar `metrics.json`, `telemetry.json`, figuras y visor 3D si aplica.
3. Comprobar en `metrics.metadata` el comando, commit, estado limpio/sucio, version de Python, hash de escenario y hash de `uv.lock`.
4. Referenciar el escenario y los criterios de este documento.

## Evidencias minimas por escenario

Cada escenario usado en la memoria debe conservar:

- YAML versionado en `scenarios/`.
- `metrics.json`, con al menos:
  - `position_rmse_m`, `position_mae_m` y `position_max_err_m`;
  - `collective_thrust_mean_N` y `collective_thrust_max_N`;
  - `body_moment_norm_mean_Nm` y `body_moment_norm_max_Nm`;
  - `saturation_percentage` y `degradation_percentage`;
  - `termination_reason`;
  - `metadata`.
- `telemetry.json`.
- Figuras estandar:
  - `trajectory_xy.png`
  - `position_time.png`
  - `attitude_time.png`
  - `angular_velocity_time.png`
  - `tracking_error.png`
  - `rotor_speeds.png`
  - `control_effort.png`
- Conclusion tecnica breve:
  - causa de terminacion;
  - error de seguimiento;
  - saturacion/degradacion;
  - perturbaciones activas;
  - limitaciones del resultado.

## Escenarios de fallo y estres

Los escenarios de estres o fallo esperado no deben mezclarse con escenarios nominales. Si se anaden, deben declararse con:

- objetivo del fallo o estres;
- condicion esperada de terminacion;
- motivo fisico o de validacion;
- criterio para considerar correcto el fallo.

Los resultados historicos `results/stress_*` o `results/test_line` no son escenarios oficiales si no existe YAML reproducible correspondiente en `scenarios/`.

## Dataset clasico v1

El dataset clasico generado bajo `data/classic_dataset/v1/` es una evidencia distinta de los escenarios oficiales manuales. Sus YAML se generan a partir de `src/simulador_quad/datasets/classic.py` y se indexan en `manifest.csv`.

La version `v1` contiene 150 episodios:

- `hold`: 18.
- `circle`: 48.
- `lissajous`: 48.
- `waypoint`: 36.

Cada episodio queda identificado por familia, geometria, perturbacion, PID, semilla y split. Los resultados se consideran trazables si existen:

- fila correspondiente en `manifest.csv`;
- YAML generado en `scenarios/<family>/`;
- `metrics.json` y `telemetry.json` en el `result_dir`;
- `summary.csv` generado por `tools/summarize_classic_dataset.py`;
- PID YAML correspondiente en `pids/`.

Los escenarios de dataset `v1` empiezan en la referencia de la trayectoria en `t = 0`. Por tanto, sus metricas de error se interpretan como seguimiento desde condicion inicial consistente. No deben usarse para justificar capacidad de captura desde una posicion inicial lejana.

Los filtros duros de validez del dataset estan implementados en `passes_hard_filters`: terminacion esperada por familia, metricas finitas, saturacion y degradacion no superiores al 2%, y error maximo por debajo del umbral de familia. Para `waypoint`, la terminacion esperada puede ser `"Trajectory completed"`.

## Control neuronal

La validacion neuronal tiene tres evidencias distintas:

1. Entrenamiento supervisado: `tools\train_neural_controller.py` genera `config.yaml`, `normalization.json`, checkpoint y metricas de entrenamiento/validacion.
2. Evaluacion supervisada: `tools\evaluate_neural_controller.py` escribe `train_metrics.json`, `val_metrics.json` y `test_metrics.json`; si se proporciona `--ood-dataset`, escribe tambien `ood_metrics.json`.
3. Bucle cerrado: `tools\run_neural_scenario.py` ejecuta un escenario YAML existente sustituyendo el controlador por un checkpoint neuronal en memoria.

El split `test` del dataset clasico mide desempeno in-distribution. No debe presentarse como prueba fuerte de generalizacion, porque las familias, geometrias y perturbaciones del dataset estan repartidas entre `train`, `val` y `test`. La generalizacion debe apoyarse en OOD separado, por ejemplo la lemniscata.

La metrica supervisada `saturation_percentage` del evaluador neuronal mide comandos predichos fuera de limites antes del clipping, no saturacion fisica aplicada por actuadores. Por defecto usa masa `1.0 kg`, gravedad `9.81 m/s^2`, empuje maximo `m*g*2.5` y momentos `[10, 10, 2] Nm`. Si el dataset OOD usa otra masa o limites, esa metrica debe interpretarse con cautela hasta parametrizar esos limites desde CLI o metadata.

En bucle cerrado, las saturaciones y degradaciones relevantes son las de `metrics.json` del simulador, que proceden del mixer y actuadores reales de la ejecucion.

## Relacion con pruebas automaticas

La suite actual ya incluye validaciones automaticas del modelo clasico:

- `tests/test_attitude.py`: convenciones ENU/FRD y signo del empuje.
- `tests/test_dynamics.py`: casos analiticos de RK4 y conservacion de norma de cuaternion en una integracion larga.
- `tests/test_perturbations.py`: drag disipativo, tambien con orientacion no trivial.
- `tests/test_runner.py`: multi-rate, ZOH, evolucion de actuadores a `physics_dt_s` y terminaciones por altura, actitud, posicion, velocidad, no finitos y saturacion persistente.
- `tests/test_scenarios.py`: escenarios oficiales validos y rechazo temprano de configuraciones fisicas invalidas.
- `tests/test_model_regressions.py`: ejecucion corta de escenario en directorio temporal, sin depender de `results/`, comprobando `termination_reason`, metricas, esquema minimo de `metrics.json`/`telemetry.json` y valores finitos.
- `tests/test_classic_controller_config.py`: ganancias explicitas del controlador desde YAML y validacion de vectores no negativos.
- `tests/test_classic_dataset_generation.py`: manifiesto `v1`, conteos por familia, determinismo y YAML generados validos.
- `tests/test_classic_dataset_scripts.py`: flujo CLI generacion, ejecucion limitada y resumen en directorio temporal.
- `tests/test_classic_pid_selection.py`: filtros duros, finitud y score de seleccion PID.
- `tests/test_neural_dataset.py`: carga de telemetria, features, normalizacion y ventanas recurrentes.
- `tests/test_neural_models.py`: forward de MLP, GRU y LSTM.
- `tests/test_neural_training.py`: entrenamiento corto por CLI y dimensiones recurrentes.
- `tests/test_neural_evaluation.py`: evaluacion supervisada por CLI y escritura de metricas.
- `tests/test_neural_controller.py`: carga de checkpoint dummy e inferencia en bucle cerrado.

Las regresiones automaticas no sustituyen a las ejecuciones oficiales completas para la memoria. Su papel es detectar roturas rapidas de contrato y evitar que `results/` historico actue como unico oraculo.

## Limites de validez

Estos escenarios validan el simulador dentro del alcance actual:

- cuerpo rigido 6DOF;
- cuaterniones;
- RK4;
- control clasico y control neuronal por imitacion;
- drag lineal simplificado;
- viento constante y ruido de observacion simple;
- actuadores simplificados con saturacion, retardo y lag.

No validan vuelo real, aerodinamica formal, sensores realistas ni estimador onboard. El control neuronal queda validado solo dentro del alcance de imitacion supervisada y simulacion cerrada sobre este modelo 6DOF simplificado.
