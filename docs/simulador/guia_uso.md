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
- `figures/`: subdirectorio con figuras PNG estándar (`trajectory_xy.png`, `position_time.png`, etc.).

Si se desea omitir la generación de gráficos (por ejemplo, para ejecuciones masivas), se puede usar la bandera:

```powershell
uv run simulador-quad run <ruta_escenario.yaml> --no-visualization
```

Un episodio que termina por una condición física, por ejemplo saturación persistente o altura inválida, no implica por sí mismo un error del programa. La causa queda registrada como resultado del experimento.

En trayectorias finitas `line` / `waypoint`, `"Trajectory completed"` es una terminación normal: indica que la misión de puntos ha completado el último waypoint. Estas trayectorias usan comportamiento `waypoint_stop`: la referencia avanza punto a punto, frena en cada waypoint y solo pasa al siguiente cuando el vehículo cumple tolerancia de posición, tolerancia de velocidad y tiempo de permanencia (`dwell_time_s`).

Si el YAML contiene parametros fisicos invalidos, el simulador falla antes de ejecutar. El mensaje indica la ruta del campo, por ejemplo `Invalid vehicle.mass_kg: expected positive kg value, got -1.0`.

El comando `plot` sigue estando disponible para regenerar figuras desde un JSON existente:

```powershell
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
```

El argumento `--metrics` es opcional, pero permite anotar información como el RMSE.

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

Una vez ejecutado el dataset clasico y generados sus `telemetry.json`, se puede entrenar un controlador neuronal por imitacion:

```powershell
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture mlp --out data\neural_control\mlp_v1 --device cuda
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture gru --out data\neural_control\gru_v1 --device cuda
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture lstm --out data\neural_control\lstm_v1 --device cuda
```

Evaluacion supervisada in-distribution:

```powershell
uv run python tools\evaluate_neural_controller.py --dataset data\classic_dataset\v1 --run data\neural_control\gru_v1 --device cuda
```

Evaluacion supervisada OOD sobre un dataset ya generado:

```powershell
uv run python tools\evaluate_neural_controller.py --dataset data\classic_dataset\v1 --run data\neural_control\gru_v1 --ood-dataset data\neural_ood\lemniscate_v1 --device cuda
```

El directorio pasado a `--ood-dataset` debe tener `manifest.csv` y telemetria existente. El evaluador no ejecuta escenarios; solo compara predicciones con comandos expertos ya exportados.

Ejecucion en bucle cerrado de un checkpoint neuronal:

```powershell
uv run python tools\run_neural_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\gru_v1\checkpoints\gru_best.pt --normalization data\neural_control\gru_v1\normalization.json --device cuda --no-visualization
```

Este comando no modifica el YAML original. Sustituye el controlador en memoria, ejecuta el simulador y escribe telemetria/metricas en un directorio derivado de `output.dir` o en `--out` si se proporciona. Si no se indica `--architecture`, se lee desde el `config.yaml` del entrenamiento.

La metrica supervisada `saturation_percentage` del evaluador neuronal mide comandos predichos fuera de limites antes del clipping. Por defecto usa masa `1.0 kg`, gravedad `9.81 m/s^2`, empuje maximo `m*g*2.5` y momentos `[10, 10, 2] Nm`; si el dataset usa otros limites, interpretar esa metrica con cautela hasta parametrizarla desde CLI o metadata.

Figuras generadas (tanto en `run` automático como en `plot` manual):

- `trajectory_xy.png`: trayectoria real y referencia en el plano horizontal ENU.
- `position_time.png`: componentes `X_W`, `Y_W`, `Z_W` frente al tiempo.
- `attitude_time.png`: roll, pitch y yaw en grados, calculados desde `orientation_WB` con el convenio ENU/FRD del simulador.
- `angular_velocity_time.png`: componentes `p`, `q`, `r` de `angular_velocity_B_rad_s` en `rad/s`.
- `tracking_error.png`: norma del error de posición `||p_ref - p||`.
- `rotor_speeds.png`: velocidades de rotor aplicadas en `rad/s`.
- `control_effort.png`: empuje colectivo, momentos de cuerpo y un indice heuristico agregado para diagnostico visual.

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
