# Plan de fuentes

## Criterio

Antes de reunir artículos o iniciar un análisis extenso con la herramienta, 
debe quedar claro qué afirmación se pretende respaldar. Se priorizarán 
fuentes originales, libros académicos reconocidos, artículos revisados 
por pares y documentación oficial para describir herramientas.

## Fuentes prioritarias

### Simulación y modelado de cuadricópteros

- Modelos 6DOF de cuerpo rígido y ecuaciones de Newton--Euler aplicadas a
  cuadricópteros.
- Convenciones de sistemas de referencia y representación de actitud mediante
  cuaterniones.
- Integración RK4 y simulación con distintas frecuencias de física y control.
- Valores físicos representativos de cuadricópteros de aproximadamente
  1 kg: masa, geometría, inercia y coeficientes de propulsión.

Se necesita especialmente una fuente o criterio defendible para los parámetros
numéricos elegidos, porque actualmente están implementados pero no justificados.

### Plataformas de simulación

- Documentación oficial sobre las capacidades y licencias de MATLAB, Simulink y
  herramientas UAV relacionadas.
- Artículo y documentación oficial de RotorPy.
- Otras plataformas relevantes solo si ayudan a justificar por qué un banco
  propio, acotado y trazable resulta adecuado para esta pregunta.

Debe evitarse afirmar genéricamente que una herramienta es «caja negra»,
demasiado cerrada o excesivamente costosa sin una fuente concreta y una
comparación delimitada.

### Control clásico y sintonización

- Control en cascada de posición y actitud para cuadricópteros.
- Control PD/PID y métodos clásicos de sintonización: ajuste manual,
  Ziegler--Nichols y alternativas basadas en modelo u optimización.
- Métodos de búsqueda numérica y criterios multiobjetivo con restricciones de
  seguridad.

Estas fuentes deben permitir explicar por qué la búsqueda progresiva
determinista resulta apropiada para escenarios reproducibles y por qué no se
adoptan directamente otros métodos.

### Redes neuronales y aprendizaje por imitación

- Trabajo original o fuente académica fundamental sobre perceptrones
  multicapa.
- Trabajo original de LSTM y trabajo original de GRU.
- Función de activación ReLU y papel de las no linealidades.
- Tensores y procesamiento por lotes o secuencias, explicados con el nivel
  necesario para comprender la implementación.
- Aprendizaje por imitación, clonación de comportamiento y desplazamiento de
  distribución; incluir DAgger como referencia conceptual aunque no se
  implemente.
- Control híbrido o enfoques que combinan aprendizaje con estructuras clásicas.

Se buscarán argumentos para defender la imitación y la frontera híbrida como una
forma de conservar interpretación y contenido de ingeniería aeroespacial frente
a un controlador completamente aprendido.

### Evaluación, vuelo real y trabajo futuro

- Evaluación en condiciones dentro y fuera de la distribución de entrenamiento.
- Sensores necesarios para implementar seguimiento y estabilización en un dron
  real: IMU, estimación de actitud, posición, velocidad y percepción del entorno.
- Navegación visual, reconocimiento a bordo y conciencia situacional.
- Sim-to-real, identificación de parámetros y robustificación de datasets.

## Entregable deseado antes de usar la herramienta

Para cada bloque se reunirá:

1. una lista corta de fuentes candidatas;
2. la afirmación concreta que puede sostener cada fuente;
3. DOI, URL oficial o referencia bibliográfica verificable;
4. posibles ecuaciones o figuras que puedan citarse sin reproducir material
   protegido de forma inapropiada;
5. dudas que requieran comparar varias fuentes.

Después podrá prepararse un cuaderno temático y solicitar un informe con citas
IEEE propuestas, que deberán verificarse contra las fuentes originales.
