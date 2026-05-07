# Spec: Refuerzo de pruebas del modelo clasico

## Objective

Definir el refuerzo de pruebas necesario para que el simulador clasico no dependa solo de tests unitarios aislados, sino tambien de invariantes fisicas, convenciones ENU/FRD y regresiones de escenarios.

El objetivo es convertir pruebas y escenarios en evidencia de validacion para el TFG.

## Tech Stack

- pytest.
- NumPy.
- `uv` para ejecucion.
- Directorios temporales de pytest para no depender de `results/` como oraculo.

## Commands

Comandos de verificacion futura:

```powershell
uv run pytest
uv run python -m pytest tests\test_dynamics.py tests\test_runner.py tests\test_metrics.py
```

Comandos de escenarios para validacion manual:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
uv run simulador-quad run scenarios\circle_drag.yaml --no-visualization
```

## Project Structure

```text
tests/
  Tests unitarios y de regresion.

scenarios/
  Escenarios oficiales; no deben usarse como unico oraculo numerico.

src/simulador_quad/
  Modulos fisicos y de simulacion cubiertos por pruebas.
```

## Code Style

Ejemplo de criterio de prueba:

```python
def test_hover_uses_level_enu_frd_convention():
    q_level = get_level_quaternion(0.0)
    force_B_N = np.array([0.0, 0.0, -mass_kg * gravity_m_s2])
    ...
```

Reglas:

- Tests fisicos deben usar nombres con unidades.
- Evitar tests que pasen por una convencion no fisica si el requisito exige ENU/FRD.
- Preferir tolerancias numericas explicitas a igualdad exacta en integracion.

## Testing Strategy

Areas a reforzar:

- Empuje ENU/FRD con `get_level_quaternion`.
- RK4 en casos analiticos simples.
- Conservacion de norma de cuaternion en simulaciones largas.
- Drag disipativo con orientaciones no triviales.
- ZOH multi-rate y actuador evolucionando a `physics_dt_s`.
- Saturacion y degradacion de mixer/actuadores.
- Terminacion por actitud, posicion, velocidad, saturacion persistente y no finitos.
- Exportacion JSON con esquema minimo.
- Regresiones de escenarios cortos con tolerancias por metrica.

## Boundaries

- Always: derivar tests desde requisitos fisicos documentados.
- Always: usar `uv`.
- Ask first: crear nuevos escenarios oficiales.
- Ask first: endurecer tolerancias que puedan hacer fragil la suite.
- Never: eliminar tests fallidos sin reemplazo equivalente.
- Never: depender de artefactos historicos de `results/` como unica verdad.

## Success Criteria

- La suite cubre convenciones fisicas centrales.
- Existen regresiones de escenarios completos o cortos con criterios numericos.
- Los JSON exportados tienen campos obligatorios y valores finitos.
- La validacion sigue excluyendo control neuronal.

## Open Questions

No hay preguntas abiertas.
