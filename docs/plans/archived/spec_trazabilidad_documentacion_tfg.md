# Spec: Trazabilidad y documentacion TFG

## Objective

Crear una capa documental que permita defender el simulador clasico ante tribunal: README raiz util, mapa documental claro, estado de revisiones historicas y matriz de trazabilidad requisito-modelo-codigo-prueba-escenario-metrica.

El usuario principal es un lector tecnico de TFG que necesita entender que esta implementado, que queda fuera de alcance y como se conecta cada decision con evidencia.

## Tech Stack

- Markdown para documentacion.
- Repositorio existente `simulador-quad`.
- Sin dependencias nuevas.

## Commands

Comandos que deben aparecer como flujo minimo reproducible:

```powershell
uv sync
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
```

## Project Structure

```text
README.md
  Entrada principal del repositorio.

docs/simulador/README.md
  Documentacion viva del estado implementado.

docs/simulador/trazabilidad.md
  Nueva matriz de trazabilidad.

docs/reviews/README.md
  Indice recomendado de auditorias y estado.

docs/plans/
  Specs vigentes.

docs/plans/archived/
  Planes historicos.
```

## Code Style

Formato recomendado para la matriz:

```markdown
| Requisito | Justificacion | Codigo | Prueba | Escenario | Metrica | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| Empuje en `-Z_B` | Convencion ENU/FRD | `dynamics/actuators.py` | `tests/test_attitude.py` | `hover_clean.yaml` | hover estable | Parcial |
```

Reglas:

- Usar rutas relativas al repositorio.
- Separar "implementado", "parcial" y "pendiente".
- No enlazar documentos preliminares eliminados.
- Indicar que el control neuronal es futuro.

## Testing Strategy

Verificacion documental:

- El README raiz describe objetivo, estado, instalacion, comandos y mapa documental.
- `docs/simulador/trazabilidad.md` cubre al menos ENU/FRD, cuaterniones, RK4, mixer, actuadores, perturbaciones, escenarios, telemetria, metricas y terminacion.
- El indice de revisiones deja claro que las auditorias nuevas son diagnostico vigente.
- No hay afirmaciones de control neuronal implementado.

## Boundaries

- Always: priorizar claridad academica y trazabilidad.
- Always: distinguir v1 clasica de fase neuronal futura.
- Ask first: cambiar documentos normativos principales.
- Ask first: eliminar auditorias o planes historicos.
- Never: presentar specs historicas como vigentes.
- Never: introducir promesas de aerodinamica avanzada no implementada.

## Success Criteria

- El README raiz deja de estar vacio y permite reproducir una ejecucion minima.
- Existe una matriz de trazabilidad auditable.
- `docs/plans/archived/README.md` explica el estado historico de planes pasados.

## Open Questions

No hay preguntas abiertas.

