# Índice detallado de la memoria

## Estado y criterio de uso

Esta estructura incorpora las indicaciones de los tutores y sustituye el índice
anterior. Su finalidad es orientar la redacción de la memoria hacia la
contribución real del trabajo: una arquitectura de control híbrido en cascada en
la que una política neuronal única sustituye varios controladores especializados
del lazo externo, mientras se conserva el lazo interno clásico.

Los títulos numerados que aparecen en este documento deben coincidir con el
índice del PDF. Los epígrafes internos sugeridos sirven para organizar la
redacción, pero no se numerarán ni se incorporarán al índice general. La
estructura solo se modificará de nuevo por una necesidad académica o técnica
justificada.

## Título

**Español:** Control híbrido en cascada de un cuadricóptero: sustitución neuronal
de controladores especializados del lazo externo.

**Inglés:** Cascaded hybrid control of a quadcopter: neural replacement of
specialized outer-loop controllers.

## Hipótesis central

> Una política neuronal única, entrenada por imitación para predecir la fuerza
> deseada del lazo externo, puede alcanzar una capacidad de seguimiento
> competitiva frente al PD especializado de cada familia en condiciones
> conocidas y transferir mejor que los PD aplicados fuera de su familia,
> conservando el lazo interno clásico común.

La hipótesis se evaluará de forma multidimensional. No bastará una pérdida
supervisada baja ni una única media agregada: se considerarán éxito de misión,
seguridad, error de seguimiento, actuación y uso de protecciones.

## Terminología y límites narrativos

- El controlador implementado se denomina **PD en cascada**, aunque algunas
  descripciones externas utilicen PID como término genérico.
- La ruta neuronal principal realiza **predicción de fuerza deseada** en mundo
  ENU. No predice empuje de rotor ni ganancias del controlador.
- La **programación de ganancias (gain scheduling)** se presenta como técnica de
  control clásico y antecedente conceptual. La ruta `neural_position` sí aprende
  multiplicadores de ganancias, pero queda fuera de la comparación principal.
- MLP, GRU y LSTM comparten la frontera aprendida y forman parte de la
  comparación principal.
- La memoria distinguirá condiciones dentro de la distribución de entrenamiento
  (ID) y fuera de ella (OOD), separando recombinación de capacidades conocidas y
  novedad geométrica.
- No se atribuirán a la red la acción estabilizadora del lazo interno ni las
  protecciones impuestas mediante saturaciones o recorte de fuerza.

## Fronteras entre capítulos

- La introducción formula la motivación, la hipótesis y los objetivos, sin
  anticipar resultados.
- El estado del arte presenta fundamentos y alternativas bibliográficas; las
  decisiones propias se justifican en metodología.
- La metodología reúne modelo, controladores, datos, métricas y protocolo. Es la
  fuente de verdad para las condiciones de comparación.
- Los resultados experimentales presentan e interpretan la evidencia sin
  redefinir métricas ni criterios después de observarla.
- Las conclusiones valoran la hipótesis y los objetivos, y separan resultados
  demostrados de extensiones futuras.

# 1. Introducción

## 1.1 Motivación

**Función narrativa.** Presentar el seguimiento de trayectorias de un
cuadricóptero como un problema de control en cascada y explicar la limitación de
depender de controladores externos especializados.

**Contenido esencial.** Contexto aeroespacial, necesidad de un entorno experimental
común, arquitectura con lazo externo de traslación y lazo interno de actitud, y
motivación de sustituir la selección de especialistas por una política aprendida
única. Aquí se define el problema, pero no se formula una lista de preguntas de
investigación.

## 1.2 Hipótesis y objetivos

**Función narrativa.** Formular una hipótesis falsable y convertirla en objetivos
verificables.

**Contenido esencial.** Hipótesis central; objetivo general; objetivos específicos
relativos al simulador 6DOF, el conjunto de PD, las demostraciones, MLP/GRU/LSTM y la
evaluación ID/OOD. El alcance físico, las simplificaciones y las limitaciones se
integrarán mediante un epígrafe no numerado, sin constituir un cuarto apartado.

## 1.3 Estructura del documento

**Función narrativa.** Resumir la contribución y explicar la progresión desde los
fundamentos hasta la evidencia y las conclusiones.

# 2. Estado del arte

## 2.1 Simulación y modelado de cuadricópteros

**Función narrativa.** Presentar las alternativas de simulación y las bases del
modelo de cuerpo rígido 6DOF.

**Contenido esencial.** Plataformas relevantes, Newton--Euler, marcos de
referencia, cuaterniones, integración numérica y justificación de un entorno propio
acotado y trazable. Los parámetros concretos se reservan para metodología.

## 2.2 Control clásico en cascada y programación de ganancias

**Función narrativa.** Explicar la separación entre control de posición y actitud
y situar la programación de ganancias como respuesta clásica a condiciones de
operación variables.

**Contenido esencial.** PD/PID, control en cascada, sintonización y programación
de ganancias mediante selección o interpolación. Se establecerá la analogía con
la sustitución de especialistas, pero se aclarará que predecir fuerza no equivale
a interpolar ganancias.

## 2.3 Aprendizaje por imitación y control híbrido

**Función narrativa.** Justificar la clonación de comportamiento y la conservación
del lazo interno clásico.

**Contenido esencial.** Experto, demostración, desplazamiento de distribución,
evaluación en bucle cerrado y límites de los enfoques híbridos. DAgger y el
aprendizaje por refuerzo se mencionarán únicamente como alternativas no
implementadas.

## 2.4 Redes neuronales para control

**Función narrativa.** Proporcionar solo los fundamentos necesarios para entender
las arquitecturas comparadas.

### 2.4.1 Redes feedforward

Tensores, capas lineales, funciones de activación y perceptrón multicapa. La MLP
se presenta como referencia sin memoria explícita.

### 2.4.2 Redes recurrentes

Se comenzará por la RNN básica, el estado oculto y el tratamiento de secuencias.
LSTM y GRU aparecerán después mediante epígrafes internos sin numerar.

## 2.5 Posicionamiento del trabajo

**Función narrativa.** Situar la contribución entre el control clásico con conjunto
de especialistas, la programación neuronal de ganancias y el control aprendido
de fuerza con estabilización interna clásica.

# 3. Metodología

## 3.1 Modelo físico y simulador 6DOF

**Función narrativa.** Definir la interfaz física, numérica y de observación
común a todos los controladores.

**Epígrafes internos previstos.** Convenciones ENU/FRD e hipótesis; vehículo de
referencia; dinámica 6DOF; actuadores y mezclador; perturbaciones y seguridad;
trayectorias; flujo multirrate; telemetría y verificación; entorno de
implementación.

Las métricas comparativas y los splits no se definirán aquí.

## 3.2 Control clásico en cascada

**Función narrativa.** Documentar la referencia clásica, los expertos y el lazo
interno compartido.

**Epígrafes internos previstos.** Arquitectura PD; ecuaciones, ganancias y
límites; método de sintonización; búsqueda progresiva; controladores con parámetros fijados y
transferencia cruzada. Estos epígrafes no aparecerán numerados.

## 3.3 Control neuronal por imitación

**Función narrativa.** Definir la frontera aprendida y el proceso de inferencia
sin confundirlo con actuación directa ni programación de ganancias.

**Epígrafes internos previstos.** Predicción de fuerza deseada; selección de
demostraciones; entradas, objetivos y secuencias; arquitecturas; normalización y
entrenamiento; inferencia y protecciones; alternativas fuera de comparación.

## 3.4 Conjuntos de datos y métricas de desempeño

**Función narrativa.** Fijar qué datos se emplean, cómo se dividen y con qué
indicadores se juzga cada controlador.

**Epígrafes internos previstos.** Contrastes H1--H5; dataset clásico; dataset de
imitación; RMSE, MAE y error máximo; éxito de misión y seguridad; actuación,
saturación, degradación y clipping.

## 3.5 Protocolo experimental y reproducibilidad

**Función narrativa.** Establecer el orden del procedimiento experimental y las reglas que impiden
contaminación entre entrenamiento y evaluación.

**Epígrafes internos previstos.** Fases del procedimiento experimental; configuración común de
entrenamiento; evaluación ID y transferencia clásica; evaluación OOD por niveles;
criterios de inclusión de evidencia; metadatos y reproducibilidad.

# 4. Resultados experimentales

## 4.1 Cobertura y comprobaciones de validez

Verificará conteos, artefactos, metadatos, terminaciones y comparabilidad antes de
presentar métricas de rendimiento.

## 4.2 Referencia clásica y especialización

Caracterizará los PD nativos y la matriz de transferencia cruzada para establecer
la ventaja de especialización y el baseline sin reajuste.

## 4.3 Desempeño neuronal en condiciones conocidas

Comparará MLP, GRU y LSTM con los PD nativos en test ID. Relacionará fidelidad
supervisada, seguimiento cerrado, actuación y protecciones.

## 4.4 Transferencia y generalización fuera de distribución

Separará variaciones y composiciones conocidas de familias geométricas nuevas.
La comparación principal será entre la política común y los PD con parámetros fijados
transferidos sin reajuste. Arquitecturas, actuación y clipping se tratarán como
epígrafes internos, no como apartados adicionales.

## 4.5 Discusión de resultados y limitaciones

Interpretará la evidencia respecto a la hipótesis y los objetivos. Distinguirá
dependencia del experto, efecto del dataset, valor del enfoque híbrido, papel de
la arquitectura, amenazas a la validez y reproducibilidad. No repetirá H1--H5
como preguntas al inicio del apartado.

# 5. Conclusiones y trabajo futuro

## 5.1 Conclusiones

Valorará explícitamente la hipótesis central y cada objetivo, distinguiendo
resultados confirmados, resultados negativos e incertidumbres.

## 5.2 Trabajo futuro

Recogerá extensiones justificadas: programación neuronal de ganancias,
sensibilidad de hiperparámetros, mejora de datasets, aerodinámica, estimación y
validación sobre hardware. No presentará estas extensiones como capacidades
demostradas.

# Anejos

## Anejo 1. Comandos y trazabilidad experimental

Conservará los comandos necesarios para reconstruir datasets, entrenamientos,
evaluaciones y tablas, evitando trasladar detalles operativos al cuerpo principal.
