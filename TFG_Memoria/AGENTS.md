# AGENTS.md

## Propósito

Esta carpeta contiene la memoria LaTeX del TFG sobre un simulador 6DOF de
cuadricóptero para comparar control clásico y control neuronal por imitación.
El agente debe trabajar aquí con criterio académico y contrastar siempre la
redacción con la evidencia disponible en la raíz del repositorio.

## Contexto que debes consultar

- `../README.md`: entrada general, alcance y comandos principales.
- `../docs/01_principios_tfg.md`: principios académicos y de trazabilidad.
- `../docs/02_requisitos_ingenieria_simulador.md`: requisitos físicos.
- `../docs/03_criterios_ingenieria_software.md`: criterios de software científico.
- `../docs/simulador/`: documentación viva del simulador implementado.
- `../src/`, `../scenarios/`, `../tests/`, `../tools/`, `../data/` y
  `../results/`: código y evidencia experimental.
- `docs/requisitos_reglamento.md`: requisitos extraídos del reglamento de TFG.
- `docs/indice_detallado_memoria.md`: estructura narrativa prevista.
- `docs/criterios_redaccion_y_decisiones.md`: procedimiento de redacción y
  decisiones que deben justificarse durante el desarrollo de la memoria.
- `docs/revision_documentacion_programacion.md`: revisión y riesgos narrativos
  de la documentación técnica del repositorio.

No uses `../docs/html/` como fuente de verdad.

## Principios de trabajo

- Escribe siempre en español correcto, con tildes.
- La memoria debe contar una historia cohesionada. Al inicio deben quedar claros
  el problema, la pregunta de comparación, los objetivos, el método y el alcance.
- Ninguna decisión relevante de ingeniería aeroespacial, control, redes
  neuronales o metodología experimental debe presentarse como arbitraria.
  Explica su motivación, alternativas consideradas, implementación y efecto
  esperado o medido.
- No inventes resultados, referencias, decisiones ni capacidades del simulador.
- Distingue hechos verificados, interpretaciones y contenido pendiente.
- Mantén trazabilidad entre objetivos, modelo, implementación, escenarios,
  métricas y resultados.
- Prioriza dinámica, control, escenarios, datasets, entrenamiento y resultados;
  evita convertir la memoria en documentación extensa de software.
- Mantén mundo ENU y cuerpo FRD, con unidades, signos e hipótesis explícitos.
- Cita fuentes reales y verificadas; identifica la procedencia de figuras,
  tablas, datos y resultados.
- Respeta la estructura, macros y estilo LaTeX existentes. Compila y revisa el
  PDF tras cambios relevantes.
- Se permiten fragmentos breves de código cuando aclaren una decisión física o
  metodológica. Para el resto, enlaza el repositorio mediante una nota al pie.
- Declara como pendiente cualquier afirmación que aún no tenga evidencia.
- No hagas commits salvo petición explícita del usuario.

## Herramientas de apoyo

### Exploración del código

Para explorar el código, formula primero preguntas dirigidas a la CLI `grok`.
Pídele que identifique el flujo, los módulos relevantes y las rutas concretas.
Usa su respuesta como mapa y verifica directamente solo los archivos necesarios;
no llenes el contexto recorriendo decenas de archivos sin una pregunta concreta.

### NotebookLM

La CLI `nlm` da acceso a NotebookLM. Úsala para procesar documentación extensa
o conjuntos de artículos académicos, responder preguntas concretas y generar
informes ampliados. Solicita citas en formato IEEE cuando el resultado vaya a
servir para la memoria. Verifica siempre las afirmaciones y citas en las fuentes
originales antes de incorporarlas.

### Context7

Usa Context7 cuando sea necesario consultar documentación actualizada de LaTeX,
sus paquetes o herramientas relacionadas. Prioriza documentación oficial y
aplica únicamente soluciones compatibles con la configuración real del proyecto.

## Procedimiento de redacción

- Para redactar decisiones, metodología y desarrollo, parte normalmente de las
  ideas, opiniones y explicaciones verbalizadas por el usuario.
- Convierte esas explicaciones en texto académico y señala al usuario cuando
  falte información o una justificación resulte insuficiente. Puedes añadir
  contexto técnico, pero distingue lo aportado y compruébalo.
- También puede redactarse directamente mediante IA cuando el usuario lo pida,
  siempre con trazabilidad y sin inventar decisiones.
- Durante la redacción, pide de forma habitual a `grok` búsquedas dirigidas sobre
  aspectos concretos del código que deban explicarse o verificarse.
- No modifiques ni mantengas incrementalmente la declaración de uso de IA. Se
  redactará al final a partir del relato completo proporcionado por el usuario.
