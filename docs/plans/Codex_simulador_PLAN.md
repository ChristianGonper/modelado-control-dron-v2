# Plan de Documentación Inicial del TFG

## Resumen
Crear tres documentos Markdown estructurados que fijen el marco definitivo del TFG: simulador 6DOF como banco de comparación entre control clásico y control neuronal por imitación. La versión previa del repositorio será referencia, no contrato; se corregirá especialmente el enfoque de software hacia código científico claro para ingeniería aeroespacial.

## Documentos a Crear
- `01_principios_tfg.md`: objetivo del TFG, criterios de calidad, límites de documentación, enfoque aeroespacial, reproducibilidad y prioridad de claridad sobre sobreingeniería.
- `02_requisitos_ingenieria_simulador.md`: requisitos físicos y matemáticos del simulador, sistemas de referencia, estado, ecuaciones 6DOF, cuaterniones, RK4, actuadores, perturbaciones y métricas de comparación.
- `03_criterios_ingenieria_software.md`: convenciones de software, estructura esperada, uso limitado de dataclasses, política de librerías, trazabilidad experimental y documentación técnica mínima necesaria.

## Decisiones Técnicas Fijadas
- Alcance: simulador 6DOF con cuaterniones para comparar control clásico frente a control neuronal.
- Control neuronal: aprendizaje por imitación a partir de datos generados por el controlador clásico.
- Control clásico: controlador de referencia trazable, presumiblemente PID/PD en cascada salvo revisión posterior.
- Sistemas de referencia: mundo ENU y cuerpo FRD.
- Convención crítica: en FRD, `Z_body` apunta hacia abajo; el empuje sustentador actúa en dirección `-Z_body`.
- Integrador oficial: RK4 únicamente.
- Primera versión sin aerodinámica formal: no se incluirán arrastre, flapping, pérdidas inducidas ni modelo aerodinámico detallado.
- Perturbaciones v1: ruido de observación, retardos/lag de actuadores y viento simple externo.
- Métricas obligatorias: error de seguimiento, esfuerzo de control y estabilidad/saturación.
- Librerías: NumPy, SciPy, Matplotlib y PyTorch permitidas; otras librerías se justificarán y se discutirán antes de incorporarlas.
- Software: código científico simple, legible para un ingeniero aeroespacial; dataclasses solo para contratos de datos, configuración y estructuras claramente pasivas.

## Criterios de Aceptación
- Los documentos separan principios, ingeniería física y software sin mezclar arquitectura con ecuaciones.
- Cada decisión importante queda justificada por el objetivo académico del TFG.
- Las ecuaciones del simulador usan una convención de ejes explícita y consistente.
- Quedan documentados los límites de validez del modelo físico.
- Queda claro qué pertenece a la primera versión y qué se reserva como trabajo futuro.
- La comparación clásico-neuronal queda definida como experimento reproducible con escenarios, métricas y trazabilidad.

## Supuestos
- Los documentos se redactarán inicialmente en Markdown, no en LaTeX.
- El material existente se podrá reutilizar parcialmente, pero se reescribirá donde contradiga estas decisiones.
- La memoria final del TFG podrá derivarse después de estos documentos, pero estos no serán todavía la memoria formal.
