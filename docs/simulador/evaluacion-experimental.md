# Evaluar los controladores en simulación

Esta guía reúne los comandos para ejecutar comparaciones en bucle cerrado y consultar sus resultados. La evaluación comprende escenarios de prueba de familias conocidas (`test`) y una batería separada de escenarios fuera de distribución (`ood`). Para una simulación individual empieza por la [guía de uso](guia_uso.md); para preparar modelos, consulta la [guía de NeuroFlight](../neuroflight.md).

## Antes de empezar

Los comandos están escritos para PowerShell y se ejecutan desde la raíz del repositorio. Necesitas haber instalado las dependencias con `uv sync` y haber generado:

- `data/classic_dataset/v1/`, con su manifiesto, escenarios y los cuatro PD de familia en `pids/`.
- `data/outer_force_dataset/v1/`, con las demostraciones y el manifiesto para las redes.
- Los modelos MLP, GRU y LSTM entrenados bajo `data/neural_control/outer_force_<arquitectura>_min_v1/`, cada uno con su checkpoint y `normalization.json`.

La [guía de NeuroFlight](../neuroflight.md#entrenar-los-modelos-desde-cero) describe cómo preparar estos artefactos. El paquete de la aplicación permite probar NeuroFlight, pero no contiene por sí solo los conjuntos de datos completos necesarios para esta evaluación.

Las ejecuciones pueden tardar bastante y escribir numerosos archivos en `data/`. Usa una copia de trabajo y directorios de datos que puedas modificar. Los comandos de generación se detienen si el destino existe, salvo que se indique explícitamente `--overwrite`; `--rerun` vuelve a ejecutar simulaciones ya terminadas.

## 1. Evaluar las redes en escenarios de prueba

Para cada arquitectura, el siguiente bucle ejecuta las filas `test` del conjunto de fuerza exterior con el checkpoint y la normalización correspondientes. Se usa CPU para las simulaciones; `--workers 4` puede ajustarse al equipo.

```powershell
foreach ($arquitectura in @('mlp', 'gru', 'lstm')) {
  $modelo = "data\neural_control\outer_force_${arquitectura}_min_v1"
  uv run python tools\run_neural_outer_force_dataset.py `
    --dataset data\outer_force_dataset\v1 --split test `
    --architecture $arquitectura --checkpoint "$modelo\checkpoints\${arquitectura}_best.pt" `
    --normalization "$modelo\normalization.json" --device cpu --workers 4 --no-visualization
  if ($LASTEXITCODE -ne 0) { throw "Ha fallado la evaluación test de $arquitectura" }
}
```

Cada ejecución guarda métricas y telemetría en el conjunto de datos, además de un informe por arquitectura. Esta prueba mide seguimiento con el simulador completo; la evaluación supervisada de la [guía de modelos](../neuroflight.md#3-entrenar-mlp-gru-y-lstm-en-gpu) mide, en cambio, la imitación de la fuerza del experto.

## 2. Generar los escenarios fuera de distribución

La batería se construye a partir de los PD de familia preparados en el conjunto clásico:

```powershell
uv run python tools\generate_ood_battery.py `
  --out data\neural_ood\battery_v1 --pid-source-dataset data\classic_dataset\v1
```

El manifiesto generado contiene escenarios con `split=ood`. Es una lista de misiones, no una colección de resultados ni un conjunto de telemetría de expertos para evaluación supervisada.

## 3. Ejecutar los PD y las redes

Para comparar los PD de familia en los escenarios `test` conocidos y los escenarios OOD:

```powershell
uv run python tools\run_classic_transfer_dataset.py `
  --dataset data\classic_dataset\v1 --split test `
  --pid-source-dataset data\classic_dataset\v1 --pid-family all --include-native `
  --workers 4 --no-visualization

uv run python tools\run_classic_transfer_dataset.py `
  --dataset data\neural_ood\battery_v1 --split ood `
  --pid-source-dataset data\classic_dataset\v1 --pid-family all --include-native `
  --workers 4 --no-visualization
```

Para las tres redes sobre la batería OOD:

```powershell
foreach ($arquitectura in @('mlp', 'gru', 'lstm')) {
  $modelo = "data\neural_control\outer_force_${arquitectura}_min_v1"
  uv run python tools\run_neural_outer_force_dataset.py `
    --dataset data\neural_ood\battery_v1 --split ood `
    --architecture $arquitectura --checkpoint "$modelo\checkpoints\${arquitectura}_best.pt" `
    --normalization "$modelo\normalization.json" --device cpu --workers 4 --no-visualization
  if ($LASTEXITCODE -ne 0) { throw "Ha fallado la evaluación OOD de $arquitectura" }
}
```

Comprueba el estado de los informes generados antes de consolidar: una ejecución fallida o detenida prematuramente no debe interpretarse como una misión completa.

## 4. Consolidar y generar figuras

El siguiente comando recoge los resultados disponibles. Se indica un directorio de salida separado para no sustituir los CSV históricos del repositorio. El directorio pasado a `--dataset-position` debe permanecer inexistente o vacío para no añadir otras ejecuciones ajenas a esta comparación.

```powershell
uv run python tools\summarize_comparison.py `
  --dataset-classic data\classic_dataset\v1 `
  --dataset-neural data\outer_force_dataset\v1 `
  --dataset-ood data\neural_ood\battery_v1 `
  --dataset-position data\sin-ejecuciones-adicionales `
  --out-dir results\reproduccion

uv run simulador-quad plot-comparison results\reproduccion\comparison_all_runs.csv `
  --out results\reproduccion\figuras --formats png pdf
```

El resumen solo puede incluir ejecuciones que existan: revisa los recuentos, las familias y los motivos de terminación antes de compararlo con otros resultados. `mission_success` indica si se completó la misión y `safety_success` si terminó sin un fallo físico contemplado. Un límite de tiempo puede ser normal para una trayectoria sin final definido, pero no equivale a completar una trayectoria finita. La [validación](validacion.md) detalla estos criterios.

Las salidas obtenidas aquí son nuevas ejecuciones. Para interpretar los resultados académicos publicados, consulta la [memoria del TFG](../../site/assets/reports/TFG_Memoria_es.pdf).
