# Índice detallado congelado de la memoria

## Estado y criterio de uso

Esta es la estructura congelada para la primera versión completa de la memoria.
Puede ajustarse si aparece una necesidad académica real, pero no debe modificarse
por conveniencia durante la redacción. Cada apartado tiene una función narrativa
distinta y debe cerrarse siguiendo `metodologia_redaccion.md`.

La clase LaTeX actual utiliza `\section` para los capítulos principales y
`\subsection` para los apartados indicados aquí. Los posibles epígrafes internos
se resolverán mediante `\subsubsection` solo cuando ayuden a separar argumentos
claramente distintos.

## Criterio de cierre y justificación

El índice se considerará cerrado solo cuando cada decisión con impacto en la
validez del trabajo quede justificada. Esto incluye decisiones de simulación,
física, modelado, ingeniería, integración numérica, control, diseño experimental
y redes neuronales. No bastará con describir qué se implementó: según proceda,
deberán explicarse la necesidad o motivación, las alternativas consideradas, el
criterio de elección, la correspondencia con la implementación o la evidencia y
las limitaciones introducidas. Cuando falte alguno de estos elementos, la
decisión se declarará pendiente y no se presentará como cerrada ni arbitraria.

Las decisiones puras de ingeniería de software sin efecto físico, metodológico,
experimental o de reproducibilidad se resumirán. La organización interna del
código, funciones auxiliares y detalles de bajo nivel se remitirán al repositorio
o, si son necesarios para reproducir la campaña, al anejo. La memoria explicará
software solo cuando ayude a comprender, auditar o reproducir el trabajo.

## Pregunta central

> ¿Es posible entrenar, a partir de demostraciones generadas por controladores PD
> ajustados para distintas familias de trayectorias y perturbaciones, una red
> neuronal que sustituya ese banco de controladores, mantenga un comportamiento
> competitivo en las condiciones conocidas y transfiera mejor a variaciones,
> composiciones y trayectorias nuevas?

La memoria debe responder progresivamente a esta pregunta. Primero establece las
bases físicas y de control; después construye un banco experimental trazable;
finalmente compara especialización, transferencia y generalización sin atribuir
a la red capacidades que realmente procedan del experto, del conjunto de datos o de las
protecciones clásicas compartidas.

## Terminología acordada

- El controlador clásico implementado se denominará **PD en cascada**.
- La ruta neuronal principal se denominará **predicción de fuerza deseada**.
  No se empleará `outer-force` en la narración ni «predicción de empuje», porque
  la red produce una fuerza en ENU y no comandos directos de rotor.
- Se utilizarán **dentro de la distribución de entrenamiento (ID)** y **fuera de
  la distribución de entrenamiento (OOD)** al introducir estos conceptos.
- MLP, GRU y LSTM con predicción de fuerza forman parte de la comparación.
  `neural_position` y las 31 variables de `outer_force_full_v1` quedan como
  extensiones.

## Fronteras entre capítulos

- El capítulo 2 presenta fundamentos, alternativas y evidencia bibliográfica;
  los modelos, parámetros y decisiones propias se desarrollan después.
- El capítulo 3 define el contrato físico y numérico del simulador. El diseño de
  los conjuntos experimentales y la clasificación ID/OOD pertenecen al capítulo
  6.
- Los capítulos 4 y 5 explican los controladores implementados. El protocolo que
  hace válida su comparación, incluidos splits, semillas y criterios de éxito,
  se fija en el capítulo 6.
- El capítulo 6 es la fuente de verdad para el diseño experimental, las métricas
  y la reproducibilidad de la campaña.
- El capítulo 7 presenta evidencia y el capítulo 8 la interpreta; ninguno debe
  introducir a posteriori criterios de evaluación o decisiones metodológicas.

# Capítulo 1. Introducción

## 1.1 Motivación y contexto

**Función narrativa.** Presentar el seguimiento autónomo de trayectorias como un
problema que combina dinámica, control y evaluación, y explicar por qué comparar
controladores requiere condiciones equivalentes y trazables.

**Preguntas que debe responder.**

- ¿Qué problema aeroespacial y de control se estudia?
- ¿Por qué resulta interesante reducir la dependencia de un banco de
  controladores especializados?
- ¿Por qué se necesita un entorno de simulación controlable para responderlo?

**Elementos previstos.** Contexto breve sobre cuadricópteros, especialización de
controladores y motivación de una política aprendida común. Diagrama inicial de
la pregunta y estrategia experimental.

## 1.2 Problema y pregunta de investigación

**Función narrativa.** Formular de manera inequívoca la pregunta central y
delimitar qué significa que una red «sustituya» o transfiera mejor que el banco.

**Preguntas que debe responder.**

- ¿Qué controladores se comparan y bajo qué condiciones?
- ¿Qué significa rendimiento competitivo, transferencia y generalización?
- ¿Qué no pretende demostrar el trabajo?

**Elementos previstos.** Definición de PD especializado, PD transferido y red de
predicción de fuerza deseada. Distinción entre familias vistas, variaciones,
composiciones y trayectorias completamente nuevas.

## 1.3 Objetivos

**Función narrativa.** Convertir la pregunta central en objetivos verificables.

**Preguntas que debe responder.**

- ¿Qué debe construirse antes de poder comparar?
- ¿Qué experimentos permiten responder cada parte de la pregunta?
- ¿Qué evidencia demostrará el cumplimiento de cada objetivo?

**Elementos previstos.** Objetivo general y objetivos específicos conectados con
modelo, simulador, PD, demostraciones, MLP/GRU/LSTM y niveles de evaluación.

## 1.4 Alcance, hipótesis y limitaciones

**Función narrativa.** Evitar que los resultados se interpreten fuera del modelo
y condiciones realmente estudiados.

**Preguntas que debe responder.**

- ¿Qué fenómenos físicos, perturbaciones y sensores se representan?
- ¿Qué simplificaciones se aceptan y con qué consecuencias?
- ¿Por qué este trabajo no equivale todavía a validar un dron real?

**Elementos previstos.** Cuerpo rígido 6DOF, actuadores simplificados, drag,
viento, ruido y límites de validez.

Las hipótesis de este apartado son hipótesis y simplificaciones del modelo. Las
hipótesis experimentales comprobables se formularán en 6.1.

## 1.5 Contribuciones y estructura de la memoria

**Función narrativa.** Resumir la aportación sin anticipar conclusiones y guiar
al lector por la secuencia de capítulos.

**Preguntas que debe responder.**

- ¿Qué aporta el trabajo frente a limitarse a aplicar herramientas existentes?
- ¿Cómo contribuye cada capítulo a responder la pregunta central?

**Elementos previstos.** Banco trazable, campaña reproducible y comparación
escalonada entre especialización, transferencia y generalización.

# Capítulo 2. Estado del arte

## 2.1 Simulación de cuadricópteros y elección de un banco propio

**Función narrativa.** Situar las alternativas existentes y preparar la decisión
de desarrollar un simulador acotado y completamente controlable.

**Preguntas que debe responder.**

- ¿Qué aportan plataformas comerciales como MATLAB/Simulink?
- ¿Qué ofrece RotorPy y por qué su alcance no coincide exactamente con este TFG?
- ¿Qué control, trazabilidad o adaptación aporta construir un banco propio?

**Fuentes necesarias.** Documentación oficial y publicaciones de las
plataformas. Las afirmaciones sobre coste, apertura o complejidad deberán
delimitarse y citarse.

**Elementos previstos.** Tabla comparativa breve de capacidades relevantes, sin
convertir el apartado en un catálogo de simuladores.

## 2.2 Modelado dinámico, actitud e integración

**Función narrativa.** Establecer las bases físicas y numéricas necesarias para
comprender las decisiones del simulador.

**Preguntas que debe responder.**

- ¿Cómo se modela un cuadricóptero como cuerpo rígido 6DOF?
- ¿Por qué se usan ecuaciones de Newton--Euler y cuaterniones?
- ¿Qué aporta RK4 y una ejecución con diferentes frecuencias?

**Elementos previstos.** Ecuaciones generales y fuentes académicas. La aplicación
concreta y los parámetros propios se reservarán para el capítulo 3.

## 2.3 Control clásico y métodos de sintonización

**Función narrativa.** Explicar el control PD en cascada y presentar las
alternativas de sintonización que permitirán justificar la búsqueda progresiva.

**Preguntas que debe responder.**

- ¿Por qué se separan posición y actitud?
- ¿Qué aportan los términos proporcional y derivativo?
- ¿Cómo funcionan el ajuste manual, Ziegler--Nichols, métodos basados en modelo
  y búsquedas numéricas?
- ¿Qué limitaciones presentan para múltiples trayectorias y restricciones?

**Conexión posterior.** Este apartado debe preparar explícitamente la elección
descrita en 4.3 y 4.4.

## 2.4 Aprendizaje por imitación y control híbrido

**Función narrativa.** Justificar la elección del aprendizaje por imitación y de
una frontera híbrida frente a un controlador completamente aprendido.

**Preguntas que debe responder.**

- ¿Qué son experto, demostración, clonación de comportamiento y desplazamiento
  de distribución?
- ¿Por qué imitar acciones no equivale a minimizar error de posición?
- ¿Por qué se conserva un lazo clásico interno?
- ¿Cómo mantiene este enfoque una conexión explícita con dinámica y control
  aeroespacial?

**Elementos previstos.** Diferencia frente a aprendizaje por refuerzo y mención
conceptual de DAgger como alternativa no implementada.

## 2.5 Fundamentos de redes neuronales

**Función narrativa.** Dar al lector la base mínima necesaria para comprender las
arquitecturas y su implementación.

Este apartado se limitará a los fundamentos necesarios para leer el capítulo 5;
no desarrollará una introducción general al aprendizaje profundo.

### 2.5.1 Tensores, capas y no linealidad

Explicará tensores, capas lineales, pesos, sesgos, lotes y secuencias. Mostrará
por qué encadenar solo operaciones lineales no proporciona la capacidad de
aproximación buscada y situará la función ReLU empleada.

### 2.5.2 Perceptrón multicapa

Explicará la MLP como referencia sin memoria explícita, su estructura por capas
y su relación con una predicción basada en la muestra actual.

### 2.5.3 Redes recurrentes GRU y LSTM

Explicará estado oculto, ventanas temporales y mecanismos de compuerta. Comparará
la mayor memoria explícita de GRU/LSTM con su coste y complejidad.

**Fuentes necesarias.** Trabajos originales o fuentes académicas fundamentales
de MLP, ReLU, LSTM y GRU.

## 2.6 Posicionamiento del trabajo

**Función narrativa.** Unir simulación, control e imitación para explicar la
contribución concreta del TFG.

**Preguntas que debe responder.**

- ¿Qué hueco cubre el banco personalizado?
- ¿Por qué la comparación no es solo entre arquitecturas neuronales?
- ¿Cómo se conserva trazabilidad desde las ecuaciones hasta los resultados?

**Elementos previstos.** Diagrama de posicionamiento entre control clásico,
control completamente aprendido y enfoque híbrido.

# Capítulo 3. Simulador 6DOF desarrollado

## 3.1 Requisitos, convenciones e hipótesis

**Función narrativa.** Fijar el contrato físico del simulador antes de presentar
ecuaciones o resultados.

**Preguntas que debe responder.**

- ¿Cuáles son el estado, las entradas y las salidas?
- ¿Cómo se definen mundo ENU, cuerpo FRD, signos y unidades?
- ¿Qué hipótesis simplificadoras se adoptan?

**Elementos previstos.** Diagrama SVG de marcos ENU/FRD y tabla de convenciones.

## 3.2 Vehículo de referencia y parámetros físicos

**Función narrativa.** Presentar y defender el cuadricóptero elegido como base de
todos los experimentos.

**Preguntas que debe responder.**

- ¿Por qué se eligen masa, geometría, inercia y coeficientes de propulsión?
- ¿Representan un vehículo real, uno típico o un caso académico controlado?
- ¿Cómo afectan estos valores a autoridad de control y límites?

**Evidencia actual.** Valores implementados en el conjunto de datos y escenarios.

**Pendiente principal.** Aportar fuente o criterio defendible para los valores
numéricos; no existe todavía una justificación suficiente.

## 3.3 Cinemática y dinámica del cuerpo rígido

**Función narrativa.** Aplicar las bases del estado del arte al modelo concreto
implementado.

**Preguntas que debe responder.**

- ¿Cómo se calculan aceleraciones lineales, angulares y evolución de actitud?
- ¿Cómo se transforman fuerzas entre ENU y FRD?
- ¿Cómo se conserva la norma del cuaternión?

**Elementos previstos.** Ecuaciones completas y snippet breve que demuestre su
correspondencia con `dynamics/rigid_body.py`.

## 3.4 Actuadores, mezclador y límites de actuación

**Función narrativa.** Explicar cómo una intención de control acaba convirtiéndose
en actuación física limitada.

**Preguntas que debe responder.**

- ¿Cómo se relacionan velocidad de rotor, empuje y par?
- ¿Cómo asigna el mezclador empuje colectivo y momentos?
- ¿Por qué se modelan retardo, dinámica de primer orden y saturación?
- ¿Qué ocurre cuando una orden no es realizable?

**Elementos previstos.** Diagrama de cadena de actuación y tabla de límites.

**Pendiente principal.** Justificar tanto la forma de los modelos como sus
parámetros: ley cuadrática, configuración del mezclador, dinámica de primer orden,
retardo, saturaciones y tratamiento de órdenes no realizables.

## 3.5 Perturbaciones, observación y seguridad

**Función narrativa.** Definir las incertidumbres y protecciones que condicionan
los experimentos.

**Preguntas que debe responder.**

- ¿Por qué se seleccionan drag lineal, viento constante y ruido gaussiano?
- ¿Qué representan y qué no representan?
- ¿Cómo se definen límite de vuelco, impacto y saturación persistente?
- ¿Por qué se han escogido esos umbrales?

**Pendiente principal.** Justificar los valores concretos, incluido el límite de
actitud y los perfiles de perturbación.

## 3.6 Trayectorias y escenarios reproducibles

**Función narrativa.** Explicar las familias como estímulos experimentales, no
solo como funciones geométricas.

**Preguntas que debe responder.**

- ¿Qué habilidad exige `hold`, círculo, Lissajous y waypoint?
- ¿Por qué se eligen esas geometrías, velocidades y duraciones?
- ¿Cómo fijan los YAML una condición reproducible?

**Elementos previstos.** Figura conjunta de las familias y tabla que relacione
cada trayectoria con la capacidad evaluada.

Las composiciones y trayectorias reservadas para evaluación, como lemniscatas o
waypoints helicoidales, se definirán y clasificarán en 6.7, no como familias de
entrenamiento de este apartado.

## 3.7 Flujo multirrate de simulación

**Función narrativa.** Mostrar el flujo completo desde referencia hasta nuevo
estado y telemetría.

**Preguntas que debe responder.**

- ¿Por qué física, control y telemetría usan periodos distintos?
- ¿Cómo se aplica la retención de orden cero?
- ¿En qué orden se actualizan observación, control, actuadores y dinámica?

**Elementos previstos.** Diagrama SVG del ciclo multirrate.

**Pendiente principal.** Justificar los periodos concretos, la retención de orden
cero y el orden de actualización por su efecto numérico y sobre el control, no
por la estructura interna del programa.

## 3.8 Telemetría, métricas, verificación y trazabilidad

**Función narrativa.** Declarar la telemetría necesaria para el análisis y las
comprobaciones que sostienen la coherencia interna del simulador, sin convertir
el apartado en documentación de pruebas de software.

**Preguntas que debe responder.**

- ¿Qué variables y metadatos se registran?
- ¿Qué verifican las pruebas y escenarios de sanidad?
- ¿Qué diferencia existe entre verificación interna y validación real?

**Elementos previstos.** Tabla breve de variables, unidades y metadatos
esenciales. La trazabilidad detallada, los comandos y los artefactos se
concentrarán en 6.9 y en el Anejo 1.

## 3.9 Elección del entorno de implementación

**Función narrativa.** Justificar brevemente Python y el banco propio como medios
al servicio del experimento, remitiendo la comparación de plataformas a 2.1 y
los detalles de código al repositorio.

**Preguntas que debe responder.**

- ¿Por qué Python resulta adecuado para simulación y redes neuronales?
- ¿Qué requisitos físicos, experimentales y de reproducibilidad satisface?
- ¿Qué limitaciones introduce esta elección?

**Elementos previstos.** Síntesis breve y enlace al repositorio. No se repetirán
la tabla de 2.1 ni detalles de arquitectura, clases o funciones sin efecto en la
comprensión del experimento.

# Capítulo 4. Control clásico

## 4.1 Arquitectura PD en cascada

**Función narrativa.** Explicar el controlador que sirve de referencia, experto y
lazo interno compartido.

**Preguntas que debe responder.**

- ¿Cómo convierte el lazo externo errores de posición y velocidad en fuerza?
- ¿Cómo transforma el lazo interno esa fuerza en actitud, empuje y momentos?
- ¿Por qué es útil esta separación?

**Elementos previstos.** Diagrama de bloques y snippet breve del cálculo de
fuerza deseada.

## 4.2 Ecuaciones, ganancias y límites

**Función narrativa.** Documentar exactamente el comportamiento implementado.

**Preguntas que debe responder.**

- ¿Qué términos de referencia y compensación gravitatoria se emplean?
- ¿Por qué el controlador es PD y no PID?
- ¿Qué saturaciones y límites protegen la simulación?

**Elementos previstos.** Ecuaciones y tabla de ganancias/límites finalmente
congelados.

**Pendiente principal.** Justificar la elección de PD frente a PID, los términos
incluidos y omitidos, las ganancias y cada saturación o límite relevante.

## 4.3 Elección del método de sintonización

**Función narrativa.** Pasar de las alternativas del estado del arte a una
decisión propia razonada.

**Preguntas que debe responder.**

- ¿Por qué no se utiliza directamente ajuste manual, Ziegler--Nichols u otro
  método basado en modelo?
- ¿Por qué evaluar candidatos en los escenarios simulados resulta coherente con
  el objetivo?
- ¿Qué ventajas y limitaciones tiene una búsqueda determinista?

**Pendiente principal.** Incorporar la valoración del autor y fuentes sobre las
alternativas.

## 4.4 Algoritmo de búsqueda progresiva

**Función narrativa.** Hacer reproducible el tuneo y justificar sus decisiones no
triviales.

**Preguntas que debe responder.**

- ¿Cómo funcionan diagnóstico, generación de candidatos y refinamiento?
- ¿Por qué se usan esos multiplicadores, presupuesto, semilla y umbrales?
- ¿Cómo intervienen filtros duros, penalizaciones y esfuerzo?
- ¿Qué evita que el tuneo favorezca una solución insegura?

**Elementos previstos.** Diagrama del algoritmo, pseudocódigo y tabla de pesos,
umbrales y justificaciones.

**Pendiente principal.** Justificar multiplicadores, presupuesto, semilla,
filtros, penalizaciones y umbrales; distinguir criterios fundamentados de
elecciones heurísticas y analizar su sensibilidad cuando sea necesario.

## 4.5 Controladores congelados y transferencia cruzada

**Función narrativa.** Definir el banco clásico que después se intenta condensar.

**Preguntas que debe responder.**

- ¿Cómo se congela un controlador por familia sin contaminar prueba?
- ¿Qué significa especialización?
- ¿Qué revela aplicar cada PD a las demás familias?

**Elementos previstos.** Matriz conceptual de transferencia que preparará el
resultado equivalente.

# Capítulo 5. Control neuronal por imitación

## 5.1 Formulación híbrida de predicción de fuerza deseada

**Función narrativa.** Explicar qué sustituye la red, qué permanece clásico y por
qué esta frontera resulta adecuada.

**Preguntas que debe responder.**

- ¿Qué entradas recibe la red y qué fuerza tridimensional predice?
- ¿Por qué no predice directamente empuje y momentos?
- ¿Cómo conserva el lazo interno una base de ingeniería aeroespacial?
- ¿Qué comparabilidad y protecciones aporta el diseño híbrido?

**Elementos previstos.** Diagrama SVG del controlador híbrido.

**Pendiente principal.** Justificar la frontera híbrida frente a predecir
actuación directa u otras variables, indicando ventajas, alternativas y límites
de comparabilidad.

## 5.2 Construcción y selección de demostraciones

**Función narrativa.** Explicar de dónde procede el comportamiento que aprende la
red.

**Preguntas que debe responder.**

- ¿Por qué se generan variantes del PD externo para cada escenario?
- ¿Cómo se selecciona un experto seguro?
- ¿Por qué se acepta un margen del 5 % y se desempata por esfuerzo?
- ¿Qué sesgos introduce aprender exclusivamente de estos expertos?

**Elementos previstos.** Pseudocódigo o snippet breve del criterio de selección.

**Pendiente principal.** Justificar el número de variantes, el margen del 5 %, el
desempate por esfuerzo y los criterios de seguridad, además del sesgo que estas
decisiones trasladan al conjunto de demostraciones.

## 5.3 Tensores, variables de entrada, objetivos y secuencias

**Función narrativa.** Aplicar los fundamentos neuronales al conjunto de datos
real, sin repetir la teoría del apartado 2.5.

**Preguntas que debe responder.**

- ¿Cómo se representan muestras, lotes y ventanas como tensores?
- ¿Por qué se usan nueve variables y no las 31 disponibles?
- ¿Por qué se emplean errores y aceleración de referencia?
- ¿Por qué el objetivo es fuerza deseada y no error de posición?
- ¿Qué información aporta una ventana de 20 muestras?

**Pendiente principal.** Justificar formalmente la selección de variables y la
longitud de secuencia.

## 5.4 Arquitecturas y parámetros de MLP, GRU y LSTM

**Función narrativa.** Describir y defender las tres redes comparadas.

**Preguntas que debe responder.**

- ¿Cómo se implementa cada arquitectura?
- ¿Por qué se usa ReLU en la MLP?
- ¿Por qué 64 unidades ocultas y una capa recurrente?
- ¿Qué hipótesis se prueba al comparar memoria y ausencia de memoria?
- ¿Qué parámetros se probaron y cuáles se fijaron por defecto?

**Elementos previstos.** Tabla de arquitecturas, número de parámetros y
justificación de hiperparámetros.

**Pendiente principal.** Justificar activación, anchura, profundidad y longitud
de secuencia a partir de alternativas probadas, bibliografía o un criterio
experimental declarado; no presentar valores por defecto como decisiones
fundamentadas.

## 5.5 Normalización, entrenamiento y selección del modelo

**Función narrativa.** Documentar el pipeline de aprendizaje implementado y
separar fidelidad supervisada de calidad de control. El diseño de una comparación
justa entre arquitecturas corresponde a 6.5.

**Preguntas que debe responder.**

- ¿Por qué la normalización se ajusta solo con entrenamiento?
- ¿Por qué se usan MSE, Adam, tamaño de lote, tasa de aprendizaje y parada
  temprana?
- ¿Cómo se selecciona el checkpoint?
- ¿Por qué una pérdida baja no garantiza buen seguimiento en bucle cerrado?

**Elementos previstos.** Diagrama de entrenamiento y tabla de hiperparámetros.

**Pendiente principal.** Justificar normalización, pérdida, optimizador,
hiperparámetros, parada temprana y selección de checkpoint, indicando qué se fijó
por criterio previo y qué se eligió mediante validación.

## 5.6 Inferencia en bucle cerrado y protecciones

**Función narrativa.** Explicar cómo se despliega la red y qué parte de su
estabilidad depende de protecciones externas.

**Preguntas que debe responder.**

- ¿Cómo se limita norma, inclinación y componente vertical?
- ¿Por qué se eligieron esos límites?
- ¿Cómo se mide la activación de las protecciones?
- ¿Cómo se evita atribuir a la red una estabilidad proporcionada por el sistema
  híbrido?

**Elementos previstos.** Tabla de límites y métricas de clipping.

**Pendiente principal.** Relacionar cada protección y umbral con límites del
simulador o del controlador clásico, y declarar cuánto del comportamiento seguro
depende de estas protecciones externas a la red.

## 5.7 Alternativas implementadas fuera de la comparación

**Función narrativa.** Documentar trabajo realizado sin confundirlo con la
evidencia principal.

**Preguntas que debe responder.**

- ¿Cómo funciona `neural_position` y qué log-multiplicadores produce?
- ¿Qué aportaría entrenar con las 31 variables?
- ¿Por qué ambas rutas quedan fuera de la primera comparación?

**Conexión posterior.** Estas alternativas reaparecerán como trabajo futuro.

# Capítulo 6. Metodología experimental

## 6.1 Preguntas e hipótesis experimentales

**Función narrativa.** Traducir la pregunta central en comparaciones medibles y
predefinidas.

**Preguntas que debe responder.**

- ¿Cuánto aporta especializar un PD por familia?
- ¿Cómo se degradan esos PD al transferirlos?
- ¿Puede una red imitar fuerzas y conservar rendimiento cerrado?
- ¿Qué ocurre ante variaciones, composiciones y trayectorias nuevas?
- ¿Aporta ventaja la memoria recurrente?

**Elementos previstos.** Tabla pregunta--comparación--métrica--resultado.

## 6.2 Diseño global de la campaña

**Función narrativa.** Presentar el flujo completo antes de detallar conjuntos de
datos y evaluaciones.

**Preguntas que debe responder.**

- ¿En qué orden se verifican, generan, tunean, entrenan y evalúan artefactos?
- ¿Qué decisiones solo pueden usar entrenamiento o validación?
- ¿Cómo se evita contaminar prueba?

**Elementos previstos.** Diagrama SVG de la campaña completa.

## 6.3 Diseño del conjunto de datos clásico

**Función narrativa.** Defender la composición del conjunto que sostiene todo el
experimento.

**Preguntas que debe responder.**

- ¿Por qué se eligen cuatro familias, esas geometrías y esos perfiles?
- ¿Por qué se generan 150 episodios?
- ¿Por qué `hold` utiliza menos perturbaciones?
- ¿Cómo y por qué se dividen entrenamiento, validación y prueba?
- ¿Qué papel tiene la semilla?

**Pendiente principal.** Justificar conteos, ratios y selección concreta de
geometrías y perfiles.

## 6.4 Diseño del conjunto de datos de imitación

**Función narrativa.** Explicar cómo el conjunto clásico se transforma en
demostraciones de fuerza y qué dependencia crea respecto al experto.

**Preguntas que debe responder.**

- ¿Cómo se conserva trazabilidad entre escenario, experto y muestra?
- ¿Qué filtros impiden entrenar con demostraciones inseguras?
- ¿Qué distribución de comportamientos aprende realmente la red?

**Elementos previstos.** Tabla de artefactos y diagrama de transformación.

## 6.5 Configuración y comparación del entrenamiento

**Función narrativa.** Definir una comparación justa entre MLP, GRU y LSTM.

**Preguntas que debe responder.**

- ¿Qué hiperparámetros son comunes y cuáles dependen de la arquitectura?
- ¿Qué experimentación se realizó para elegirlos?
- ¿Cómo se controla aleatoriedad, dispositivo y selección de checkpoints?
- ¿Qué constituye una comparación equivalente?

**Elementos previstos.** Tabla final de configuraciones y semillas.

**Pendiente principal.** Declarar qué factores permanecen idénticos entre
arquitecturas, cuáles se ajustan por validación y por qué el presupuesto de
búsqueda permite una comparación defendible.

## 6.6 Evaluación en familias conocidas y transferencia clásica

**Función narrativa.** Medir rendimiento dentro de la distribución y establecer
la dificultad de sustituir el banco de PD.

**Preguntas que debe responder.**

- ¿Cómo rinden los PD nativos y las redes en familias conocidas?
- ¿Cómo se comporta cada PD especializado en las demás familias?
- ¿Qué referencia debe superar o igualar una red común?

**Elementos previstos.** Derivación explícita de los 23 escenarios de prueba y de
las 92 transferencias clásicas a partir de familias, splits y reglas de
exclusión.

## 6.7 Evaluación fuera de la distribución de entrenamiento

**Función narrativa.** Separar dos niveles distintos de novedad.

### 6.7.1 Variaciones y composiciones de familias conocidas

Evaluará geometrías, exigencias o composiciones que reutilizan capacidades
presentes en entrenamiento. Debe explicarse qué componentes son conocidos y qué
cambia.

### 6.7.2 Trayectorias completamente nuevas

Evaluará familias geométricas nuevas, como la lemniscata, separándolas de las
composiciones. Debe aclararse por qué constituyen una prueba más fuerte.

**Elementos previstos.** Tabla de clasificación de cada escenario y comparación
equivalente con PD transferidos.

## 6.8 Métricas, criterios de éxito y análisis

**Función narrativa.** Definir cómo se juzga el comportamiento antes de observar
los resultados.

**Preguntas que debe responder.**

- ¿Por qué se usan RMSE, MAE, error máximo, esfuerzo y saturación?
- ¿Qué diferencia existe entre éxito de misión y seguridad?
- ¿Cómo se interpretan degradación y activación de protecciones?
- ¿Qué métricas son físicas y cuáles heurísticas?

**Elementos previstos.** Tabla de métricas, unidades, sentido y limitaciones.

**Pendiente principal.** Justificar métricas, agregaciones, umbrales de éxito y
criterios de seguridad antes de observar resultados; identificar expresamente
los criterios heurísticos y realizar análisis de sensibilidad cuando condicionen
las conclusiones.

## 6.9 Reproducibilidad y validez de la evidencia

**Función narrativa.** Establecer qué condiciones debe cumplir un resultado para
entrar en la memoria.

Este apartado concentra el detalle reproducible de la campaña. Los comandos y
listados extensos se remitirán al Anejo 1.

**Preguntas que debe responder.**

- ¿Qué comandos, hashes, configuraciones y metadatos se conservan?
- ¿Cómo se comprueba que toda la campaña pertenece a una misma revisión?
- ¿Qué resultados se excluyen y por qué?

# Capítulo 7. Resultados

## 7.1 Cobertura y comprobaciones previas

**Función narrativa.** Verificar la evidencia antes de comparar controladores.

**Resultados previstos.** Tabla de ejecuciones esperadas, válidas, fallidas y
excluidas; revisión de metadatos y condiciones comparables.

## 7.2 Rendimiento en familias conocidas

**Función narrativa.** Comparar PD nativos y MLP/GRU/LSTM dentro de la
distribución de entrenamiento.

**Visualizaciones previstas.** RMSE y éxito por familia, distribución de error y
tabla de precisión, seguridad y actuación.

## 7.3 Transferencia cruzada de controladores PD

**Función narrativa.** Mostrar el coste de mantener controladores especializados
y establecer el baseline de transferencia.

**Visualizaciones previstas.** Mapa de calor controlador--familia y tabla de
degradación respecto al PD nativo.

## 7.4 Variaciones y composiciones de familias conocidas

**Función narrativa.** Evaluar si los controladores combinan o extrapolan
capacidades ya presentes en entrenamiento.

**Visualizaciones previstas.** Comparaciones por escenario y trayectoria,
separadas de las familias completamente nuevas.

## 7.5 Trayectorias completamente nuevas

**Función narrativa.** Evaluar la prueba más fuerte de generalización geométrica.

**Visualizaciones previstas.** Seguimiento espacial y métricas para lemniscatas u
otras familias nuevas, con PD transferido como referencia.

## 7.6 Comparación entre MLP, GRU y LSTM

**Función narrativa.** Sintetizar transversalmente los resultados ya presentados
en 7.2--7.5 para determinar si la memoria recurrente aporta ventajas
consistentes, sin repetir tablas o figuras por escenario.

**Visualizaciones previstas.** Resultado por arquitectura y categoría de
evaluación; evitar una única media que oculte fallos.

## 7.7 Fidelidad de imitación, actuación y protecciones

**Función narrativa.** Relacionar error de fuerza supervisado con comportamiento
cerrado y mostrar la dependencia de límites y protecciones.

**Visualizaciones previstas.** Fidelidad frente a RMSE de posición, seguimiento
frente a esfuerzo, saturación, degradación y clipping.

## 7.8 Síntesis de respuestas experimentales

**Función narrativa.** Responder de forma compacta a cada pregunta de 6.1 sin
adelantar explicaciones causales no demostradas.

**Elementos previstos.** Tabla pregunta--evidencia--respuesta--confianza.

# Capítulo 8. Discusión

## 8.1 Interpretación respecto a objetivos y pregunta central

**Función narrativa.** Integrar resultados y establecer qué se ha demostrado,
qué solo se sugiere y qué no puede concluirse.

## 8.2 Dependencia del experto y del conjunto de datos

**Función narrativa.** Dejar explícito que la red imita fuerzas del controlador y
no optimiza directamente el error de posición.

**Preguntas que debe responder.**

- ¿Cómo limita el conjunto de datos lo que la red puede aprender?
- ¿Qué ocurre si el experto se degrada bajo viento u otra perturbación?
- ¿Cuándo una red puede suavizar o combinar demostraciones y cuándo solo hereda
  sus fallos?

## 8.3 Valor y límites del enfoque híbrido

**Función narrativa.** Discutir la elección de conservar el lazo interno clásico
y el contenido aeroespacial frente a un controlador completamente caja negra.

**Preguntas que debe responder.**

- ¿Qué interpretabilidad, estabilidad estructural y comparabilidad se conserva?
- ¿Qué capacidades quedan restringidas por no aprender el control completo?
- ¿Qué parte del resultado pertenece a la red y cuál al controlador compartido?

## 8.4 Papel de la arquitectura neuronal

**Función narrativa.** Interpretar diferencias entre MLP, GRU y LSTM sin atribuir
causalidad más allá de la evidencia.

## 8.5 Validez, limitaciones y amenazas

**Función narrativa.** Delimitar los resultados por fidelidad física,
representatividad del conjunto de datos, semillas, hiperparámetros y ausencia de vuelo
real.

## 8.6 Implicaciones para la reproducibilidad

**Función narrativa.** Valorar brevemente cómo escenarios y metadatos sostienen
el rigor experimental, sin repetir el detalle de 3.8, 3.9 o 6.9 ni convertir la
discusión en una evaluación de ingeniería de software.

# Capítulo 9. Conclusiones y trabajo futuro

## 9.1 Conclusiones

**Función narrativa.** Responder directamente a la pregunta central y a cada
objetivo, separando contribución, evidencia, interpretación y límites.

## 9.2 Trabajo futuro

**Función narrativa.** Proponer una progresión realista desde el banco actual.

**Líneas previstas.**

- evaluar `neural_position` y el conjunto de 31 variables;
- ampliar y equilibrar el conjunto de datos, mejorar expertos y estudiar técnicas como
  DAgger u otras formas de refuerzo de demostraciones;
- aumentar fidelidad física, perturbaciones y complejidad de escenarios;
- identificar parámetros y validar progresivamente con hardware;
- incorporar sensores reales, IMU, posicionamiento y estimación de estado;
- estudiar percepción visual a bordo, reconocimiento y conciencia situacional;
- analizar despliegue, capacidad de cálculo, latencia y seguridad.

# Anejos

## Anejo 1. Comandos y trazabilidad experimental

Recogerá únicamente comandos y artefactos necesarios para regenerar la evidencia
final. El cuerpo de la memoria contendrá solo snippets breves con valor
explicativo y enlazará el repositorio para el resto de la implementación.

## Anejo futuro opcional. Parámetros completos

Si las tablas de parámetros físicos, controladores, conjuntos de datos y redes resultan
demasiado extensas para el cuerpo, podrán trasladarse a un segundo anejo sin
eliminar las justificaciones principales de los capítulos correspondientes.
