# Constitución local del demostrador de control

## Finalidad

Estos principios protegen la fidelidad del TFG mientras se construye una nueva
experiencia de aplicación. La memoria y la documentación del simulador siguen
siendo las fuentes canónicas para los hechos científicos y técnicos existentes.

## 1. Núcleo congelado

No se modifican para este producto:

- el modelo físico 6DOF;
- la arquitectura de control y sus protecciones;
- los controladores PD especializados;
- la generación del dataset;
- el pipeline de entrenamiento;
- las arquitecturas y pesos de MLP, GRU y LSTM;
- el protocolo experimental y los resultados del TFG.

La aplicación consume ese sistema. Cualquier necesidad que parezca exigir
alterarlo debe detenerse y revisarse con el usuario.

## 2. Extensión acotada

Es admisible añadir código para la interfaz, adaptar contratos, ejecutar casos,
reproducir telemetría y visualizar resultados. También se pueden construir
trayectorias nuevas mediante tramos parametrizados y composiciones compatibles
con el motor. No se admite dibujo libre ni reentrenamiento.

## 3. Evidencia sin exageración

La aplicación distingue siempre:

- el resultado de la ejecución que el usuario acaba de realizar;
- la evidencia agregada y las conclusiones ya obtenidas en el TFG.

Una ejecución no demuestra una conclusión general. Tampoco se atribuyen al TFG
prestaciones, generalización o superioridad que sus fuentes canónicas no avalen.

## 4. Trazabilidad sin duplicación

Las ecuaciones, decisiones del simulador, entrenamiento y resultados no se
reescriben aquí. Se enlazan desde [docs/simulador/](../simulador/), [TFG_Memoria/](../../TFG_Memoria/),
[TFG_Report/](../../TFG_Report/) o [results/](../../results/) según corresponda. Los documentos de producto sólo
definen la experiencia nueva.

## 5. Desarrollo guiado por especificaciones

Cada capacidad sustancial se acuerda primero en su spec. Planificación, creación
de tareas e implementación son fases independientes y requieren autorización
explícita. Si cambia una capacidad ya especificada, se reabre y actualiza su spec
gobernante antes de adaptar el plan y el código.

La estructura documental puede evolucionar cuando una separación mejore la
claridad. No se crean documentos pequeños sin una responsabilidad propia ni se
concentran responsabilidades distintas en un único archivo mastodóntico.

## 6. Producto antes que panel técnico

La primera capa debe ser clara para un jurado de ingeniería sin exigirle conocer
el TFG. La profundidad técnica permanece accesible de forma progresiva. Cada
control o métrica visible debe ayudar a experimentar, comprender o interpretar un
resultado; mostrar cantidad de parámetros no es un objetivo.
