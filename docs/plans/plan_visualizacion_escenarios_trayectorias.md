# Plan: escenarios por trayectoria y visualizacion 3D posterior

## 1. Dependencia Plotly

Actualizar `pyproject.toml` con `plotly` y regenerar `uv.lock` mediante:

```powershell
uv sync
```

Riesgo: cambio de lockfile relativamente grande. Mitigacion: revisar que solo se incorporan dependencias transitivas esperadas y ejecutar `uv run pytest`.

## 2. Generador 3D posterior

Crear `src/simulador_quad/visualization/three_d.py` con una funcion principal:

```python
export_trajectory_viewer_html(telemetry_path, output_path, metrics_path=None) -> str
```

Responsabilidades:

- Leer `telemetry.json` y opcionalmente `metrics.json`.
- Extraer `state.position_W_m` y `reference.position_W_m`.
- Generar una figura Plotly 3D con:
  - trayectoria real;
  - referencia;
  - punto inicial;
  - punto final;
  - ejes ENU etiquetados `X_W Este [m]`, `Y_W Norte [m]`, `Z_W arriba [m]`;
  - titulo con nombre de escenario, causa de terminacion y RMSE si estan disponibles.
- Guardar `visualization_3d.html` como HTML navegable sin servidor.

Riesgo: telemetria vacia o incompleta. Mitigacion: errores claros, igual que `plot_telemetry`.

## 3. Flujo CLI unificado

Modificar `src/simulador_quad/app.py`:

- `run` mantiene el argumento posicional de escenario.
- `run` incorpora `--no-visualization`.
- Tras exportar telemetria y metricas, si no se desactiva:
  - generar figuras PNG en `<output.dir>/figures`;
  - generar `<output.dir>/visualization_3d.html`.
- Imprimir rutas generadas para trazabilidad.
- Mantener el subcomando `plot` existente sin romper compatibilidad.

Riesgo: que `run_simulation` quede demasiado acoplada a CLI. Mitigacion: mantener una funcion clara que acepte `generate_visualization: bool = True`.

## 4. Escenarios faltantes

Crear:

- `scenarios/lissajous_clean.yaml`
- `scenarios/waypoint_clean.yaml`

Ambos reutilizaran parametros fisicos y controlador clasico de los escenarios existentes, ajustando solo trayectoria, duracion y `output.dir`.

Riesgo: escenarios demasiado exigentes para el controlador actual. Mitigacion: usar amplitudes, tiempos y velocidades suaves para que sirvan como casos reproducibles iniciales, no como pruebas extremas.

## 5. Pruebas

Ampliar `tests/test_visualization.py`:

- Prueba de generacion HTML con telemetria minima.
- Comprobar que el archivo incluye trazas de estado y referencia.

Agregar o ampliar prueba de CLI/orquestacion si es viable sin hacer la simulacion completa pesada:

- Usar escenario temporal corto o probar funcion auxiliar con telemetria sintetica.
- Verificar existencia de `figures/` y `visualization_3d.html`.

Ejecutar:

```powershell
uv run pytest
```

## 6. Documentacion

Actualizar bajo `docs/simulador/`:

- `guia_uso.md`: nuevo flujo por defecto, `--no-visualization`, ubicacion de `figures/` y `visualization_3d.html`.
- `escenarios_yaml.md`: mencionar escenarios `lissajous_clean.yaml` y `waypoint_clean.yaml`.
- `arquitectura.md` si describe el flujo de resultados, para incluir visualizacion automatica posterior.

## 7. Orden de implementacion

1. Dependencia Plotly.
2. Generador `visualization/three_d.py` con prueba unitaria.
3. Integracion en CLI con `--no-visualization`.
4. Escenarios `lissajous_clean.yaml` y `waypoint_clean.yaml`.
5. Documentacion en `docs/simulador/`.
6. Ejecucion de pruebas completas.
7. Ejecucion manual de un escenario representativo para verificar artefactos.

## 8. Checkpoints de verificacion

- Tras dependencia: `uv run python -c "import plotly"` funciona.
- Tras generador HTML: test unitario de visualizacion pasa.
- Tras CLI: `uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization` conserva salida JSON.
- Tras flujo completo: `uv run simulador-quad run scenarios\hover_clean.yaml` genera JSON, PNG y HTML.
- Final: `uv run pytest` pasa.
