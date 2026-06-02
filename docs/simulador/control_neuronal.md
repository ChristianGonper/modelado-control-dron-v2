# Control neuronal por imitacion

Este documento describe los dos modos neuronales implementados. El modo principal para la nueva comparacion es `controller.type: "neural"`, que sustituye solo el lazo externo de posicion por una red de fuerza. El modo `neural_position` se conserva como alternativa que programa ganancias del PID externo.

## Controlador `neural` outer-force

El flujo de inferencia es:

```text
observacion + referencia
        |
        v
MLP / GRU / LSTM -> desired_force_W_N[3]
        |
        v
limites de fuerza e inclinacion
        |
        v
conversion clasica fuerza-actitud + PID clasico de actitud
        |
        v
collective_thrust_N + body_moments_Nm
```

La salida aprendida es una fuerza deseada expresada en mundo ENU y en N:

- `force_x_W_N`
- `force_y_W_N`
- `force_z_W_N`

El lazo interno no se aprende. Utiliza las ganancias de actitud y limites del controlador clasico para convertir la fuerza y el yaw de referencia en empuje colectivo y momentos FRD. Esto separa la decision de traslacion neuronal de la estabilizacion angular.

## Features y targets

`outer_force_min_v1` es la configuracion inicial recomendada para MLP. Tiene 9 entradas obtenidas de la observacion del controlador, no del estado verdadero:

- error de posicion ENU `[3]`;
- error de velocidad ENU `[3]`;
- aceleracion de referencia ENU `[3]`.

`outer_force_full_v1` tiene 31 entradas e incorpora estado observado, referencia, errores y representacion continua del yaw para estudiar arquitecturas de mayor capacidad.

El target `desired_force_W_v1` se calcula con el mismo metodo del controlador clasico, `compute_desired_force_W(...)`, aplicado a la observacion y a las ganancias del experto seleccionado. La normalizacion de entradas y targets se ajusta exclusivamente con el split `train`.

## Construccion del dataset experto

El dataset clasico es la fuente de escenarios, splits y condiciones, pero no se usa directamente como dataset final del modo outer-force. El flujo implementado es:

1. Para cada fila del `manifest.csv` clasico, ejecutar variantes de PID externo con `tools\generate_outer_force_pid_bank.py`.
2. Mantener sin cambios el PID interno (`Kp_att`, `Kd_att`), los limites, la trayectoria, las perturbaciones, la semilla y los parametros del vehiculo del YAML fuente.
3. Excluir variantes que fallen `passes_hard_filters`.
4. Elegir un experto por escenario: menor `position_rmse_m`; entre candidatos dentro del 5% del mejor RMSE, menor esfuerzo de control; ante empate real de esfuerzo, variante mas conservadora.
5. Copiar la telemetria del experto elegido y escribir el YAML de salida con sus `Kp_pos` y `Kd_pos` exactas.

Si ningun candidato de un escenario pasa los filtros de seguridad, la generacion falla de forma explicita. No se fabrica una demostracion valida.

```powershell
uv run python tools\generate_outer_force_pid_bank.py --dataset data\classic_dataset\v1 --out data\outer_force_pid_bank\v1
uv run python tools\generate_outer_force_dataset.py --source-dataset data\classic_dataset\v1 --pid-bank data\outer_force_pid_bank\v1 --out data\outer_force_dataset\v1
```

## Entrenamiento y evaluacion

La primera configuracion a defender es una MLP con features minimas:

```powershell
uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 --architecture mlp --feature-version outer_force_min_v1 --out data\neural_control\outer_force_mlp_min_v1 --device auto
uv run python tools\evaluate_neural_controller.py --dataset data\outer_force_dataset\v1 --run data\neural_control\outer_force_mlp_min_v1 --device auto
```

El script tambien soporta `gru` y `lstm`, y `outer_force_full_v1` permite comparar un vector de entrada mas completo. El entrenamiento produce `config.yaml`, `normalization.json` y checkpoints. La evaluacion outer-force escribe metricas de error de fuerza por split bajo `metrics/*_force_metrics.json`.

Estas metricas miden fidelidad de imitacion del experto, no seguimiento de trayectoria. La comparacion de control exige una ejecucion cerrada:

```powershell
uv run python tools\run_neural_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --device auto --no-visualization
uv run python tools\run_neural_outer_force_dataset.py --dataset data\outer_force_dataset\v1 --split test --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --device auto --no-visualization --limit 2
```

OOD con `data\neural_ood\battery_v1` (solo escenarios YAML, sin telemetria de experto; directorio generado localmente e ignorado por git):

```powershell
uv run python tools\generate_ood_battery.py --out data\neural_ood\battery_v1 --overwrite
uv run python tools\run_neural_outer_force_dataset.py --dataset data\neural_ood\battery_v1 --split ood --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --no-visualization
```

Evaluacion supervisada OOD (requiere telemetria con targets de fuerza bajo `result_dir`, manifest `split=ood`):

```powershell
# Tras generar telemetria OOD (p. ej. copiar experto desde escenarios de battery_v1):
# uv run python tools\generate_outer_force_dataset.py --source-dataset data\neural_ood\battery_v1 --pid-bank data\outer_force_pid_bank\v1 --out data\neural_ood\outer_force_v1
uv run python tools\evaluate_neural_controller.py --dataset data\outer_force_dataset\v1 --run data\neural_control\outer_force_mlp_min_v1 --ood-dataset data\neural_ood\outer_force_v1 --splits ood --device auto
```

`battery_v1` no sirve para `evaluate_neural_controller.py --ood-dataset` (falla con error explicito). El evaluador usa `split=ood` en el manifiesto OOD; no remapea OOD a `train`. Sin `--ood-dataset`, el split `ood` falla de forma explicita.

En bucle cerrado se deben informar `position_rmse_m`, `position_mae_m`, `position_max_err_m`, `termination_reason`, `saturation_percentage`, `degradation_percentage`, `force_norm_clip_percentage` y `force_tilt_clip_percentage`. La telemetria exporta `desired_force_W_N` (salida de red, **pre-clip**), `desired_force_clipped_W_N` (fuerza enviada al PID interno) y `perturbation.wind_W_m_s` por muestra cuando aplica.

Instruccion operativa: al preparar evidencia de memoria, regenerar `battery_v1`, ejecutar el batch cerrado y construir la tabla comparativa en la misma revision de codigo. No usar `battery_v1` por si solo como resultado: es una lista de escenarios, no una corrida experimental.

## Configuracion y seguridad

Un escenario `neural` debe indicar el checkpoint, la normalizacion, las features outer-force y el limite de inclinacion:

```yaml
controller:
  type: "neural"
  architecture: "mlp"
  checkpoint_path: "data/neural_control/outer_force_mlp_min_v1/checkpoints/mlp_best.pt"
  normalization_path: "data/neural_control/outer_force_mlp_min_v1/normalization.json"
  feature_version: "outer_force_min_v1"
  clip_to_classic_limits: true
  max_desired_tilt_rad: 0.52
  Kp_att: [4.0, 4.0, 1.0]
  Kd_att: [1.5, 1.5, 0.5]
  max_body_moments_Nm: [10.0, 10.0, 2.0]
  device: "auto"
```

Con `clip_to_classic_limits: true`, el controlador limita la norma de fuerza a `mass_kg * gravity_m_s2 * 2.5`, restringe la inclinacion solicitada a `max_desired_tilt_rad` y mantiene una componente ascendente minima antes de ejecutar el PID interno. El wrapper `run_neural_scenario.py` usa `0.52 rad` si ese limite no esta registrado en la configuracion del entrenamiento.

Un checkpoint legacy que produce cuatro comandos finales o un checkpoint `neural_position` de seis salidas se rechaza al cargarse como `neural`. Por tanto, los modelos anteriores no deben reutilizarse como outer-force sin regenerar dataset y entrenar de nuevo.

## Arquitectura recurrente outer-force

GRU/LSTM estan soportados en entrenamiento (`tools/train_neural_controller.py`). Para la evidencia final del TFG se prioriza **MLP + `outer_force_min_v1`**. Una segunda arquitectura recurrente outer-force es extension opcional; no es requisito para la comparacion principal frente al clasico.

## Modo conservado `neural_position`

`controller.type: "neural_position"` permanece separado. Entrenamiento e inferencia usan la **observacion** del controlador (no el estado verdadero), alineado con bucle cerrado bajo ruido. Telemetria historica sin bloque `observation` cae en `state` y puede desalinear train/inferencia: regenerar `position_gain_dataset` si aplica. Su red predice seis log-multiplicadores para `Kp_pos[3]` y `Kd_pos[3]`; tras aplicar `exp` y `multiplier_clip`, el controlador clasico calcula fuerza y estabiliza actitud. Sus scripts siguen siendo:

```powershell
uv run python tools\generate_pid_bank.py --dataset data\classic_dataset\v1 --out data\pid_bank\v1
uv run python tools\generate_position_gain_dataset_from_bank.py --source-dataset data\classic_dataset\v1 --pid-bank data\pid_bank\v1 --out data\position_gain_dataset\v1
uv run python tools\train_neural_position_controller.py --dataset data\position_gain_dataset\v1 --architecture gru --out data\neural_control\position_gru_v1 --device auto
uv run python tools\run_neural_position_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\position_gru_v1\checkpoints\gru_best.pt --normalization data\neural_control\position_gru_v1\normalization.json --device auto --no-visualization
```

## Alcance

El codigo implementa el pipeline y sus protecciones, pero no aporta por si mismo un modelo entrenado ni resultados finales para la memoria. Las conclusiones experimentales solo son validas tras regenerar los datasets, entrenar checkpoints identificables y ejecutar los mismos escenarios para baseline, experto y controlador neuronal.
