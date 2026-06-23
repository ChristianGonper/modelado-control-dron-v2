# AGENTS.md

## Propósito

Esta carpeta contiene la memoria LaTeX del TFG sobre un simulador 6DOF de
cuadricóptero para comparar control clásico y control neuronal por imitación.
La redacción debe mantener criterio académico y corresponderse con la evidencia
del repositorio.

## Fuentes de verdad

- `../README.md` y `../docs/`: alcance, requisitos y estado del simulador.
- `../src/`, `../scenarios/`, `../tests/`, `../tools/`, `../data/` y
  `../results/`: implementación y evidencia experimental.
- `docs/requisitos_reglamento.md`: requisitos formales del TFG.
- `docs/indice_detallado_memoria.md`: estructura prevista de la memoria.
- `docs/metodologia_redaccion.md`: proceso para redactar y revisar apartados.
- `docs/criterios_redaccion_y_decisiones.md`: criterios académicos, decisiones
  técnicas que deben justificarse y frontera entre contenido técnico y software.
- `docs/plan_fuentes.md`, `docs/plan_figuras_diagramas.md` y
  `docs/referencias_cruzadas_pendientes.md`: planificación de fuentes, material
  gráfico y referencias pendientes.
- `docs/citas_pendientes_redaccion.md`: afirmaciones que requieren fuente
  bibliográfica antes de cerrar la memoria.
- `Figuras/diagramas/`: fichas y fuentes editables de diagramas previstos.

No uses `../docs/html/` como fuente de verdad.

## Reglas esenciales

- Escribe en español correcto y respeta la estructura, macros y estilo LaTeX.
- No conviertas la memoria en una explicación de técnicas propias de ingeniería
  de software cuando no aporten a la hipótesis, al método o a los resultados.
  Sí debes explicar con el detalle necesario la ingeniería espacial, dinámica,
  control, redes neuronales, procedimientos experimentales, algoritmos,
  parámetros, pseudocódigo, fragmentos breves de código y decisiones de
  implementación que afecten al comportamiento físico, matemático o experimental
  del trabajo.
- No inventes resultados, referencias, decisiones ni capacidades. Distingue
  hechos verificados, interpretaciones, propuestas y contenido pendiente.
- Justifica las decisiones relevantes y mantén trazabilidad entre objetivos,
  modelo, implementación, escenarios, métricas y resultados.
- Cita fuentes reales y verificadas e identifica la procedencia de figuras,
  tablas, datos y resultados.
- Los diagramas pueden realizarse en SVG, TikZ u otro formato original integrado
  en LaTeX. Conserva la fuente editable y una ficha que describa su intención,
  contenido, convenciones y procedimiento de reproducción.
- Introduce los términos técnicos primero en español y registra los nuevos
  acrónimos en `sections/00_abreviaturas.tex`.
- Registra referencias aún inestables en
  `docs/referencias_cruzadas_pendientes.md`.
- No modifiques la declaración de uso de IA hasta la revisión final.
- No hagas commits salvo petición explícita del usuario.

## Herramientas de exploración

- Usa Context7 para documentación actualizada de LaTeX, paquetes y herramientas,
  priorizando fuentes oficiales compatibles con la configuración del proyecto.

## Cómo debe trabajar la IA

- No te limites a traducir o limpiar verbalizaciones. Actúa como editor técnico:
  identifica huecos argumentales, contradicciones, necesidades de ampliación,
  afirmaciones que requieren cita, conceptos que deben moverse a otro apartado y
  figuras, tablas, ecuaciones o pseudocódigo que mejorarían la explicación.
- Cuando una idea verbalizada encaje mejor en otro capítulo, o requiera
  preparación en un apartado previo y cierre en uno posterior, indícalo y
  actualiza la planificación o las referencias pendientes que correspondan.
- Si falta contexto técnico para que el lector entienda cómo funciona algo,
  consulta la evidencia del repositorio y propón una ampliación concreta. Evita
  descripciones vagas cuando el funcionamiento real esté implementado y sea
  relevante para dinámica, control, aprendizaje, simulación o evaluación.
- Diferencia explícitamente entre contenido ya verificable, inferencias
  razonables, propuestas de redacción y tareas pendientes. No presentes como
  resultado experimental lo que solo sea planificación, diseño o expectativa.
- Al cerrar una subsección, sección o capítulo, revisa coherencia global,
  ubicación de ideas, nivel técnico, necesidad de figuras y citas pendientes; no
  cierres solo con correcciones gramaticales.

## Trabajo con el usuario

- Usa las verbalizaciones como entrada principal de criterio autoral, pero
  devuelve trabajo editorial: texto integrado, avisos de reubicación,
  ampliaciones recomendadas y pendientes concretos.
- No preguntes por cada decisión menor. Si una mejora es coherente con la
  estructura, la evidencia y las preferencias expresadas, aplícala y explícala
  al cerrar el trabajo.
- Pregunta solo cuando falte una decisión autoral que no pueda inferirse del
  repositorio o cuando haya varias opciones con consecuencias narrativas o
  técnicas relevantes.
- Al finalizar, resume qué se ha cambiado, qué se ha movido o propuesto, qué
  citas/figuras quedan pendientes y qué verificaciones se han realizado.

## Documentación que consultar según la tarea

- Para redactar o revisar un apartado: `docs/metodologia_redaccion.md`,
  `docs/criterios_redaccion_y_decisiones.md` e
  `docs/indice_detallado_memoria.md`.
- Para comprobar alcance, hipótesis, trazabilidad y criterios académicos:
  `../docs/01_principios_tfg.md` y los documentos vivos de `../docs/simulador/`.
- Para explicar simulador, dinámica, control, redes neuronales, campañas,
  métricas o resultados: contrasta con `../src/`, `../scenarios/`, `../tools/`,
  `../data/`, `../results/` y la documentación relacionada en `../docs/`.
- Para bibliografía: usa `docs/plan_fuentes.md` y registra nuevas necesidades en
  `docs/citas_pendientes_redaccion.md`; no añadas citas no verificadas.
- Para figuras o diagramas: revisa `docs/plan_figuras_diagramas.md` y las fichas
  de `Figuras/diagramas/`; si propones una figura nueva, crea o actualiza su
  ficha con intención, contenido, convenciones y fuente de reproducción.
- Para referencias cruzadas todavía inestables: registra o actualiza
  `docs/referencias_cruzadas_pendientes.md`.

## Verbalizaciones del usuario

Salvo que el usuario indique lo contrario, cada verbalización se entiende como
una revisión autoral apoyada en una versión preliminar redactada previamente por
un agente. Usa esa versión como base de estructura y contraste, pero da prioridad
a las decisiones, correcciones y preferencias expresadas en la verbalización; no
la trates como una transcripción literal ni como una redacción desde cero.

Al integrar una verbalización:

1. extrae decisiones, motivaciones, matices, dudas y cambios de criterio;
2. decide si cada idea pertenece al apartado actual, a otro apartado o a una
   nota pendiente;
3. completa el texto con evidencia del repositorio cuando sea necesario;
4. propone ampliaciones técnicas, citas, figuras o reubicaciones si mejoran la
   memoria;
5. conserva la voz y prioridad del usuario, pero convierte el contenido en
   argumentación académica verificable.
