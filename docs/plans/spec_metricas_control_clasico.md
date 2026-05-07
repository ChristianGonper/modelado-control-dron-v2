# Spec: Metricas y control clasico

## Objective

Definir metricas fisicas claras para evaluar el simulador clasico y documentar el baseline de control clasico como experto reproducible.

El objetivo es evitar metricas ambiguas, especialmente agregados que mezclan unidades, y dejar trazadas las ganancias y saturaciones del controlador.

## Tech Stack

- NumPy para calculo numerico.
- JSON para metricas.
- Markdown para documentacion de significado fisico.
- pytest para pruebas futuras.

## Commands

Comandos de verificacion futura:

```powershell
uv run python -m pytest tests\test_metrics.py tests\test_control.py
uv run pytest
```

Comandos de generacion de evidencia:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
uv run simulador-quad run scenarios\circle_drag.yaml --no-visualization
```

## Project Structure

```text
src/simulador_quad/metrics/report.py
  Calculo de metricas agregadas.

src/simulador_quad/control/classic.py
  Ganancias y saturaciones del baseline clasico.

docs/simulador/arquitectura.md
docs/simulador/guia_uso.md
  Documentacion de metricas y lectura de resultados.
```

## Code Style

Metricas recomendadas:

```text
position_rmse_m
position_mae_m
position_max_err_m
collective_thrust_mean_N
collective_thrust_max_N
body_moment_norm_mean_Nm
body_moment_norm_max_Nm
max_rotor_speed_rad_s
saturation_percentage
degradation_percentage
termination_reason
```

Reglas:

- No sumar N y Nm como metrica fisica principal.
- Si se conserva un indice compuesto, nombrarlo como heuristico y documentar limitacion.
- Exportar ganancias efectivas del controlador clasico o incluirlas en metadata.

## Testing Strategy

Fase documental:

- Definir lista de metricas obligatorias.
- Documentar unidades y uso recomendado.
- Declarar cuales son aptas para comparacion y cuales solo para diagnostico.

Fase futura:

- Tests de calculo con telemetria sintetica.
- Tests de unidades/nombres esperados.
- Tests de presencia de ganancias del controlador en metadata.

## Boundaries

- Always: separar magnitudes por unidad fisica.
- Always: reportar causa de terminacion.
- Ask first: eliminar campos de metricas existentes.
- Ask first: cambiar formato JSON incompatible.
- Never: usar un indice sin unidad como argumento principal de comparacion.
- Never: presentar el controlador clasico como caja negra sin ganancias o limites.

## Success Criteria

- Las metricas principales tienen unidades claras.
- Las ganancias y saturaciones del controlador clasico son trazables.
- La documentacion explica como interpretar saturacion y degradacion.
- Los resultados clasicos quedan listos para futura comparacion neuronal bajo las mismas metricas.

## Open Questions

No hay preguntas abiertas.

