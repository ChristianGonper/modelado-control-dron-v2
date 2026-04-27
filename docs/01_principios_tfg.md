# Principios del Trabajo de Fin de Grado

## 1. Propósito del TFG

El objetivo del Trabajo de Fin de Grado es desarrollar y documentar un simulador de un vehículo cuadricóptero de seis grados de libertad que permita comparar, de forma trazable y reproducible, un controlador clásico frente a un controlador neuronal entrenado por imitación.

El simulador no se plantea como un gemelo digital de alta fidelidad ni como un producto software industrial. Su finalidad principal es servir como banco de ensayo académico para estudiar el modelado dinámico, la generación de escenarios, el diseño de controladores y la comparación cuantitativa entre estrategias de control.

## 2. Principio de documentación y trazabilidad

La documentación y la trazabilidad son principios centrales del TFG. Cada decisión relevante deberá poder seguirse desde el objetivo académico hasta los resultados experimentales:

1. Objetivo del trabajo.
2. Requisito de ingeniería.
3. Modelo matemático o hipótesis física.
4. Implementación software asociada.
5. Escenario de simulación.
6. Métrica o resultado experimental.

La documentación deberá permitir responder, de manera explícita, por qué se ha elegido un modelo, qué limitaciones tiene, cómo se implementa y cómo se verifica. No se buscará documentar cada línea de código, sino las decisiones con impacto en la validez del trabajo.

## 3. Separación entre ingeniería aeroespacial y software

El TFG debe distinguir claramente entre:

- Ingeniería física y de control: sistemas de referencia, ecuaciones de movimiento, hipótesis de modelado, perturbaciones, integrador, control clásico, control neuronal y métricas.
- Ingeniería de software: módulos, responsabilidades, contratos de datos, flujo de ejecución, funciones principales, extensibilidad y reproducibilidad.

La documentación física no debe depender de cómo estén nombradas las clases o funciones del código. Del mismo modo, la documentación software no debe sustituir a la justificación física del modelo.

## 4. Nivel de detalle esperado

El nivel de documentación deberá ser suficiente para elaborar una memoria de TFG de calidad y para que otra persona pueda entender, reproducir y auditar el trabajo.

Se documentará con detalle:

- Las hipótesis del modelo.
- Las ecuaciones usadas.
- Los sistemas de referencia.
- Los límites de validez.
- Los escenarios de comparación.
- Las métricas de evaluación.
- Las funciones y módulos importantes del software.

No se documentará de forma exhaustiva:

- La implementación interna de funciones triviales.
- Decisiones menores de estilo sin impacto técnico.
- Detalles de bajo nivel que puedan leerse directamente en el código sin afectar a la comprensión del sistema.

## 5. Principio de claridad para ingeniería aeroespacial

El software se escribirá y documentará pensando en un perfil de ingeniería aeroespacial, no en un especialista en ingeniería de software. Por ello, se priorizará:

- Código explícito frente a abstracciones innecesarias.
- Nombres físicos claros frente a nombres genéricos.
- Funciones cortas con responsabilidad evidente.
- Documentación de unidades, sistemas de referencia y signos.
- Estructuras de datos simples y verificables.

La arquitectura deberá ayudar a entender el simulador, no convertirse en el objeto principal del TFG.

## 6. Principio de reproducibilidad experimental

Los experimentos deberán ser reproducibles. Para ello se documentarán:

- Escenarios de simulación.
- Condiciones iniciales.
- Parámetros físicos.
- Parámetros del controlador clásico.
- Datos usados para entrenar el controlador neuronal.
- Semillas aleatorias cuando existan perturbaciones o entrenamiento estocástico.
- Versiones o condiciones relevantes del entorno de ejecución.

La comparación entre control clásico y control neuronal solo será válida si ambos se evalúan bajo escenarios definidos de forma común y trazable.

## 7. Principio de alcance limitado

La primera versión del TFG incluirá:

- Dinámica de cuerpo rígido 6DOF.
- Orientación con cuaterniones.
- Integración numérica mediante RK4.
- Control clásico de referencia.
- Control neuronal por imitación.
- Actuadores con velocidad de giro, saturación, lag de primer orden y relación cuadrática empuje-velocidad.
- Perturbaciones simples: ruido de observación, retardo o lag de actuadores, viento externo simplificado y drag lineal.
- Métricas de seguimiento, esfuerzo de control y estabilidad.

La primera versión no incluirá aerodinámica formal detallada más allá de un término de amortiguamiento lineal sencillo. Quedan fuera del alcance inicial:

- Flapping de rotores.
- Arrastre aerodinámico detallado o identificación experimental de coeficientes aerodinámicos.
- Pérdidas inducidas.
- Modelo de batería.
- Modelo de sensores realista.
- Estimador onboard completo.
- Identificación experimental con datos reales.

Estos elementos podrán citarse como trabajo futuro si aportan contexto, pero no deberán introducirse como requisitos de la primera versión.

## 8. Principio de justificación bibliográfica

La parte no software del TFG deberá apoyarse en bibliografía técnica cuando trate:

- Mecánica de vuelo y dinámica de vehículos.
- Dinámica de cuerpo rígido.
- Representación de actitud con cuaterniones.
- Métodos de integración numérica.
- Control clásico.
- Aprendizaje automático y aprendizaje por imitación.

Las referencias no sustituyen al razonamiento propio del TFG, pero deben justificar que los modelos y métodos usados pertenecen a prácticas conocidas y defendibles.

## 9. Principio de software científico simple

El software seguirá un enfoque de código científico simple. Se permite usar herramientas modernas, pero solo cuando aporten claridad, reproducibilidad o capacidad experimental.

Las `dataclasses` se usarán preferentemente para:

- Estados físicos.
- Referencias de trayectoria.
- Comandos de control.
- Parámetros de configuración.
- Resultados o muestras de telemetría.

No se usarán `dataclasses` para encapsular lógica compleja si una función o clase explícita resulta más clara.

## 10. Política de librerías

Se consideran aceptables las librerías científicas estándar:

- NumPy para cálculo vectorial.
- SciPy si aporta métodos numéricos o utilidades justificadas.
- Matplotlib para visualización.
- PyTorch para modelos neuronales y entrenamiento.

Cualquier dependencia adicional deberá justificarse por beneficio técnico claro. Si una librería simplifica una parte importante del trabajo, podrá discutirse antes de incorporarla.

## 11. Criterio académico de calidad

Un resultado se considerará aceptable si:

- Está conectado con un requisito documentado.
- Tiene una justificación física, matemática o experimental.
- Puede reproducirse.
- Puede evaluarse con una métrica definida.
- Sus limitaciones están declaradas.

El objetivo no será demostrar que el control neuronal siempre es mejor que el clásico, sino comparar ambos de forma honesta y trazable.

## 12. Referencias iniciales

- Stevens, B. L., Lewis, F. L., & Johnson, E. N. (2015). *Aircraft Control and Simulation: Dynamics, Controls Design, and Autonomous Systems*. Wiley.
- Beard, R. W., & McLain, T. W. (2012). *Small Unmanned Aircraft: Theory and Practice*. Princeton University Press.
- Diebel, J. (2006). *Representing Attitude: Euler Angles, Unit Quaternions, and Rotation Vectors*. Stanford University.
- Hairer, E., Nørsett, S. P., & Wanner, G. (1993). *Solving Ordinary Differential Equations I: Nonstiff Problems*. Springer.
- Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning*. MIT Press.
- Sutton, R. S., & Barto, A. G. (2018). *Reinforcement Learning: An Introduction*. MIT Press.
- Ross, S., Gordon, G., & Bagnell, D. (2011). A reduction of imitation learning and structured prediction to no-regret online learning. *Proceedings of AISTATS*.
