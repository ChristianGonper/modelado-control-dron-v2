---
name: redactar-latex-academico
description: Redactar, revisar y editar documentos academicos o tecnicos escritos en LaTeX, incluidas memorias, articulos, informes, tesis, ecuaciones, figuras, tablas, bibliografia, resultados y anexos. Usar cuando el usuario pida escribir, reestructurar, corregir o integrar contenido en un documento academico LaTeX.
---

# Redactar documentos academicos en LaTeX

## Preparar el trabajo

1. Leer las instrucciones aplicables y localizar el documento principal, el preambulo, la bibliografia y las secciones relacionadas.
2. Identificar el idioma, tono, estructura, convenciones y macros existentes antes de editar.
3. Consultar las fuentes del proyecto necesarias para distinguir hechos verificados, interpretaciones, afirmaciones que requieren cita y contenido pendiente.
4. Leer [guia-redaccion.md](references/guia-redaccion.md) como lista de comprobacion.

## Redactar

- Escribir con registro academico claro, preciso y sobrio, respetando el idioma del documento.
- Mantener una linea argumental explicita: motivacion, metodo, evidencia, interpretacion y limites.
- Separar hechos, decisiones metodologicas, resultados e interpretaciones.
- Definir conceptos, simbolos, siglas y unidades antes de depender de ellos.
- Declarar hipotesis, alcance y limitaciones cerca del contenido al que afectan.
- No inventar datos, resultados, referencias, procedencias ni conclusiones.
- Marcar claramente el contenido pendiente cuando falte evidencia o una fuente.
- Conservar la voz, terminologia y nivel de detalle del documento salvo que el usuario pida cambiarlos.

## Integrar LaTeX

- Respetar la clase documental, estructura modular, paquetes, macros y estilo bibliografico existentes.
- Reutilizar comandos semanticos definidos por el proyecto antes de introducir formato manual repetido.
- Usar referencias cruzadas y citas en lugar de referencias textuales fragiles.
- Mantener ecuaciones, figuras y tablas numeradas, etiquetadas y mencionadas en el texto.
- Añadir referencias bibliograficas solo cuando sean reales y verificadas.
- Dar procedencia a datos, figuras, tablas y resultados.
- Evitar bloques de codigo extensos cuando una explicacion, ecuacion o pseudocodigo breve sea suficiente.
- No versionar artefactos auxiliares generados por la compilacion salvo que el proyecto indique lo contrario.

## Verificar

1. Contrastar las afirmaciones tecnicas y los resultados con sus fuentes.
2. Revisar coherencia argumental, terminologia, simbolos, unidades, citas y referencias cruzadas.
3. Compilar el documento con la herramienta establecida por el proyecto y resolver errores o avisos relevantes.
4. Inspeccionar visualmente el resultado cuando cambien ecuaciones, tablas, figuras o maquetacion.
5. Revisar el diff para evitar cambios narrativos o de formato no solicitados.
