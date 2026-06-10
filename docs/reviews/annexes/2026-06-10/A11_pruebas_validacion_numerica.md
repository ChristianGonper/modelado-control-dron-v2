# Anexo A11 — Pruebas y validación numérica

**Fecha:** 2026-06-10 | **Owner:** A11

## Superficie revisada

`tests/` (33 ficheros), `docs/simulador/trazabilidad.md`, `docs/simulador/validacion.md`, correspondencia requisito-prueba.

## Invariantes y contratos comprobados

- Suite completa 151 tests, 0 fallos.
- Cobertura neuronal sustancial (≈58 tests en módulos neural_*).
- Regresión escenario corto (`test_model_regressions.py`).

## Hallazgos referenciados (otros dominios)

F-006, F-007 (A03); ninguno propietario A11 adicional.

## Históricos revalidados

- ~29 tests (mayo): **obsoleto** — 151 tests.

## No verificable

- Cobertura línea % (no medida en auditoría).

## Zonas sin problemas

- Todos los módulos `tests/test_*.py` importan sin error en collect.
- Parametrización escenarios (`test_scenarios.py` 18 collect).

## Comandos — salida verbatim pytest

```
........................................................................ [ 47%]
........................................................................ [ 95%]
.......                                                                  [100%]
151 passed in 74.77s (0:01:14)
```

Collect-only: `151 tests collected in 1.74s`.

## Conteo exacto por fichero (33 archivos, 151 total)

| Fichero | Tests |
|---------|-------|
| test_actuators.py | 4 |
| test_app_metadata.py | 1 |
| test_attitude.py | 5 |
| test_campaign_scripts.py | 3 |
| test_classic_controller_config.py | 3 |
| test_classic_dataset_generation.py | 5 |
| test_classic_dataset_scripts.py | 2 |
| test_classic_pid_selection.py | 2 |
| test_classic_pid_tuning.py | 12 |
| test_composite_trajectory.py | 4 |
| test_control.py | 3 |
| test_dynamics.py | 6 |
| test_evaluate_ood_split.py | 5 |
| test_generate_ood_battery.py | 3 |
| test_metrics.py | 2 |
| test_mixer.py | 3 |
| test_model_regressions.py | 1 |
| test_neural_batch_tools.py | 7 |
| test_neural_controller.py | 1 |
| test_neural_dataset.py | 10 |
| test_neural_evaluation.py | 1 |
| test_neural_imports.py | 3 |
| test_neural_models.py | 4 |
| test_neural_outer_force.py | 11 |
| test_neural_position_control.py | 7 |
| test_neural_training.py | 2 |
| test_outer_force_generation_integration.py | 2 |
| test_perturbations.py | 3 |
| test_runner.py | 7 |
| test_scenarios.py | 18 |
| test_telemetry_desired_force.py | 2 |
| test_trajectories.py | 7 |
| test_visualization.py | 2 |
| **TOTAL** | **151** |

## Matriz de trazabilidad requisito → prueba (28 filas)

| # | Requisito (trazabilidad.md) | Prueba(s) primaria(s) | Estado evidencia |
|---|----------------------------|------------------------|------------------|
| 1 | Mundo ENU y cuerpo FRD | test_attitude.py | E3 OK |
| 2 | Empuje en -Z_B | test_attitude.py, test_actuators.py | E3 OK |
| 3 | Estado 6DOF mínimo | test_runner.py, test_dynamics.py | E3 OK |
| 4 | Cuaterniones unitarios | test_attitude.py, test_dynamics.py | E3 OK |
| 5 | Dinámica translacional gravedad ENU | test_dynamics.py | E3 OK |
| 6 | Dinámica rotacional Newton-Euler | test_dynamics.py, test_runner.py | E3 parcial |
| 7 | Integración RK4 | test_dynamics.py, test_runner.py | E3 OK |
| 8 | Multi-rate y ZOH | test_runner.py | E3 OK |
| 9 | Mixer cuadricóptero | test_mixer.py | E3 OK |
| 10 | Actuadores lag/delay/sat | test_actuators.py, test_runner.py | E3 OK |
| 11 | Drag lineal | test_perturbations.py | E3 OK |
| 12 | Viento y ruido observación | test_perturbations.py, test_runner.py | E3 OK |
| 13 | Controlador clásico cascada | test_control.py | E3 OK |
| 14 | Ganancias configurables YAML | test_classic_controller_config.py | E3 OK |
| 15 | Trayectorias analíticas/waypoint | test_trajectories.py | E3 OK |
| 16 | Trayectorias compuestas OOD | test_composite_trajectory.py | E3 OK |
| 17 | Escenarios YAML validación | test_scenarios.py | E3 OK |
| 18 | Telemetría JSON | test_metrics.py, test_visualization.py | E3 OK |
| 19 | Métricas JSON unidades | test_metrics.py | E3 OK |
| 20 | Terminación episodio | test_runner.py | E3 OK |
| 21 | Visualización postproceso | test_visualization.py, test_model_regressions.py | E3 OK |
| 22 | Reproducibilidad metadata | test_app_metadata.py | E3 diseño; E5 F-003 |
| 23 | Dataset clásico versionado | test_classic_dataset_*.py | E3 OK; E5 local |
| 24 | Dataset outer-force experto | test_neural_dataset.py, test_outer_force_generation_integration.py | E3 OK |
| 25 | Control neural outer-force | test_neural_outer_force.py | E3 OK |
| 26 | Control neural_position | test_neural_position_control.py | E3 OK; E4 F-004 |
| 27 | Evaluación OOD neuronal | test_evaluate_ood_split.py, test_neural_batch_tools.py | E3 OK; E5 parcial |
| 28 | Telemetría fuerza y viento | test_telemetry_desired_force.py | E3 OK |

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A02 | ¿Cada requisito normativo con prueba? | 28/28 con al menos una prueba |
| A03 | ¿Huecos física numérica? | F-007 sin dt-study |
| A10 | ¿Tests campaña? | test_campaign_scripts.py 3 tests |