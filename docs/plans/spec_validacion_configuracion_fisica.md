# Spec: Validacion de configuracion fisica

## Objective

Definir validaciones simples para impedir que escenarios fisicamente invalidos produzcan resultados aparentemente validos.

El objetivo es mantener codigo cientifico simple: validaciones claras, mensajes comprensibles y sin introducir frameworks pesados de schema.

## Tech Stack

- Python.
- NumPy para dimensiones, finitud y propiedades matriciales.
- PyYAML ya existente para carga de escenarios.
- pytest para pruebas futuras.

## Commands

Comandos de verificacion futura:

```powershell
uv run python -m pytest tests\test_scenarios.py
uv run pytest
```

Comandos de smoke test:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
```

## Project Structure

```text
src/simulador_quad/scenarios/loader.py
  Punto de entrada actual para validar configuracion YAML.

src/simulador_quad/scenarios/schema.py
  Lugar recomendado para helpers o contratos de validacion si se reutilizan.

src/simulador_quad/core/contracts.py
  Dataclasses fisicas; pueden recibir validaciones minimas futuras.

tests/
  Tests de configuracion valida e invalida.
```

## Code Style

Mensaje de error esperado:

```text
Invalid vehicle.mass_kg: expected positive kg value, got -1.0
```

Validaciones minimas:

- `mass_kg > 0`
- `gravity_m_s2 > 0`
- `inertia_B_kg_m2` 3x3, finita, simetrica y definida positiva
- `linear_drag_coefficient` escalar o vector `[3]`, finito y no negativo
- cuatro rotores con posicion `[3]`
- `turning_direction in {-1, 1}`
- `k_f > 0`, `k_m >= 0`, `omega_max_rad_s > 0`
- tiempos `physics_dt_s`, `control_dt_s`, `telemetry_dt_s > 0`
- `orientation_WB` finito y normalizable si se proporciona

## Testing Strategy

Fase documental:

- Definir lista cerrada de validaciones v1.
- Definir mensajes de error orientados a usuario tecnico.

Fase futura:

- Tests parametrizados para cada configuracion invalida.
- Tests de escenarios oficiales validos.
- Tests de cuaternion no unitario: normalizar con aviso documentado o rechazar, segun decision de implementacion.

## Boundaries

- Always: validar antes de ejecutar la simulacion.
- Always: dar errores con ruta de campo y valor recibido.
- Ask first: cambiar formato YAML.
- Ask first: incorporar librerias de validacion externas.
- Never: aceptar parametros fisicos invalidos silenciosamente.
- Never: convertir validacion en arquitectura compleja ajena al TFG.

## Success Criteria

- Todo escenario oficial pasa validacion.
- Escenarios invalidos fallan temprano con mensajes comprensibles.
- Las validaciones cubren parametros fisicos que afectan a validez del TFG.
- La documentacion YAML indica las restricciones principales.

## Open Questions

Decision futura de implementacion: si `orientation_WB` no es unitario, normalizar registrando accion o rechazar el escenario. Por defecto recomendado: rechazar si la norma no esta cerca de 1 salvo `orientation_WB: null`.

