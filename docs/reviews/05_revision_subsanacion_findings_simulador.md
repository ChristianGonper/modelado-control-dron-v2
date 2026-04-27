# Revision de Subsanacion de Findings del Simulador

## Resultado

La subsanacion no esta completa. Aunque `uv run pytest` pasa, todavia hay incumplimientos contra la spec aprobada y contra los criterios de aceptacion de escenarios.

## Verificacion Ejecutada

```powershell
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml
uv run simulador-quad run scenarios\circle_drag.yaml
uv run simulador-quad run scenarios\circle_noisy_wind.yaml
```

Resultados observados:

- `uv run pytest`: pasa con 27 tests.
- `hover_clean`: termina por `Time limit reached`.
- `circle_drag`: termina prematuramente a 0.90 s con `Persistent actuator saturation`.
- `circle_noisy_wind`: termina prematuramente a 0.30 s por `Attitude angle exceeded limit`.

## Findings

### Finding 1: [P1] Escenarios de aceptacion siguen fallando

Archivo: `scenarios/circle_drag.yaml`

La verificacion final exigia que `circle_drag` y `circle_noisy_wind` no terminasen prematuramente. Al ejecutar la CLI, `circle_drag` termina a los 0.90 s con `Persistent actuator saturation` y `circle_noisy_wind` termina a los 0.30 s por actitud excesiva.

Por tanto, la tarea no puede darse por subsanada aunque la suite unitaria pase.

### Finding 2: [P1] Falta `LineTrajectory` y soporte YAML `line`

Archivo: `src/simulador_quad/trajectories/analytic.py`

La spec aprobada pedia `LineTrajectory` con smoothstep cubico y `trajectory.type: line`. En su lugar se anadio `WaypointTrajectory` con interpolacion lineal por tramos, que ademas documenta aceleracion infinita en waypoints.

El loader tampoco acepta `type: line`, asi que las tareas 11 y 12 no estan completadas.

### Finding 3: [P2] El loader referencia `WaypointTrajectory` sin importarla

Archivo: `src/simulador_quad/scenarios/loader.py`

Si aparece un escenario con `trajectory.type: waypoint`, esta rama intentara construir `WaypointTrajectory`, pero el nombre no esta importado desde `simulador_quad.trajectories.analytic`.

Los tests instancian la clase directamente y no cubren la carga YAML, por eso la suite pasa pese a este fallo.

### Finding 4: [P2] Los limites de momento del controlador no se cargan desde YAML

Archivo: `src/simulador_quad/scenarios/loader.py`

La decision aprobada fue declarar `controller.max_body_moments_Nm` en YAML con defaults conservadores. El loader ignora cualquier parametro de controlador y construye `ClassicCascadeController` solo con masa, gravedad e inercia.

Ademas, los escenarios no declaran el campo. Esto impide ajustar de forma trazable las saturaciones que ahora condicionan los escenarios.

### Finding 5: [P2] Metricas incompletas respecto a la spec

Archivo: `src/simulador_quad/metrics/report.py`

La spec pedia porcentaje de tiempo en saturacion, esfuerzo medio y maximo, y parametros relevantes. El reporte actual guarda duraciones de saturacion/degradacion y esfuerzo medio/std, pero no porcentaje ni esfuerzo maximo ni parametros relevantes del escenario, vehiculo o controlador.

## Criterio de Cierre

La subsanacion puede considerarse completa cuando:

1. `uv run pytest` siga pasando.
2. Los tres escenarios de aceptacion ejecuten con la CLI.
3. `hover_clean`, `circle_drag` y `circle_noisy_wind` generen telemetria y metricas reproducibles.
4. `circle_drag` y `circle_noisy_wind` no terminen prematuramente por saturacion persistente, actitud excesiva o no finitos.
5. Exista `LineTrajectory` con smoothstep cubico y soporte `trajectory.type: line` desde YAML.
6. `controller.max_body_moments_Nm` se pueda declarar en YAML y se use al construir el controlador.
7. Las metricas incluyan porcentaje de saturacion, esfuerzo maximo y parametros relevantes.

