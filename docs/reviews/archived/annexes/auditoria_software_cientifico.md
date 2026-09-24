# Auditoria de software cientifico simple

Fecha de auditoria: 2026-05-04

Alcance: revision del repositorio desde la perspectiva de software cientifico simple, mantenibilidad y reproducibilidad. Se han leido `AGENTS.md` y los documentos normativos `docs/01_principios_tfg.md`, `docs/02_requisitos_ingenieria_simulador.md` y `docs/03_criterios_ingenieria_software.md`. No se ha modificado codigo fuente ni tests.

Verificacion ejecutada:

```powershell
uv run pytest
```

Resultado: 29 tests pasan en Python 3.13.11.

## Resumen ejecutivo

El repositorio ya tiene una base razonable para codigo cientifico simple: paquete `src/simulador_quad`, separacion clara entre nucleo fisico, control, escenarios, runner, telemetria, metricas y visualizacion; escenarios YAML; `uv.lock`; CLI instalable; tests de los bloques fisicos principales; y documentacion viva en `docs/simulador/`.

El riesgo principal no es exceso de arquitectura, sino falta de contratos ejecutables y validacion de entrada. Muchas decisiones estan documentadas, pero el codigo acepta configuraciones crudas y arrays NumPy sin comprobar dimensiones, unidades, finitud ni rangos fisicos. Esto reduce la mantenibilidad y aumenta el riesgo de que un escenario invalido produzca resultados aparentemente reproducibles pero fisicamente no defendibles.

Tambien hay una brecha funcional respecto al objetivo global del TFG: la parte neuronal por imitacion esta reconocida como no implementada. Para la fase actual puede ser aceptable, pero para una entrega final impide cerrar la comparacion clasico-neuronal exigida por los documentos normativos.

## Fortalezas observadas

- La estructura del paquete es legible y alineada con los conceptos del TFG: `core`, `dynamics`, `control`, `scenarios`, `telemetry`, `metrics`, `trajectories` y `visualization`.
- Los contratos principales estan centralizados como dataclasses en `src/simulador_quad/core/contracts.py:5`, `src/simulador_quad/core/contracts.py:23`, `src/simulador_quad/core/contracts.py:31`, `src/simulador_quad/core/contracts.py:38` y `src/simulador_quad/core/contracts.py:57`.
- El flujo de ejecucion esta concentrado en un runner unico con pasos de fisica, control y telemetria separados en `src/simulador_quad/runner.py:13`, `src/simulador_quad/runner.py:14`, `src/simulador_quad/runner.py:15` y el bucle principal en `src/simulador_quad/runner.py:137`.
- El CLI existe y usa el entry point `simulador-quad` definido en `pyproject.toml:19` y `pyproject.toml:20`.
- La telemetria distingue estado, observacion, referencia, comando solicitado, comando de rotor y estado aplicado en `src/simulador_quad/telemetry/export.py:19` a `src/simulador_quad/telemetry/export.py:53`.
- La documentacion de usuario y arquitectura es util para un tribunal: comandos con `uv` en `docs/simulador/guia_uso.md:5` a `docs/simulador/guia_uso.md:10`, flujo de simulacion en `docs/simulador/arquitectura.md:5` a `docs/simulador/arquitectura.md:20` y referencia YAML en `docs/simulador/escenarios_yaml.md:1` a `docs/simulador/escenarios_yaml.md:21`.
- La suite de tests cubre actitud, dinamica, actuadores, mezclador, perturbaciones, runner, metricas, trayectorias y visualizacion.

## Hallazgos priorizados

### P1 - Falta validacion ejecutable de contratos fisicos y escenarios

Los contratos de datos son dataclasses pasivas: no validan dimensiones, finitud, unidades esperadas ni rangos. Por ejemplo, `VehicleState` acepta cualquier array en `src/simulador_quad/core/contracts.py:5` a `src/simulador_quad/core/contracts.py:11`, `VehicleParameters` no comprueba masa positiva ni matriz de inercia en `src/simulador_quad/core/contracts.py:23` a `src/simulador_quad/core/contracts.py:29`, y `RotorParameters` no comprueba signos o rangos en `src/simulador_quad/core/contracts.py:13` a `src/simulador_quad/core/contracts.py:21`.

El cargador YAML lee diccionarios crudos y accede a claves directamente en `src/simulador_quad/scenarios/loader.py:12` a `src/simulador_quad/scenarios/loader.py:15` y `src/simulador_quad/scenarios/loader.py:21` en adelante. Existe `ScenarioConfig`, pero queda como dataclass no usada en `src/simulador_quad/scenarios/schema.py:6` a `src/simulador_quad/scenarios/schema.py:17`.

Riesgo: un escenario con `inertia_B_kg_m2` mal dimensionada, `mass_kg <= 0`, `k_f <= 0`, `times` no crecientes o `orientation_WB` no normalizado puede fallar tarde, con `KeyError`/`LinAlgError`, o peor, generar resultados numericos no defendibles.

Recomendacion: introducir validaciones simples, no una capa compleja. Bastaria con funciones `validate_vehicle_config`, `validate_timing_config`, `validate_trajectory_config` y `validate_state`, mas `__post_init__` en dataclasses criticas. Los errores deben decir campo, unidad esperada y valor recibido.

### P1 - La comparacion con control neuronal todavia no es reproducible

Los documentos normativos fijan como objetivo comparar control clasico y neuronal por imitacion. El codigo solo instancia `ClassicCascadeController`: `src/simulador_quad/scenarios/loader.py:81` a `src/simulador_quad/scenarios/loader.py:90`. La documentacion viva lo declara explicitamente como no implementado en `docs/simulador/README.md:23` a `docs/simulador/README.md:28`.

Riesgo: para una entrega final, el repositorio no permite reproducir generacion de dataset, entrenamiento, carga de artefacto neuronal, normalizacion ni evaluacion en bucle cerrado. La trazabilidad experimental queda limitada al controlador clasico.

Recomendacion: mantener esta limitacion como estado actual, pero planificar una interfaz minima de controlador neuronal compatible con `Controller.compute_control` en `src/simulador_quad/control/contract.py:4` a `src/simulador_quad/control/contract.py:7`. La prioridad no deberia ser entrenar modelos sofisticados, sino cerrar el flujo reproducible: dataset, semilla, normalizacion, checkpoint, evaluacion cerrada y metricas comunes.

### P1 - La configuracion `pyproject.toml` mezcla dependencias de ejecucion, desarrollo y visualizacion

`pytest` aparece como dependencia principal en `pyproject.toml:10` a `pyproject.toml:17`, aunque es una dependencia de desarrollo. `plotly` tambien es dependencia principal por la visualizacion HTML, pero no esta justificada en el propio `pyproject.toml` ni separada como extra opcional. El proyecto exige `requires-python = ">=3.13"` en `pyproject.toml:9`, lo que reduce portabilidad academica y puede complicar reproduccion en equipos del tribunal.

Riesgo: instalacion mas pesada de lo necesario, menor portabilidad y mas superficie de cambios por dependencias. Aunque `uv.lock` mejora la reproducibilidad, la especificacion del proyecto no distingue claramente entorno minimo, entorno de desarrollo y entorno de visualizacion.

Recomendacion: mover `pytest` a un grupo de desarrollo de `uv`; valorar `plotly` como extra de visualizacion si se quiere mantener un entorno minimo; documentar por que Python 3.13 es necesario o bajar a una version comun si no hay dependencia real de 3.13.

### P1 - La reproducibilidad experimental no registra version exacta del codigo ni entorno

El CLI guarda nombre de escenario, semilla y configuracion completa en metadatos en `src/simulador_quad/app.py:49` a `src/simulador_quad/app.py:53`. Esto es positivo, pero no registra commit Git, estado dirty, version del paquete, version de Python, hash de `uv.lock` ni comando ejecutado.

Riesgo: dos resultados con el mismo YAML pueden no ser equivalentes si cambian codigo, dependencias o version de Python. Para un tribunal, esto dificulta demostrar que una figura de la memoria sale exactamente de una revision concreta.

Recomendacion: ampliar `metadata` con `package_version`, `python_version`, `platform`, `git_commit`, `git_dirty`, `uv_lock_hash` y `command`. Si Git no esta disponible, registrar `"unknown"` en vez de fallar.

### P2 - Las metricas mezclan magnitudes fisicas con unidades incompatibles

`compute_metrics` calcula el esfuerzo como `abs(T) + ||tau||` en `src/simulador_quad/metrics/report.py:25` a `src/simulador_quad/metrics/report.py:27`, y exporta `control_effort_mean`, `control_effort_max` y `control_effort_std` en `src/simulador_quad/metrics/report.py:48` a `src/simulador_quad/metrics/report.py:50`. Esa suma mezcla newtons y newton-metro.

Riesgo: la metrica agregada es util como indicador interno, pero no tiene unidad fisica interpretable. Puede inducir conclusiones debiles al comparar controladores.

Recomendacion: separar metricas dimensionales: empuje medio/maximo en N, norma de momentos media/maxima en Nm, velocidades de rotor, energia o proxy normalizado si se justifica. Si se mantiene el agregado, nombrarlo como indice adimensional o heuristico y documentar su limitacion.

### P2 - Hay duplicacion conceptual en el calculo de drag lineal

Existe `compute_linear_drag` en `src/simulador_quad/dynamics/perturbations.py:5` a `src/simulador_quad/dynamics/perturbations.py:21`, pero `compute_state_derivative` implementa de nuevo el drag dentro de `src/simulador_quad/dynamics/rigid_body.py:29` a `src/simulador_quad/dynamics/rigid_body.py:34`. Ademas, `runner.py` importa `compute_linear_drag` en `src/simulador_quad/runner.py:8`, pero no lo usa.

Riesgo: dos implementaciones pueden divergir en signos, marcos o unidades. En software cientifico simple conviene que una ecuacion fisica importante tenga una unica fuente ejecutable.

Recomendacion: dejar una sola implementacion del drag. Preferible que `rigid_body.py` llame a una funcion pura documentada, o mover la formula al nucleo dinamico y eliminar el helper no usado.

### P2 - Algunos limites de terminacion existen en codigo pero no son configurables desde YAML

`SimulationRunner` acepta `max_position_m` y `max_velocity_m_s` en `src/simulador_quad/runner.py:22` a `src/simulador_quad/runner.py:24`, y los aplica en `src/simulador_quad/runner.py:67` a `src/simulador_quad/runner.py:73`. El CLI solo carga duracion, altura, actitud y saturacion en `src/simulador_quad/app.py:30` a `src/simulador_quad/app.py:33`.

Riesgo: dos experimentos pueden tener limites internos importantes no visibles en el YAML. La documentacion ya advierte esta limitacion, pero desde reproducibilidad experimental sigue siendo un punto debil.

Recomendacion: declarar `max_position_m` y `max_velocity_m_s` en todos los escenarios YAML o documentar sus valores por defecto dentro del `metrics.metadata.config_resolved`.

### P2 - El runner guarda objetos mutables en telemetria sin copia profunda completa

En `src/simulador_quad/runner.py:181` a `src/simulador_quad/runner.py:198`, el estado se copia manualmente, pero `observation`, `reference`, `rotor_command` y `rotor_applied` se guardan como objetos existentes. Actualmente muchas asignaciones crean objetos nuevos por ciclo, pero el contrato no protege frente a mutaciones futuras.

Riesgo: un cambio posterior que reutilice arrays por rendimiento podria corromper muestras historicas de telemetria. Es un fallo tipico en codigo cientifico con NumPy.

Recomendacion: crear funciones pequenas `copy_vehicle_state`, `copy_control_command`, `copy_rotor_command`, `copy_rotor_applied` o un constructor de `TelemetrySample` que congele una muestra con copias defensivas.

### P2 - El README raiz esta vacio

`pyproject.toml` declara `readme = "README.md"` en `pyproject.toml:5`, pero `README.md` raiz esta vacio. La documentacion util esta en `docs/simulador/README.md`.

Riesgo: quien abra el repositorio o el paquete instalado no ve los comandos minimos ni el estado actual. Esto perjudica la reproducibilidad inmediata ante un tribunal.

Recomendacion: convertir el README raiz en una entrada corta que enlace a `docs/simulador/README.md`, indique `uv sync`, `uv run pytest` y un escenario minimo.

### P3 - Uso de `assert` para validacion de configuracion

`QuadcopterMixer` usa `assert self.num_rotors == 4` en `src/simulador_quad/dynamics/mixer.py:11` a `src/simulador_quad/dynamics/mixer.py:13`.

Riesgo: `assert` puede desactivarse con optimizacion de Python y no da un mensaje de error consistente para usuarios tecnicos.

Recomendacion: reemplazar por `if self.num_rotors != 4: raise ValueError(...)` con contexto de numero recibido y requisito.

### P3 - Docstrings utiles pero insuficientes en funciones criticas

Hay docstrings breves en actitud, dinamica, actuadores y runner, pero varias funciones criticas no documentan completamente entradas, unidades, marco y errores. Ejemplos: `compute_state_derivative` en `src/simulador_quad/dynamics/rigid_body.py:5` a `src/simulador_quad/dynamics/rigid_body.py:21`, `rk4_step` en `src/simulador_quad/dynamics/rigid_body.py:52` a `src/simulador_quad/dynamics/rigid_body.py:68`, y `ClassicCascadeController.compute_control` en `src/simulador_quad/control/classic.py:27`.

Riesgo: la implementacion es legible para un programador, pero un lector de ingenieria aeroespacial necesita ver explicitamente ENU/FRD, unidades y supuestos junto a las funciones que sostienen la validez del TFG.

Recomendacion: completar docstrings solo en funciones fisicas y experimentales principales. No documentar auxiliares triviales.

## Riesgos transversales

- Resultados reproducibles pero no auditables: el YAML y la semilla se guardan, pero falta versionado del codigo y entorno.
- Errores tardios por configuracion: el uso directo de diccionarios YAML y arrays sin validacion puede hacer que fallos simples aparezcan dentro de algebra lineal o integracion.
- Deriva entre documentacion e implementacion: hay buena documentacion, pero la ausencia de validadores y de un `config_resolved` exportado deja algunos valores efectivos fuera del YAML.
- Alcance incompleto para la memoria final: sin controlador neuronal, dataset y evaluacion cerrada, el proyecto aun no cumple el objetivo comparativo completo.

## Recomendaciones concretas por orden de retorno

1. Anadir validacion minima de escenarios y dataclasses criticas: dimensiones `[3]`, quaternion `[4]` normalizable, masa positiva, inercia `3x3`, `k_f > 0`, `omega_max > 0`, tiempos positivos y relaciones razonables entre `physics_dt_s`, `control_dt_s` y `telemetry_dt_s`.
2. Exportar metadatos de reproducibilidad: version de paquete, Python, plataforma, commit, dirty flag, hash de `uv.lock`, comando y configuracion resuelta con defaults.
3. Separar dependencias de runtime y desarrollo en `pyproject.toml`; justificar o relajar Python 3.13 si no es imprescindible.
4. Corregir metricas de esfuerzo para no mezclar N y Nm sin normalizacion documentada.
5. Unificar el calculo de drag lineal en una unica funcion usada por la dinamica.
6. Hacer configurables desde YAML todos los limites de terminacion aplicados por el runner, o exportar explicitamente sus defaults.
7. Crear un README raiz minimo orientado a reproduccion.
8. Planificar el flujo neuronal minimo reproducible antes de aumentar complejidad: dataset trazable, normalizacion, entrenamiento con semilla, checkpoint, carga desde YAML y evaluacion en bucle cerrado.

## Criterio de aceptacion sugerido

Para considerar robusta la parte de software cientifico simple antes de la defensa, el repositorio deberia permitir que una persona externa ejecute:

```powershell
uv sync
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
```

y obtenga resultados con metadatos suficientes para reconstruir codigo, entorno, escenario, semilla, parametros efectivos, telemetria y metricas. Para la version final del TFG, el mismo flujo deberia existir tambien para al menos un escenario clasico y uno neuronal en bucle cerrado.
