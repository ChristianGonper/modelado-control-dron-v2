# Tasks: escenarios por trayectoria y visualizacion 3D posterior

## Politica de commits

La implementacion debe hacerse con commits pequenos, revisables y coherentes. Cada commit debe cubrir una unidad funcional clara, por ejemplo:

- dependencia y lockfile;
- generador HTML 3D y sus tests;
- integracion CLI;
- escenarios YAML;
- documentacion.

No agrupar toda la funcionalidad en un unico commit. Antes de cada commit debe ejecutarse la verificacion razonable para el cambio tocado; al final debe ejecutarse `uv run pytest`.

## Tareas

- [x] Task: Anadir Plotly como dependencia del proyecto
  - Acceptance: `pyproject.toml` incluye `plotly` y `uv.lock` queda actualizado con `uv`.
  - Verify: `uv sync` y `uv run python -c "import plotly"`.
  - Files: `pyproject.toml`, `uv.lock`.
  - Suggested commit: `Add Plotly dependency`

- [x] Task: Crear generador HTML 3D posterior
  - Acceptance: existe `export_trajectory_viewer_html(...)` y genera un HTML navegable con trayectoria real, referencia, inicio, fin, ejes ENU y resumen basico de metricas/terminacion cuando existan.
  - Verify: nuevo test unitario de visualizacion HTML pasa con `uv run pytest tests\test_visualization.py`.
  - Files: `src/simulador_quad/visualization/three_d.py`, `src/simulador_quad/visualization/__init__.py` si hace falta, `tests/test_visualization.py`.
  - Suggested commit: `Add 3D trajectory HTML export`

- [x] Task: Integrar visualizacion automatica en `run`
  - Acceptance: `uv run simulador-quad run <escenario>` genera `telemetry.json`, `metrics.json`, `figures/*.png` y `visualization_3d.html` por defecto.
  - Verify: ejecutar un escenario corto, por ejemplo `uv run simulador-quad run scenarios\hover_clean.yaml`, y comprobar artefactos en `results\hover_clean`.
  - Files: `src/simulador_quad/app.py`, tests de CLI/orquestacion si procede.
  - Suggested commit: `Generate visual outputs during scenario run`

- [x] Task: Anadir bandera `--no-visualization`
  - Acceptance: `uv run simulador-quad run <escenario> --no-visualization` conserva telemetria y metricas, pero no regenera `figures/` ni `visualization_3d.html`.
  - Verify: ejecutar `uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization` en un directorio de salida limpio o temporal.
  - Files: `src/simulador_quad/app.py`, tests de CLI/orquestacion si procede.
  - Suggested commit: `Add no visualization run flag`

- [x] Task: Crear escenario Lissajous
  - Acceptance: `scenarios/lissajous_clean.yaml` define una trayectoria `lissajous` suave, con salida propia en `results/lissajous_clean`.
  - Verify: `uv run simulador-quad run scenarios\lissajous_clean.yaml --no-visualization` finaliza y escribe JSON de resultados.
  - Files: `scenarios/lissajous_clean.yaml`.
  - Suggested commit: `Add Lissajous scenario`

- [x] Task: Crear escenario waypoint
  - Acceptance: `scenarios/waypoint_clean.yaml` define una trayectoria `line` o `waypoint` suave, con salida propia en `results/waypoint_clean`.
  - Verify: `uv run simulador-quad run scenarios\waypoint_clean.yaml --no-visualization` finaliza y escribe JSON de resultados.
  - Files: `scenarios/waypoint_clean.yaml`.
  - Suggested commit: `Add waypoint scenario`

- [x] Task: Actualizar documentacion de uso
  - Acceptance: `docs/simulador/guia_uso.md` describe el flujo unificado, los artefactos generados por `run`, el visor 3D y la bandera `--no-visualization`.
  - Verify: lectura manual y comprobacion de comandos con rutas reales.
  - Files: `docs/simulador/guia_uso.md`.
  - Suggested commit: `Document unified visualization workflow`

- [x] Task: Actualizar documentacion de escenarios
  - Acceptance: `docs/simulador/escenarios_yaml.md` menciona los escenarios disponibles para `hold`, `circle`, `lissajous` y `line/waypoint`, y mantiene las convenciones fisicas existentes.
  - Verify: lectura manual y consistencia con YAML reales.
  - Files: `docs/simulador/escenarios_yaml.md`.
  - Suggested commit: `Document trajectory scenarios`

- [x] Task: Actualizar arquitectura de resultados si aplica
  - Acceptance: `docs/simulador/arquitectura.md` refleja que el flujo de simulacion termina en telemetria, metricas, figuras PNG y visor HTML 3D.
  - Verify: lectura manual y consistencia con `app.py`.
  - Files: `docs/simulador/arquitectura.md`.
  - Suggested commit: `Document visualization artifacts in architecture`

- [x] Task: Verificacion final completa
  - Acceptance: todos los tests pasan y al menos un escenario completo genera PNG y HTML 3D.
  - Verify: `uv run pytest` y `uv run simulador-quad run scenarios\hover_clean.yaml`.
  - Files: sin cambios esperados salvo ajustes menores derivados de fallos encontrados.
  - Suggested commit: solo si la verificacion exige correcciones; no crear commit vacio.
