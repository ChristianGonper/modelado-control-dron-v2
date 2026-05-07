# Trazabilidad del simulador clasico

Esta matriz conecta requisitos del TFG con modelo, implementacion, pruebas, escenarios y metricas. Su objetivo es hacer auditable el estado actual del simulador clasico.

Estados usados:

- `Implementado`: existe implementacion y evidencia basica.
- `Parcial`: existe implementacion, pero falta validacion, metadata, documentacion o cobertura suficiente.
- `Pendiente`: requisito previsto pero no disponible en la version actual.

## Matriz requisito-modelo-codigo-prueba-escenario-metrica

| Requisito | Justificacion | Codigo | Prueba | Escenario | Metrica / evidencia | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| Mundo ENU y cuerpo FRD | Fijar signos y marcos para que empuje, gravedad y momentos sean interpretables. | `src/simulador_quad/core/frames.py`, `src/simulador_quad/core/attitude.py`, `src/simulador_quad/core/contracts.py` | `tests/test_attitude.py` | `scenarios/hover_clean.yaml` | Convencion documentada y prueba de signo de empuje. | Implementado |
| Empuje en `-Z_B` | En FRD el eje `Z_B` apunta hacia abajo; el empuje sustentador actua en `-Z_B`. | `src/simulador_quad/dynamics/actuators.py`, `src/simulador_quad/dynamics/rigid_body.py` | `tests/test_attitude.py`, `tests/test_actuators.py` | `scenarios/hover_clean.yaml` | Hover y tests de fuerza aplicada. | Parcial |
| Estado 6DOF minimo | Representar posicion, velocidad, actitud y velocidad angular para cuerpo rigido. | `src/simulador_quad/core/contracts.py`, `src/simulador_quad/runner.py` | `tests/test_runner.py`, `tests/test_dynamics.py` | Todos los escenarios YAML | Telemetria exportada con `state`. | Implementado |
| Cuaterniones unitarios | Evitar singularidades de Euler y conservar actitud valida. | `src/simulador_quad/core/attitude.py`, `src/simulador_quad/dynamics/rigid_body.py` | `tests/test_attitude.py`, `tests/test_dynamics.py` | `scenarios/hover_clean.yaml`, `scenarios/circle_drag.yaml` | Norma normalizada en integracion. | Parcial |
| Dinamica translacional con gravedad ENU | Asegurar aceleracion vertical y equilibrio de hover coherentes. | `src/simulador_quad/dynamics/rigid_body.py` | `tests/test_dynamics.py` | `scenarios/hover_clean.yaml` | Terminacion por tiempo y error de posicion. | Implementado |
| Dinamica rotacional Newton-Euler | Simular momentos de cuerpo y acoplamiento giroscopico. | `src/simulador_quad/dynamics/rigid_body.py` | `tests/test_dynamics.py` | Escenarios con seguimiento de trayectoria | Estabilidad y ausencia de fallo por actitud. | Parcial |
| Integracion RK4 | Cumplir integrador oficial y separar fisica/control/telemetria. | `src/simulador_quad/dynamics/rigid_body.py`, `src/simulador_quad/runner.py` | `tests/test_dynamics.py`, `tests/test_runner.py` | Todos los escenarios YAML | Duracion y telemetria con paso definido. | Implementado |
| Simulacion multi-rate y ZOH | Controlar con `control_dt_s`, integrar con `physics_dt_s` y registrar con `telemetry_dt_s`. | `src/simulador_quad/runner.py` | `tests/test_runner.py` | Todos los escenarios YAML | Numero de llamadas y muestras de telemetria. | Parcial |
| Mixer de cuadricoptero | Convertir empuje colectivo y momentos en comandos de rotor. | `src/simulador_quad/dynamics/mixer.py` | `tests/test_mixer.py` | `scenarios/hover_clean.yaml`, `scenarios/circle_drag.yaml` | `rotor_command` y degradacion colectiva. | Parcial |
| Actuadores con `omega`, saturacion, retardo y lag | Distinguir comando objetivo y actuacion aplicada. | `src/simulador_quad/dynamics/actuators.py`, `src/simulador_quad/core/contracts.py` | `tests/test_actuators.py`, `tests/test_runner.py` | Todos los escenarios YAML | `rotor_applied`, `saturation_percentage`. | Implementado |
| Drag lineal simplificado | Introducir disipacion compatible con alcance limitado, sin aerodinamica formal. | `src/simulador_quad/dynamics/perturbations.py`, `src/simulador_quad/dynamics/rigid_body.py` | `tests/test_perturbations.py` | `scenarios/circle_drag.yaml` | Error de seguimiento con drag activo. | Parcial |
| Viento constante y ruido de observacion | Evaluar perturbaciones simples sin sensores realistas. | `src/simulador_quad/dynamics/perturbations.py`, `src/simulador_quad/runner.py` | `tests/test_perturbations.py`, `tests/test_runner.py` | `scenarios/circle_noisy_wind.yaml` | Metadata de semilla y observacion exportada. | Parcial |
| Controlador clasico en cascada | Baseline interpretable para seguimiento y futura imitacion. | `src/simulador_quad/control/classic.py`, `src/simulador_quad/control/contract.py` | `tests/test_control.py` | Todos los escenarios actuales | RMSE, MAE, error maximo y esfuerzo. | Parcial |
| Trayectorias analiticas o suavizadas | Dar referencias reproducibles con posicion, velocidad y aceleracion. | `src/simulador_quad/trajectories/analytic.py`, `src/simulador_quad/scenarios/loader.py` | `tests/test_trajectories.py` | `hover_clean`, `circle_drag`, `lissajous_clean`, `waypoint_clean` | Error de seguimiento por escenario. | Implementado |
| Escenarios YAML reproducibles | Separar parametros experimentales del codigo. | `src/simulador_quad/scenarios/loader.py`, `scenarios/*.yaml` | `tests/test_runner.py`, pruebas manuales CLI | Todos los escenarios YAML | `metrics.metadata.config`. | Parcial |
| Telemetria JSON | Registrar estado, observacion, referencia, comando y rotores. | `src/simulador_quad/core/contracts.py`, `src/simulador_quad/telemetry/export.py` | `tests/test_metrics.py`, `tests/test_visualization.py` | Todos los escenarios YAML | `telemetry.json`. | Implementado |
| Metricas JSON | Resumir seguimiento, empuje, momentos, saturacion, degradacion y terminacion con unidades explicitas. | `src/simulador_quad/metrics/report.py` | `tests/test_metrics.py` | Todos los escenarios YAML | `position_rmse_m`, `collective_thrust_*_N`, `body_moment_norm_*_Nm`, `saturation_percentage`, `degradation_percentage`, `termination_reason`. | Implementado |
| Terminacion de episodio | Marcar fallos por altura, actitud, limites, no finitos o saturacion persistente. | `src/simulador_quad/runner.py` | `tests/test_runner.py` | Escenarios nominales y futuros escenarios de fallo | `termination_reason`, `termination_cause`. | Parcial |
| Visualizacion postproceso | Generar figuras y visor 3D para inspeccion de resultados. | `src/simulador_quad/visualization/plots.py`, `src/simulador_quad/visualization/three_d.py` | `tests/test_visualization.py` | Resultados de cualquier escenario | Figuras PNG y `visualization_3d.html`. | Implementado |
| Reproducibilidad fuerte de ejecucion | Vincular resultados con codigo, entorno y comando exacto. | `src/simulador_quad/app.py`, `src/simulador_quad/metrics/report.py` | `tests/test_app_metadata.py` | Todos los escenarios oficiales | Metadata de commit, entorno, comando, hashes y configuracion efectiva. | Implementado |
| Control neuronal por imitacion | Objetivo final de comparacion del TFG. | Pendiente | Pendiente | Pendiente | Dataset, entrenamiento y evaluacion cerrada. | Pendiente |

## Lectura recomendada

Para auditar un resultado concreto:

1. Revisar el YAML en `scenarios/`.
2. Ejecutar el escenario con `uv run simulador-quad run`.
3. Consultar `metrics.json` para terminacion, errores y saturacion.
4. Consultar `telemetry.json` y figuras para diagnostico temporal.
5. Cruzar el requisito correspondiente en esta matriz.

## Deudas documentadas

- Reforzar validacion de parametros fisicos de escenarios.
- Mantener la lectura de metricas por unidades fisicas; `control_effort_heuristic_*` queda solo como diagnostico heredado.
- Revisar que la metadata de entorno y commit se conserva en todos los resultados finales de memoria.
- Reforzar pruebas de convenciones ENU/FRD con actitudes no triviales.
- Mantener control neuronal como fase futura hasta que exista evaluacion en bucle cerrado.
