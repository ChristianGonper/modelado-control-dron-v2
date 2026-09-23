# Instrucciones de trabajo

Este repositorio contiene el TFG terminado y es el lugar donde se desarrollará la aplicación que lo presenta en el concurso. La aplicación parte del simulador y de los resultados existentes; no redefine el trabajo académico.

## Frontera del TFG

- Conserva el modelo físico, los controladores, los datos, el entrenamiento, los pesos, el protocolo experimental y los resultados del TFG.
- Añade la experiencia de concurso alrededor del sistema existente: configuración de misiones, ejecución, reproducción, visualización y explicación de resultados.
- Si una función de la aplicación exige tocar código del TFG, comprueba primero si puede resolverse mediante una capa de integración. Si el cambio en el núcleo es necesario, hazlo mínimo, justifícalo y verifica que no altera los resultados ni las afirmaciones del TFG.
- Distingue las ejecuciones nuevas de la evidencia agregada del TFG. No presentes una comparación puntual como conclusión general ni atribuyas al TFG capacidades añadidas para el concurso.

## Dónde trabajar

- La aplicación, sus decisiones y sus futuras especificaciones viven en este repositorio.
- Para el simulador existente, consulta [docs/simulador/README.md](docs/simulador/README.md) y después sólo el documento técnico necesario. Para afirmaciones académicas, consulta [TFG_Memoria/](TFG_Memoria/) o [results/](results/) según el caso.
- La identidad, la candidatura y los materiales compartidos se gestionan en [concurso-prototipos-eiiia-2026](../concurso-prototipos-eiiia-2026/). Una decisión propia de esta aplicación se documenta aquí.

## Forma de trabajo

Define las capacidades nuevas antes de implementarlas con el detalle que necesiten. Para un cambio sustancial, actualiza primero su especificación; prepara plan y tareas cuando ayuden a ejecutar el trabajo. Un ajuste pequeño puede hacerse directamente. Conserva una fuente por decisión y enlaza la documentación existente en vez de copiarla.

Las instrucciones más específicas de los subdirectorios se aplican a las tareas dentro de ellos.
