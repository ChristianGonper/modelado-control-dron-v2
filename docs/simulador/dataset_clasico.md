# Datos del controlador clásico

El conjunto de datos clásico reúne episodios reproducibles ejecutados con controladores clásicos. Sirve para comparar su comportamiento y para preparar los ejemplos que utilizará el aprendizaje por imitación.

Generar este conjunto no entrena ni ejecuta redes. Para la variante de fuerza exterior, el manifiesto define los escenarios y sus divisiones; sobre ellos se prueba un banco adicional de PD. Los valores que aprende la red proceden de la telemetría del experto seleccionado en cada escenario.

## Alcance

La versión `v1` contiene 150 episodios, distribuidos en cuatro familias de trayectorias:

| Familia | Episodios | PD |
| --- | ---: | --- |
| `hold` | 18 | `pid_hold_v1` |
| `circle` | 48 | `pid_circle_v1` |
| `lissajous` | 48 | `pid_lissajous_v1` |
| `waypoint` | 36 | `pid_waypoint_v1` |

Cada familia tiene un PD propio. El diagnóstico y ajuste utilizan dos geometrías de entrenamiento por familia, cada una con los perfiles P0 nominal, P2 de viento este y P5 combinado; después se conservan las ganancias seleccionadas para evaluar las variantes de esa familia.

En el conjunto de datos clásico, el perfil `P0_nominal` reúne estas condiciones (los escenarios «limpios» de `scenarios/` pueden usar otras):

- resistencia aerodinámica lineal nominal activa;
- dinámica de actuadores activa;
- sin viento;
- sin ruido de observación.

Los episodios perturbados permiten estudiar condiciones más exigentes de manera reproducible; no representan trayectorias perfectas. Para preparar los datos de fuerza exterior se vuelve a ejecutar cada escenario con variantes del PD externo y se selecciona una demostración que cumpla los filtros. La evaluación supervisada mide la fidelidad a la fuerza del experto; el seguimiento de la trayectoria se mide después en bucle cerrado con `position_rmse_m`, `position_mae_m` y `position_max_err_m`.

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

Esto asegura que el ajuste PD y las métricas del dataset midan el seguimiento de la trayectoria sin verse penalizados por un error de posición inicial artificial.

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

Las divisiones de entrenamiento, validación y prueba se asignan por familia:

- `hold`: 12 train, 3 val, 3 test.
- `circle`: 34 train, 7 val, 7 test.
- `lissajous`: 34 train, 7 val, 7 test.
- `waypoint`: 25 train, 5 val, 6 test.

Estas divisiones permiten entrenar y evaluar en condiciones conocidas, pero no demuestran por sí solas generalización a geometrías nuevas. Las mismas familias, geometrías y perturbaciones aparecen entre divisiones, aunque no se repiten pares exactos `geometry_id + perturbation_id`. Para estudiar condiciones fuera de distribución se necesita una evaluación OOD separada; la [documentación neuronal](control_neuronal.md) distingue la evaluación supervisada de la simulación en bucle cerrado.

## Comandos

Para generar la estructura, los PD iniciales y los escenarios YAML:

```powershell
uv run python tools\generate_classic_dataset.py --version v1 --out data\classic_dataset\v1
```

Si el directorio ya existe, el comando falla para evitar sobrescribirlo. Para regenerarlo en una copia de trabajo cuyos datos puedas sustituir:

```powershell
uv run python tools\generate_classic_dataset.py --version v1 --out data\classic_dataset\v1 --overwrite
```

Ajuste reproducible de los PD base: se diagnostican dos geometrías de entrenamiento de cada familia con los perfiles P0, P2 y P5, y se reajustan solo las familias que no cumplen los criterios. Los umbrales de RMSE por defecto son 0,25 m para `hold`, 0,35 m para `circle`, 0,45 m para `lissajous` y 0,40 m para `waypoint`. La búsqueda utiliza por defecto la semilla 1042:

```powershell
uv run python tools\tune_classic_pid.py --dataset data\classic_dataset\v1 --out data\classic_dataset\v1\pids --workers 8
# Ejemplo alternativo: forzar el ajuste y cambiar el umbral de hold a 0,20 m (experimento distinto)
uv run python tools\tune_classic_pid.py --dataset data\classic_dataset\v1 --out data\classic_dataset\v1\pids --force --rmse-hold 0.20 --workers 8
```

`--workers` reparte candidatos PD independientes entre procesos CPU; cada candidato conserva sus casos diagnosticos en serie y los resultados se agregan en orden determinista. Los PD resultantes (frozen) se guardan en `pids/pid_<f>_v1.yaml` con `source`, configuracion de busqueda, diagnostico usado y motivo. Regenerar escenarios clasicos (fase 4 de campana o generacion con `--overwrite`) reutiliza los congelados en lugar de defaults. El banco `outer_force` parte de esos PD base y solo varía las ganancias externas. Los valores por defecto vigentes están en la ayuda de `tools/tune_classic_pid.py`; `docs/plans/archived/` es solo historico.

El runner ejecuta el controlador embebido en cada YAML, no carga ganancias dinamicamente desde `pids/`. Antes de ejecutar comprueba que ambos coincidan y falla con una instruccion de regeneracion si los escenarios quedaron desactualizados tras un tuneo.

Ejecutar episodios:

```powershell
uv run python tools\run_classic_dataset.py --dataset data\classic_dataset\v1 --no-visualization --workers 4
```

Opciones útiles:

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

Construccion del dataset de imitacion de fuerza externa:

```powershell
uv run python tools\generate_outer_force_pid_bank.py --dataset data\classic_dataset\v1 --out data\outer_force_pid_bank\v1 --workers 8
uv run python tools\generate_outer_force_dataset.py --source-dataset data\classic_dataset\v1 --pid-bank data\outer_force_pid_bank\v1 --out data\outer_force_dataset\v1
uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 --architecture mlp --feature-version outer_force_min_v1 --out data\neural_control\outer_force_mlp_min_v1 --device auto
uv run python tools\evaluate_neural_controller.py --dataset data\outer_force_dataset\v1 --run data\neural_control\outer_force_mlp_min_v1 --device auto
```

El banco conserva por escenario el PD interno, limites, vehiculo, semilla y perturbaciones originales, y varia solo `Kp_pos` y `Kd_pos`. El generador `outer_force` excluye candidatos inseguros y conserva el split del escenario fuente. La normalizacion neuronal se calcula solo con muestras `train`. Para evaluar OOD supervisado, usar un directorio con `manifest.csv` donde todas las filas tengan `split=ood` y telemetria compatible de fuerza bajo cada `result_dir` (p. ej. `data/neural_ood/outer_force_v1` tras `generate_outer_force_dataset` sobre escenarios OOD). `data/neural_ood/battery_v1` (`generate_ood_battery.py`) es un artefacto local ignorado por git y solo contiene escenarios para bucle cerrado hasta generar esa telemetria. El evaluador filtra `split=ood` y **no** remapea a `train`. No mezclar filas OOD en el manifest in-distribution.

Bucle cerrado OOD por lotes:

```powershell
uv run python tools\generate_ood_battery.py --out data\neural_ood\battery_v1 --overwrite
uv run python tools\run_neural_outer_force_dataset.py --dataset data\neural_ood\battery_v1 --split ood --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --no-visualization
```

Tabla comparativa cerrada (varios controladores):

```powershell
uv run python tools\summarize_comparison.py --dataset-classic data/classic_dataset/v1 --dataset-neural data/outer_force_dataset/v1 --dataset-ood data/neural_ood/battery_v1 --out-dir results
```

El consolidador `summarize_comparison.py` lee los reportes de simulación clásica y neuronal y produce:
`results/comparison_all_runs.csv` (comparable: `test`/`ood`),
`results/comparison_all_runs_full.csv` (todos los splits) y
`results/comparison_summary.csv`, además de tablas LaTeX para la memoria.

Los informes de transferencia se pueden refrescar sin re-simular con:
`uv run python tools/run_classic_transfer_dataset.py --dataset data/classic_dataset/v1 --refresh-report-only`

Para comparar el controlador clásico y el neuronal, no basta con las métricas supervisadas de fuerza. Estas comparan la fuerza de la red con `desired_force_W_N` del experto PD seleccionado. La comparación experimental principal se realiza con ejecuciones en bucle cerrado y métricas comunes de simulación (incluyendo las matrices cruzadas completas en test e OOD y el baseline representativo), usando `position_rmse_m` como métrica principal y reportando también error máximo, terminación, saturación y clipping de fuerza.

## Criterios de validez

Un episodio se considera valido por los filtros duros del dataset si:

- `termination_reason` coherente con el tipo de trayectoria: `Time limit reached` en trayectorias infinitas; `Trajectory completed` en `waypoint`/`line`; `Composite trajectory completed` en `composite`;
- las metricas usadas por filtros y score son finitas;
- `saturation_percentage <= 2.0`;
- `degradation_percentage <= 2.0`;
- `position_max_err_m` no supera el umbral de su familia:
  - `hold`: `0.40 m`;
  - `circle`: `0.75 m`;
  - `lissajous`: `0.90 m`;
  - `waypoint`: `0.80 m`.

Para la familia `waypoint`, el dataset mide la capacidad de alcanzar secuencialmente una lista de puntos, frenar y asentarse en cada uno antes de avanzar al siguiente. La causa de terminación normal es `"Trajectory completed"`. Los escenarios generados ya no emiten el campo legacy `times`; el avance depende de tolerancia de posición, tolerancia de velocidad y dwell de la trayectoria `waypoint_stop`. Los YAML antiguos con `times` siguen siendo aceptados por compatibilidad, pero ese campo no gobierna el avance entre waypoints.

El score de ajuste PD combina error de posicion, actitud RMS, esfuerzo de control normalizado, saturacion y degradacion. El empuje se normaliza por el peso `m*g` y los momentos por `0.1 Nm`, para no mezclar unidades directamente.

## Pruebas automaticas

La cobertura especifica de este flujo esta en:

- `tests/test_classic_controller_config.py`
- `tests/test_classic_dataset_generation.py`
- `tests/test_classic_dataset_scripts.py`
- `tests/test_classic_pid_selection.py`
- `tests/test_outer_force_generation_integration.py`

Estas pruebas verifican ganancias explicitas del controlador, generacion determinista, PD versionados, manifiesto, scripts CLI, filtros de finitud y, para outer-force, preservacion del lazo interno y seleccion coherente del experto por escenario.
