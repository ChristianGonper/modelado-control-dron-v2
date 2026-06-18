# Metodología incremental de redacción

## Objetivo

La memoria no se redactará completa de una sola vez. Se trabajará apartado por
apartado para conservar una línea argumental reconocible, justificar las
decisiones y evitar que las explicaciones añadidas en momentos distintos se
perciban como fragmentos aislados.

## Unidad de trabajo

La unidad normal de redacción será una subsección. Antes de escribirla se
preparará una ficha breve con:

1. propósito narrativo y relación con la pregunta central;
2. preguntas concretas que debe responder;
3. decisiones del usuario que deben quedar reflejadas;
4. evidencia del repositorio que debe verificarse mediante una consulta dirigida
   a `grok` y lectura de las rutas necesarias;
5. afirmaciones externas que requieren bibliografía;
6. ecuaciones, snippets, figuras o tablas previstas; para cada diagrama, formato
   fuente e intención, mensaje, elementos, relaciones y procedimiento de
   reproducción que se registrarán en su ficha;
7. conexión de entrada con el apartado anterior y conclusión que prepara el
   siguiente.

## Ciclo de redacción de una subsección

1. **Recoger la voz del autor.** Solicitar al usuario las decisiones, motivos,
   alternativas descartadas y valoraciones personales relevantes.
2. **Completar y contrastar.** La IA puede proponer explicaciones, detectar
   huecos y añadir contexto técnico, indicando qué elementos son propuestas.
3. **Verificar implementación.** Pedir a `grok` una búsqueda concreta y comprobar
   directamente solo los archivos necesarios.
4. **Cubrir fuentes.** Consultar `plan_fuentes.md`; si intervienen varias fuentes
   extensas, preparar después el trabajo con NotebookLM.
5. **Redactar.** Separar fundamentos externos, decisiones propias,
   implementación, evidencia y limitaciones.
6. **Cerrar localmente.** Revisar terminología, acrónimos, referencias,
   transiciones, figuras y ausencia de afirmaciones sin justificar.

## Cierre de sección y capítulo

Al terminar una sección principal se releerá completa para:

- eliminar repeticiones y contradicciones;
- comprobar que cada subsección responde a una función distinta;
- distribuir correctamente conceptos que deban explicarse en varios lugares;
- resolver o registrar referencias cruzadas hacia apartados posteriores;
- comprobar que la conclusión de cada bloque prepara el siguiente;
- actualizar la lista de acrónimos y el plan de figuras.

Al cerrar un capítulo se revisará además su relación con la pregunta central y
con los capítulos anterior y posterior.

## Gestión de referencias cruzadas

Cuando un texto deba remitir a un resultado, decisión o explicación que todavía
no tenga etiqueta estable, se anotará en `referencias_cruzadas_pendientes.md`.
Las referencias se resolverán de atrás hacia delante al cerrar cada capítulo y
en una revisión global final.

## Orden inicial de redacción recomendado

1. Introducción, hasta fijar pregunta, objetivos y alcance.
2. Metodología experimental, porque define qué se pretende demostrar.
3. Simulador y control clásico, respaldados por código y decisiones del autor.
4. Control neuronal por imitación.
5. Estado del arte, una vez estén claras las afirmaciones que necesitan fuentes.
6. Resultados, discusión y conclusiones, tras congelar la evidencia.

Este orden de escritura no altera el orden final de lectura de la memoria.
