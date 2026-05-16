# Control Neuronal por Imitación (Imitation Learning)

Este documento describe la arquitectura y el flujo de trabajo del controlador neuronal implementado en el simulador.

## Arquitectura de Inferencia

El controlador neuronal (`NeuralController`) implementa la interfaz estándar `Controller`, permitiendo su integración transparente en cualquier escenario.

### Vector de Características (Features)
La red recibe un vector de 31 elementos en cada paso de control:
- **Estado (13)**: Posición (3), Velocidad (3), Orientación (Cuaternión 4), Velocidad Angular (3).
- **Referencia (10)**: Posición (3), Velocidad (3), Aceleración (3), Yaw (1).
- **Errores (6)**: Error de posición (3), Error de velocidad (3).
- **Trig Yaw (2)**: Seno y Coseno del Yaw de referencia para continuidad.

### Salidas (Targets)
La red predice 4 valores:
- Empuje colectivo (Thrust) en Newtons.
- Momentos en el cuerpo (Roll, Pitch, Yaw) en Newton-metros.

## Modelos Soportados

1.  **MLP (Multi-Layer Perceptron)**: Red densa simple. Ideal para control reactivo basado en el estado instantáneo.
2.  **GRU / LSTM**: Redes recurrentes que mantienen una ventana de historia (por defecto 20 pasos, 2.0s). Capturan dinámicas temporales y son más robustas ante ruido o retrasos.

## Flujo de Trabajo

### 1. Generación de Dataset
Se utiliza el controlador clásico (PID cascada) para generar trayectorias expertas.
```powershell
uv run python tools\generate_classic_dataset.py --version v1 --out data\classic_dataset\v1
uv run python tools\run_classic_dataset.py --dataset data\classic_dataset\v1 --no-visualization
uv run python tools\summarize_classic_dataset.py --dataset data\classic_dataset\v1
```

### 2. Entrenamiento
El entrenamiento utiliza `Normalizer` (basado solo en `train`) y soporta *early stopping*.
```powershell
uv run python tools\train_neural_controller.py --dataset data\classic_dataset\v1 --architecture gru --out data\neural_control\gru_v1
```

### 3. Evaluación Supervisada
Calcula el error (MSE/MAE) comparando las salidas de la red con los comandos que habría dado el experto sobre los mismos datos.
```powershell
uv run python tools\evaluate_neural_controller.py --dataset data\classic_dataset\v1 --run data\neural_control\gru_v1
```

La evaluación supervisada escribe métricas por split (`train_metrics.json`, `val_metrics.json`, `test_metrics.json`) en el directorio de la ejecución neuronal. Incluye error normalizado, errores en unidades físicas y `saturation_percentage`, entendido como porcentaje de muestras donde la red predice comandos fuera de límites antes de aplicar clipping.

Estas métricas miden fidelidad de imitación, no calidad final de seguimiento. El entrenamiento minimiza MSE normalizado sobre los comandos del PID (`collective_thrust_N` y `body_moments_Nm`), por lo que un valor bajo indica que la red reproduce el experto clásico sobre las muestras disponibles. No implica por sí mismo que la trayectoria en bucle cerrado tenga menor error.

Por defecto, la métrica supervisada de saturación usa los límites del vehículo base del dataset clásico: masa `1.0 kg`, gravedad `9.81 m/s^2`, empuje máximo `m*g*2.5` y momentos máximos `[10, 10, 2] Nm`. Si se evalúan datasets con otra masa o límites personalizados, esta métrica debe parametrizarse desde código o ampliarse en una fase posterior para leer esos valores desde metadata.

### 4. Evaluación OOD Supervisada
Para medir generalización fuera de distribución, el script acepta un dataset OOD separado:

```powershell
uv run python tools\evaluate_neural_controller.py --dataset data\classic_dataset\v1 --run data\neural_control\gru_v1 --ood-dataset data\neural_ood\lemniscate_v1
```

`--ood-dataset` debe apuntar a un directorio con la misma estructura mínima que el dataset clásico: `manifest.csv` y `telemetry.json` bajo los `result_dir` indicados. El comando no ejecuta automáticamente el escenario OOD; evalúa telemetría ya generada. El resultado se escribe como `metrics/ood_metrics.json`.

### 5. Ejecución en Bucle Cerrado (Inferencia)
Para probar el modelo en el simulador (donde la red decide el siguiente estado), se usa el script de ejecución:
```powershell
uv run python tools\run_neural_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\gru_v1\checkpoints\gru_best.pt --normalization data\neural_control\gru_v1\normalization.json --architecture gru --no-visualization
```

Este comando carga el YAML base, sustituye el bloque `controller` en memoria por un controlador neuronal y ejecuta el simulador. No modifica el YAML original. Si no se indica `--out`, el directorio de salida se deriva del `output.dir` original añadiendo un sufijo con la arquitectura.

La métrica principal para comparar controladores en el objetivo físico del TFG es el error de trayectoria en bucle cerrado, no la loss supervisada. En las salidas `metrics.json`, la métrica principal es:

- `position_rmse_m`: RMSE de la norma del error de posición `||reference.position_W_m - state.position_W_m||`.

Como métricas auxiliares deben reportarse `position_mae_m`, `position_max_err_m`, `termination_reason`, `saturation_percentage` y `degradation_percentage`. Esta separación es especialmente importante porque el PID se ajusta en condiciones nominales sin viento ni ruido, mientras que parte del dataset de imitación incluye perturbaciones: en esos episodios el comando del PID es una demostración reproducible, pero no necesariamente produce seguimiento perfecto de la referencia.

## Normalización
Es crítica para el entrenamiento de redes neuronales. Los parámetros de normalización se guardan en `normalization.json` y deben ser los mismos durante el entrenamiento y la inferencia. El sistema los carga automáticamente desde el directorio del modelo.

Los estadísticos se calculan exclusivamente con el split `train`. Para GRU/LSTM, la normalización reduce todas las dimensiones excepto la de features, de modo que una ventana `[N, L, D]` produce medias y desviaciones de dimensión `D`. Esto evita que `val`, `test` u OOD contaminen el entrenamiento y mantiene la misma escala en inferencia.

## Limitaciones y Seguridad
El controlador neuronal incluye un flag `clip_to_classic_limits` (por defecto `true`) que limita las salidas de la red a los rangos físicos razonables del dron, evitando divergencias catastróficas por predicciones fuera de rango.

En inferencia, los límites efectivos son:

- empuje colectivo entre `0` y `mass_kg * gravity_m_s2 * 2.5`;
- momentos de cuerpo entre `-max_body_moments_Nm` y `+max_body_moments_Nm`.

`max_body_moments_Nm` puede declararse en el YAML del controlador neuronal. Si falta, se usa `[10.0, 10.0, 2.0] Nm`, igual que el controlador clásico.

## Alcance Actual

El pipeline implementado cubre entrenamiento supervisado, evaluación supervisada y ejecución en bucle cerrado. La calidad final de un modelo entrenado depende del dataset disponible, de los hiperparámetros y de la validación experimental posterior. El test `train`/`val`/`test` del dataset clásico mide fidelidad de imitación in-distribution; la calidad de control debe evaluarse ejecutando el controlador neuronal en el simulador y comparando métricas de trayectoria. La generalización debe justificarse con datasets o escenarios OOD separados.
