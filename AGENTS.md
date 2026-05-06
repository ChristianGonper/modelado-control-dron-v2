# AGENTS.md

## Proposito del repo

Este repositorio contiene el TFG de un simulador 6DOF de cuadricoptero para comparar control clasico y, en una fase posterior, control neuronal por imitacion. El estado actual se centra en consolidar el simulador clasico.

## Fuentes de verdad

- `docs/01_principios_tfg.md`: alcance, trazabilidad y criterios academicos.
- `docs/02_requisitos_ingenieria_simulador.md`: requisitos fisicos y de ingenieria del simulador.
- `docs/03_criterios_ingenieria_software.md`: criterios de software cientifico, pruebas y reproducibilidad.
- `docs/simulador/`: documentacion viva del estado actual implementado.
- `README.md`: entrada principal del repositorio.

Si cambia el comportamiento, el alcance, los comandos, los escenarios, la telemetria, las metricas o la arquitectura del simulador, actualiza tambien `README.md` y los documentos afectados en `docs/simulador/`.

## Planes y revisiones

- `docs/plans/`: specs y planes vigentes.
- `docs/plans/archived/`: planes historicos no vigentes.
- `docs/reviews/`: auditorias y revisiones tecnicas.

## Reglas de trabajo

- Mantén codigo cientifico simple: nombres fisicos claros, unidades y marcos de referencia explicitos, pocas abstracciones.
- No introduzcas cambios de alcance sin actualizar los documentos normativos afectados.
