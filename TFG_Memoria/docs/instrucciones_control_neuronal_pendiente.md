# Instrucciones pendientes para control neuronal

Este documento recoge decisiones que no deben aparecer como texto pendiente en
la memoria, pero que conviene resolver o tener localizadas antes de cerrar la
discusión experimental.

## Verificación del flujo de datos de imitación

El texto de `sections/05_control_neuronal.tex` se ha contrastado con el código y
la documentación del repositorio:

- `tools/run_experimental_campaign.py` separa la fase de tuneo clásico de la
  fase de generación del dataset neuronal. La fase 3 ajusta los PD clásicos; la
  fase 5 genera el conjunto y el dataset de fuerza externa.
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

## Estudio de sensibilidad ejecutado

El estudio recomendado se ejecutó en el worktree de comparación y quedó
documentado en
`../docs/reviews/estudio_sensibilidad_neuronal_outer_force_2026-06-25.md`.
También se incorporaron al repositorio las herramientas de reproducción:
`tools/run_neural_sensitivity_study.py`,
`tools/summarize_neural_sensitivity.py` y la opción `--variant-tag` de
`tools/run_neural_outer_force_dataset.py`.

Cobertura ejecutada:

- Baseline `outer_force_min_v1` con MLP, GRU y LSTM.
- `hidden_dim=128` para MLP, GRU y LSTM.
- Ventanas recurrentes `L=10` y `L=40` para GRU y LSTM.
- Semillas adicionales 7 y 123 para MLP.
- Evaluación supervisada en `train`, `val` y `test`.
- Bucle cerrado en `test` y OOD.

Lectura técnica:

- Ninguna variante cambia el éxito de misión en `test`.
- `hidden_dim=128` reduce el MSE supervisado de GRU/LSTM, pero no mejora de
  forma uniforme el bucle cerrado de test.
- LSTM con `hidden_dim=128` y LSTM con `L=40` reducen el RMSE medio de test,
  principalmente en escenarios Lissajous, con empeoramientos pequeños en otros
  escenarios.
- Las semillas adicionales de MLP muestran variabilidad baja en test.
- OOD es más disperso y no debe usarse para seleccionar hiperparámetros de la
  comparación principal.

Conclusión para la memoria:

La configuración `hidden_dim=64`, `L=20`, semilla 42 se mantiene como
configuración principal común. No procede rehacer la comparativa principal con
`hidden_dim=128` ni con `L=40` porque la mejora no es sistemática en todas las
arquitecturas y escenarios. Sí procede declarar en la memoria que esta decisión
fue contrastada mediante un estudio de sensibilidad separado.
