# Simulador quad 6DOF para TFG

Este repositorio contiene el desarrollo de un simulador 6DOF de cuadricoptero para un Trabajo de Fin de Grado. El objetivo academico es disponer de un banco de ensayo trazable para comparar un controlador clasico con, en una fase posterior, un controlador neuronal entrenado por imitacion.

El estado actual consolida la parte clasica del simulador. La capa neuronal no esta implementada todavia: no hay dataset, entrenamiento, carga de modelo ni evaluacion neuronal en bucle cerrado.

## Estado actual

Implementado:

- Dinamica de cuerpo rigido 6DOF con mundo ENU y cuerpo FRD.
- Actitud mediante cuaterniones `[w, x, y, z]`.
- Integracion RK4 con pasos separados de fisica, control y telemetria.
- Controlador clasico en cascada.
- Mixer de cuadricoptero, actuadores con saturacion, retardo puro opcional y lag de primer orden sobre `omega`.
- Drag lineal simplificado, viento constante y ruido gaussiano de observacion en posicion/velocidad.
- Escenarios YAML, telemetria JSON, metricas JSON, figuras PNG y visor 3D HTML.

Fuera de alcance actual:

- Control neuronal por imitacion.
- Aerodinamica formal mas alla del drag lineal.
- Modelo de bateria, sensores realistas, estimador onboard, contacto con suelo o validacion con datos reales.

## Comandos minimos

```powershell
uv sync
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
```

Para ejecutar otros escenarios:

```powershell
uv run simulador-quad run scenarios\circle_drag.yaml --no-visualization
uv run simulador-quad run scenarios\circle_noisy_wind.yaml --no-visualization
uv run simulador-quad run scenarios\lissajous_clean.yaml --no-visualization
uv run simulador-quad run scenarios\waypoint_clean.yaml --no-visualization
```

## Mapa documental

- `docs/01_principios_tfg.md`: principios academicos, alcance, trazabilidad y limites del TFG.
- `docs/02_requisitos_ingenieria_simulador.md`: requisitos fisicos y de ingenieria del simulador.
- `docs/03_criterios_ingenieria_software.md`: criterios de software cientifico, pruebas y reproducibilidad.
- `docs/simulador/`: documentacion viva del estado implementado.
- `docs/simulador/trazabilidad.md`: matriz requisito-modelo-codigo-prueba-escenario-metrica.
- `docs/plans/`: specs vigentes de saneamiento y trabajo futuro inmediato.
- `docs/plans/archived/`: planes historicos no vigentes.
- `docs/reviews/`: auditorias y revisiones tecnicas.

## Estructura principal

- `src/simulador_quad/`: codigo del paquete Python.
- `tests/`: pruebas unitarias y de integracion ligera.
- `scenarios/`: escenarios YAML reproducibles.
- `results/`: salidas generadas por ejecuciones.
- `docs/`: documentacion normativa, viva, planes y revisiones.

## Regla de mantenimiento

Si cambia el comportamiento del simulador, los comandos, escenarios, telemetria, metricas, arquitectura o alcance, deben actualizarse tambien `README.md` y los documentos afectados en `docs/simulador/`.
