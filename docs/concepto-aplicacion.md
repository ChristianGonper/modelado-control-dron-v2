# Concepto de la aplicación de control de cuadricópteros

Este documento define la intención del producto, no la interfaz ni su implementación.

## Qué ofrece

Una aplicación interactiva para plantear una misión de vuelo y observar cómo responde un cuadricóptero simulado bajo distintas estrategias de control. Permite comparar un controlador clásico y los controladores neuronales entrenados por imitación en condiciones equivalentes, comprender el resultado y examinar la ingeniería que lo sustenta.

El modelo, los controladores, el entrenamiento y los resultados del TFG constituyen la base de la aplicación. Se presentan mediante una experiencia completa y explorable, sin alterar las conclusiones académicas.

## Pregunta que guía la experiencia

> Ante una misma misión, ¿cómo cambia el comportamiento del dron según el método de control y las condiciones de vuelo?

La aplicación permite observar diferencias y buscar sus causas. No convierte una única ejecución o métrica en un veredicto sobre qué método es siempre mejor.

## Recorrido principal

1. Tras una introducción breve del autor, el visitante elige una trayectoria habitual con valores iniciales listos para usar. La composición de una misión por tramos también está a la vista, sin imponerse en la primera prueba.
2. Ve la misión antes de ejecutarla, incluido su punto de inicio, que queda fijado por la trayectoria elegida y no puede modificar el visitante. Puede ajustar los parámetros de la trayectoria y una perturbación comprensible, como el viento, cuando quiera intervenir más; el primer experimento puede hacerse directamente con los valores propuestos.
3. Ejecuta la misma misión para el método clásico y los tres modelos neuronales, con condiciones comparables; después elige cuáles visualizar juntos.
4. Observa primero una comparación clara entre el método clásico y MLP, con una primera lectura sencilla del seguimiento, la finalización o motivo de interrupción y las diferencias relevantes. Puede después incorporar GRU y LSTM a la vista.
5. Si quiere profundizar, explora la telemetría, el funcionamiento de los controladores, el entrenamiento, las protecciones y la evidencia experimental del TFG.

El autor puede mostrar primero un ejemplo completo o ceder el control tras explicar lo básico. En ambos casos, el visitante debe poder continuar con poca ayuda.

Los valores iniciales de una trayectoria nueva no deben repetir siempre exactamente la misma configuración. Las variaciones estarán dentro de rangos razonables y la configuración concreta de cada prueba quedará visible y podrá reproducirse. No se despliegan todos los parámetros al comenzar, pero se pueden consultar y modificar sin abandonar el recorrido.

## Qué debe quedar claro

- Las redes neuronales aprenden a imitar las decisiones con las que el controlador clásico sigue la trayectoria en el lazo externo. La estabilización de actitud sigue en manos de un controlador clásico.
- El resultado de la misión elegida es una observación concreta. Las conclusiones generales requieren mirar los ensayos documentados del TFG.
- Las condiciones de comparación y las razones de una terminación anticipada deben poder consultarse; una animación atractiva no basta para interpretar el desempeño.
- La capa inicial habla en términos comprensibles. Los detalles físicos y de aprendizaje permanecen disponibles para quien quiera examinarlos.

## Límites de esta visión

El simulador, los modelos y el entrenamiento del TFG no se rediseñan para el concurso. Las misiones nuevas sirven para exploración e inferencia, no para generar nuevos datos de entrenamiento ni para rehacer los resultados académicos. La aplicación no representa un dron físico ni promete comportamiento fuera de los límites del modelo.

Quedan para decisiones posteriores el catálogo exacto de misiones, la forma de componerlas, qué controles se ofrecen al visitante, las métricas de primera lectura, la arquitectura de la aplicación y su diseño visual. Habrá que resolver también qué controlador clásico sirve de referencia cuando una misión compuesta no pertenece claramente a una familia ya ensayada.

## Fuentes para concretarla

- [Descripción del simulador y de sus capacidades](simulador/README.md)
- [Memoria del TFG](../TFG_Memoria/)
- [Resultados experimentales](../results/)
- [Principios compartidos del concurso](../../concurso-prototipos-eiiia-2026/docs/constitucion.md)
