# Tasks: Subsanacion de Findings del Simulador

## Regla de Ejecucion

Todo el trabajo se ejecutara de forma secuencial. No hay tareas paralelas. Cada tarea debe completarse y verificarse antes de pasar a la siguiente.

## Tareas

- [ ] Task 1: Fijar la convencion fisica del mixer
  - Acceptance: `QuadcopterMixer` usa una matriz de asignacion coherente con `F_i_B=[0,0,-T_i]`, `tau_x=-y_i T_i`, `tau_y=x_i T_i` y `tau_z=s_i(k_m/k_f)T_i`.
  - Acceptance: Los comentarios del mixer documentan la misma convencion que implementa el codigo.
  - Verify: `uv run python -m pytest tests\test_mixer.py`
  - Files: `src/simulador_quad/dynamics/mixer.py`, `tests/test_mixer.py`

- [ ] Task 2: Alinear actuadores con la convencion de par y empuje
  - Acceptance: `ActuatorSystem` calcula `F_i_B=[0,0,-T_i]`, `Q_i=s_i k_m omega_i^2`, torque por posicion `r_i x F_i` y torque total coherente con el mixer.
  - Acceptance: La prueba de un rotor aislado valida signo de torque posicional y torque de reaccion.
  - Verify: `uv run python -m pytest tests\test_actuators.py`
  - Files: `src/simulador_quad/dynamics/actuators.py`, `tests/test_actuators.py`

- [ ] Task 3: Corregir el lag discreto de primer orden
  - Acceptance: El lag usa `alpha = 1 - exp(-dt_s / tau_s)` cuando `tau_s > 0`.
  - Acceptance: Si `tau_s <= 0`, la salida sigue el comando retrasado sin filtrado.
  - Acceptance: El retardo puro de `N` pasos sigue cubierto por tests.
  - Verify: `uv run python -m pytest tests\test_actuators.py`
  - Files: `src/simulador_quad/dynamics/actuators.py`, `tests/test_actuators.py`

- [ ] Task 4: Extender contratos de rotor, telemetria y flags
  - Acceptance: Los contratos distinguen empuje objetivo por rotor, omega objetivo, omega aplicada, RPM, empuje aplicado, par aplicado y flags de saturacion/degradacion.
  - Acceptance: `TelemetrySample` incluye observacion usada por el controlador y campos suficientes para causa de terminacion.
  - Verify: `uv run python -m pytest tests\test_metrics.py tests\test_runner.py`
  - Files: `src/simulador_quad/core/contracts.py`, tests relacionados

- [ ] Task 5: Hacer que mixer y actuadores produzcan informacion trazable
  - Acceptance: El mixer devuelve o permite registrar empuje objetivo por rotor, omega objetivo y degradacion de empuje colectivo.
  - Acceptance: Los actuadores devuelven omega aplicada, RPM, empuje aplicado, par aplicado y flags de saturacion por rotor.
  - Verify: `uv run python -m pytest tests\test_mixer.py tests\test_actuators.py`
  - Files: `src/simulador_quad/dynamics/mixer.py`, `src/simulador_quad/dynamics/actuators.py`, `tests/test_mixer.py`, `tests/test_actuators.py`

- [ ] Task 6: Registrar observacion y telemetria completa en el runner
  - Acceptance: Cada muestra de telemetria guarda estado verdadero, observacion, referencia, comando solicitado y comando aplicado por rotor.
  - Acceptance: La observacion se guarda incluso si no hay ruido y coincide numericamente con el estado verdadero.
  - Verify: `uv run python -m pytest tests\test_runner.py`
  - Files: `src/simulador_quad/runner.py`, `tests/test_runner.py`

- [ ] Task 7: Implementar terminacion por saturacion persistente
  - Acceptance: El runner acumula duracion de saturacion/degradacion.
  - Acceptance: El umbral se configura en segundos desde `termination`.
  - Acceptance: La causa `Persistent actuator saturation` aparece cuando se supera el umbral.
  - Verify: `uv run python -m pytest tests\test_runner.py`
  - Files: `src/simulador_quad/runner.py`, `src/simulador_quad/scenarios/loader.py`, `tests/test_runner.py`

- [ ] Task 8: Exportar telemetria JSON completa
  - Acceptance: `export_telemetry_json` incluye estado, observacion, referencia, control, empuje objetivo, omega objetivo, omega aplicada, RPM, empuje aplicado, par aplicado, flags y causa de terminacion si aplica.
  - Acceptance: El JSON sigue siendo legible y no pierde campos existentes.
  - Verify: `uv run python -m pytest tests\test_metrics.py`
  - Files: `src/simulador_quad/telemetry/export.py`, `tests/test_metrics.py`

- [ ] Task 9: Completar metricas de comparacion y saturacion
  - Acceptance: Las metricas incluyen RMSE, MAE, error maximo, esfuerzo medio y maximo, velocidad maxima de rotor, porcentaje de tiempo en saturacion, causa y tiempo de terminacion, metadatos de escenario/controlador/semilla y parametros relevantes disponibles.
  - Acceptance: La saturacion no se confunde con lag; se calcula desde flags.
  - Verify: `uv run python -m pytest tests\test_metrics.py`
  - Files: `src/simulador_quad/metrics/report.py`, `tests/test_metrics.py`

- [ ] Task 10: Anadir saturacion de momentos al controlador clasico
  - Acceptance: `ClassicCascadeController` limita `body_moments_Nm` por eje.
  - Acceptance: Los limites pueden venir de YAML como `controller.max_body_moments_Nm`.
  - Acceptance: Si faltan limites en YAML, se usan defaults conservadores documentados.
  - Verify: `uv run python -m pytest tests\test_control.py`
  - Files: `src/simulador_quad/control/classic.py`, `src/simulador_quad/scenarios/loader.py`, `tests/test_control.py`

- [ ] Task 11: Implementar `LineTrajectory` con smoothstep cubico
  - Acceptance: La trayectoria lineal acepta inicio, fin, duracion o velocidad, y yaw.
  - Acceptance: Posicion y velocidad son continuas, finitas y acotadas.
  - Acceptance: La aceleracion devuelta es finita.
  - Verify: `uv run python -m pytest tests\test_trajectories.py`
  - Files: `src/simulador_quad/trajectories/analytic.py`, `tests/test_trajectories.py`

- [ ] Task 12: Cargar trayectoria `line` desde YAML
  - Acceptance: `instantiate_scenario` acepta `trajectory.type: line`.
  - Acceptance: Errores de configuracion de `line` producen mensajes comprensibles.
  - Verify: `uv run python -m pytest tests\test_trajectories.py`
  - Files: `src/simulador_quad/scenarios/loader.py`, `tests/test_trajectories.py`

- [ ] Task 13: Ajustar escenarios para nuevos campos trazables
  - Acceptance: Los escenarios existentes declaran, cuando aplique, `controller.max_body_moments_Nm` y `termination.max_saturation_duration_s`.
  - Acceptance: `circle_noisy_wind` queda como escenario de seguimiento robusto y no como fallo prematuro.
  - Verify: `uv run simulador-quad run scenarios\hover_clean.yaml`; `uv run simulador-quad run scenarios\circle_drag.yaml`; `uv run simulador-quad run scenarios\circle_noisy_wind.yaml`
  - Files: `scenarios/hover_clean.yaml`, `scenarios/circle_drag.yaml`, `scenarios/circle_noisy_wind.yaml`

- [ ] Task 14: Ejecutar suite completa y corregir regresiones
  - Acceptance: La suite completa pasa sin fallos.
  - Acceptance: No quedan tests obsoletos que validen la convencion antigua.
  - Verify: `uv run pytest`
  - Files: `tests/*`, modulos necesarios segun regresiones encontradas

- [ ] Task 15: Verificacion final de escenarios y resultados
  - Acceptance: Los tres escenarios generan telemetria y metricas reproducibles.
  - Acceptance: `hover_clean` y `circle_drag` llegan al limite de tiempo sin fallo fisico.
  - Acceptance: `circle_noisy_wind` no termina prematuramente por actitud, saturacion persistente o valores no finitos.
  - Verify: `uv run simulador-quad run scenarios\hover_clean.yaml`; `uv run simulador-quad run scenarios\circle_drag.yaml`; `uv run simulador-quad run scenarios\circle_noisy_wind.yaml`
  - Files: `results/*` generados por ejecucion, sin depender de ellos como fuente principal del sistema

## Criterio para Pasar a IMPLEMENT

Se puede pasar a implementacion cuando esta lista de tareas sea aprobada. Durante implementacion, las tareas se ejecutaran una por una en el orden indicado.
