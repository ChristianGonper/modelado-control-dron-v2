# Spec: Saneamiento del simulador clasico

## Objective

Definir la fase de saneamiento del simulador clasico antes de abordar control neuronal por imitacion.

El objetivo es convertir la version clasica actual en una base defendible para el TFG: documentada, trazable, reproducible, con escenarios clasificados, metricas fisicas claras, validacion de configuracion y pruebas suficientes para sostener resultados academicos.

Esta spec es el indice de la serie. No implementa cambios de codigo por si misma; organiza specs de trabajo que se implementaran despues.

## Tech Stack

- Python `>=3.13`.
- `uv` como gestor obligatorio.
- NumPy, SciPy, Matplotlib, Plotly, PyYAML y pytest segun `pyproject.toml`.
- Markdown en `docs/` para documentacion y specs.

## Commands

Comandos de referencia para esta fase:

```powershell
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
uv run simulador-quad run scenarios\circle_drag.yaml --no-visualization
uv run simulador-quad run scenarios\circle_noisy_wind.yaml --no-visualization
```

## Project Structure

```text
docs/plans/
  Specs vigentes de saneamiento.

docs/plans/archived/
  Specs, planes y tareas historicas no vigentes.

docs/reviews/
  Auditorias usadas como diagnostico.

docs/simulador/
  Documentacion viva del simulador clasico.

src/simulador_quad/
  Codigo que se podra modificar en fases posteriores, no en esta spec documental.

tests/
  Pruebas a reforzar segun specs posteriores.
```

## Code Style

Las specs deben escribirse como documentos ejecutables por un agente o ingeniero:

```markdown
## Success Criteria

- `uv run pytest` pasa.
- El escenario `hover_clean` termina por `Time limit reached`.
- El resultado exporta metadatos suficientes para reconstruir escenario, controlador, semilla y entorno.
```

Reglas:

- Usar nombres fisicos con unidades y marcos cuando aplique.
- Evitar prometer control neuronal en esta fase.
- Distinguir entre "documentar", "validar" e "implementar".
- Mantener criterios de exito verificables.

## Testing Strategy

La serie se validara documentalmente comprobando que cada spec:

- no contradice los documentos normativos;
- deriva de hallazgos de auditoria vigentes;
- declara comandos de verificacion;
- separa claramente alcance clasico y futuro neuronal;
- incluye criterios de aceptacion verificables.

La validacion tecnica completa queda definida en las specs especificas.

## Boundaries

- Always: mantener foco en v1 clasica, trazabilidad, reproducibilidad y claridad para ingenieria aeroespacial.
- Always: usar `uv` en comandos.
- Ask first: cambiar alcance fisico, introducir dependencias nuevas, modificar documentos normativos.
- Never: implementar capa neuronal en esta fase.
- Never: presentar resultados de la version clasica como comparacion clasico-neuronal.
- Never: recuperar `docs/preliminar/` como fuente vigente.

## Success Criteria

- `docs/plans/` contiene solo specs vigentes y `archived/`.
- Los planes historicos estan archivados sin renombrar.
- Existe una spec por cada area prioritaria:
  - trazabilidad/documentacion;
  - validacion de escenarios/resultados;
  - reproducibilidad/metadata;
  - validacion de configuracion fisica;
  - metricas/control clasico;
  - refuerzo de pruebas.
- La capa neuronal queda documentada como fuera de alcance.

## Open Questions

No hay preguntas abiertas para esta fase documental inicial.

