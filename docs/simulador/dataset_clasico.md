# Dataset clasico

Este documento describe el estado implementado de la generacion de datos clasicos. El objetivo es producir episodios reproducibles con el controlador clasico y usarlos como dataset experto para imitacion neuronal.

La generacion del dataset sigue siendo clasica: no entrena redes ni ejecuta control neuronal. La capa neuronal consume sus `manifest.csv` y `telemetry.json` mediante los scripts descritos en `docs/simulador/control_neuronal.md`.

## Alcance

La version inicial del dataset es `v1` y contiene 150 episodios:

| Familia | Episodios | PID |
| --- | ---: | --- |
| `hold` | 18 | `pid_hold_v1` |
| `circle` | 48 | `pid_circle_v1` |
| `lissajous` | 48 | `pid_lissajous_v1` |
| `waypoint` | 36 | `pid_waypoint_v1` |

Cada familia tiene un PID propio. El PID se ajusta solo en el perfil nominal de esa familia y despues se congela para variantes geometricas y perturbadas.

En este repo, nominal significa:

- drag lineal nominal activo;
- dinamica de actuadores activa;
- sin viento;
- sin ruido de observacion.

Por tanto, los episodios perturbados del dataset son demostraciones del PID congelado bajo condiciones mas exigentes, no trayectorias expertas perfectas. Cuando se usan para aprendizaje por imitacion, la red aprende a reproducir los comandos del PID observados en esas condiciones. La metrica supervisada de la red mide esa fidelidad de imitacion; la metrica que responde al objetivo de seguimiento de trayectoria debe obtenerse despues, ejecutando el controlador neuronal en bucle cerrado y analizando `position_rmse_m`, `position_mae_m` y `position_max_err_m`.

## Perfiles de entorno

| Perfil | Papel |
| --- | --- |
| `P0_nominal` | Drag nominal y actuadores nominales, sin viento ni ruido. |
| `P1_drag_high` | Drag aumentado, sin viento ni ruido. |
| `P2_wind_east` | Viento constante Este con drag nominal. |
| `P3_wind_ne` | Viento constante Este/Norte con drag nominal. |
| `P4_noise_low` | Ruido bajo en posicion y velocidad. |
| `P5_combined` | Viento, ruido, drag alto y actuadores mas lentos. |

El mundo sigue siendo ENU y el cuerpo FRD. El viento se expresa como vector ENU.

## Inicialización consistente

A partir de la versión `v1`, todos los escenarios se inicializan de forma coherente con la trayectoria en `t = 0`. El estado inicial del dron se deriva de la referencia:

- `initial_state.position_W_m = trajectory.get_reference(0.0).position_W_m`
- `initial_state.yaw_rad = trajectory.get_reference(0.0).yaw_rad`
- `initial_state.velocity_W_m_s = [0.0, 0.0, 0.0]`
- El dron comienza nivelado (`orientation_WB = null` en el YAML).

Esto asegura que el ajuste PID y las métricas del dataset midan el seguimiento de la trayectoria sin verse penalizados por un error de posición inicial artificial.

## Artefactos

La estructura generada esperada es:

```text
data/classic_dataset/v1/
  README.md
  manifest.csv
  pids/
  scenarios/
  results/
  run_report.csv
  summary.csv
```

`manifest.csv` contiene:

- `scenario_id`
- `family`
- `geometry_id`
- `perturbation_id`
- `pid_id`
- `seed`
- `split`
- `scenario_path`
- `result_dir`

Los splits se asignan de forma estratificada por familia:

- `hold`: 12 train, 3 val, 3 test.
- `circle`: 34 train, 7 val, 7 test.
- `lissajous`: 34 train, 7 val, 7 test.
- `waypoint`: 25 train, 5 val, 6 test.

Estos splits son adecuados para entrenamiento supervisado y evaluacion in-distribution, pero no constituyen por si solos una prueba fuerte de generalizacion geometrica. Las mismas familias, geometrias y perturbaciones aparecen repartidas entre splits, aunque no se repiten pares exactos `geometry_id + perturbation_id`. Para estudiar generalizacion debe generarse o aportar un dataset OOD separado y evaluarlo con `tools\evaluate_neural_controller.py --ood-dataset`.

## Comandos

Generar estructura, PIDs iniciales y escenarios YAML:

```powershell
uv run python tools\generate_classic_dataset.py --version v1 --out data\classic_dataset\v1
```

Si el directorio existe, el comando falla para no sobrescribir datasets versionados. Para regenerar en desarrollo:

```powershell
uv run python tools\generate_classic_dataset.py --version v1 --out data\classic_dataset\v1 --overwrite
```

Ajustar PIDs por familia:

```powershell
uv run python tools\tune_classic_pid.py --family hold --out data\classic_dataset\v1\pids --version v1
uv run python tools\tune_classic_pid.py --family circle --out data\classic_dataset\v1\pids --version v1
uv run python tools\tune_classic_pid.py --family lissajous --out data\classic_dataset\v1\pids --version v1
uv run python tools\tune_classic_pid.py --family waypoint --out data\classic_dataset\v1\pids --version v1
```

Ejecutar episodios:

```powershell
uv run python tools\run_classic_dataset.py --dataset data\classic_dataset\v1 --no-visualization --workers 4
```

Opciones utiles:

- `--family hold`: ejecuta solo una familia.
- `--scenario-id hold_g01_P0_nominal_s1042`: ejecuta un escenario concreto.
- `--limit 10`: limita el numero de episodios.
- `--rerun`: vuelve a ejecutar episodios con `metrics.json` ya existente.
- `--fail-fast`: detiene al primer error.
- `--workers 4`: reparte escenarios independientes en varios procesos.

Resumir resultados:

```powershell
uv run python tools\summarize_classic_dataset.py --dataset data\classic_dataset\v1
```

El resumen clasifica cada episodio como `VALID`, `INVALID`, `MISSING` o `ERROR` y escribe `summary.csv`.

Uso como dataset de imitacion neuronal:

```powershell
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture mlp --out data\neural_control\mlp_v1
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture gru --out data\neural_control\gru_v1
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture lstm --out data\neural_control\lstm_v1
uv run python tools\evaluate_neural_controller.py --dataset data\classic_dataset\v1 --run data\neural_control\gru_v1
```

La normalizacion neuronal se calcula solo con muestras `train`. Para evaluar OOD, el directorio pasado a `--ood-dataset` debe contener `manifest.csv` y telemetria ya generada; el evaluador no simula esos episodios.

Para comparar el controlador clasico y el neuronal, no basta con `mse_normalized` de la evaluacion supervisada. Esa metrica compara comandos de red contra comandos PID. La comparacion experimental principal debe hacerse con ejecuciones en bucle cerrado y metricas comunes de simulacion, usando `position_rmse_m` como metrica principal de error de trayectoria y reportando tambien error maximo, terminacion y saturacion.

## Criterios de validez

Un episodio se considera valido por los filtros duros del dataset si:

- `termination_reason == "Time limit reached"` (o `"Trajectory completed"` para familias de trayectorias finitas como `waypoint`);
- las metricas usadas por filtros y score son finitas;
- `saturation_percentage <= 2.0`;
- `degradation_percentage <= 2.0`;
- `position_max_err_m` no supera el umbral de su familia:
  - `hold`: `0.40 m`;
  - `circle`: `0.75 m`;
  - `lissajous`: `0.90 m`;
  - `waypoint`: `0.80 m`.

Para la familia `waypoint`, el dataset mide la capacidad de alcanzar secuencialmente una lista de puntos, frenar y asentarse en cada uno antes de avanzar al siguiente. La causa de terminación normal es `"Trajectory completed"`. Los escenarios generados ya no emiten el campo legacy `times`; el avance depende de tolerancia de posición, tolerancia de velocidad y dwell de la trayectoria `waypoint_stop`. Los YAML antiguos con `times` siguen siendo aceptados por compatibilidad, pero ese campo no gobierna el avance entre waypoints.

El score de ajuste PID combina error de posicion, actitud RMS, esfuerzo de control normalizado, saturacion y degradacion. El empuje se normaliza por el peso `m*g` y los momentos por `0.1 Nm`, para no mezclar unidades directamente.

## Pruebas automaticas

La cobertura especifica de este flujo esta en:

- `tests/test_classic_controller_config.py`
- `tests/test_classic_dataset_generation.py`
- `tests/test_classic_dataset_scripts.py`
- `tests/test_classic_pid_selection.py`

Estas pruebas verifican ganancias explicitas del controlador, generacion determinista, PIDs versionados, manifiesto, scripts CLI, filtros de finitud y criterio de seleccion.
