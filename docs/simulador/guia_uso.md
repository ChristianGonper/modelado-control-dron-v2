# Guia de uso del simulador

## Preparacion

El proyecto usa `uv` para gestionar entorno, dependencias y ejecucion. Desde la raiz del repositorio:

```powershell
uv sync
uv run pytest
```

El comando de pruebas valida los elementos criticos del simulador: actitud, dinamica, actuadores, mezclador, perturbaciones, runner, trayectorias, metricas y visualizacion.

## Ejecutar un escenario

La interfaz principal es:

```powershell
uv run simulador-quad run <ruta_escenario.yaml>
```

Ejemplos:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml
uv run simulador-quad run scenarios\circle_drag.yaml
uv run simulador-quad run scenarios\circle_noisy_wind.yaml
```

Cada escenario define su directorio de salida en `output.dir`. Por defecto, el simulador escribe:

- `telemetry.json`: historia temporal de estado, observación, referencia, comando y rotores.
- `metrics.json`: resumen numérico de seguimiento, esfuerzo de control, saturación y terminación.
- `visualization_3d.html`: visor interactivo 3D de la trayectoria (basado en Plotly).
- `figures/`: subdirectorio con figuras estándar (`trajectory_xy.png`, `position_time.png`, etc.) en PNG y, con perfil `report`, también en PDF a 300 dpi.

Si se desea omitir la generación de gráficos (por ejemplo, para ejecuciones masivas), se puede usar la bandera:

```powershell
uv run simulador-quad run <ruta_escenario.yaml> --no-visualization
```

Un episodio que termina por una condición física, por ejemplo saturación persistente o altura inválida, no implica por sí mismo un error del programa. La causa queda registrada como resultado del experimento.

En trayectorias finitas `line` / `waypoint`, `"Trajectory completed"` es una terminación normal: indica que la misión de puntos ha completado el último waypoint. Estas trayectorias usan comportamiento `waypoint_stop`: la referencia avanza punto a punto, frena en cada waypoint y solo pasa al siguiente cuando el vehículo cumple tolerancia de posición, tolerancia de velocidad y tiempo de permanencia (`dwell_time_s`).

Si el YAML contiene parametros fisicos invalidos, el simulador falla antes de ejecutar. El mensaje indica la ruta del campo, por ejemplo `Invalid vehicle.mass_kg: expected positive kg value, got -1.0`.

El comando `plot` regenera figuras desde un `telemetry.json` existente:

```powershell
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures_report --profile report --formats png pdf
```

- `--metrics`: opcional; permite anotar información como el RMSE en perfiles de diagnóstico.
- `--profile`: `diagnostic` (por defecto) o `report` (tipografía y tamaño para memoria).
- `--formats`: lista de formatos (`png`, `pdf`). Si se omite, `report` exporta PNG y PDF; `diagnostic` solo PNG.

Para figuras agregadas de campaña (C1–C7) a partir de `comparison_all_runs.csv`:

```powershell
uv run python tools\summarize_comparison.py --out-dir results
uv run simulador-quad plot-comparison results\comparison_all_runs.csv --out results\figures_comparison --formats png pdf
```

Las figuras comparativas distinguen cada PID congelado por familia (`classic_pid_hold`, `classic_pid_circle`, etc.), incluyen evaluaciones cruzadas con la misma identidad de PID y reportan qué figuras se omitieron cuando faltan splits o columnas. C1–C7 son condicionales: por ejemplo, C3 requiere filas `test` y `ood`, y C5 requiere `collective_thrust_mean_N` y `body_moment_norm_mean_Nm`. C5 se publica como dos paneles con eje Y compartido: RMSE frente a empuje colectivo medio [N] y RMSE frente a norma media de momentos [N·m].

## Generar dataset clasico

El repo incluye un flujo de datos clasicos que sirve como experto para imitacion neuronal. Genera escenarios YAML, PIDs por familia, manifiesto y resultados separados bajo `data/classic_dataset/<version>/`.

Generar el dataset `v1`:

```powershell
uv run python tools\generate_classic_dataset.py --version v1 --out data\classic_dataset\v1
```

Este comando crea tambien PIDs iniciales por familia si no existen:

- `pid_hold_v1.yaml`
- `pid_circle_v1.yaml`
- `pid_lissajous_v1.yaml`
- `pid_waypoint_v1.yaml`

Ejecutar el dataset completo sin visualizacion:

```powershell
uv run python tools\run_classic_dataset.py --dataset data\classic_dataset\v1 --no-visualization --workers 4
```

Para pruebas rapidas:

```powershell
uv run python tools\run_classic_dataset.py --dataset data\classic_dataset\v1 --family hold --limit 1 --no-visualization
```

Resumir resultados:

```powershell
uv run python tools\summarize_classic_dataset.py --dataset data\classic_dataset\v1
```

El flujo completo esta descrito en `docs/simulador/dataset_clasico.md`.

## Entrenar y evaluar control neuronal

Una vez disponible el dataset clasico, el modo `neural` requiere construir demostraciones de fuerza externa con un experto PID seleccionado por escenario:

```powershell
uv run python tools\generate_outer_force_pid_bank.py --dataset data\classic_dataset\v1 --out data\outer_force_pid_bank\v1 --workers 8
uv run python tools\generate_outer_force_dataset.py --source-dataset data\classic_dataset\v1 --pid-bank data\outer_force_pid_bank\v1 --out data\outer_force_dataset\v1
uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 --architecture mlp --feature-version outer_force_min_v1 --out data\neural_control\outer_force_mlp_min_v1 --device auto
```

Evaluacion supervisada in-distribution:

```powershell
uv run python tools\evaluate_neural_controller.py --dataset data\outer_force_dataset\v1 --run data\neural_control\outer_force_mlp_min_v1 --device auto
```

Evaluacion supervisada OOD sobre un dataset ya generado:

```powershell
uv run python tools\evaluate_neural_controller.py --dataset data\outer_force_dataset\v1 --run data\neural_control\outer_force_mlp_min_v1 --ood-dataset data\neural_ood\outer_force_lemniscate_v1 --device auto
```

El directorio pasado a `--ood-dataset` debe tener `manifest.csv` y telemetria compatible con targets de fuerza existente. El evaluador no ejecuta escenarios; solo compara fuerzas predichas con el experto ya exportado.

Ejecucion en bucle cerrado de un checkpoint neuronal:

```powershell
uv run python tools\run_neural_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --device auto --no-visualization
```

Este comando no modifica el YAML original. Sustituye el controlador en memoria por `neural`, cuya red predice `desired_force_W_N[3]` y cuyo PID interno clasico produce empuje y momentos; despues ejecuta el simulador y escribe telemetria/metricas. Si no se indica `--architecture`, se lee desde el `config.yaml` del entrenamiento.

Las metricas supervisadas miden error de fuerza de imitacion. En ejecucion cerrada, `metrics.json` registra ademas `force_norm_clip_percentage` y `force_tilt_clip_percentage`, junto con saturacion y degradacion del sistema fisico; son las metricas relevantes para comprobar si la proteccion esta dominando el vuelo simulado.

Figuras generadas (tanto en `run` automático como en `plot` manual):

- `trajectory_xy`: trayectoria real y referencia en el plano horizontal ENU.
- `trajectory_3d_static`: trayectoria 3D estatica en mundo ENU.
- `position_time`: componentes `X_W`, `Y_W`, `Z_W` frente al tiempo.
- `attitude_time`: roll, pitch y yaw en grados, calculados desde `orientation_WB` con el convenio ENU/FRD del simulador.
- `angular_velocity_time`: componentes `p`, `q`, `r` de `angular_velocity_B_rad_s` en `rad/s`.
- `tracking_error`: norma del error de posicion `||p_ref - p||` sin umbrales inventados.
- `rotor_speeds`: velocidades de rotor aplicadas en `rad/s`.
- `control_effort`: empuje colectivo y momentos de cuerpo.
- `neural_outer_force` y `perturbation_response`: solo si la telemetria incluye fuerza deseada y/o viento.

Con `--profile report --formats png pdf`, cada figura base se exporta en PNG y PDF a 300 dpi.

### Visor 3D Interactivo

El archivo `visualization_3d.html` generado permite inspeccionar la trayectoria en 3D desde cualquier navegador. Incluye:
- Trayectoria real (rojo) y referencia (azul discontinuo).
- Puntos de inicio (diamante verde) y fin (cuadrado negro).
- Ejes coordenados ENU escalados uniformemente.
- Resumen de métricas y razón de terminación en la leyenda.

## Interpretar resultados

Para un analisis rapido:

1. Revisar `metrics.json`.
2. Confirmar `termination_reason`.
3. Ver `position_rmse_m`, `position_mae_m` y `position_max_err_m`.
4. Comprobar `saturation_percentage` y `degradation_percentage`.
5. Inspeccionar las figuras para detectar desfase, saturacion o divergencia.

Campos principales de `metrics.json`:

- `position_rmse_m`: raiz del error cuadratico medio de posicion.
- `position_mae_m`: error absoluto medio de posicion.
- `position_max_err_m`: maximo error de posicion.
- `collective_thrust_mean_N`, `collective_thrust_max_N`, `collective_thrust_min_N` y `collective_thrust_std_N`: estadisticos del empuje colectivo solicitado por el controlador.
- `body_moment_norm_mean_Nm`, `body_moment_norm_max_Nm` y `body_moment_norm_std_Nm`: estadisticos de la norma de momentos de cuerpo solicitados.
- `control_effort_heuristic_mean`, `control_effort_heuristic_max` y `control_effort_heuristic_std`: indice diagnostico heredado `|T| + ||tau||`. Mezcla N y Nm; no debe usarse como metrica fisica principal.
- `control_effort_mean`, `control_effort_max` y `control_effort_std`: alias de compatibilidad del indice heuristico anterior.
- `max_rotor_speed_rad_s` y `max_rotor_speed_rpm`: maxima velocidad aplicada.
- `saturation_duration_s` y `saturation_percentage`: tiempo con algun rotor saturado.
- `degradation_duration_s` y `degradation_percentage`: tiempo con empuje colectivo degradado por el mezclador.
- `termination_reason`: causa final del episodio.
- `metadata`: nombre y ruta del escenario, semilla, controlador, comando, version del paquete, Python/plataforma, estado Git, hashes de escenario/`uv.lock`, configuracion original y configuracion efectiva con defaults.

Para comparar escenarios en la memoria, usar primero metricas con unidades explicitas: error de posicion en m, empuje colectivo en N, momentos en Nm, velocidad de rotor en rad/s y porcentajes de saturacion/degradacion. El indice `control_effort_heuristic_*` solo sirve para detectar tendencias de mando en una figura, no para justificar una conclusion fisica.

En `metadata.controller.parameters` quedan registradas las ganancias efectivas del controlador clasico (`Kp_pos`, `Kd_pos`, `Kp_att`, `Kd_att`) y sus limites principales (`min_thrust`, `max_thrust`, `max_moments_Nm`). Esto permite tratar el controlador clasico como baseline reproducible, no como caja negra.

## Campaña Experimental Automatizada

`tools/run_experimental_campaign.py` orquesta el protocolo completo (flujo reproducible desde clon limpio). Las fases actuales (11 tras insercion de tuneo PID base en Fase E):

| Fase | Operacion principal |
|---|---|
| 1 | Suite de pruebas y escenarios de sanidad |
| 2 | Generacion inicial del dataset clasico (PIDs default_initial) |
| 3 | Diagnostico + tuneo condicional PID base (progresivo, solo train; congela en pids/) |
| 4 | Regeneracion de escenarios clasicos con PIDs congelados + baseline + summarize |
| 5 | Banco y seleccion del experto outer-force (por escenario) |
| 6 | Banco y dataset de ganancias de posicion (neural_position, solo externas) |
| 7 | Entrenamiento secuencial MLP, GRU y LSTM |
| 8 | Evaluacion supervisada |
| 9 | Evaluacion en bucle cerrado sobre el split `test` |
| 10 | Generacion y evaluacion de la bateria OOD |
| 11 | Transferencia cruzada + Consolidacion CSV y tablas LaTeX |

Las fases se pueden ejecutar como `all`, una fase (`--phase 7`), una lista
(`--phase 1,3,5`) o un intervalo (`--phase 1-4`). No resuelve dependencias:
ejecutar una fase aislada exige que ya existan los artefactos de las fases
anteriores (el orquestador falla con mensaje accionable si falta prerequisito).
`--workers` controla procesos CPU; entrenamiento usa `--device`.

Tuneo configurable desde orquestador (pasa a la herramienta):

```powershell
uv run python tools\run_experimental_campaign.py --dry-run

# Con parametros de tune (cambiar umbrales o presupuesto = experimento distinto)
uv run python tools\run_experimental_campaign.py --phase 1-6 --workers 8 \
  --tune-seed 1042 --tune-initial-candidates 32 --tune-refinement-candidates 16 \
  --tune-rmse-hold 0.25 --tune-rmse-circle 0.35
```

`--rerun` fuerza simulaciones y --overwrite en generadores, y --force en tune.

Diferenciacion de PIDs (documentada en artefactos):
- PID inicial: source default_initial (generado en fase 2).
- PID base tuneado/congelado: pid_<familia>_v1.yaml con source tuned_progressive_search o default_initial_accepted, full tuning_info, thresholds, diagnostic set usado.
- Banco neural_position: variantes por familia, solo Kp/Kd_pos (att = base congelado), multipliers + base_pid registrados.
- Oraculo outer-force: por escenario (pos-only), PID interno fijo del base.

Cambiar umbrales, semilla o n_candidatos produce condicion experimental distinta (registrado en pid_tuning/summary.json y YAMLs). Mantener test/OOD fuera del tuneo.

### Transferencia clasica

`tools/run_classic_transfer_dataset.py` ejecuta cada escenario seleccionado con
los PID disponibles de las otras familias; excluye el PID de la familia
original. Lee `manifest.csv` y `pids/pid_<familia>_*.yaml`, guarda los YAML
materializados en `scenarios_transfer/`, las ejecuciones en
`results_transfer/` y el indice `run_report_classic_transfer.csv`.

```powershell
uv run python tools\run_classic_transfer_dataset.py --dataset data\classic_dataset\v1 --workers 8 --no-visualization

# Smoke de un escenario de una familia
uv run python tools\run_classic_transfer_dataset.py --dataset data\classic_dataset\v1 --family hold --limit 1
```

Por defecto no reejecuta combinaciones con `metrics.json`; usar `--rerun` para
forzarlas. El proceso devuelve codigo distinto de cero si falla alguna
simulacion de la invocacion.

### Consolidacion comparativa

`tools/summarize_comparison.py` recoge los `metrics.json` existentes del
baseline clasico, transferencia, oraculo outer-force, redes outer-force y
redes de posicion, tanto `test` como OOD. Produce:

- `comparison_all_runs.csv`: subconjunto comparable (`test` y `ood`) con columnas de terminacion y exito.
- `comparison_all_runs_full.csv`: todas las corridas encontradas, incluidos `train` y `val` con cobertura parcial.
- `comparison_summary.csv`: agregacion por controlador, split y familia sobre el subconjunto comparable.
- tablas LaTeX para `test` y `ood` impresas por salida estandar.

La tasa de exito principal (`mission_success_rate`) exige completar la mision segun el tipo de trayectoria:
`Time limit reached` solo cuenta como exito en trayectorias infinitas; `waypoint`/`line` requieren `Trajectory completed`; `composite` requiere `Composite trajectory completed`.
`safety_success_rate` separa estabilidad fisica (sin crash ni limites violados) de completitud de mision.
Los reportes de transferencia (`run_report_classic_transfer.csv`) distinguen `execution_status`, `mission_success`, `safety_success` y `report_provenance`.
Un refresco (`--refresh-report-only`) marca filas como `RECOVERED` salvo que conserve un estado previo de ejecucion en vivo (`report_provenance=live`).
`safety_success` solo acepta explicitamente `Time limit reached`, `Trajectory completed` y `Composite trajectory completed`.
Los artefactos ausentes se omiten; antes de usar la comparacion en la memoria revisar los conteos de `comparison_summary.csv`.

```powershell
uv run python tools\summarize_comparison.py --dataset-classic data\classic_dataset\v1 --dataset-neural data\outer_force_dataset\v1 --dataset-position data\position_gain_dataset\v1 --dataset-ood data\neural_ood\battery_v1 --out-dir results
```

Los scripts batch `run_classic_dataset.py`,
`run_neural_outer_force_dataset.py` y `run_neural_position_dataset.py` tambien
devuelven codigo distinto de cero si alguna simulacion de la invocacion falla.
Conservan el reporte CSV para poder inspeccionar los fallos.

## Flujo recomendado para un alumno

1. Copiar un escenario existente en `scenarios/`.
2. Cambiar solo una familia de parámetros: trayectoria, perturbación, vehículo o tiempos.
3. Ejecutar el escenario con `uv run simulador-quad run`.
4. Inspeccionar el visor `visualization_3d.html` para una visión global.
5. Revisar las figuras en `figures/` para análisis temporal.
6. Guardar resultados en un subdirectorio distinto dentro de `results/`.
7. Comparar métricas y figuras con el escenario base.

Este flujo mantiene trazabilidad: el `metrics.json` conserva el YAML usado dentro de `metadata.config`, los defaults efectivos dentro de `metadata.config_resolved`, el comando de ejecucion, hashes de escenario/`uv.lock` y datos de entorno. Las figuras se generan directamente desde la telemetria exportada.

Para resultados destinados a la memoria, conservar siempre `metrics.json` junto con `telemetry.json` y las figuras. La metadata permite reconstruir la ejecucion incluso si posteriormente cambian el codigo o los escenarios.
