# AGENTS.md

## Mapa del repositorio

Los documentos normativos del TFG están en `docs/`:

- `docs/01_principios_tfg.md`: principios generales del trabajo, trazabilidad, alcance y criterios académicos.
- `docs/02_requisitos_ingenieria_simulador.md`: requisitos físicos y de ingeniería del simulador cuadricóptero.
- `docs/03_criterios_ingenieria_software.md`: criterios de ingeniería de software, documentación, configuración, pruebas y reproducibilidad.

Estos tres documentos son la fuente principal de decisiones. Cualquier cambio posterior debe respetarlos o actualizar explícitamente el documento afectado.

## Otros documentos

- `docs/reviews/`: revisiones de los documentos normativos.
- `docs/plans/`: planes de trabajo generados durante la definición del proyecto.

## Instrucciones para agentes

- Mantener el enfoque del TFG: simulador 6DOF de cuadricóptero para comparar control clásico y control neuronal por imitación.
- Priorizar documentación, trazabilidad, reproducibilidad y claridad para ingeniería aeroespacial.
- No introducir cambios de alcance sin reflejarlos en los documentos normativos.
- Usar `uv` para gestión de dependencias Python.
- Tratar la parte software como código científico simple: evitar sobreingeniería y documentar módulos, funciones importantes, unidades y sistemas de referencia.
