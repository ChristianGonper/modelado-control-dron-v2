# Storytelling del demostrador de control

## Idea central

La aplicación hace tangible una pregunta de control: cómo se comportan unos
controladores neuronales ya entrenados por imitación frente al controlador
clásico cuando se enfrentan a misiones conocidas y nuevas. El trabajo técnico
del TFG se percibe mediante la experiencia y sus capas de profundidad; no se
articula como una historia explícita de “antes el TFG y ahora la aplicación”.

## Recorrido principal

1. Presentar en muy poco tiempo el sistema: los PD especializados proporcionaron
   los datos con los que se entrenaron MLP, GRU y LSTM; las redes sustituyen sólo
   la decisión del lazo externo.
2. Elegir una trayectoria de un tipo conocido o diferente, o componerla mediante
   tramos parametrizados.
3. Previsualizarla en 3D y, si procede, añadir viento.
4. Ejecutar PD especializado, MLP, GRU y LSTM en condiciones idénticas.
5. Reproducir los vuelos sincronizados por tiempo y elegir qué métodos comparar.
6. Leer el resultado inmediato con pocas métricas comprensibles.
7. Revelar progresivamente telemetría, arquitectura, entrenamiento, protecciones
   y evidencia agregada.

Este orden es contexto mínimo, experimento visible y profundidad científica. No
se comienza con una explicación exhaustiva del TFG.

## Revelación científica

Uno de los hallazgos centrales es que imitar mejor la fuerza del experto en una
métrica supervisada no implica necesariamente controlar mejor la trayectoria al
cerrar el bucle. La aplicación debe permitir comprender esta diferencia sin
reducirla a “una red gana”: entrenamiento supervisado y desempeño de control
responden a preguntas relacionadas, pero no idénticas.

## Dos escalas de evidencia

La narración separa claramente:

- **Esta ejecución:** el comportamiento ante la trayectoria y condiciones
  seleccionadas.
- **Resultados del TFG:** la evaluación agregada en los ensayos documentados y
  sus conclusiones.

Los números exactos, figuras y afirmaciones se toman siempre de las fuentes
canónicas del TFG; no se duplican ni se reinterpretan en este documento.

## Lenguaje

Primero se habla de trayectorias de tipos utilizados durante el aprendizaje y de
trayectorias nuevas o de tipo diferente. Después se introducen ID y OOD para
quien quiera la precisión técnica. La aplicación explica lo necesario con
palabras concretas, sin sobrecargar la experiencia con jerga ni simplificar hasta
perder rigor.

## El momento «hay más»

La primera comparación debe sostenerse por sí sola. Después puede abrirse una
capa avanzada con telemetría, protecciones, saturaciones, flujo de información,
arquitecturas neuronales, entrenamiento y resultados agregados. Ese segundo acto
demuestra la profundidad del trabajo sin obligar a verla antes de entender la
pregunta principal.

Un posible bucle visual o pieza subtitulada será apoyo de la presentación, no su
sustituto. Puede mostrar entrenamiento, flujo de señales o animaciones difíciles
de explicar en directo, manteniendo un alcance contenido.
