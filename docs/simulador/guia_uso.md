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

El comando `plot` sigue estando disponible para regenerar figuras desde un JSON existente:

```powershell
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
```

El argumento `--metrics` es opcional, pero permite anotar información como el RMSE.

Figuras generadas (tanto en `run` automático como en `plot` manual):

- `trajectory_xy.png`: trayectoria real y referencia en el plano horizontal ENU.
- `position_time.png`: componentes `X_W`, `Y_W`, `Z_W` frente al tiempo.
- `tracking_error.png`: norma del error de posición `||p_ref - p||`.
- `rotor_speeds.png`: velocidades de rotor aplicadas en `rad/s`.
- `control_effort.png`: empuje colectivo, momentos de cuerpo y esfuerzo agregado.

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
- `control_effort_mean` y `control_effort_max`: magnitud agregada de empuje y momentos.
- `max_rotor_speed_rad_s` y `max_rotor_speed_rpm`: maxima velocidad aplicada.
- `saturation_duration_s` y `saturation_percentage`: tiempo con algun rotor saturado.
- `degradation_duration_s` y `degradation_percentage`: tiempo con empuje colectivo degradado por el mezclador.
- `termination_reason`: causa final del episodio.
- `metadata`: escenario completo, nombre y semilla usados.

## Flujo recomendado para un alumno

1. Copiar un escenario existente en `scenarios/`.
2. Cambiar solo una familia de parámetros: trayectoria, perturbación, vehículo o tiempos.
3. Ejecutar el escenario con `uv run simulador-quad run`.
4. Inspeccionar el visor `visualization_3d.html` para una visión global.
5. Revisar las figuras en `figures/` para análisis temporal.
6. Guardar resultados en un subdirectorio distinto dentro de `results/`.
7. Comparar métricas y figuras con el escenario base.

Este flujo mantiene trazabilidad: el `metrics.json` conserva el YAML usado dentro de `metadata.config`, y las figuras se generan directamente desde la telemetria exportada.

