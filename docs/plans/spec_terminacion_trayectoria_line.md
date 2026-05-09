# Spec: Terminacion de Trayectorias Line / Waypoint

## Objective

Permitir que las trayectorias finitas de tipo `line` / `waypoint` finalicen el episodio al llegar al final de la trayectoria, en lugar de quedarse indefinidamente como un `hold` sobre el ultimo waypoint hasta agotar `max_duration_s`.

El objetivo es que las metricas y resultados de una trayectoria por puntos midan el seguimiento del recorrido definido, no una fase posterior de estacionario que ensucia RMSE, esfuerzo, saturacion y duracion.

Esta spec aplica al simulador clasico y a la ejecucion general de escenarios YAML. No introduce red neuronal, nuevos controladores ni cambios de modelo fisico.

## Assumptions

- `line` y `waypoint` son trayectorias finitas porque declaran una lista de `times` con un ultimo instante definido.
- `hold`, `circle` y `lissajous` siguen siendo trayectorias no finitas para el runner, salvo `max_duration_s`.
- La llegada al final debe registrarse como una terminacion normal y esperada, no como fallo.
- `LineTrajectory.get_reference(t)` puede seguir devolviendo el ultimo waypoint para `t >= times[-1]`; lo que cambia es la politica de terminacion del episodio.
- Para esta primera version, la terminacion por trayectoria completada se basa en llegada fisica al ultimo waypoint, con tolerancia espacial y de velocidad. El tiempo final planificado solo evita terminar antes de que la referencia haya completado el recorrido.

## Current Behavior

`LineTrajectory` usa smoothstep cubico entre waypoints y devuelve:

- primer waypoint si `time_s <= times[0]`;
- interpolacion si `times[0] < time_s < times[-1]`;
- ultimo waypoint si `time_s >= times[-1]`.

El runner no sabe si una trayectoria es finita. Por tanto, despues de `times[-1]`, el episodio continua hasta `termination.max_duration_s`, y la trayectoria se comporta como un hold sobre el ultimo waypoint.

Esto tiene efectos no deseados:

- el RMSE mezcla seguimiento del recorrido y estacionario final;
- la duracion del episodio deja de representar la duracion de la trayectoria;
- el dataset de `waypoint` queda menos comparable con `circle` o `lissajous`;
- los resultados pueden parecer mejores o peores por una cola artificial no definida como parte del experimento.

## Desired Behavior

Las trayectorias `line` y `waypoint` deben exponer que son finitas, su tiempo final y su punto final. El runner debe terminar el episodio cuando la referencia haya llegado al ultimo waypoint y el vehiculo real este suficientemente cerca de ese punto final.

Terminacion esperada:

```text
termination_reason = "Trajectory completed"
```

Regla de llegada:

```text
if trajectory.has_reached_end(state, time_s):
    terminate episode with "Trajectory completed"
```

Para `line` / `waypoint`, `has_reached_end(state, time_s)` debe ser verdadero cuando se cumplen todas estas condiciones:

```text
time_s >= times[-1]
||state.position_W_m - final_waypoint_W_m|| <= final_position_tolerance_m
||state.velocity_W_m_s|| <= final_velocity_tolerance_m_s
```

Valores por defecto:

```text
final_position_tolerance_m = 0.20
final_velocity_tolerance_m_s = 0.30
```

Justificacion:

- `0.20 m` es suficientemente estrecho para un cuadricoptero pequeno simulado y coherente con los umbrales de error de waypoint ya usados en el dataset.
- `0.30 m/s` evita terminar por un cruce rapido del punto final sin estabilizacion minima.
- No se exige dwell time en esta primera version para mantener el contrato simple; si aparecen terminaciones por cruce, se definira despues una permanencia minima.

El tiempo `times[-1]` no significa que el episodio termine automaticamente. Significa que, a partir de ese momento, la referencia ya esta en el ultimo waypoint y el controlador puede estabilizarse ahi hasta entrar en tolerancia. Si no entra en tolerancia, el episodio seguira hasta otra condicion de terminacion, normalmente `max_duration_s`.

La terminacion debe ocurrir despues de haber generado al menos una referencia y una muestra de telemetria alrededor del final planificado, para que `telemetry.json` y `metrics.json` incluyan evidencia del ultimo tramo y de la llegada. Si el orden exacto del runner impide una muestra en el instante de terminacion, se debe documentar y testear que la ultima muestra queda dentro de una tolerancia de `telemetry_dt_s`.

## Interface Design

Preferencia de diseno: añadir un contrato ligero opcional a las trayectorias, sin obligar a todas a heredar nueva jerarquia compleja.

Opcion recomendada:

```python
class LineTrajectory(Trajectory):
    @property
    def final_time_s(self) -> float:
        return float(self.times[-1])

    @property
    def final_position_W_m(self) -> np.ndarray:
        return self.waypoints[-1].copy()
```

El runner puede detectar la capacidad de terminacion con `hasattr(trajectory, "final_position_W_m")` y `hasattr(trajectory, "final_time_s")`. Si la trayectoria no expone esos atributos, se mantiene el comportamiento actual y solo termina por las condiciones globales.

La comprobacion de llegada pertenece al runner, porque depende del estado real del vehiculo, no solo de la referencia.

No se recomienda que `LineTrajectory.get_reference()` lance una excepcion despues del final. La referencia post-final sigue siendo util para visualizacion, pruebas o diagnostico, pero la simulacion normal debe terminar antes de usar una cola larga de hold.

## YAML and Configuration

Comportamiento por defecto propuesto:

- `line` / `waypoint`: terminan al completarse por defecto.
- `hold`, `circle`, `lissajous`: no terminan por trayectoria completada.

No se anade campo YAML obligatorio en esta fase.

Campo opcional futuro si hace falta compatibilidad:

```yaml
termination:
  stop_at_trajectory_end: true
  final_position_tolerance_m: 0.20
  final_velocity_tolerance_m_s: 0.30
```

Para esta spec, no implementar nuevos campos YAML salvo que aparezca una necesidad real de configurar tolerancias por escenario. Los defaults de codigo deben ser `0.20 m` y `0.30 m/s`.

## Metrics and Validation

`metrics.json` debe registrar:

```json
"termination_reason": "Trajectory completed"
```

Los criterios de validacion de escenarios `waypoint` y dataset deben aceptar esta terminacion como exito para familias finitas. En particular:

- `scenarios/waypoint_clean.yaml` dejara de esperar necesariamente `"Time limit reached"`.
- `passes_hard_filters(..., family="waypoint")` debe considerar `"Trajectory completed"` como terminacion valida.
- Para `hold`, `circle` y `lissajous`, `"Time limit reached"` sigue siendo la terminacion normal esperada.

No cambiar en esta fase los umbrales de error, saturacion o degradacion.

## Commands

Comandos de verificacion tras implementar:

```powershell
uv run pytest tests\test_trajectories.py tests\test_runner.py tests\test_scenarios.py tests\test_model_regressions.py
uv run pytest tests\test_classic_dataset_generation.py tests\test_classic_pid_selection.py tests\test_classic_dataset_scripts.py
uv run pytest
```

Prueba manual recomendada:

```powershell
uv run simulador-quad run scenarios\waypoint_clean.yaml --no-visualization
```

Despues de ejecutar, comprobar:

```text
results/waypoint_clean/metrics.json -> termination_reason == "Trajectory completed"
```

## Project Structure

- `src/simulador_quad/trajectories/analytic.py`: exponer `final_time_s` y `final_position_W_m` en `LineTrajectory`.
- `src/simulador_quad/runner.py`: comprobar terminacion por trayectoria finita.
- `src/simulador_quad/datasets/classic.py`: aceptar terminacion completada para familia `waypoint` en filtros duros.
- `tests/test_trajectories.py`: pruebas unitarias de `LineTrajectory.final_time_s` y `final_position_W_m`.
- `tests/test_runner.py`: prueba de terminacion por trayectoria completada.
- `tests/test_classic_pid_selection.py`: filtros duros aceptan `Trajectory completed` para `waypoint` y no lo aceptan para familias infinitas.
- `docs/simulador/escenarios_yaml.md`: documentar que `line` / `waypoint` son finitas y terminan al final.
- `docs/simulador/validacion.md`: actualizar criterio de `waypoint_clean`.
- `docs/simulador/arquitectura.md`: documentar la terminacion por trayectoria finita.

## Code Style

Mantener el estilo cientifico simple: nombres con unidades, condiciones explicitas y pocas abstracciones.

Ejemplo esperado:

```python
def _check_trajectory_completion(self, state: VehicleState, trajectory) -> tuple[bool, str]:
    if hasattr(trajectory, "final_time_s") and hasattr(trajectory, "final_position_W_m"):
        if state.time_s < trajectory.final_time_s:
            return False, ""
        position_error_m = np.linalg.norm(state.position_W_m - trajectory.final_position_W_m)
        speed_m_s = np.linalg.norm(state.velocity_W_m_s)
        if position_error_m <= 0.20 and speed_m_s <= 0.30:
            return True, "Trajectory completed"
    return False, ""
```

La condicion debe quedar separada de fallos fisicos como saturacion, no finitos, crash o limites de actitud.

## Testing Strategy

### Unit tests

- `LineTrajectory.final_time_s` devuelve `times[-1]`.
- `LineTrajectory.final_position_W_m` devuelve el ultimo waypoint.
- `get_reference(t)` sigue devolviendo el ultimo waypoint para `t >= times[-1]`, para mantener una referencia bien definida.

### Runner tests

- Con una `LineTrajectory` corta, el runner termina con `"Trajectory completed"` antes de `max_duration_s` cuando el estado llega al ultimo waypoint dentro de `0.20 m` y `0.30 m/s`.
- Si `time_s >= final_time_s` pero el estado esta fuera de tolerancia, el runner no termina por trayectoria completada.
- Si el estado cruza cerca del ultimo waypoint antes de `final_time_s`, el runner no termina por trayectoria completada.
- Una trayectoria `hold` equivalente sigue terminando por `"Time limit reached"`.
- La ultima telemetria exportada incluye una referencia valida y `termination_cause`.

### Dataset / PID tests

- `passes_hard_filters` acepta `"Trajectory completed"` para `waypoint`.
- `passes_hard_filters` no acepta `"Trajectory completed"` para `hold`, `circle` ni `lissajous`.
- El flujo CLI del dataset sigue generando, ejecutando y resumiendo al menos un episodio `waypoint`.

### Documentation tests

No hay test automatico de Markdown. Revisar manualmente que:

- `docs/simulador/escenarios_yaml.md` no siga diciendo que despues del ultimo waypoint el episodio continua como hold sin matiz.
- `docs/simulador/validacion.md` acepta `"Trajectory completed"` para `waypoint_clean`.

## Implementation Plan

1. Exponer finitud y punto final en `LineTrajectory`
   - Añadir `final_time_s`.
   - Añadir `final_position_W_m`.
   - Mantener `get_reference()` compatible.

2. Integrar terminacion en el runner
   - Añadir helper privado de terminacion por llegada al final.
   - Evaluarlo en el bucle principal usando `state.position_W_m`, `state.velocity_W_m_s`, `trajectory.final_time_s` y `trajectory.final_position_W_m`.
   - Usar defaults `0.20 m` y `0.30 m/s`.
   - Registrar `termination_reason` y `termination_cause` como ya se hace con el resto de terminaciones.

3. Ajustar filtros de dataset
   - Permitir `"Trajectory completed"` solo para `waypoint`.
   - Mantener `"Time limit reached"` como exito para familias no finitas.

4. Actualizar pruebas
   - Ampliar tests de trayectoria.
   - Ampliar tests de runner.
   - Ampliar tests de filtros duros.
   - Ejecutar suite completa.

5. Actualizar documentacion viva
   - `docs/simulador/escenarios_yaml.md`.
   - `docs/simulador/validacion.md`.
   - `docs/simulador/arquitectura.md`.
   - `docs/simulador/dataset_clasico.md` si cambia la interpretacion de `waypoint`.

## Boundaries

- Always: mantener mundo ENU y cuerpo FRD; tratar `"Trajectory completed"` como terminacion normal; limitar este comportamiento a trayectorias finitas; terminar por llegada real al ultimo waypoint; mantener `get_reference()` definido tras el final.
- Ask first: anadir campos YAML obligatorios; cambiar duraciones de escenarios; cambiar `final_position_tolerance_m` o `final_velocity_tolerance_m_s`; anadir dwell time; cambiar metricas para recortar telemetria; aplicar terminacion finita a `circle` o `lissajous`.
- Never: usar `max_duration_s` como sustituto silencioso de fin de trayectoria `line`; mezclar terminacion por trayectoria con fallos fisicos; cambiar el modelo de control o dinamica para resolver este problema; implementar red neuronal.

## Success Criteria

- `line` / `waypoint` terminan con `termination_reason == "Trajectory completed"` cuando el vehiculo llega al ultimo waypoint con error de posicion `<= 0.20 m` y velocidad `<= 0.30 m/s`, una vez alcanzado el tiempo final de referencia.
- `hold`, `circle` y `lissajous` conservan su comportamiento de terminacion por `max_duration_s`.
- `waypoint_clean` deja de incluir una cola artificial larga de hold final.
- Las metricas de `waypoint` se calculan sobre el recorrido planificado y no sobre estacionario posterior.
- Los filtros del dataset aceptan la terminacion completada para `waypoint`.
- La suite `uv run pytest` pasa.
- La documentacion viva refleja el nuevo comportamiento.

## Open Questions

- No hay preguntas abiertas para la primera implementacion. Las tolerancias iniciales quedan fijadas en `0.20 m` y `0.30 m/s`; cualquier ajuste posterior debe documentarse con resultados.
