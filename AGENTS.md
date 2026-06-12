# AGENTS.md

## Proposito del repo

Este repositorio contiene el TFG de un simulador 6DOF de cuadricóptero para comparar control clásico y control neuronal por imitación.

## Fuentes de verdad

- `docs/01_principios_tfg.md`: alcance, trazabilidad y criterios academicos.
- `docs/02_requisitos_ingenieria_simulador.md`: requisitos fisicos y de ingenieria del simulador.
- `docs/03_criterios_ingenieria_software.md`: criterios de software cientifico, pruebas y reproducibilidad.
- `docs/simulador/`: documentacion viva del estado actual implementado.
- `TFG_Memoria/`: memoria LaTeX del TFG.
- `README.md`: entrada principal del repositorio.

`docs/html/` es una instantánea didáctica adicional identificada por su huella Git. No es fuente de verdad, no sustituye al Markdown y solo se actualiza cuando el usuario lo solicita.

Si cambia el comportamiento, el alcance, los comandos, los escenarios, la telemetria, las metricas o la arquitectura del simulador, actualiza tambien `README.md` y los documentos afectados en `docs/simulador/`.
Si se cambia la narrativa, estructura, bibliografia, figuras o resultados usados en la memoria, actualiza tambien `TFG_Memoria/` y deja claro si el cambio procede de evidencia experimental o de redaccion pendiente.

## Planes y revisiones

- `docs/plans/archived/`: planes historicos no vigentes.
- `docs/reviews/`: auditorias y revisiones tecnicas.

## Reglas de trabajo

- Mantén codigo cientifico simple: nombres fisicos claros, unidades y marcos de referencia explicitos, pocas abstracciones.
- Mantén mundo ENU y cuerpo FRD en escenarios, documentacion, figuras y datasets.
- No introduzcas cambios de alcance sin actualizar los documentos normativos afectados.
- En la memoria, prioriza dinamica, control, escenarios, datasets, entrenamiento y resultados; no convertir la memoria en una explicacion extensa de ingenieria de software.
- Solo hagas commits cuando el usuario lo indique explicitamente. Cuando se pidan commits, hazlos pequeños, revisables y con una unica unidad funcional por commit.
