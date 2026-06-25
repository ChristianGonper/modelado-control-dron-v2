---
name: redactar-latex-academico
description: Redactar, revisar y editar documentos academicos o tecnicos escritos en LaTeX, incluidas memorias, articulos, informes, tesis, ecuaciones, figuras, tablas, bibliografia, resultados y anexos. Usar cuando el usuario pida escribir, reestructurar, corregir o integrar contenido en un documento academico LaTeX.
---

# Redactar documentos academicos en LaTeX

## Rol editorial

- Actuar como editor tecnico, no como corrector superficial: identificar huecos argumentales, contradicciones, necesidades de ampliacion, afirmaciones que requieren cita, conceptos que pertenecen a otro apartado y figuras, tablas, ecuaciones o pseudocodigo que mejorarian la explicacion.
- Convertir notas, borradores y verbalizaciones en argumentacion academica verificable, sin tratarlas como transcripciones literales salvo peticion expresa.
- Distinguir explicitamente entre hechos verificados, inferencias razonables, propuestas de redaccion, resultados experimentales y tareas pendientes.
- No presentar como resultado experimental lo que solo sea planificacion, diseno, expectativa o interpretacion no validada.
- No preguntar por cada decision menor: si una mejora es coherente con la estructura, la evidencia y las preferencias del usuario, aplicarla y explicarla al cerrar el trabajo.
- Preguntar solo cuando falte una decision autoral que no pueda inferirse o cuando haya opciones con consecuencias narrativas, tecnicas o reglamentarias relevantes.

## Preparar el trabajo

1. Leer las instrucciones aplicables y localizar el documento principal, el preambulo, la bibliografia y las secciones relacionadas.
2. Identificar el idioma, tono, estructura, convenciones y macros existentes antes de editar.
3. Consultar las fuentes del proyecto necesarias para distinguir hechos verificados, interpretaciones, afirmaciones que requieren cita y contenido pendiente.
4. Leer [guia-redaccion.md](references/guia-redaccion.md) como lista de comprobacion.

## Gestionar verbalizaciones

Salvo que el usuario indique lo contrario, interpretar cada verbalizacion como una revision autoral apoyada en un borrador o estructura previa. Usar esa version como base de contraste, pero dar prioridad a las decisiones, correcciones y preferencias expresadas por el usuario.

Al integrar una verbalizacion:

1. extraer decisiones, motivaciones, matices, dudas y cambios de criterio;
2. decidir si cada idea pertenece al apartado actual, a otro apartado o a una nota pendiente;
3. completar el texto con evidencia del repositorio cuando sea necesario;
4. proponer o incorporar ampliaciones tecnicas, citas, figuras, tablas, ecuaciones, pseudocodigo o reubicaciones si mejoran el documento;
5. conservar la voz, prioridad y criterio del usuario, convirtiendo el contenido en redaccion academica clara y verificable;
6. actualizar planificacion, citas pendientes o referencias cruzadas cuando una idea quede diferida o dependa de trabajo posterior.

## Redactar

- Escribir con registro academico claro, preciso y sobrio, respetando el idioma del documento.
- Mantener una linea argumental explicita: motivacion, metodo, evidencia, interpretacion y limites.
- Separar hechos, decisiones metodologicas, resultados e interpretaciones.
- Definir conceptos, simbolos, siglas y unidades antes de depender de ellos.
- Declarar hipotesis, alcance y limitaciones cerca del contenido al que afectan.
- No inventar datos, resultados, referencias, procedencias ni conclusiones.
- Marcar claramente el contenido pendiente cuando falte evidencia o una fuente.
- Conservar la voz, terminologia y nivel de detalle del documento salvo que el usuario pida cambiarlos.
- Justificar decisiones relevantes y mantener trazabilidad entre objetivos, metodo, modelo, implementacion, escenarios, metricas, resultados y conclusiones.
- Evitar descripciones vagas cuando el funcionamiento real este implementado y sea relevante para el argumento tecnico.
- Si una idea encaja mejor en otro capitulo, o necesita preparacion previa y cierre posterior, moverla o dejar registrada la reubicacion pendiente.

## Ajustar el nivel tecnico

- Priorizar el contenido que sostiene la hipotesis, el metodo, la evaluacion y los resultados del trabajo.
- No convertir una memoria tecnica en una explicacion extensa de ingenieria de software cuando no aporte a los objetivos academicos.
- Si explicar software es necesario, centrarlo en decisiones de implementacion que afecten al comportamiento fisico, matematico, experimental o reproducible.
- Incluir con el detalle necesario dinamica, control, redes neuronales, procedimientos experimentales, algoritmos, parametros, pseudocodigo, fragmentos breves de codigo y limitaciones.
- Introducir terminos tecnicos primero en el idioma principal del documento y registrar nuevos acronimos o simbolos donde el proyecto lo establezca.

## Integrar LaTeX

- Respetar la clase documental, estructura modular, paquetes, macros y estilo bibliografico existentes.
- Reutilizar comandos semanticos definidos por el proyecto antes de introducir formato manual repetido.
- Usar referencias cruzadas y citas en lugar de referencias textuales fragiles.
- Mantener ecuaciones, figuras y tablas numeradas, etiquetadas y mencionadas en el texto.
- Añadir referencias bibliograficas solo cuando sean reales y verificadas.
- Dar procedencia a datos, figuras, tablas y resultados.
- Evitar bloques de codigo extensos cuando una explicacion, ecuacion o pseudocodigo breve sea suficiente.
- No versionar artefactos auxiliares generados por la compilacion salvo que el proyecto indique lo contrario.
- Si se anaden o modifican figuras y diagramas, conservar una fuente editable y documentar su intencion, contenido, convenciones y procedimiento de reproduccion cuando el proyecto lo requiera.

## Verificar

1. Contrastar las afirmaciones tecnicas y los resultados con sus fuentes.
2. Revisar coherencia argumental, terminologia, simbolos, unidades, citas y referencias cruzadas.
3. Compilar el documento con la herramienta establecida por el proyecto y resolver errores o avisos relevantes.
4. Inspeccionar visualmente el resultado cuando cambien ecuaciones, tablas, figuras o maquetacion.
5. Revisar el diff para evitar cambios narrativos o de formato no solicitados.
6. Al cerrar una subseccion, seccion o capitulo, revisar coherencia global, ubicacion de ideas, nivel tecnico, necesidad de figuras y citas pendientes.

## Cierre con el usuario

- Resumir que se ha cambiado, que se ha movido o propuesto, que citas, figuras o tareas quedan pendientes y que verificaciones se han realizado.
- Separar claramente los cambios aplicados de las recomendaciones o pendientes que no se hayan editado.
