# Visión del demostrador interactivo de control

## Promesa

La aplicación permite comparar, ante una misma misión, un método clásico de
control y tres controladores neuronales entrenados por imitación. El usuario
puede elegir o componer una trayectoria, introducir viento, ejecutar el
experimento y explorar tanto el comportamiento visible como la ingeniería que lo
sustenta.

La pregunta que organiza la experiencia es:

> ¿Cómo se comportan los controladores neuronales, ya entrenados por imitación,
> frente al controlador clásico al afrontar trayectorias de tipos conocidos y
> diferentes?

La explicación técnica aclarará que las redes sustituyen únicamente la decisión
del lazo externo que produce la fuerza deseada; el resto del sistema de control
permanece clásico.

## Público

El público principal es el jurado del concurso, con formación en ingeniería pero
sin necesidad de especialización en control de vuelo. La experiencia también
debe resultar valiosa para estudiantes y personas del sector que quieran
profundizar.

## Responsabilidades del producto

### Experimentar

- Elegir una trayectoria existente o construir una composición de tramos
  parametrizados.
- Previsualizar la trayectoria completa en 3D, con navegación espacial.
- Añadir, editar, reordenar y eliminar tramos; no dibujar a mano alzada.
- Configurar viento como perturbación principal comprensible.
- Ejecutar siempre, bajo las mismas condiciones, el PD especializado de la
  familia y los modelos MLP, GRU y LSTM.
- Elegir después de la ejecución qué resultados visualizar, incluidos presets de
  comparación entre todos o entre un subconjunto.

No se incorporan al experimento principal los PD transferidos entre familias ni
se reentrenan modelos.

### Comprender

- Explicar con progresión el modelo, los dos lazos, el papel de las redes y el
  entrenamiento por imitación.
- Presentar primero lenguaje natural: trayectorias de tipos utilizados durante
  el aprendizaje frente a trayectorias nuevas o de tipo diferente.
- Usar ID y OOD como terminología técnica secundaria.
- Permitir profundizar en telemetría y mecanismos físicos sin convertir la
  pantalla principal en un panel exhaustivo.

### Consultar resultados

- Separar la ejecución actual de la evidencia agregada del TFG.
- Mostrar como primera lectura el RMSE de posición, si la misión se completó, la
  causa de terminación y un resumen de la intervención de protecciones.
- Reservar para la capa técnica otras series y métricas existentes: error,
  actitud, fuerza deseada y recortada, empuje, momentos, rotores, saturación,
  viento, degradación y telemetría disponible.
- No convertir una métrica aislada en un veredicto automático ni declarar un
  ganador universal.

## Reproducción

La simulación se calcula completamente antes de reproducirse. La comparación se
sincroniza principalmente por tiempo mediante un cursor común. Si una ejecución
termina antes, conserva su último estado. Una comparación por progreso de misión
puede estudiarse más adelante, pero no sustituye la referencia temporal.

## Profundidad progresiva

La vista inicial debe permitir una interacción clara: trayectoria, viento,
ejecución y comparación. A partir de ahí se revela el trabajo técnico, la
telemetría, el entrenamiento, las protecciones y los resultados agregados.
Perturbaciones como ruido, retardo, dinámica de actuadores o degradación pueden
formar parte de experimentos avanzados o demostraciones preparadas si una spec
posterior lo justifica.

## Límites actuales

- No se rediseña el simulador ni el entrenamiento.
- No se entrena durante la demostración.
- No hay dibujo libre de trayectorias.
- No se incluyen los PD cruzados en la aplicación interactiva.
- Queda pendiente especificar qué PD especializado sirve de referencia cuando
  una trayectoria nueva o compuesta no pertenece inequívocamente a una familia.
- La interfaz concreta, la arquitectura web, los componentes y el contenido de
  posibles vídeos se decidirán en specs y diseño posteriores.
