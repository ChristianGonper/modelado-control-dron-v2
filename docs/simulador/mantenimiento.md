# Mantenimiento de la documentación

Actualiza esta documentación cuando cambie el comportamiento del simulador. Las listas siguientes ayudan a localizar qué páginas revisar según el tipo de cambio; contrastar el texto con el código sigue siendo necesario.

## Si cambia la interfaz de comandos

Revisar:

- `docs/simulador/README.md`
- `docs/simulador/guia_uso.md`

Comprueba los nombres de los subcomandos, sus argumentos y ejemplos. Ejecuta los comandos documentados que se vean afectados antes de dar por terminado el cambio.

## Si cambia el formato de escenarios

Revisar:

- `docs/simulador/escenarios_yaml.md`
- ejemplos en `docs/simulador/guia_uso.md`

Comprueba los campos en `src/simulador_quad/scenarios/loader.py` y, cuando afecten a la validez física, en `src/simulador_quad/scenarios/schema.py`. Distingue las capacidades existentes de las que estén previstas pero aún no implementadas.

## Si cambian las trayectorias

Revisar:

- seccion `trajectory` en `docs/simulador/escenarios_yaml.md`;
- ejemplos de ejecución en `docs/simulador/guia_uso.md`;
- pruebas en `tests/test_trajectories.py`.

Explica qué posición, velocidad, aceleración y orientación devuelve cada trayectoria, junto con sus unidades y marco de referencia.

## Si cambian la telemetría o las métricas

Revisar:

- `docs/simulador/arquitectura.md`;
- `docs/simulador/guia_uso.md`;
- `src/simulador_quad/visualization/plots.py`;
- pruebas de metricas y visualizacion.

Si se renombra un campo de `telemetry.json`, revisa también las visualizaciones que lo usan. Para cada métrica nueva, explica su significado físico y sus unidades.

Revisa `tests/test_model_regressions.py` si cambia el esquema mínimo esperado de `metrics.json` o `telemetry.json`.

## Si cambia el conjunto de datos clásico

Revisar:

- `docs/simulador/dataset_clasico.md`
- `docs/simulador/validacion.md`
- `docs/simulador/trazabilidad.md`
- `README.md`

Actualiza las familias, perfiles, recuentos, divisiones, nombres de PD, campos del manifiesto, comandos y criterios que se vean afectados. Si cambia el YAML generado, revisa también la referencia de escenarios.

Ejecutar al menos:

```powershell
uv run pytest tests\test_classic_controller_config.py tests\test_classic_dataset_generation.py tests\test_classic_dataset_scripts.py tests\test_classic_pid_selection.py
```

## Si cambia el control neuronal

Revisar:

- `docs/simulador/control_neuronal.md`
- `docs/simulador/arquitectura.md`
- `docs/simulador/escenarios_yaml.md`
- `docs/simulador/validacion.md`
- `docs/simulador/trazabilidad.md`
- `README.md`

Revisa las entradas y salidas de la red, la normalización, los artefactos, los comandos, las protecciones y los criterios OOD. Para el control de fuerza exterior, comprueba también la selección del experto, las ganancias del lazo interno y las métricas de limitación de fuerza e inclinación. Distingue los comandos que ejecutan escenarios de los que consumen telemetría ya generada.

Ejecutar al menos:

```powershell
uv run pytest tests\test_neural_dataset.py tests\test_neural_models.py tests\test_neural_training.py tests\test_neural_evaluation.py tests\test_neural_controller.py tests\test_neural_outer_force.py tests\test_outer_force_generation_integration.py
```

## Si cambia el modelo físico

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

## Comprobaciones antes de terminar

```powershell
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml
uv run simulador-quad run scenarios\circle_drag.yaml
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
uv run python tools\generate_classic_dataset.py --version test_v1 --out $env:TEMP\simulador_quad_dataset_test_v1 --overwrite
uv run pytest tests\test_neural_dataset.py tests\test_neural_models.py tests\test_neural_training.py tests\test_neural_evaluation.py tests\test_neural_controller.py tests\test_neural_outer_force.py tests\test_outer_force_generation_integration.py
```

Después de ejecutar las comprobaciones, revisa que:

- `telemetry.json` y `metrics.json` existen para los escenarios ejecutados.
- Las ocho figuras PNG base existen y tienen contenido; las figuras neuronales y de perturbaciones aparecen cuando la telemetria aporta esos campos.
- La documentación no contradiga `loader.py`, `export.py`, `report.py` ni el CLI.
- La validación de escenarios no contradiga `schema.py`.
- La documentación del conjunto de datos no contradiga `src/simulador_quad/datasets/classic.py` ni los scripts en `tools/`.
- La documentación neuronal no contradiga `src/simulador_quad/ml/`, `src/simulador_quad/control/neural.py` ni los scripts neuronales en `tools/`.
- OOD quede documentado como evaluación separada y no se mezcla con `test`.
- Los documentos normativos solo se hayan modificado si existe una decisión explícita.
