# Plan experimental y memoria TFG — junio 2026

## Objetivo

Cerrar la evidencia experimental y arrancar la memoria del TFG con una comparacion defendible entre control clasico y control neuronal por imitacion en un simulador 6DOF de cuadricoptero.

La tesis experimental no sera que una red neuronal sea siempre mejor que cualquier PID, sino que puede aprender una politica de lazo externo que generaliza mejor que PIDs ajustados de forma especifica o transferidos fuera de su familia de trayectorias, especialmente bajo perturbaciones y escenarios OOD.

## Estado actual

- Simulador 6DOF, escenarios, telemetria, metricas, OOD tooling y batch tooling estan implementados.
- Faltan las evidencias pesadas: banco PID, dataset `outer_force`, entrenamientos, ejecuciones cerradas y tabla comparativa.
- `data/` y `results/` estan ignorados por defecto. Los artefactos experimentales se generan localmente y solo se versionan si se decide explicitamente.
- `TFG_Memoria/` contiene una plantilla LaTeX de la ULE/EIIIA con portada, resumen, indices, bibliografia IEEE y anexos.

## Principios metodologicos

- Mantener ENU/FRD en toda la campana.
- CPU: ejecutar simulaciones independientes con `--workers 16`.
- GPU: entrenamientos y evaluaciones con `--device cuda` o `--device auto`, de uno en uno.
- No mezclar `test` in-distribution con OOD.
- No usar checkpoints legacy de 4 salidas como evidencia del modo `neural`.
- Para viento y perturbaciones, el maestro debe seleccionarse bajo la condicion del escenario. Si el PID experto no pasa filtros, ese escenario no debe fabricarse como demostracion valida.

## Controladores a comparar

### Baselines clasicos

1. `classic_family_pid`: PID especifico de la familia de trayectoria (`pid_hold_v1`, `pid_circle_v1`, `pid_lissajous_v1`, `pid_waypoint_v1`).
2. `classic_cross_pid`: PID entrenado/ajustado para otra familia aplicado a una familia distinta. Se usara para medir transferencia clasica.
3. `outer_force_oracle`: experto por escenario seleccionado por `generate_outer_force_pid_bank.py` + `generate_outer_force_dataset.py`. Es techo de imitacion, no controlador neuronal.

### Neuronales

Se entrenaran tres arquitecturas para cada modo:

| Modo | Arquitecturas | Dataset | Salida |
| --- | --- | --- | --- |
| `neural` outer-force | MLP, GRU, LSTM | `data/outer_force_dataset/v1` | `desired_force_W_N[3]` |
| `neural_position` | MLP, GRU, LSTM | `data/position_gain_dataset/v1` | multiplicadores de `Kp_pos`, `Kd_pos` |

Para `neural` se usara `outer_force_min_v1` como configuracion principal. `outer_force_full_v1` queda como ablation opcional si hay tiempo.

## Flujo experimental

### Fase 1 — Sanidad inicial

```powershell
uv sync
uv run pytest -q
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
uv run simulador-quad run scenarios\composite_ood.yaml --no-visualization
```

Aceptar solo si no hay fallos fisicos, no finitos ni cambios inesperados en metadata.

### Fase 2 — Dataset clasico y PIDs base

```powershell
uv run python tools\generate_classic_dataset.py --version v1 --out data\classic_dataset\v1
uv run python tools\run_classic_dataset.py --dataset data\classic_dataset\v1 --no-visualization --workers 16
uv run python tools\summarize_classic_dataset.py --dataset data\classic_dataset\v1
```

Si `data/classic_dataset/v1` ya existe y se decide reutilizarlo, verificar `manifest.csv`, `run_report.csv`, `summary.csv` y metadata antes de usarlo en memoria.

### Fase 3 — Experto outer-force por escenario

```powershell
uv run python tools\generate_outer_force_pid_bank.py --dataset data\classic_dataset\v1 --out data\outer_force_pid_bank\v1
uv run python tools\generate_outer_force_dataset.py --source-dataset data\classic_dataset\v1 --pid-bank data\outer_force_pid_bank\v1 --out data\outer_force_dataset\v1
```

Decision critica: el banco debe evaluar variantes del PID externo bajo la trayectoria, viento, ruido, drag, retardo y lag de cada escenario. Esto evita entrenar la red contra un maestro que no sabe resolver la perturbacion.

### Fase 4 — Dataset `neural_position`

```powershell
uv run python tools\generate_pid_bank.py --dataset data\classic_dataset\v1 --out data\pid_bank\v1
uv run python tools\generate_position_gain_dataset_from_bank.py --source-dataset data\classic_dataset\v1 --pid-bank data\pid_bank\v1 --out data\position_gain_dataset\v1
uv run python tools\run_classic_dataset.py --dataset data\position_gain_dataset\v1 --no-visualization --workers 16
```

Si este modo consume demasiado tiempo, se mantiene como comparacion secundaria, pero el usuario ha pedido entrenar MLP/GRU/LSTM tambien aqui.

### Fase 5 — Entrenamiento GPU secuencial

Outer-force:

```powershell
uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 --architecture mlp --feature-version outer_force_min_v1 --out data\neural_control\outer_force_mlp_min_v1 --device cuda
uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 --architecture gru --feature-version outer_force_min_v1 --out data\neural_control\outer_force_gru_min_v1 --device cuda
uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 --architecture lstm --feature-version outer_force_min_v1 --out data\neural_control\outer_force_lstm_min_v1 --device cuda
```

Position:

```powershell
uv run python tools\train_neural_position_controller.py --dataset data\position_gain_dataset\v1 --architecture mlp --out data\neural_control\position_mlp_v1 --device cuda
uv run python tools\train_neural_position_controller.py --dataset data\position_gain_dataset\v1 --architecture gru --out data\neural_control\position_gru_v1 --device cuda
uv run python tools\train_neural_position_controller.py --dataset data\position_gain_dataset\v1 --architecture lstm --out data\neural_control\position_lstm_v1 --device cuda
```

Si CUDA no esta disponible, usar `--device auto` y registrar en memoria que el entrenamiento se hizo en CPU.

### Fase 6 — Evaluacion supervisada

```powershell
uv run python tools\evaluate_neural_controller.py --dataset data\outer_force_dataset\v1 --run data\neural_control\outer_force_mlp_min_v1 --device cuda
uv run python tools\evaluate_neural_controller.py --dataset data\outer_force_dataset\v1 --run data\neural_control\outer_force_gru_min_v1 --device cuda
uv run python tools\evaluate_neural_controller.py --dataset data\outer_force_dataset\v1 --run data\neural_control\outer_force_lstm_min_v1 --device cuda

uv run python tools\evaluate_neural_position_controller.py --dataset data\position_gain_dataset\v1 --run data\neural_control\position_mlp_v1 --device cuda
uv run python tools\evaluate_neural_position_controller.py --dataset data\position_gain_dataset\v1 --run data\neural_control\position_gru_v1 --device cuda
uv run python tools\evaluate_neural_position_controller.py --dataset data\position_gain_dataset\v1 --run data\neural_control\position_lstm_v1 --device cuda
```

Estas metricas son fidelidad de imitacion, no conclusion de control.

### Fase 7 — Bucle cerrado in-distribution

Ejecutar `split test` con CPU y 16 workers:

```powershell
uv run python tools\run_neural_outer_force_dataset.py --dataset data\outer_force_dataset\v1 --split test --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --architecture mlp --device cpu --workers 16 --no-visualization
uv run python tools\run_neural_outer_force_dataset.py --dataset data\outer_force_dataset\v1 --split test --checkpoint data\neural_control\outer_force_gru_min_v1\checkpoints\gru_best.pt --normalization data\neural_control\outer_force_gru_min_v1\normalization.json --architecture gru --device cpu --workers 16 --no-visualization
uv run python tools\run_neural_outer_force_dataset.py --dataset data\outer_force_dataset\v1 --split test --checkpoint data\neural_control\outer_force_lstm_min_v1\checkpoints\lstm_best.pt --normalization data\neural_control\outer_force_lstm_min_v1\normalization.json --architecture lstm --device cpu --workers 16 --no-visualization
```

Repetir equivalente para `run_neural_position_dataset.py` sobre `data\position_gain_dataset\v1`.

### Fase 8 — OOD

```powershell
uv run python tools\generate_ood_battery.py --out data\neural_ood\battery_v1 --overwrite
```

Ejecutar todos los modelos neuronales sobre `split ood` con `--workers 16 --device cpu`.

Para PIDs clasicos OOD, se necesita una herramienta o procedimiento que ejecute:

- PID especifico de la familia mas cercana.
- PIDs de otras familias sobre el mismo escenario.
- Oraculo si se genera banco outer-force sobre OOD.

Si no existe el script, se implementara antes de arrancar la campana pesada.

### Fase 9 — Tabla comparativa

Construir una tabla unica:

```powershell
uv run python tools\build_comparison_closed_loop.py --classic-report data\classic_dataset\v1\run_report.csv --classic-dataset data\classic_dataset\v1 --neural-report data\outer_force_dataset\v1\run_report_neural_mlp.csv --neural-dataset data\outer_force_dataset\v1 --out results\comparison_closed_loop_v1.csv
```

Probablemente habra que ampliar el agregador para aceptar multiples reportes neuronales y etiquetar cada controlador con nombre estable. Esta ampliacion es parte del trabajo de codigo previo a la campana.

## Codigo adicional a implementar antes de la campana

1. Script orquestador `tools/run_experimental_campaign.py`.
   - Ejecuta fases en orden.
   - Permite `--phase`, `--dry-run`, `--workers 16`, `--device cuda|auto`.
   - No lanza entrenamientos GPU en paralelo.

2. Script de transferencia clasica `tools/run_classic_transfer_dataset.py`.
   - Ejecuta cada escenario con PID de su familia y PIDs de otras familias.
   - Escribe `run_report_classic_transfer.csv` con `controller_label`.

3. Extension de `tools/build_comparison_closed_loop.py`.
   - Acepta multiples `--report controller=path,dataset=...,split=...`.
   - Conserva `controller_label`, `mode`, `architecture`, `dataset`, `split`, `ood`.

4. Script de resumen `tools/summarize_comparison.py`.
   - Agrega media, mediana, desviacion, tasa de fallo y ranking por familia/OOD.
   - Exporta CSV para tablas de memoria.

5. Generacion de figuras reproducibles.
   - Trayectorias representativas: circle, lissajous, waypoint, composite, OOD.
   - Barras/boxplots de RMSE por controlador.

## Esquema inicial de memoria

### 1. Introduccion

- Motivacion: control de cuadricopteros, seguimiento de trayectorias y comparacion entre control clasico y aprendizaje por imitacion.
- Decision de alcance: se intento usar simuladores existentes, pero por cierre, exceso de funcionalidad, dificultad de trazabilidad o falta de ajuste al objetivo docente, se incluye como parte del TFG desarrollar un simulador propio 6DOF acotado.
- Objetivos y contribuciones.

### 2. Estado del arte

- Modelado de UAV multirrotor y cuadricopteros.
- Dinamica de cuerpo rigido, quaterniones y sistemas de referencia.
- Control clasico PID/cascada en cuadricopteros.
- Aprendizaje por imitacion y redes MLP/GRU/LSTM para control.
- Simuladores y bancos de ensayo: justificar por que no se adopta uno cerrado como nucleo del TFG.

### 3. Modelo fisico del cuadricoptero

- Marcos ENU/FRD y convencion de empuje `-Z_B`.
- Estado, cinematicas con quaterniones.
- Dinamica translacional y rotacional Newton-Euler.
- Actuadores, mixer, saturacion, retardo, lag.
- Perturbaciones: viento, ruido de observacion, drag lineal.
- Integracion RK4 multi-rate.

### 4. Control clasico

- Control en cascada: posicion -> fuerza deseada -> actitud -> empuje/momentos.
- Ganancias, saturaciones, limites y filtros.
- Ajuste de PIDs por familia de trayectoria.
- Definicion de PID especifico, PID transferido y oraculo por escenario.

### 5. Control neuronal por imitacion

- Formulacion de imitacion supervisada.
- `neural` outer-force: entradas, targets, clipping, PID interno.
- `neural_position`: multiplicadores de ganancias externas.
- Arquitecturas MLP, GRU, LSTM.
- Normalizacion, splits, entrenamiento, semillas.

### 6. Escenarios, datasets y metodologia experimental

- Escenarios nominales, perturbados y OOD.
- Dataset clasico.
- Banco de PIDs y seleccion de maestro bajo perturbaciones.
- Dataset outer-force y position-gain.
- Protocolo de comparacion: in-distribution, transferencia, OOD.
- Metricas: RMSE, MAE, error maximo, terminacion, saturacion, clipping, degradacion.

### 7. Resultados

- Sanidad del simulador y validacion fisica.
- Comparacion PID especifico vs modelos neuronales por trayectoria.
- Comparacion PID transferido vs modelos neuronales.
- Oraculo vs red: brecha de imitacion.
- OOD: degradacion, fallos, robustez.
- Discusion de viento: si el maestro se optimiza bajo viento, la red aprende esa respuesta; si no, la imitacion hereda la debilidad del maestro.

### 8. Discusion

- Que demuestra realmente el TFG.
- Donde la red mejora/generaliza.
- Donde el PID especifico sigue siendo superior.
- Limitaciones del simulador y de la imitacion.

### 9. Conclusiones y trabajo futuro

- Conclusiones tecnicas y academicas.
- Futuro: aerodinamica formal, sensores/estimador, validacion real, aprendizaje con DAgger/RL, optimizacion robusta.

### Anexos

- Tablas completas de escenarios.
- Parametros de PIDs.
- Arquitecturas y comandos.
- Figuras adicionales.
- Extractos minimos de codigo o pseudocodigo.

## Reglas de LaTeX

Basado en la plantilla local y buenas practicas LaTeX:

- Mantener fuente LaTeX bajo versionado y no versionar salidas generadas.
- Usar compilacion automatizada (`latexmk`) cuando se estabilice el proyecto.
- Separar secciones en archivos si `main.tex` crece demasiado.
- Usar citas y referencias no rompibles (`~\cite{}`, `Figura~\ref{}`).
- Evitar fragmentos de codigo largos; preferir ecuaciones, diagramas y pseudocodigo.
- Usar bibliografia IEEE salvo instruccion distinta del tutor.

## Siguientes pasos inmediatos

1. Implementar el orquestador y las herramientas de transferencia clasica.
2. Preparar la estructura modular de `TFG_Memoria/`.
3. Ejecutar una campana smoke con `--limit 2` para todos los modos.
4. Ejecutar la campana completa CPU/GPU.
5. Volcar tablas y figuras a la memoria.
