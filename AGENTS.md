# AGENTS.md

## Proposito del repo

Este repositorio contiene el TFG de un simulador 6DOF de cuadricóptero para comparar control clásico y control neuronal por imitación. El estado actual incluye la consolidación del simulador clásico, la generación de datos reproducibles, y la evaluación Out-of-Distribution (OOD) de controladores neuronales (directos e híbridos de lazo externo) en trayectorias 2D y 3D (e.g., Lemniscatas con oscilación vertical).

## Fuentes de verdad

- `docs/01_principios_tfg.md`: alcance, trazabilidad y criterios academicos.
- `docs/02_requisitos_ingenieria_simulador.md`: requisitos fisicos y de ingenieria del simulador.
- `docs/03_criterios_ingenieria_software.md`: criterios de software cientifico, pruebas y reproducibilidad.
- `docs/simulador/`: documentacion viva del estado actual implementado.
- `docs/simulador/dataset_clasico.md`: flujo vigente de generacion, ejecucion y resumen del dataset clasico.
- `README.md`: entrada principal del repositorio.

Si cambia el comportamiento, el alcance, los comandos, los escenarios, la telemetria, las metricas o la arquitectura del simulador, actualiza tambien `README.md` y los documentos afectados en `docs/simulador/`.

## Planes y revisiones

- `docs/plans/`: specs y planes vigentes.
- `docs/plans/archived/`: planes historicos no vigentes.
- `docs/reviews/`: auditorias y revisiones tecnicas.

## Reglas de trabajo

- Mantén codigo cientifico simple: nombres fisicos claros, unidades y marcos de referencia explicitos, pocas abstracciones.
- Mantén mundo ENU y cuerpo FRD en escenarios, documentacion, figuras y datasets.
- No introduzcas cambios de alcance sin actualizar los documentos normativos afectados.
- Solo hagas commits cuando el usuario lo indique explicitamente. Cuando se pidan commits, hazlos pequeños, revisables y con una unica unidad funcional por commit.
