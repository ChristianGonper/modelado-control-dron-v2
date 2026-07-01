# Instrucciones pendientes para metodologia

Este documento recoge valoraciones metodologicas que no deben aparecer como
texto pendiente dentro de la memoria.

## Tamano del conjunto clasico

El conjunto implementado contiene 150 episodios: 105 de entrenamiento, 22 de
validacion y 23 de prueba. La generacion esta fijada en
`src/simulador_quad/datasets/classic.py` y documentada en
`docs/simulador/dataset_clasico.md`.

Valoracion actual:

- Es defendible para el alcance del TFG si la memoria lo presenta como una
  cobertura reproducible y acotada, no como una muestra estadistica exhaustiva.
- No recomiendo ampliar automaticamente a 300--350 episodios antes de ver los
  resultados consolidados, porque implicaria regenerar dataset clasico, dataset
  de imitacion, entrenamientos y evaluacion cerrada.
- Si las tablas finales muestran mucha variabilidad por familia, pocos exitos en
  `test`, o conclusiones muy dependientes de una familia con pocos escenarios,
  entonces si conviene ampliar.

Si se decide ampliar:

1. Mantener las cuatro familias y aumentar principalmente geometrías/perfiles de
   `test` y OOD, no solo muestras de entrenamiento.
2. Preservar splits por escenario completo; nunca repartir ventanas de un mismo
   episodio entre splits.
3. Regenerar tambien el conjunto de fuerza externa, el dataset de imitacion y los
   checkpoints neuronales.
4. Actualizar `docs/simulador/dataset_clasico.md`, la metodologia y cualquier
   tabla de resultados.

## Hiperparametros neuronales

La metodologia ya declara que MLP, GRU y LSTM se comparan con configuraciones
igualadas. Si se quiere defender que `hidden_dim=64`, `sequence_length=20`,
`lr=10^{-3}` y `patience=10` son suficientes, usar las instrucciones especificas
de `docs/instrucciones_control_neuronal_pendiente.md`.

## Referencia auxiliar OOD

La memoria deja abierta la posibilidad de ejecutar un PD ajustado
especificamente para alguna condicion OOD. No debe mezclarse con la comparacion
principal de transferencia, porque usaria informacion de la condicion nueva.

Usarlo solo si aporta una lectura clara:

- Si una trayectoria OOD nueva resulta fallida para todos los PD con parámetros fijados y las
  redes, puede ayudar a distinguir si el escenario es fisicamente razonable o si
  el problema es la falta de transferencia.
- Si se usa, presentarlo como cota auxiliar de especializacion para esa
  trayectoria concreta, no como referencia principal ni como resultado de
  generalizacion.
- Documentar el procedimiento de ajuste y mantenerlo fuera de train, validacion
  y prueba ID.
