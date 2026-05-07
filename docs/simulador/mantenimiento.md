# Mantenimiento documental

Esta carpeta debe actualizarse cuando cambie el comportamiento real del simulador. El objetivo es que siga siendo una fuente fiable para usar y explicar el sistema despues de refactors o cambios agresivos.

## Cuando cambie el CLI

Revisar:

- `docs/simulador/README.md`
- `docs/simulador/guia_uso.md`

Actualizar comandos, argumentos, nombres de subcomandos y ejemplos. Ejecutar los comandos documentados antes de cerrar el cambio.

## Cuando cambie el YAML de escenarios

Revisar:

- `docs/simulador/escenarios_yaml.md`
- ejemplos en `docs/simulador/guia_uso.md`

Comprobar que cada campo documentado existe en `src/simulador_quad/scenarios/loader.py` y, si afecta a validez fisica, en `src/simulador_quad/scenarios/schema.py`; si no existe, declararlo explicitamente como limite/futuro. No documentar campos aspiracionales como si ya estuvieran implementados.

## Cuando cambien trayectorias

Revisar:

- seccion `trajectory` en `docs/simulador/escenarios_yaml.md`;
- figuras de trayectoria en `docs/simulador/guia_uso.md`;
- pruebas en `tests/test_trajectories.py`.

Cada trayectoria documentada debe indicar posicion, velocidad, aceleracion y yaw que devuelve, ademas de unidades y marco de referencia.

## Cuando cambien telemetria o metricas

Revisar:

- `docs/simulador/arquitectura.md`;
- `docs/simulador/guia_uso.md`;
- `src/simulador_quad/visualization/plots.py`;
- pruebas de metricas y visualizacion.

Si se renombra un campo de `telemetry.json`, actualizar tambien la visualizacion. Si se añade una metrica nueva, explicar su significado fisico y sus unidades.

Actualizar tambien `tests/test_model_regressions.py` si cambia el esquema minimo esperado de `metrics.json` o `telemetry.json`.

## Cuando cambie el modelo fisico

Revisar:

- `docs/simulador/arquitectura.md`;
- `docs/simulador/escenarios_yaml.md`;
- documentos normativos solo si el cambio altera el alcance o contradice requisitos existentes.

Ejemplos que obligan a documentar con cuidado:

- nuevo modelo de drag;
- viento no constante;
- sensores o estimador;
- contacto con suelo;
- bateria;
- aerodinamica formal;
- controlador neuronal operativo.

## Checklist antes de cerrar una actualizacion

```powershell
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml
uv run simulador-quad run scenarios\circle_drag.yaml
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
```

Despues de ejecutar:

- `telemetry.json` y `metrics.json` existen para los escenarios ejecutados.
- Las cinco figuras PNG existen y tienen contenido.
- La documentacion no contradice `loader.py`, `export.py`, `report.py` ni el CLI.
- La validacion de escenarios no contradice `schema.py`.
- Los documentos normativos no se han modificado salvo decision explicita.
