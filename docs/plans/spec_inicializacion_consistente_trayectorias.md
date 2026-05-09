# Spec: Inicializacion Consistente con Trayectorias Clasicas

## Objective

Corregir la generacion de escenarios de tuning y dataset clasico para que el estado inicial sea coherente con la trayectoria evaluada. El objetivo es que el ajuste PID mida seguimiento de trayectoria, no captura desde una posicion inicial arbitrariamente alejada.

El problema actual es que `tools/tune_classic_pid.py` y la generacion de dataset usan una posicion inicial fija, por ejemplo `[0, 0, 1]`, aunque la referencia en `t = 0` pueda empezar en otro punto. Esto penaliza artificialmente `position_rmse_m` y `position_max_err_m`, hace que ningun PID pase filtros duros y contamina la comparacion entre familias.

Esta spec aplica solo al simulador clasico y a la generacion de datos clasicos. La capa neuronal, loaders de ML y entrenamiento quedan fuera de alcance.

## Assumptions

- El objetivo inmediato es hacer viable el tuning PID por familia, no evaluar recuperacion desde condiciones iniciales lejanas.
- El dataset clasico `v1` debe medir seguimiento desde un estado inicial razonable y trazable.
- Las trayectorias actuales mantienen mundo ENU y cuerpo FRD.
- No se introducen por ahora trayectorias compuestas tipo `approach + circle`; eso queda como extension futura.
- No se cambian los umbrales de filtros duros hasta haber corregido la inicializacion.

## Current Problem

Las referencias actuales en `src/simulador_quad/trajectories/analytic.py` empiezan asi:

- `hold`: `position_W_m`.
- `circle`: `center_W_m + [radius_m, 0, 0]`.
- `lissajous`: `center_W_m`, porque `sin(0) = 0`.
- `waypoint` / `line`: primer waypoint.

En cambio, los escenarios generados por `src/simulador_quad/datasets/classic.py` inicializan el estado en una posicion fija independiente de la trayectoria. El primer error de posicion puede ser grande aunque el controlador sea razonable, y ese error entra en:

- `position_rmse_m`;
- `position_max_err_m`;
- filtros duros de seleccion PID;
- score de tuning;
- resumen posterior del dataset.

## Desired Behavior

Todo escenario generado para tuning PID y dataset clasico debe inicializarse a partir de la referencia de la trayectoria en `t = 0`.

Regla principal:

```text
initial_state.position_W_m = trajectory.get_reference(0.0).position_W_m
initial_state.velocity_W_m_s = [0.0, 0.0, 0.0]
initial_state.yaw_rad = trajectory.get_reference(0.0).yaw_rad
initial_state.orientation_WB = null
initial_state.angular_velocity_B_rad_s = [0.0, 0.0, 0.0]
```

La velocidad inicial se mantiene nula en esta fase para evitar introducir una condicion inicial dinamica mas compleja. Si se desea evaluar seguimiento con velocidad inicial igual a la referencia, se hara en una spec posterior.

### Reglas por familia

`hold`:

- Empezar en la posicion objetivo de hold.
- El tuning mide mantenimiento de posicion y rechazo de perturbaciones, no despegue.

`circle`:

- Empezar en el primer punto del circulo: `center_W_m + [radius_m, 0, 0]`.
- Si `yaw_mode == "forward"`, usar el yaw de la referencia en `t = 0`.
- No empezar en el centro del circulo.

`lissajous`:

- Empezar en `center_W_m` para las formulas actuales.
- Mantener yaw inicial `0.0`.

`waypoint` / `line`:

- Empezar en el primer waypoint.
- Medir seguimiento de la trayectoria suavizada desde su inicio, no aproximacion desde otro punto.

## Future Work: Capture / Approach Episodes

La capacidad de llegar desde una posicion inicial lejana es un experimento distinto. No debe mezclarse con el tuning PID principal.

Si se necesita evaluar esa capacidad, crear en el futuro escenarios separados con alguno de estos enfoques:

- fase inicial de `hold` o `line` desde el estado inicial hasta el punto de entrada de la trayectoria;
- metrica con ventana de evaluacion que ignore un tiempo inicial de convergencia;
- familia o perfil explicito `capture`;
- metricas separadas de settling time, error durante aproximacion y error de seguimiento en regimen.

No se implementa ahora una metrica proyectada especial para waypoint. Para mantener claridad academica, el criterio principal sigue siendo error 3D frente a la referencia, una vez corregida la inicializacion.

## Commands

Comandos de verificacion esperados tras implementar la spec:

```powershell
uv run pytest tests\test_classic_dataset_generation.py tests\test_classic_pid_selection.py tests\test_classic_dataset_scripts.py
uv run python tools\tune_classic_pid.py --family hold --out data\classic_dataset\v1\pids --version v1
uv run python tools\tune_classic_pid.py --family circle --out data\classic_dataset\v1\pids --version v1
uv run python tools\tune_classic_pid.py --family lissajous --out data\classic_dataset\v1\pids --version v1
uv run python tools\tune_classic_pid.py --family waypoint --out data\classic_dataset\v1\pids --version v1
```

Para evitar escribir artefactos definitivos durante pruebas manuales:

```powershell
uv run python tools\generate_classic_dataset.py --version test_init --out $env:TEMP\simulador_quad_dataset_test_init --overwrite
uv run python tools\run_classic_dataset.py --dataset $env:TEMP\simulador_quad_dataset_test_init --family circle --limit 1 --no-visualization
uv run python tools\summarize_classic_dataset.py --dataset $env:TEMP\simulador_quad_dataset_test_init
```

## Project Structure

- `src/simulador_quad/datasets/classic.py`: logica central para construir estado inicial consistente y escenarios generados.
- `tools/tune_classic_pid.py`: debe reutilizar la misma logica de escenario nominal que el dataset.
- `tests/test_classic_dataset_generation.py`: pruebas de estado inicial generado por familia.
- `tests/test_classic_pid_selection.py`: pruebas de filtros y seleccion sin error inicial artificial.
- `tests/test_classic_dataset_scripts.py`: flujo CLI con al menos un episodio generado y ejecutado.
- `docs/simulador/dataset_clasico.md`: documentacion viva si cambia el contrato de inicializacion.
- `docs/simulador/escenarios_yaml.md`: documentacion de YAML generado si se exponen nuevos campos.

## Code Style

La implementacion debe mantenerse como codigo cientifico simple. Preferir funciones puras y nombres fisicos con unidades.

Ejemplo de estilo esperado:

```python
def initial_state_from_trajectory_config(trajectory_cfg: dict[str, object]) -> dict[str, object]:
    reference_0 = reference_from_trajectory_config(trajectory_cfg, time_s=0.0)
    return {
        "position_W_m": reference_0.position_W_m.tolist(),
        "velocity_W_m_s": [0.0, 0.0, 0.0],
        "orientation_WB": None,
        "yaw_rad": float(reference_0.yaw_rad),
        "angular_velocity_B_rad_s": [0.0, 0.0, 0.0],
    }
```

Si se instancia una trayectoria para obtener la referencia inicial, debe hacerse mediante el mismo contrato que usa el runner o con una funcion equivalente y testeada. No duplicar formulas de circulo, Lissajous y waypoint en varios sitios si se puede reutilizar una unica ruta.

## Testing Strategy

### Unit tests

Crear o ampliar pruebas para verificar:

- `hold`: `initial_state.position_W_m == trajectory.position_W_m`.
- `circle`: `initial_state.position_W_m == center_W_m + [radius_m, 0, 0]`.
- `lissajous`: `initial_state.position_W_m == center_W_m`.
- `waypoint`: `initial_state.position_W_m == waypoints[0]`.
- `initial_state.yaw_rad` coincide con la referencia en `t = 0`.
- `orientation_WB` permanece `null` para que el loader genere actitud nivelada ENU/FRD.
- Todos los YAML generados siguen pasando `validate_scenario_config`.

### Integration tests

Actualizar el test CLI del dataset para confirmar que el primer escenario generado:

- tiene estado inicial coherente con su referencia en `t = 0`;
- puede ejecutarse con `run_classic_dataset.py`;
- produce `metrics.json` y `summary.csv`.

### Manual validation

Tras implementar, ejecutar tuning de al menos una familia dinamica:

```powershell
uv run python tools\tune_classic_pid.py --family circle --out $env:TEMP\pids_test --version test_init
```

El resultado esperado no es garantizar que cualquier PID sea excelente, sino eliminar el fallo sistematico provocado por error inicial artificial.

## Boundaries

- Always: mantener mundo ENU y cuerpo FRD; derivar el estado inicial desde la referencia en `t = 0`; usar la misma logica para tuning y dataset; conservar metricas fisicas 3D claras; actualizar documentacion viva si cambia el contrato.
- Ask first: cambiar umbrales de filtros duros; usar velocidad inicial igual a la velocidad de referencia; introducir ventana temporal que ignore segundos iniciales; anadir trayectorias compuestas `approach + tracking`; crear nueva familia `capture`.
- Never: implementar red neuronal; ocultar errores modificando metricas sin documentarlo; reajustar PID por perturbacion; mezclar evaluacion de captura inicial con seleccion principal de PID; cambiar convenciones ENU/FRD.

## Success Criteria

- Los escenarios generados para tuning y dataset empiezan en la posicion de referencia en `t = 0`.
- `circle` ya no empieza en el centro si la referencia empieza sobre la circunferencia.
- `waypoint` empieza en el primer waypoint.
- `lissajous` empieza en su centro segun la formula actual.
- Las pruebas automaticas cubren las cuatro familias.
- `tools/tune_classic_pid.py` deja de fallar por error inicial artificial en todas las familias.
- La documentacion viva del dataset explica que `v1` evalua seguimiento desde estado inicial consistente, no captura desde posicion lejana.

## Open Questions

- No hay preguntas abiertas para esta fase.
