# Spec: Waypoint stop como trayectoria por defecto

## Objective

Sustituir la trayectoria `line` / `waypoint` actual por una trayectoria de puntos con parada controlada en cada waypoint. El comportamiento por defecto de `trajectory.type: "waypoint"` y `trajectory.type: "line"` sera `waypoint_stop`: una secuencia de tramos punto a punto donde el vehiculo debe llegar, frenar, permanecer estable y solo entonces avanzar al siguiente waypoint.

Esta trayectoria complementa a `hold`, `circle` y `lissajous`:

- `hold`: referencia estacionaria.
- `circle`: referencia continua periodica.
- `lissajous`: referencia continua suave 3D.
- `waypoint` / `line`: mision discreta de alcanzar puntos con parada en cada vertice.

El cambio pertenece a la generacion de referencia y a la terminacion de trayectorias finitas. No cambia la dinamica 6DOF, el controlador clasico, el mixer, los actuadores ni la arquitectura del dataset neuronal futuro.

## Current Problem

La trayectoria waypoint existente usa interpolacion temporal entre waypoints. Aunque puede incluir velocidad cero en los extremos, la referencia avanza segun el tiempo y no segun la llegada real del vehiculo. En la practica, el dron puede llegar con energia lateral al vertice, pasarse de largo, corregir con curvas amplias y aun asi continuar hacia el siguiente tramo.

Una guia tipo lookahead sobre la polilinea mejora el seguimiento del segmento, pero no garantiza una llegada limpia al waypoint. Para una trayectoria cuyo significado es "alcanzar estos puntos", la referencia debe planificar explicitamente salida, avance, frenado y asentamiento.

## Desired Behavior

`waypoint` sera una trayectoria stateful con fases por tramo:

```text
MOVE_TO_WAYPOINT -> HOLD_AT_WAYPOINT -> SWITCH_SEGMENT
```

Para cada tramo `waypoints[i] -> waypoints[i + 1]`:

1. Se genera una referencia sobre la recta entre ambos puntos.
2. La referencia usa un perfil de movimiento con velocidad y aceleracion limitadas.
3. La referencia llega al waypoint de destino con velocidad cero.
4. El vehiculo mantiene un hold sobre el waypoint hasta cumplir tolerancias de posicion, velocidad y dwell.
5. Solo entonces la trayectoria pasa al siguiente tramo.

No se redondean esquinas y no se implementa seguimiento continuo sin parada. Esos modos quedan fuera de esta implementacion.

## YAML Interface

### Default waypoint stop

El YAML publico actual sigue siendo valido:

```yaml
trajectory:
  type: "waypoint"
  waypoints:
    - [0, 0, 0]
    - [0, 0, 2]
    - [2, 0, 2]
    - [2, 2, 2]
  yaw_rad: 0.0
```

Tambien sigue siendo valido:

```yaml
trajectory:
  type: "line"
```

`line` sera un alias de `waypoint` con comportamiento `waypoint_stop`.

### Deprecated `times`

`times` queda deprecated para `waypoint` / `line`.

Si aparece en un YAML existente:

- no debe romper la carga del escenario;
- no debe usarse para cambiar de waypoint;
- no debe hacer avanzar la referencia si el vehiculo no ha llegado;
- puede ignorarse o usarse solo como compatibilidad documental para estimar una velocidad nominal si no se declara `max_speed_m_s`;
- debe documentarse como campo heredado.

Ejemplo legacy aceptado:

```yaml
trajectory:
  type: "waypoint"
  waypoints:
    - [0, 0, 0]
    - [0, 0, 2]
    - [2, 0, 2]
  times: [0, 5, 10]  # deprecated
  yaw_rad: 0.0
```

### New optional parameters

La nueva version expone parametros opcionales simples:

```yaml
trajectory:
  type: "waypoint"
  waypoints:
    - [0, 0, 0]
    - [0, 0, 2]
    - [2, 0, 2]
  yaw_rad: 0.0
  max_speed_m_s: 0.6
  max_acceleration_m_s2: 0.5
  waypoint_tolerance_m: 0.20
  waypoint_speed_tolerance_m_s: 0.20
  dwell_time_s: 0.40
```

Defaults:

```text
max_speed_m_s = 0.6
max_acceleration_m_s2 = 0.5
waypoint_tolerance_m = 0.20
waypoint_speed_tolerance_m_s = 0.20
dwell_time_s = 0.40
```

No se anade `mode` en esta implementacion. El unico modo implementado es `waypoint_stop`.

## Trajectory Behavior

### Segment state

La trayectoria mantiene estado interno:

```text
active_target_index = 1
phase = MOVE_TO_WAYPOINT
phase_time_s = 0.0
segment_start_W_m = waypoints[active_target_index - 1]
segment_target_W_m = waypoints[active_target_index]
```

Al iniciar o al llamar `reset()`:

```text
active_target_index = 1
phase = MOVE_TO_WAYPOINT
phase_time_s = 0.0
dwell_timer_s = 0.0
```

Si solo hay un waypoint, la trayectoria se comporta como `hold` sobre ese punto y puede completarse cuando el vehiculo cumpla tolerancias y dwell.

### Segment profile

Cada tramo se convierte en un problema 1D sobre la recta:

```text
p0 = segment_start_W_m
p1 = segment_target_W_m
d = p1 - p0
L = ||d||
u = d / L
```

La referencia se calcula con un perfil trapezoidal con aceleracion limitada:

```text
max_speed_m_s
max_acceleration_m_s2
```

Para tramos cortos donde no se alcanza `max_speed_m_s`, el perfil sera triangular.

La referencia 3D se obtiene como:

```text
position_ref_W_m = p0 + s_ref_m * u
velocity_ref_W_m_s = s_dot_ref_m_s * u
acceleration_ref_W_m_s2 = s_ddot_ref_m_s2 * u
```

Condiciones obligatorias del perfil:

- `s_ref_m` empieza en `0`.
- `s_ref_m` termina en `L`.
- `s_dot_ref_m_s` empieza en `0`.
- `s_dot_ref_m_s` termina en `0`.
- `s_ref_m` nunca sale de `[0, L]`.
- La referencia no avanza al siguiente segmento por tiempo global.

### MOVE_TO_WAYPOINT

En esta fase, la referencia sigue el perfil del tramo activo.

Si el perfil nominal llega al final del tramo antes que el vehiculo, la referencia se queda fija en:

```text
position_ref_W_m = segment_target_W_m
velocity_ref_W_m_s = [0, 0, 0]
acceleration_ref_W_m_s2 = [0, 0, 0]
```

Esto convierte el final de cada tramo en un hold local hasta que el vehiculo llegue.

La fase cambia a `HOLD_AT_WAYPOINT` cuando el perfil de referencia ya ha llegado al target del tramo. No cambia todavia al siguiente segmento.

### HOLD_AT_WAYPOINT

En esta fase, la referencia permanece fija en el waypoint objetivo:

```text
position_ref_W_m = segment_target_W_m
velocity_ref_W_m_s = [0, 0, 0]
acceleration_ref_W_m_s2 = [0, 0, 0]
```

Se acumula dwell solo mientras se cumplan simultaneamente:

```text
||state.position_W_m - segment_target_W_m|| <= waypoint_tolerance_m
||state.velocity_W_m_s|| <= waypoint_speed_tolerance_m_s
```

Si alguna condicion deja de cumplirse, `dwell_timer_s` vuelve a cero.

Cuando:

```text
dwell_timer_s >= dwell_time_s
```

el waypoint se considera alcanzado.

### SWITCH_SEGMENT

Si quedan waypoints:

```text
active_target_index += 1
phase = MOVE_TO_WAYPOINT
phase_time_s = 0.0
dwell_timer_s = 0.0
```

El nuevo tramo empieza en el waypoint que acaba de alcanzarse, no en la posicion real instantanea. Esto conserva la semantica geometrica de la lista de waypoints.

Si no quedan waypoints, la trayectoria queda completada y el runner debe terminar con:

```text
termination_reason = "Trajectory completed"
```

## Runner Integration

`waypoint` sera stateful y debe implementar:

```python
def reset(self) -> None:
    ...

def get_reference_for_state(self, time_s: float, state: VehicleState) -> TrajectoryReference:
    ...

def check_completion(self, time_s: float, state: VehicleState, dt_s: float) -> tuple[bool, str]:
    ...
```

El runner debe:

- llamar a `trajectory.reset()` al inicio si existe;
- usar `get_reference_for_state(time_s, state)` si existe;
- mantener `get_reference(time_s)` para `hold`, `circle`, `lissajous` y cualquier trayectoria sin metodo state-aware;
- evaluar `check_completion(...)` si existe;
- conservar las terminaciones de seguridad actuales.

`get_reference(time_s)` en `LineTrajectory` puede mantenerse como fallback legacy, pero el runner normal debe usar `get_reference_for_state`.

## Validation Rules

La carga YAML debe validar al menos:

- `waypoints` existe y tiene al menos un punto.
- Cada waypoint tiene tres componentes finitas.
- `max_speed_m_s > 0` si se declara.
- `max_acceleration_m_s2 > 0` si se declara.
- `waypoint_tolerance_m > 0` si se declara.
- `waypoint_speed_tolerance_m_s >= 0` si se declara.
- `dwell_time_s >= 0` si se declara.
- Si `times` existe, debe ser una lista numerica compatible con la longitud de `waypoints`, pero se debe tratar como deprecated.

## Documentation Changes

Actualizar:

- `docs/simulador/escenarios_yaml.md`: describir `waypoint` como `waypoint_stop`, documentar parametros nuevos y marcar `times` como deprecated.
- `docs/simulador/arquitectura.md`: explicar que algunas trayectorias pueden ser stateful y depender del estado.
- `docs/simulador/validacion.md`: actualizar el criterio de `waypoint_clean`.
- `docs/simulador/dataset_clasico.md`: explicar que `waypoint` mide llegada secuencial a puntos con parada.
- `README.md`: ajustar la descripcion general si menciona smoothstep o waypoints suavizados.

## Commands

Verificacion minima:

```powershell
uv run pytest tests\test_trajectories.py tests\test_runner.py
uv run simulador-quad run scenarios\waypoint_clean.yaml --no-visualization
uv run pytest
```

Si se toca dataset:

```powershell
uv run python tools\generate_classic_dataset.py --version v1 --out data\classic_dataset\v1 --overwrite
uv run python tools\run_classic_dataset.py --dataset data\classic_dataset\v1 --family waypoint --no-visualization --rerun
uv run python tools\summarize_classic_dataset.py --dataset data\classic_dataset\v1
```

## Testing Strategy

### Unit tests de trayectoria

Cubrir:

- Perfil trapezoidal en tramo largo: acelera, mantiene velocidad y frena.
- Perfil triangular en tramo corto: no supera `max_speed_m_s`.
- `position_ref` nunca sale del segmento.
- `velocity_ref` empieza y termina en cero.
- Al terminar el perfil, la referencia queda fija en el waypoint.
- El siguiente segmento no empieza hasta cumplir posicion, velocidad y dwell.
- Si el vehiculo sale de tolerancia durante dwell, el contador vuelve a cero.
- `reset()` devuelve la trayectoria al primer tramo.
- `times` legacy no controla el cambio de segmento.
- Caso de un solo waypoint como hold finito.

### Runner tests

Cubrir:

- El runner llama `reset()` si existe.
- El runner usa `get_reference_for_state(...)` si existe.
- `check_completion(...)` produce `"Trajectory completed"` al final.
- Las trayectorias sin metodo state-aware conservan `get_reference(time_s)`.
- Las terminaciones de seguridad siguen teniendo prioridad.

### Scenario tests

`scenarios/waypoint_clean.yaml` debe:

- terminar con `termination_reason == "Trajectory completed"`;
- no terminar por fallo de seguridad;
- mostrar paradas claras en los waypoints intermedios;
- no sobrepasar ampliamente los vertices en la vista XY;
- mantener `position_rmse_m` dentro del umbral documentado.

## Implementation Plan

1. Revertir o reemplazar la logica waypoint anterior
   - Eliminar dependencia de smoothstep temporal como comportamiento principal.
   - Mantener fallback solo por compatibilidad si es necesario.

2. Implementar `WaypointStopTrajectory` o refactorizar `LineTrajectory`
   - Preferencia: mantener el nombre `LineTrajectory` si minimiza cambios de loader, pero documentar que su semantica es waypoint stop.
   - Implementar fases `MOVE_TO_WAYPOINT` y `HOLD_AT_WAYPOINT`.
   - Implementar perfil trapezoidal/triangular 1D.

3. Actualizar loader
   - `type: "waypoint"` y `type: "line"` instancian la nueva trayectoria.
   - Leer parametros opcionales.
   - Aceptar `times` como deprecated sin usarlo como disparador.

4. Actualizar runner
   - Integrar `reset`, `get_reference_for_state` y `check_completion`.

5. Actualizar tests
   - Sustituir tests de smoothstep para waypoint por tests de waypoint stop.
   - Mantener pruebas de `hold`, `circle` y `lissajous`.

6. Actualizar escenarios y dataset
   - `waypoint_clean.yaml` debe usar o heredar parametros razonables.
   - Si los YAML generados incluyen `times`, mantenerlos de momento como legacy o dejar de generarlos si no rompen compatibilidad esperada.

7. Actualizar documentacion viva
   - Reflejar que `times` esta deprecated.
   - Reflejar que `waypoint` es ahora una mision de parada en puntos.

## Tasks

- [ ] Task: Implementar perfil 1D trapezoidal/triangular
  - Acceptance: devuelve `s`, `s_dot` y `s_ddot` acotados para cualquier tiempo de fase.
  - Verify: `uv run pytest tests\test_trajectories.py`
  - Files: `src/simulador_quad/trajectories/analytic.py`, `tests/test_trajectories.py`

- [ ] Task: Implementar fases waypoint stop
  - Acceptance: cada waypoint se mantiene como hold hasta cumplir tolerancia, velocidad y dwell.
  - Verify: `uv run pytest tests\test_trajectories.py`
  - Files: `src/simulador_quad/trajectories/analytic.py`, `tests/test_trajectories.py`

- [ ] Task: Actualizar loader de escenarios
  - Acceptance: `waypoint` y `line` aceptan parametros nuevos y `times` deprecated.
  - Verify: `uv run pytest tests\test_scenarios.py`
  - Files: `src/simulador_quad/scenarios/loader.py`, `src/simulador_quad/scenarios/schema.py`, `tests/test_scenarios.py`

- [ ] Task: Integrar runner state-aware
  - Acceptance: el runner usa `reset`, `get_reference_for_state` y `check_completion` cuando existan.
  - Verify: `uv run pytest tests\test_runner.py`
  - Files: `src/simulador_quad/runner.py`, `tests/test_runner.py`

- [ ] Task: Actualizar escenario oficial waypoint
  - Acceptance: `waypoint_clean.yaml` representa una mision waypoint stop y termina con `"Trajectory completed"`.
  - Verify: `uv run simulador-quad run scenarios\waypoint_clean.yaml --no-visualization`
  - Files: `scenarios/waypoint_clean.yaml`

- [ ] Task: Actualizar documentacion
  - Acceptance: no queda documentacion vigente que describa waypoint como smoothstep temporal.
  - Verify: revision manual.
  - Files: `README.md`, `docs/simulador/escenarios_yaml.md`, `docs/simulador/arquitectura.md`, `docs/simulador/validacion.md`, `docs/simulador/dataset_clasico.md`

- [ ] Task: Regresion completa
  - Acceptance: la suite completa pasa.
  - Verify: `uv run pytest`
  - Files: no aplica.

## Boundaries

- Always: usar `uv`; mantener mundo ENU y cuerpo FRD; mantener compatibilidad con `type: "waypoint"` y `type: "line"`; tratar `"Trajectory completed"` como terminacion normal; documentar `times` como deprecated.
- Ask first: eliminar soporte de `times`; cambiar PIDs por familia; cambiar modelo fisico; introducir nuevos modos YAML; redondear esquinas; anadir splines/minimum jerk/minimum snap.
- Never: avanzar al siguiente waypoint solo por tiempo; insertar puntos virtuales como waypoints reales; resolver el sobrepaso retocando solo el PID; mezclar fallos de seguridad con terminacion normal; cambiar `hold`, `circle` o `lissajous`.

## Success Criteria

- `waypoint` / `line` se comportan por defecto como waypoint stop.
- `times` sigue siendo aceptado pero no gobierna el avance entre waypoints.
- El vehiculo llega a cada waypoint, frena y permanece dentro de tolerancia antes de pasar al siguiente.
- `scenarios/waypoint_clean.yaml` termina con `termination_reason == "Trajectory completed"`.
- La vista XY no muestra sobrepasos amplios en los vertices intermedios.
- `uv run pytest` pasa.
- La documentacion viva refleja la nueva semantica.

## Open Questions

No hay preguntas abiertas para esta implementacion. Otros modos como seguimiento continuo de camino, redondeo de esquinas, splines, minimum jerk o minimum snap quedan explicitamente fuera de alcance.
