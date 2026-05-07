# Spec: Validacion de escenarios y resultados

## Objective

Definir como convertir los escenarios actuales en evidencia experimental defendible para el TFG clasico: clasificacion, criterios de aceptacion, resultados esperados y artefactos de memoria.

El objetivo no es cambiar la dinamica, sino declarar que representa cada escenario y cuando un resultado se considera valido.

## Tech Stack

- Escenarios YAML en `scenarios/`.
- Resultados JSON y figuras en `results/`.
- pytest para futuras regresiones de escenarios.
- `uv` para ejecucion.

## Commands

Comandos oficiales de validacion manual:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
uv run simulador-quad run scenarios\circle_drag.yaml --no-visualization
uv run simulador-quad run scenarios\circle_noisy_wind.yaml --no-visualization
uv run simulador-quad run scenarios\lissajous_clean.yaml --no-visualization
uv run simulador-quad run scenarios\waypoint_clean.yaml --no-visualization
```

## Project Structure

```text
scenarios/
  Escenarios oficiales.

docs/simulador/escenarios_yaml.md
  Referencia de campos y convenciones.

docs/simulador/validacion.md
  Documento futuro con matriz de escenarios, criterios y evidencias.

results/
  Artefactos generados, no fuente normativa.
```

## Code Style

Clasificacion esperada:

```markdown
| Escenario | Tipo | Objetivo | Perturbaciones | Criterio de exito |
| --- | --- | --- | --- | --- |
| `hover_clean` | nominal | comprobar equilibrio y seguimiento vertical | ninguna | termina por tiempo, sin saturacion persistente |
| `circle_noisy_wind` | robustez | seguimiento con viento y ruido | viento constante, ruido pos/vel | termina por tiempo, error acotado |
```

Reglas:

- Los escenarios de fallo deben etiquetarse como fallo esperado.
- Los escenarios nominales no deben depender de terminaciones permisivas para parecer validos.
- Los criterios deben ser numericos cuando haya baseline suficiente.

## Testing Strategy

Fase documental:

- Crear tabla de escenarios oficiales.
- Declarar criterios iniciales de aceptacion.
- Identificar que resultados existentes son historicos y cuales deben regenerarse.

Fase futura de codigo/tests:

- Anadir regresiones de escenarios cortos en directorios temporales.
- Validar `termination_reason`, RMSE maximo, saturacion, degradacion y no finitos.

## Boundaries

- Always: separar escenarios nominales, robustez, estres y fallo esperado.
- Always: conservar trazabilidad desde YAML hasta metricas.
- Ask first: cambiar parametros fisicos o ganancias para hacer pasar un escenario.
- Ask first: eliminar escenarios oficiales.
- Never: usar resultados sin YAML reproducible como evidencia final.
- Never: relajar limites de seguridad para ocultar inestabilidad.

## Success Criteria

- Existe una tabla documental de escenarios oficiales.
- Cada escenario tiene objetivo, tipo, perturbaciones, semilla y criterio de aceptacion.
- Los resultados usados en memoria tienen artefactos reproducibles.
- Los escenarios de la futura capa neuronal quedan reservados para otra fase.

## Open Questions

No hay preguntas abiertas.

