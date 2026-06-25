# Instrucciones pendientes para control neuronal

Este documento recoge decisiones que no deben aparecer como texto pendiente en
la memoria, pero que conviene resolver o tener localizadas antes de cerrar la
discusión experimental.

## Verificación del flujo de datos de imitación

El texto de `sections/05_control_neuronal.tex` se ha contrastado con el código y
la documentación del repositorio:

- `tools/run_experimental_campaign.py` separa la fase de tuneo clásico de la
  fase de generación del dataset neuronal. La fase 3 ajusta los PD clásicos; la
  fase 5 genera el banco y el dataset de fuerza externa.
- `tools/generate_outer_force_pid_bank.py` toma cada escenario del dataset
  clásico y evalúa variantes que cambian solo `Kp_pos` y `Kd_pos`. El resto del
  controlador del escenario fuente, incluido el lazo interno, se conserva.
- `tools/generate_outer_force_dataset.py` selecciona un candidato seguro por
  escenario, priorizando RMSE de posición, margen del 5 %, esfuerzo de control y
  criterio conservador. Después copia la telemetría del candidato escogido y
  escribe el escenario con las ganancias externas seleccionadas.
- `src/simulador_quad/ml/dataset.py` recalcula los objetivos de fuerza deseada
  con el PD externo experto a partir de `observation` y `reference`, no del
  estado verdadero.

Conclusión: la memoria puede afirmar que el dataset neuronal no es una simple
copia de comandos del dataset clásico ni una repetición del tuneo global de los
PD. Es una fase posterior que genera expertos externos por escenario variando
solo el lazo externo.

## Estudios recomendados antes del cierre experimental

No he encontrado en el repo una campaña versionada que compare otras longitudes
de ventana recurrente, otras anchuras de red o varias semillas para la
comparación principal `outer_force_min_v1`. Los scripts sí permiten ejecutar
esas variantes mediante `--sequence-length`, `--hidden-dim` y `--seed`.

Prioridad alta:

1. Entrenar MLP, GRU y LSTM con `--hidden-dim 128` manteniendo el resto de la
   configuración.
2. Evaluar MSE supervisado en `train`, `val` y `test`.
3. Ejecutar bucle cerrado en `test` para comprobar si mejora seguimiento,
   saturación o clipping frente a `hidden_dim=64`.

Prioridad media:

1. Repetir GRU y LSTM con `--sequence-length 10` y `--sequence-length 40`.
2. Comparar pérdida supervisada, éxito de misión, RMSE, saturación, clipping y
   coste de inferencia.
3. Mantener MLP como control sin memoria.

Prioridad media:

1. Repetir al menos la arquitectura principal con dos semillas adicionales, por
   ejemplo `--seed 7` y `--seed 123`.
2. Declarar en resultados si la conclusión cambia o si las diferencias quedan
   dentro de una variabilidad aceptable.

## Criterio para actualizar la memoria

Si estos estudios se ejecutan y no cambian la conclusión, la memoria puede
presentar `hidden_dim=64` y `L=20` como configuración suficiente dentro del banco
evaluado. Si `128` o una ventana distinta mejora claramente el bucle cerrado, la
comparación principal debería actualizarse o la discusión debe declarar la
sensibilidad observada.
