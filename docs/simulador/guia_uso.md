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

Cada escenario define su directorio de salida en `output.dir`. El simulador escribe:

- `telemetry.json`: historia temporal de estado, observacion, referencia, comando y rotores.
- `metrics.json`: resumen numerico de seguimiento, esfuerzo de control, saturacion y terminacion.

Un episodio que termina por una condicion fisica, por ejemplo saturacion persistente o altura invalida, no implica por si mismo un error del programa. La causa queda registrada como resultado del experimento.

## Generar figuras

La telemetria exportada puede convertirse en figuras reproducibles:

```powershell
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
```

El argumento `--metrics` es opcional, pero conviene pasarlo porque permite anotar informacion agregada como el RMSE de posicion en la figura XY.

Figuras generadas:

- `trajectory_xy.png`: trayectoria real y referencia en el plano horizontal ENU.
- `position_time.png`: componentes `X_W`, `Y_W`, `Z_W` frente al tiempo.
- `tracking_error.png`: norma del error de posicion `||p_ref - p||`.
- `rotor_speeds.png`: velocidades de rotor aplicadas en `rad/s`.
- `control_effort.png`: empuje colectivo, momentos de cuerpo y esfuerzo agregado.

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
2. Cambiar solo una familia de parametros: trayectoria, perturbacion, vehiculo o tiempos.
3. Ejecutar el escenario con `uv run simulador-quad run`.
4. Generar figuras con `uv run simulador-quad plot`.
5. Guardar resultados en un subdirectorio distinto dentro de `results/`.
6. Comparar metricas y figuras con el escenario base.

Este flujo mantiene trazabilidad: el `metrics.json` conserva el YAML usado dentro de `metadata.config`, y las figuras se generan directamente desde la telemetria exportada.

