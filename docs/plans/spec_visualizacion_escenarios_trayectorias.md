# Spec: escenarios por trayectoria y visualizacion 3D posterior

## Objective

Ampliar el flujo experimental del simulador para que cada tipo de trayectoria existente tenga al menos un escenario YAML ejecutable y para que una ejecucion de escenario genere automaticamente salidas visuales, ademas de telemetria y metricas.

El usuario principal es un alumno de ingenieria aeroespacial que quiere ejecutar escenarios reproducibles, inspeccionar el seguimiento de la referencia y moverse en una vista 3D posterior a la simulacion para entender como ha evolucionado el cuadricoptero.

Acceptance criteria:

- Existen escenarios en `scenarios/` para `hold`, `circle`, `lissajous` y `line` o `waypoint`.
- `uv run simulador-quad run <escenario.yaml>` genera telemetria, metricas, figuras estaticas y una visualizacion 3D posterior en el directorio `output.dir`.
- La visualizacion 3D permite inspeccionar la referencia y la trayectoria real de forma no interactiva en tiempo de simulacion, pero si navegable con camara 3D en el navegador.
- La salida mantiene trazabilidad: los artefactos se derivan de `telemetry.json`, `metrics.json` y del escenario guardado en `metrics.metadata.config`.
- El flujo `plot` existente sigue funcionando para regenerar figuras desde telemetria ya exportada.

## Tech Stack

- Python `>=3.13`.
- NumPy para transformar datos numericos.
- Matplotlib para figuras PNG estaticas existentes.
- PyYAML para escenarios.
- Pytest para pruebas.
- Visualizacion 3D: archivo HTML generado con Plotly, sin servidor obligatorio, con camara 3D navegable en el navegador.

Dependencia nueva aprobada: Plotly. Se incorpora porque resuelve directamente la inspeccion 3D posterior con camara navegable, leyendas y exportacion HTML reproducible sin desarrollar un visor WebGL propio.

## Commands

Preparar entorno:

```powershell
uv sync
```

Ejecutar pruebas:

```powershell
uv run pytest
```

Ejecutar un escenario:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml
```

Ejecutar un escenario sin generar visualizacion automatica:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
```

Regenerar figuras desde telemetria:

```powershell
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
```

Ver la visualizacion 3D generada:

```powershell
start results\hover_clean\visualization_3d.html
```

## Project Structure

```text
scenarios/
  hover_clean.yaml                  -> escenario hold existente
  circle_drag.yaml                  -> escenario circle existente
  circle_noisy_wind.yaml            -> escenario circle con perturbaciones existente
  lissajous_clean.yaml              -> nuevo escenario lissajous
  waypoint_clean.yaml               -> nuevo escenario line/waypoint

src/simulador_quad/
  app.py                            -> CLI run/plot y orquestacion de artefactos
  runner.py                         -> bucle temporal de simulacion
  trajectories/analytic.py          -> trayectorias hold, circle, lissajous y line
  visualization/plots.py            -> figuras PNG estaticas
  visualization/three_d.py          -> nueva generacion de HTML 3D posterior con Plotly
  telemetry/export.py               -> exportacion JSON existente
  metrics/report.py                 -> metricas existentes

tests/
  test_visualization.py             -> pruebas de figuras y HTML 3D
  test_runner.py                    -> pruebas del flujo temporal
  test_trajectories.py              -> pruebas de referencias analiticas

docs/simulador/
  guia_uso.md                       -> documentar que run genera visualizacion
  escenarios_yaml.md                -> documentar escenarios nuevos si aplica
  arquitectura.md                   -> actualizar flujo de simulacion y artefactos si aplica
```

## Code Style

Mantener codigo cientifico explicito, con unidades y marcos de referencia en nombres. Ejemplo esperado para una funcion de visualizacion:

```python
def export_trajectory_viewer_html(
    telemetry_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    metrics_path: str | os.PathLike[str] | None = None,
) -> str:
    """Exporta una vista 3D posterior con posicion real y referencia en mundo ENU."""
    telemetry = _load_json(telemetry_path)
    position_W_m = _as_array(telemetry, "state", "position_W_m")
    reference_W_m = _as_array(telemetry, "reference", "position_W_m")
    # ...
    return str(output_path)
```

Conventions:

- Usar nombres como `position_W_m`, `reference_W_m`, `output_dir`.
- Mantener funciones pequenas y orientadas a una salida concreta.
- Evitar abstracciones genericas para graficos; cada artefacto debe tener responsabilidad clara.
- Usar errores comprensibles si la telemetria esta vacia o incompleta.

## Testing Strategy

Framework: `pytest`.

Tests required:

- `test_visualization.py` comprueba que el generador HTML 3D crea un archivo no vacio desde telemetria minima.
- `test_visualization.py` comprueba que el HTML contiene datos de referencia y trayectoria real en formato consumible por el visor.
- Prueba de CLI o funcion de orquestacion para confirmar que `run_simulation(...)` genera `telemetry.json`, `metrics.json`, `figures/*.png` y `visualization_3d.html` en `output.dir`.
- Tests existentes de trayectorias deben seguir pasando.

Verification command:

```powershell
uv run pytest
```

## Boundaries

- Always: respetar ENU para mundo y FRD para cuerpo; generar artefactos en `output.dir`; preservar telemetria y metricas existentes; usar `uv`; documentar comandos reproducibles.
- Always: mantener `plot` como comando valido para figuras desde telemetria existente.
- Ask first: anadir dependencias nuevas adicionales a Plotly, como PyVista, VTK, Dash o Three.js empaquetado por Python; cambiar el formato de `telemetry.json`; cambiar convenciones de ejes; modificar parametros fisicos base del vehiculo.
- Never: hacer visualizacion en tiempo real dentro del runner; mezclar codigo de simulacion fisica con renderizado; eliminar figuras o metricas existentes; introducir servicios externos para ver resultados.

## Success Criteria

- Al ejecutar `uv run simulador-quad run scenarios\lissajous_clean.yaml`, el directorio de salida contiene:
  - `telemetry.json`
  - `metrics.json`
  - `figures/trajectory_xy.png`
  - `figures/position_time.png`
  - `figures/tracking_error.png`
  - `figures/rotor_speeds.png`
  - `figures/control_effort.png`
  - `visualization_3d.html`
- Lo mismo ocurre para escenarios `hold`, `circle` y `waypoint/line`.
- `visualization_3d.html` permite inspeccionar en 3D:
  - trayectoria real del vehiculo;
  - referencia o punto definido;
  - inicio y fin del episodio;
  - ejes `X_W`, `Y_W`, `Z_W`;
  - causa de terminacion y metricas basicas si existen.
- El visor no requiere ejecutar la simulacion de nuevo.
- `uv run pytest` pasa.
- `docs/simulador/guia_uso.md` describe el flujo unificado y la bandera `--no-visualization`.
- La documentacion bajo `docs/simulador/` queda actualizada con los escenarios y artefactos nuevos.

## Open Questions

Sin preguntas abiertas. Decisiones aprobadas:

- Usar Plotly para la visualizacion 3D posterior.
- Crear `scenarios/waypoint_clean.yaml` para cubrir `line/waypoint`.
- Generar visualizacion por defecto en `run`, con bandera `--no-visualization` para desactivarla.
- Mantener actualizada la documentacion bajo `docs/simulador/`.
