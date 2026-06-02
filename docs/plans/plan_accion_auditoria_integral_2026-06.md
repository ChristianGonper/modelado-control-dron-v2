# Plan de acción — Auditoría integral TFG junio 2026

## Objetivo

Convertir los hallazgos de `docs/reviews/auditoria_integral_tfg_2026-06.md` en una secuencia ejecutable para cerrar la evidencia final del TFG: dataset y oráculo `outer_force`, evaluación cerrada de controladores, escenarios OOD, documentación viva y pruebas mínimas de regresión física/software.

El objetivo no es ampliar el alcance científico del TFG, sino hacer defendible la comparación entre control clásico y control neuronal por imitación bajo el contrato vigente.

## Supuestos

- Se mantiene `uv` como gestor único de entorno y ejecución.
- No se reutilizan checkpoints legacy `data/neural_control/{mlp,gru,lstm}_v1` como evidencia de `controller.type: neural`.
- El escenario `scenarios/composite_ood.yaml` debe iniciar en el primer punto de la ruta, no en suelo.
- Las auditorías de mayo quedan como referencia histórica; el diagnóstico vigente es junio 2026.
- Los cambios deben mantener mundo ENU y cuerpo FRD.

## Comandos base

```powershell
uv sync
uv run pytest
uv run python tools\generate_outer_force_pid_bank.py --dataset data\classic_dataset\v1 --out data\outer_force_pid_bank\v1
uv run python tools\generate_outer_force_dataset.py --source-dataset data\classic_dataset\v1 --pid-bank data\outer_force_pid_bank\v1 --out data\outer_force_dataset\v1
uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 --architecture mlp --feature-version outer_force_min_v1 --out data\neural_control\outer_force_mlp_min_v1 --device auto
uv run python tools\evaluate_neural_controller.py --dataset data\outer_force_dataset\v1 --run data\neural_control\outer_force_mlp_min_v1 --device auto
uv run python tools\run_neural_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --device auto --no-visualization
```

## Estructura afectada

- `scenarios/`: escenarios oficiales y OOD.
- `tools/`: generación, entrenamiento, evaluación y ejecución batch.
- `src/simulador_quad/`: controlador neuronal, dinámica, runner, telemetría y métricas.
- `tests/`: regresiones unitarias e integración ligera.
- `data/`: datasets/checkpoints versionados o generados localmente según política del repo.
- `results/`: resultados regenerados para memoria.
- `docs/simulador/`: documentación viva de arquitectura, validación, dataset y control neuronal.
- `docs/reviews/`: auditorías históricas y diagnóstico vigente.

## Límites

- Siempre: conservar ENU/FRD, unidades explícitas, metadata reproducible, comandos con `uv`, y separación entre `neural` outer-force y `neural_position`.
- Preguntar antes: añadir dependencias, cambiar criterios académicos en `docs/01–03`, eliminar artefactos legacy versionados o modificar sustancialmente el diseño experimental.
- Nunca: presentar resultados legacy como conclusiones finales, mezclar splits `test` y OOD, borrar auditorías históricas, o hacer commits sin petición explícita del usuario.

## Orden de ejecución

### Fase 0 — Preparación documental y escenario OOD

- [ ] Verificar que `scenarios/composite_ood.yaml` inicia en `[0,0,1.0]`.
  - Aceptación: el primer `hold.position_W_m` y `initial_state.position_W_m` coinciden.
  - Verificar: inspección del YAML y, cuando toque ejecutar, smoke de escenario clásico.
  - Archivos: `scenarios/composite_ood.yaml`, `docs/simulador/validacion.md`.

- [ ] Mantener la gobernanza documental de reviews.
  - Aceptación: `docs/reviews/README.md` indica que junio 2026 es diagnóstico vigente y mayo es histórico.
  - Verificar: lectura del índice de revisiones.
  - Archivos: `docs/reviews/README.md`.

### Fase 1 — Cierre de tooling OOD y evaluación

- [ ] Renombrar e integrar `tools/generate-ood-batery.py`.
  - Aceptación: nombre correcto `generate_ood_battery.py`, ayuda CLI clara, manifest compatible con evaluación OOD y sin script duplicado con typo.
  - Verificar: `uv run python tools\generate_ood_battery.py --help`.
  - Archivos: `tools/generate_ood_battery.py`, `tools/generate-ood-batery.py` si procede eliminarlo, docs afectadas.

- [ ] Corregir el contrato de `evaluate_neural_controller.py` para OOD.
  - Aceptación: el split OOD no se trata silenciosamente como `train`; el CLI documenta si espera `manifest.csv` con split propio o dataset OOD completo.
  - Verificar: prueba unitaria o fixture mínimo de dataset OOD.
  - Archivos: `tools/evaluate_neural_controller.py`, `tests/`, `docs/simulador/control_neuronal.md`.

- [ ] Crear batch de bucle cerrado para `neural` outer-force.
  - Aceptación: script equivalente a `run_neural_position_dataset.py` que ejecuta manifest por split/controlador y escribe reporte CSV.
  - Verificar: smoke con 1–2 escenarios pequeños y `--no-visualization`.
  - Archivos: `tools/run_neural_outer_force_dataset.py`, `tests/`, README/docs.

### Fase 2 — Regeneración de datos y entrenamiento vigente

- [ ] Generar banco `outer_force_pid_bank/v1`.
  - Aceptación: manifest con candidatos, filtros, ganancias y métricas por escenario fuente.
  - Verificar: revisar `pid_bank_manifest.csv` y metadata.
  - Archivos: `data/outer_force_pid_bank/v1/`.

- [ ] Generar dataset `outer_force_dataset/v1`.
  - Aceptación: manifest con experto seguro por escenario y telemetría con targets `desired_force_W_N`.
  - Verificar: `manifest.csv`, telemetrías y ausencia de mezcla con targets legacy.
  - Archivos: `data/outer_force_dataset/v1/`.

- [ ] Entrenar al menos `outer_force_mlp_min_v1`.
  - Aceptación: `config.yaml` con `controller_mode: neural_outer_force`, `output_dim: 3`, `feature_version: outer_force_min_v1`, normalización y checkpoint.
  - Verificar: evaluación supervisada train/val/test con métricas de fuerza.
  - Archivos: `data/neural_control/outer_force_mlp_min_v1/`.

- [ ] Decidir segunda arquitectura neuronal mínima.
  - Aceptación: GRU o LSTM outer-force entrenada, o justificación documental de limitar la comparación a MLP + `neural_position`.
  - Verificar: config/checkpoint o decisión documentada.
  - Archivos: `data/neural_control/`, `docs/simulador/control_neuronal.md`.

### Fase 3 — Línea `neural_position`

- [ ] Regenerar `position_gain_dataset/v1` o documentar su exclusión experimental.
  - Aceptación: dataset y checkpoint vigente, o alcance recortado explícito para no prometer esa comparación.
  - Verificar: evaluación supervisada y bucle cerrado si se mantiene.
  - Archivos: `data/position_gain_dataset/v1/`, `data/neural_control/position_*`, docs.

- [ ] Corregir o justificar la posible desalineación observation/state.
  - Aceptación: inferencia y entrenamiento usan la misma fuente de features, o el documento declara que no hay ruido/que el riesgo queda fuera del resultado principal.
  - Verificar: prueba con ruido o revisión de features.
  - Archivos: `src/simulador_quad/control/neural.py`, `src/simulador_quad/ml/dataset.py`, tests.

### Fase 4 — Comparación cerrada y OOD

- [ ] Ejecutar controladores sobre escenarios pareados.
  - Aceptación: baseline clásico, oráculo, `neural` outer-force y `neural_position` si se conserva, con mismas métricas y metadata.
  - Verificar: reportes CSV y `metrics.metadata`.
  - Archivos: `results/`, `data/*/run_report*.csv`.

- [ ] Ejecutar OOD representativo.
  - Aceptación: al menos `neural_ood_lemniscate` y `composite_ood`; idealmente batería de 3 escenarios OOD.
  - Verificar: terminación, RMSE, saturación, degradación y clipping outer-force.
  - Archivos: `scenarios/`, `results/`, `data/neural_ood/`.

- [ ] Producir `comparison_closed_loop_v1.csv`.
  - Aceptación: filas por `scenario_id`, controlador, split/OOD, `position_rmse_m`, `position_mae_m`, `position_max_err_m`, `termination_reason`, saturación, degradación, clipping y commit/hash.
  - Verificar: CSV parseable y trazable a `metrics.json`.
  - Archivos: ubicación a decidir en `results/` o `data/`.

### Fase 5 — Pruebas y deuda física acotada

- [ ] Reforzar test hover ENU/FRD.
  - Aceptación: prueba de hover con fuerza en cuerpo FRD y orientación nivelada que detecte signo incorrecto de empuje.
  - Verificar: `uv run pytest tests\test_dynamics.py`.
  - Archivos: `tests/test_dynamics.py`.

- [ ] Unificar o documentar drag lineal.
  - Aceptación: una sola fuente efectiva de drag en dinámica, sin imports muertos, o documentación explícita de responsabilidades.
  - Verificar: tests de dinámica/runner relevantes.
  - Archivos: `src/simulador_quad/dynamics/`, `src/simulador_quad/runner.py`, docs.

- [ ] Revisar telemetría para auditoría de fuerza.
  - Aceptación: `desired_force_W_N` y, si procede, fuerzas de perturbación disponibles por muestra o justificación de no incluirlas.
  - Verificar: inspección de `telemetry.json` generado en smoke.
  - Archivos: `src/simulador_quad/telemetry.py`, `src/simulador_quad/runner.py`, docs.

### Fase 6 — Documentación final para memoria

- [ ] Actualizar `docs/simulador/validacion.md`.
  - Aceptación: escenarios oficiales, OOD, criterios comparativos y advertencia test vs OOD están completos.
  - Verificar: lectura cruzada con resultados.
  - Archivos: `docs/simulador/validacion.md`.

- [ ] Actualizar `docs/simulador/control_neuronal.md` y `dataset_clasico.md`.
  - Aceptación: comandos reales, rutas generadas, checkpoints vigentes y limitaciones legacy documentadas.
  - Verificar: comandos copiados coinciden con artefactos existentes.
  - Archivos: `docs/simulador/control_neuronal.md`, `docs/simulador/dataset_clasico.md`.

- [ ] Actualizar trazabilidad y README.
  - Aceptación: filas `Parcial` tienen criterio de cierre o pasan a estado correcto; README distingue tooling implementado de evidencia generada.
  - Verificar: revisión documental.
  - Archivos: `docs/simulador/trazabilidad.md`, `README.md`.

## Criterios de cierre global

- Existe al menos un checkpoint outer-force vigente con `output_dim: 3`.
- Existe dataset `outer_force_dataset/v1` trazable a `classic_dataset/v1`.
- Existe comparación cerrada con CSV y metadata de commit.
- Los resultados OOD no se mezclan con el split `test`.
- `composite_ood` inicia en el primer punto de ruta y figura en validación.
- La memoria puede afirmar qué está implementado, qué está evaluado y qué queda como limitación sin apoyarse en resultados legacy.

## Riesgos

- Coste computacional de regenerar banco y datasets: mitigar con smoke reducido antes de ejecución completa.
- Checkpoints legacy presentes en `data/neural_control`: mitigar con nombres y documentación que los marquen como históricos.
- OOD demasiado ambicioso para el tiempo disponible: priorizar lemniscata y composite antes de batería amplia.
- `neural_position` puede consumir tiempo sin mejorar el argumento principal: decidir temprano si se mantiene como comparación secundaria o se documenta como línea conservada sin evidencia final.
