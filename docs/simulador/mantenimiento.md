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

## Cuando cambie el dataset clasico

Revisar:

- `docs/simulador/dataset_clasico.md`
- `docs/simulador/validacion.md`
- `docs/simulador/trazabilidad.md`
- `README.md`

Actualizar familias, perfiles, conteos, splits, nombres de PID, campos de `manifest.csv`, comandos de `tools/` y criterios de validez. Si cambia el YAML generado, revisar tambien `docs/simulador/escenarios_yaml.md`.

Ejecutar al menos:

```powershell
uv run pytest tests\test_classic_controller_config.py tests\test_classic_dataset_generation.py tests\test_classic_dataset_scripts.py tests\test_classic_pid_selection.py
```

## Cuando cambie el control neuronal

Revisar:

- `docs/simulador/control_neuronal.md`
- `docs/simulador/arquitectura.md`
- `docs/simulador/escenarios_yaml.md`
- `docs/simulador/validacion.md`
- `docs/simulador/trazabilidad.md`
- `README.md`

Actualizar features, targets, normalizacion, artefactos (`config.yaml`, `normalization.json`, checkpoints, metricas), comandos de `tools/`, limites de clipping y criterios OOD. Para `neural` outer-force, revisar tambien la seleccion del experto, la preservacion del PID interno, los limites del escenario fuente y las metricas `force_norm_clip_percentage` / `force_tilt_clip_percentage`. Si cambia la evaluacion OOD, dejar claro si el comando ejecuta escenarios o consume telemetria ya generada.

Ejecutar al menos:

```powershell
uv run pytest tests\test_neural_dataset.py tests\test_neural_models.py tests\test_neural_training.py tests\test_neural_evaluation.py tests\test_neural_controller.py tests\test_neural_outer_force.py tests\test_outer_force_generation_integration.py
```

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
- cambios en el contrato del controlador neuronal, sus targets de fuerza o el reparto entre lazo externo e interno.

## Checklist antes de cerrar una actualizacion

```powershell
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml
uv run simulador-quad run scenarios\circle_drag.yaml
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
uv run python tools\generate_classic_dataset.py --version test_v1 --out $env:TEMP\simulador_quad_dataset_test_v1 --overwrite
uv run pytest tests\test_neural_dataset.py tests\test_neural_models.py tests\test_neural_training.py tests\test_neural_evaluation.py tests\test_neural_controller.py tests\test_neural_outer_force.py tests\test_outer_force_generation_integration.py
```

Despues de ejecutar:

- `telemetry.json` y `metrics.json` existen para los escenarios ejecutados.
- Las ocho figuras PNG base existen y tienen contenido; las figuras neuronales y de perturbaciones aparecen cuando la telemetria aporta esos campos.
- La documentacion no contradice `loader.py`, `export.py`, `report.py` ni el CLI.
- La validacion de escenarios no contradice `schema.py`.
- La documentacion del dataset no contradice `src/simulador_quad/datasets/classic.py` ni los scripts en `tools/`.
- La documentacion neuronal no contradice `src/simulador_quad/ml/`, `src/simulador_quad/control/neural.py` ni los scripts neuronales en `tools/`.
- OOD queda documentado como evaluacion separada y no se mezcla con `test`.
- Los documentos normativos no se han modificado salvo decision explicita.
