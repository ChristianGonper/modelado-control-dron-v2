# Spec: Reproducibilidad y metadata experimental

## Objective

Definir la metadata necesaria para que cada ejecucion del simulador clasico pueda reconstruirse: escenario, parametros efectivos, controlador, entorno, version de codigo y comando ejecutado.

El objetivo es que una figura o tabla de la memoria pueda vincularse a una ejecucion reproducible.

## Tech Stack

- Python estándar para metadata de entorno.
- Git disponible cuando el repositorio lo permita.
- JSON en `metrics.json`.
- Sin dependencias nuevas.

## Commands

Comandos que deben producir metadata suficiente:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
uv run simulador-quad run scenarios\circle_drag.yaml --no-visualization
```

Comando de verificacion general:

```powershell
uv run pytest
```

## Project Structure

```text
src/simulador_quad/app.py
  Punto natural para reunir metadata de ejecucion.

src/simulador_quad/metrics/report.py
  Exportacion agregada de metadata junto a metricas.

pyproject.toml
  Version y dependencias declaradas.

uv.lock
  Fuente de reproducibilidad de entorno.
```

## Code Style

Forma minima esperada en `metrics.metadata`:

```json
{
  "scenario_name": "Hover Clean",
  "controller": {"type": "classic", "parameters": {}},
  "seed": 42,
  "command": "uv run simulador-quad run scenarios\\hover_clean.yaml --no-visualization",
  "package_version": "0.1.0",
  "python_version": "3.13.x",
  "git_commit": "abc123",
  "git_dirty": false,
  "uv_lock_hash": "sha256:..."
}
```

Reglas:

- Si Git no esta disponible, registrar `"unknown"` sin fallar.
- La configuracion resuelta debe incluir defaults efectivos relevantes.
- La metadata no debe depender de resultados visuales.

## Testing Strategy

Fase documental:

- Definir campos obligatorios y opcionales.
- Documentar significado de cada campo.

Fase futura:

- Test de `metrics.json` con presencia y tipo de campos.
- Test de fallback cuando Git no esta disponible.
- Test de que `seed`, escenario y controlador quedan registrados.

## Boundaries

- Always: registrar semilla, escenario, controlador y configuracion efectiva.
- Always: mantener JSON legible.
- Ask first: cambiar formato publico de `metrics.json` de forma incompatible.
- Ask first: anadir dependencias para metadata.
- Never: fallar una simulacion solo porque Git no esta disponible.
- Never: usar metadata para ocultar configuracion no declarada.

## Success Criteria

- `metrics.json` permite reconstruir escenario, controlador, semilla, comando y entorno.
- La documentacion explica que metadata es obligatoria para resultados de memoria.
- Los defaults internos relevantes quedan visibles como configuracion efectiva.

## Open Questions

No hay preguntas abiertas.

