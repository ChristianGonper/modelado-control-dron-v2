# Índice detallado y línea narrativa de la memoria

## Historia central

La memoria debe responder a una pregunta única: **cómo construir un banco de
simulación trazable que permita comparar de forma honesta un controlador clásico
con controladores neuronales entrenados por imitación**. La narración avanza
desde el problema y los fundamentos necesarios, pasa por la construcción del
simulador y de los controladores, define un experimento reproducible y termina
interpretando qué demuestra realmente la evidencia.

En la clase LaTeX actual, cada `\section` funciona como capítulo principal. Las
subsecciones siguientes constituyen el índice detallado previsto.

## Capítulo 1. Introducción

### 1.1 Motivación y contexto

Presentará el interés del seguimiento autónomo de trayectorias y la dificultad
de comparar controladores clásicos y aprendidos bajo condiciones equivalentes.
Introducirá la necesidad de un simulador propio como instrumento académico
trazable, no como gemelo digital de alta fidelidad.

### 1.2 Problema y pregunta de investigación

Formulará con precisión qué se compara: controladores PD especializados y transferidos
frente a políticas neuronales outer-force entrenadas por imitación. Dejará claro
que el objetivo no es demostrar superioridad universal, sino estudiar
rendimiento, transferencia y generalización dentro del modelo adoptado.

### 1.3 Objetivos

Separará el objetivo general de los objetivos específicos: modelar, implementar,
verificar, generar expertos, entrenar MLP/GRU/LSTM y comparar en `test` y OOD.
Cada objetivo deberá poder conectarse posteriormente con un método y un
resultado.

### 1.4 Alcance, hipótesis y limitaciones

Delimitará el cuerpo rígido 6DOF, drag lineal, viento constante, ruido simple y
actuadores simplificados. Excluirá explícitamente vuelo real, aerodinámica
formal, sensores realistas, batería y estimación onboard.

### 1.5 Contribuciones y estructura de la memoria

Resumirá las contribuciones técnicas y experimentales sin anticipar conclusiones
no sustentadas. Cerrará explicando el orden de los capítulos y la lógica que
conecta fundamentos, desarrollo, metodología, resultados y discusión.

## Capítulo 2. Estado del arte

### 2.1 Modelado y simulación de cuadricópteros

Revisará los modelos habituales de cuerpo rígido 6DOF, sus sistemas de
referencia y las ecuaciones de Newton-Euler. Situará las ecuaciones empleadas en
el trabajo y justificará qué efectos físicos se conservan o simplifican.

### 2.2 Representación de actitud e integración numérica

Explicará las ventajas de los cuaterniones frente a ángulos de Euler y la
necesidad de conservar su norma. Presentará RK4 y la simulación multirrate como
base para integrar física, control y telemetría.

### 2.3 Control clásico de cuadricópteros

Describirá el control en cascada con lazo externo de posición y lazo interno de
actitud. Revisará métodos clásicos de sintonización PD/PID y preparará la
justificación de por qué se adopta una búsqueda progresiva determinista.

### 2.4 Aprendizaje por imitación aplicado al control

Definirá aprendizaje por imitación supervisada, experto, demostración y
desplazamiento de distribución. Diferenciará este enfoque del aprendizaje por
refuerzo y explicará por qué el rendimiento debe evaluarse también en bucle
cerrado.

### 2.5 Arquitecturas neuronales consideradas

Explicará MLP, GRU y LSTM, citando los trabajos donde se introducen o consolidan.
Comparará la ausencia de memoria explícita de la MLP con los estados recurrentes
y mecanismos de compuerta de GRU/LSTM.

### 2.6 Posicionamiento del trabajo

Relacionará las decisiones anteriores con la pregunta del TFG y mostrará el
hueco concreto que cubre el banco desarrollado. Evitará una enumeración de
simuladores y se centrará en trazabilidad física, reproducibilidad y comparación.

## Capítulo 3. Simulador 6DOF desarrollado

### 3.1 Requisitos, convenciones e hipótesis

Presentará el estado del vehículo, mundo ENU, cuerpo FRD, origen en el centro de
gravedad y convención de empuje en `-Z_B`. Toda ecuación posterior dependerá de
estas convenciones.

### 3.2 Cinemática y dinámica del cuerpo rígido

Desarrollará las ecuaciones traslacionales, rotacionales y cinemáticas de
cuaterniones implementadas. Incluirá un fragmento breve de
`dynamics/rigid_body.py` para mostrar la correspondencia entre ecuación y código.

### 3.3 Actuadores y mezclador

Explicará la relación cuadrática entre velocidad, empuje y par, junto con
retardo, lag y saturación. Describirá la matriz de asignación y la prioridad de
actitud frente al empuje colectivo cuando la demanda no es realizable.

### 3.4 Perturbaciones y límites físicos

Documentará drag lineal, viento constante y ruido de observación, indicando sus
unidades y simplificaciones. Declarará por qué estos modelos permiten ensayos de
robustez sin constituir aerodinámica ni sensores realistas.

### 3.5 Trayectorias y escenarios reproducibles

Presentará las familias `hold`, `circle`, `lissajous`, `waypoint`, `lemniscate`
y `composite`. Explicará los escenarios YAML como contrato reproducible entre
configuración, ejecución y resultados.

### 3.6 Integración multirrate y flujo de simulación

Narrará el ciclo referencia-observación-control-mezclador-actuadores-telemetría-
RK4. Mostrará cómo los pasos de física, control y telemetría se separan mediante
retención de orden cero.

### 3.7 Telemetría, métricas y reproducibilidad

Explicará qué se registra y cómo `metrics.json` conserva configuración efectiva,
comando, entorno, hashes y estado Git. Distinguirá métricas físicas de índices
heurísticos y justificará las métricas que se usarán en resultados.

### 3.8 Verificación del simulador

Relacionará requisitos, pruebas automáticas y escenarios de sanidad. No
presentará los tests como validación de vuelo real, sino como evidencia de
coherencia interna y prevención de regresiones.

### 3.9 Decisiones de implementación

Justificará Python por su ecosistema científico, integración con PyTorch,
legibilidad y carácter abierto. Incluirá una defensa sobria del software
open-source como facilitador de inspección, reproducción y extensión.

## Capítulo 4. Control clásico

### 4.1 Arquitectura en cascada

Explicará el lazo externo que produce fuerza deseada ENU y el lazo interno que
la convierte en actitud, empuje y momentos. Un fragmento breve de
`compute_desired_force_W` servirá para conectar formulación e implementación.

### 4.2 Ecuaciones, ganancias y límites

Desarrollará los errores de posición, velocidad y actitud, las ganancias
efectivas y las saturaciones. Declarará que la implementación es PD en cascada
aunque se conserve la denominación habitual PID en la narrativa experimental.

### 4.3 Alternativas de sintonización

Revisará métodos manuales, Ziegler-Nichols, optimización basada en modelo y
búsquedas numéricas. Explicará por qué no se aplican directamente y qué ventajas
ofrece la búsqueda progresiva determinista bajo escenarios simulados.

### 4.4 Sintonización y congelación de los controladores

Describirá el tuneo exclusivo sobre `train`, sus filtros duros, semilla,
presupuesto de candidatos y artefactos generados. Separará PD inicial, PD base
congelado, variantes del banco outer-force y controladores PD transferidos.

### 4.5 Baseline y transferencia cruzada

Definirá el comportamiento especializado por familia y la matriz de
transferencia de controladores PD a otras trayectorias. Esta sección prepara la comparación
honesta con una red entrenada sobre demostraciones diversas.

## Capítulo 5. Control neuronal por imitación

### 5.1 Formulación híbrida outer-force

Explicará que la red sustituye únicamente el lazo externo y predice
`desired_force_W_N[3]`, mientras el lazo interno clásico estabiliza actitud.
Justificará esta frontera por seguridad, interpretabilidad y comparabilidad.

### 5.2 Construcción del experto por escenario

Describirá el banco de variantes del PID externo, los filtros de seguridad y la
selección por RMSE, esfuerzo dentro del margen del 5 % y conservadurismo en
empates. Un snippet breve mostrará que el criterio es reproducible.

### 5.3 Dataset, entradas y objetivos

Presentará las nueve entradas de `outer_force_min_v1`, el objetivo de fuerza ENU
y el uso de la observación en lugar del estado verdadero. Explicará splits,
ventanas recurrentes y prevención de fuga de información.

### 5.4 Normalización y entrenamiento

Detallará normalización ajustada solo con `train`, función de pérdida, Adam,
validación y parada temprana. Justificará las features, tamaños de red e
hiperparámetros probados, y separará fidelidad supervisada de calidad de control
cerrando el bucle.

### 5.5 MLP, GRU y LSTM implementadas

Describirá los parámetros de las tres arquitecturas y la diferencia entre
procesamiento instantáneo y memoria recurrente. La MLP se presentará como
referencia simple y GRU/LSTM como comparación de sensibilidad arquitectural.

### 5.6 Inferencia cerrada y protecciones

Explicará clipping de norma, inclinación y componente vertical, junto con el PID
interno compartido. Indicará que los porcentajes de clipping deben reportarse
para no atribuir a la red estabilidad proporcionada por las protecciones.

### 5.7 Extensiones fuera de la comparación principal

Documentará brevemente `neural_position`, que predice log-multiplicadores, y el
entrenamiento outer-force con 31 variables como rutas implementadas pero fuera
del alcance experimental principal por ahora. Evitará mezclarlas con MLP, GRU y
LSTM outer-force entrenadas con las features seleccionadas para la comparación.

## Capítulo 6. Metodología experimental

### 6.1 Preguntas e hipótesis experimentales

Convertirá los objetivos en preguntas medibles sobre especialización,
transferencia, imitación, generalización OOD y efecto de la memoria recurrente.
Cada pregunta se asociará con métricas y comparaciones concretas.

### 6.2 Diseño del dataset clásico

Describirá las 150 ejecuciones, familias, perfiles de perturbación e
inicialización coherente con la referencia. Justificará la estratificación
`train`/`val`/`test` y sus límites como prueba de generalización.

### 6.3 Diseño del dataset de imitación

Explicará cómo cada condición clásica se convierte en una demostración segura
outer-force. Detallará artefactos, selección de experto y trazabilidad hasta la
telemetría utilizada para entrenar.

### 6.4 Configuración de entrenamiento

Recogerá hiperparámetros, semillas, dispositivo, ventanas y criterio de selección
de checkpoints. Indicará qué parámetros se probaron y cómo se evitó usar `test`
u OOD para tomar decisiones.

### 6.5 Escenarios `test`, transferencia y OOD

Separará evaluación in-distribution, transferencia cruzada y batería OOD. La
lemniscata, las trayectorias compuestas y otras condiciones OOD se presentarán
como ensayos distintos, no como parte del entrenamiento.

### 6.6 Métricas y criterios de éxito

Definirá RMSE, MAE, error máximo, saturación, degradación, clipping, éxito de
misión y seguridad. Explicará por qué completar una misión y evitar un fallo
físico son criterios diferentes.

### 6.7 Campaña automatizada y reproducibilidad

Describirá las once fases de la campaña y los artefactos consolidados en
`results/`. Indicará cómo regenerar evidencia y qué metadatos deben acompañar a
cualquier resultado usado en la memoria.

## Capítulo 7. Resultados

### 7.1 Comprobaciones previas

Presentará la cobertura de la campaña, ejecuciones válidas y posibles ausencias.
Antes de comparar controladores, verificará que la evidencia pertenece a una
misma condición experimental reproducible.

### 7.2 Rendimiento en `test`

Comparará controladores PD congelados, baseline representativo y MLP/GRU/LSTM por familia.
Separará precisión de seguimiento, éxito y coste de actuación.

### 7.3 Transferencia de los controladores clásicos

Mostrará qué ocurre al aplicar cada controlador PD especializado fuera de su familia.
Este resultado establecerá el baseline adecuado para discutir generalización.

### 7.4 Rendimiento fuera de distribución

Comparará controladores en lemniscatas, composiciones y otras condiciones OOD.
Analizará conjuntamente RMSE, éxito de misión, seguridad y degradación.

### 7.5 Comparación entre MLP, GRU y LSTM

Evaluará si la memoria recurrente aporta ventajas consistentes o introduce
degradaciones en determinadas familias. Evitará concluir a partir de una única
métrica agregada.

### 7.6 Saturación, degradación y clipping

Comprobará cuándo el rendimiento depende de límites físicos o protecciones de
fuerza. Esta sección permitirá interpretar estabilidad y errores sin ocultar el
papel del controlador interno.

### 7.7 Síntesis de resultados

Responderá de forma compacta a cada pregunta experimental antes de entrar en la
discusión. No añadirá explicaciones causales que no estén respaldadas por las
figuras, tablas o telemetrías.

## Capítulo 8. Discusión

### 8.1 Interpretación respecto a los objetivos

Relacionará los resultados con la pregunta inicial y distinguirá especialización,
transferencia y generalización. Explicará qué afirmaciones quedan demostradas y
cuáles solo son indicios.

### 8.2 Control clásico frente a imitación

Discutirá las ventajas de interpretabilidad y ajuste especializado del PID y la
capacidad de las redes para condensar demostraciones diversas. Considerará la
dependencia del experto y del lazo interno compartido.

### 8.3 Papel de la arquitectura neuronal

Interpretará las diferencias entre MLP, GRU y LSTM a la luz de sus mecanismos y
de las trayectorias ensayadas. Evitará atribuir causalidad arquitectural cuando
la evidencia solo muestre correlación.

### 8.4 Validez, limitaciones y amenazas

Tratará fidelidad física, representatividad de escenarios, semillas, evidencia
local no versionada y ausencia de validación real. Delimitará expresamente la
validez de las conclusiones.

### 8.5 Reproducibilidad y software abierto

Valorará el papel de escenarios declarativos, metadatos, pruebas, herramientas
abiertas y publicación del repositorio. No presentará la infraestructura de
software como contribución principal, sino como soporte del rigor experimental.

## Capítulo 9. Conclusiones y trabajo futuro

### 9.1 Conclusiones

Responderá de forma directa a los objetivos y preguntas experimentales. Separará
contribuciones desarrolladas, resultados observados y límites de interpretación.

### 9.2 Trabajo futuro

Priorizará validación con datos reales, modelos físicos más completos, mejores
sensores/estimadores y ampliación controlada de los enfoques neuronales.
`neural_position` podrá presentarse aquí como extensión ya implementada que
requiere una evaluación propia.

## Anejos

### Anejo 1. Comandos y trazabilidad experimental

Recogerá únicamente comandos ejecutados o congelados para regenerar la evidencia
final, junto con las versiones y rutas de artefactos. El repositorio completo se
enlazará mediante nota al pie; en el cuerpo solo aparecerán snippets breves con
valor explicativo.
