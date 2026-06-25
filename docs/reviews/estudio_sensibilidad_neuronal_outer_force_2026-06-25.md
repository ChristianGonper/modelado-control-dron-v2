# Handoff: estudio de sensibilidad del control neuronal outer-force

Documento para que otro agente evalúe qué se hizo, qué evidencia existe y cómo verificarlo.

**Fecha:** 2026-06-25  
**Origen del encargo:** [`TFG_Memoria/docs/instrucciones_control_neuronal_pendiente.md`](../../TFG_Memoria/docs/instrucciones_control_neuronal_pendiente.md)  
**Alcance:** control neuronal `outer_force_min_v1` (MLP, GRU, LSTM). Fuera de alcance: `neural_position`.

---

## 1. Objetivo

Comprobar si cambiar hiperparámetros respecto al baseline v1 (`hidden_dim=64`, `L=20`, `seed=42`, `patience=10`) altera de forma relevante:

1. MSE supervisado en `train`, `val` y `test`.
2. Desempeño en bucle cerrado (`test` y `ood`): RMSE de posición, éxito de misión, saturación y clipping.

Las variantes debían guardarse **sin sobrescribir** el baseline v1, para poder comparar y justificar la configuración en la memoria.

---

## 2. Cambios de código introducidos

| Archivo | Cambio |
|---------|--------|
| [`tools/run_neural_outer_force_dataset.py`](../../tools/run_neural_outer_force_dataset.py) | Nuevo flag `--variant-tag`. Escribe resultados en `{result_dir}_neural_{arch}_{tag}` y guarda informes en `data/neural_ablation/reports/` (no en el dataset v1). |
| [`tools/run_neural_sensitivity_study.py`](../../tools/run_neural_sensitivity_study.py) | Orquestador secuencial de los 9 experimentos (entrenar → eval supervisada → bucle cerrado test/ood). |
| [`tools/summarize_neural_sensitivity.py`](../../tools/summarize_neural_sensitivity.py) | Consolidador de comparativa vs baseline en `results/neural_sensitivity/`. |
| [`tests/test_neural_batch_tools.py`](../../tests/test_neural_batch_tools.py) | Actualizado el mock de `_run_row` para el nuevo parámetro `variant_tag`. |

**No se modificó:** `tools/run_experimental_campaign.py`, `results/comparison_*.csv` ni `results/evidence_manifest.csv`.

---

## 3. Diseño experimental

Constantes compartidas (salvo el parámetro bajo estudio): `feature-version=outer_force_min_v1`, `epochs=100`, `batch-size=64`, `lr=1e-3`, `patience=10`, dataset `data/outer_force_dataset/v1`.

| Bloque | ID | Arquitecturas | Parámetro variado | Directorio `--out` |
|--------|-----|---------------|-------------------|-------------------|
| A (prioridad alta) | `h128` | MLP, GRU, LSTM | `--hidden-dim 128` | `data/neural_control/outer_force_{arch}_min_v1_h128` |
| B (ventana) | `L10` | GRU, LSTM | `--sequence-length 10` | `..._min_v1_L10` |
| B (ventana) | `L40` | GRU, LSTM | `--sequence-length 40` | `..._min_v1_L40` |
| C (semillas) | `seed7` | MLP | `--seed 7` | `..._min_v1_seed7` |
| C (semillas) | `seed123` | MLP | `--seed 123` | `..._min_v1_seed123` |

**Total:** 9 entrenamientos nuevos + baseline v1 (3 arquitecturas).

**Política de paralelización aplicada:**
- Fases clásicas (generación de datasets, OOD clásico): `--workers 16`.
- Entrenamiento y bucle cerrado neuronal: secuencial, `--workers 1`.

---

## 4. Qué se ejecutó (orden cronológico)

### 4.1 Preparación del entorno local

No existía `data/` en el repositorio (gitignored). Se generó la base experimental localmente:

1. `run_experimental_campaign.py --phase 2-6 --workers 16`  
   - Fases 2–5 OK: `classic_dataset/v1`, `outer_force_pid_bank/v1`, `outer_force_dataset/v1`.  
   - Fase 6 **falló** (`position_gain_dataset`): PID de banco no encontrado. **No afecta** a este estudio.
2. Entrenamiento baseline v1 (MLP, GRU, LSTM) con CUDA (~8,5 min).
3. Evaluación supervisada baseline (`train,val,test`).
4. Generación OOD + baseline clásico OOD (`--workers 16`).
5. Bucle cerrado baseline v1 (`test` + `ood`, `--workers 1`, ~5,5 min).
6. Estudio de sensibilidad completo (`run_neural_sensitivity_study.py --device cuda --workers 1`, ~44 min).
7. Consolidación (`summarize_neural_sensitivity.py`).

### 4.2 Comandos de reproducción

```powershell
# Estudio completo (requiere baseline v1 y datasets)
uv run python tools/run_neural_sensitivity_study.py --device cuda --workers 1

# Solo un bloque
uv run python tools/run_neural_sensitivity_study.py --blocks h128 --device cuda --workers 1

# Consolidar comparativa
uv run python tools/summarize_neural_sensitivity.py
```

---

## 5. Inventario de evidencia

### 5.1 CSV consolidados (punto de entrada para evaluación)

Ubicación: [`results/neural_sensitivity/`](../../results/neural_sensitivity/)
durante la ejecución local. Para conservar una evidencia ligera dentro del
repositorio, los cuatro CSV consolidados se reflejan también en
[`docs/reviews/annexes/2026-06-25/neural_sensitivity/`](annexes/2026-06-25/neural_sensitivity/).

| Archivo | Filas | Contenido |
|---------|-------|-----------|
| `study_manifest.csv` | 12 | Estado por variante (baseline + 9 variantes). Todas en `state=complete`. |
| `supervised_comparison.csv` | 36 | MSE normalizado y RMSE de fuerza por variante × split (`train/val/test`). |
| `closed_loop_comparison.csv` | 396 | Métricas por escenario y variante en `test` y `ood`. |
| `summary_vs_baseline.csv` | 18 | Agregados y **deltas** respecto al baseline v1 por arquitectura y split. |

### 5.2 Artefactos de entrenamiento (por variante)

Bajo `data/neural_control/` (gitignored):

```
outer_force_{mlp,gru,lstm}_min_v1          # baseline
outer_force_{mlp,gru,lstm}_min_v1_h128
outer_force_{gru,lstm}_min_v1_L10
outer_force_{gru,lstm}_min_v1_L40
outer_force_mlp_min_v1_seed7
outer_force_mlp_min_v1_seed123
```

Por cada directorio:
- `config.yaml` — hiperparámetros registrados
- `checkpoints/{arch}_best.pt`
- `normalization.json`
- `metrics/{train,val,test}_force_metrics.json`
- `metrics/val_metrics.json` (historial de entrenamiento)

### 5.3 Bucle cerrado

**Baseline v1** (sin tag, rutas estándar):
- Test: `data/outer_force_dataset/v1/results/*_neural_{mlp,gru,lstm}/metrics.json`
- Informes: `data/outer_force_dataset/v1/run_report_neural_{arch}.csv`
- OOD: `data/neural_ood/battery_v1/results/*_neural_{arch}/metrics.json`
- Informes OOD: `data/neural_ood/battery_v1/run_report_neural_{arch}.csv`

**Variantes** (con tag, no pisan v1):
- Resultados: `.../results/*_neural_{arch}_{tag}/metrics.json`
- Informes: `data/neural_ablation/reports/run_report_{tag}_{arch}_{test|ood}.csv` (18 archivos)

### 5.4 Datasets compartidos (no regenerados por variante)

| Ruta | Rol |
|------|-----|
| `data/classic_dataset/v1/` | Dataset clásico + PIDs congelados |
| `data/outer_force_dataset/v1/` | Dataset de imitación outer-force (150 episodios) |
| `data/outer_force_pid_bank/v1/` | Banco PID externo por escenario |
| `data/neural_ood/battery_v1/` | Batería OOD (10 escenarios) |

### 5.5 Integridad del baseline v1

Se comprobó que los checkpoints baseline **no cambiaron** tras el estudio:

| Checkpoint | Timestamp UTC verificado |
|------------|-------------------------|
| `outer_force_mlp_min_v1/checkpoints/mlp_best.pt` | `2026-06-25T09:10:46.8661805Z` |
| `outer_force_gru_min_v1/checkpoints/gru_best.pt` | `2026-06-25T09:13:14.7976251Z` |
| `outer_force_lstm_min_v1/checkpoints/lstm_best.pt` | `2026-06-25T09:16:03.1089156Z` |

---

## 6. Resultados agregados (para evaluación rápida)

Fuente: `summary_vs_baseline.csv`. Métrica principal: **bucle cerrado `test`**, `delta_rmse_mean` (positivo = peor que baseline).

| Variante | Arch | ΔRMSE test | Δ éxito misión test | Notas |
|----------|------|------------|---------------------|-------|
| h128 | MLP | +0.001 | 0 | Prácticamente igual |
| h128 | GRU | +0.005 | 0 | Ligeramente peor en test |
| h128 | LSTM | **−0.023** | 0 | Mejor RMSE en test |
| L10 | GRU | +0.003 | 0 | Similar |
| L10 | LSTM | −0.004 | 0 | Ligeramente mejor |
| L40 | GRU | ≈ 0 | 0 | Similar |
| L40 | LSTM | −0.017 | 0 | Mejor en test |
| seed7 | MLP | +0.001 | 0 | Variabilidad baja |
| seed123 | MLP | +0.001 | 0 | Variabilidad baja |

**Supervisado (test MSE):** `h128` mejora mucho GRU/LSTM en MSE (p. ej. GRU 0.00027 vs 0.00211), pero eso **no se traduce** de forma uniforme en mejor bucle cerrado en `test`. `L40` empeora el MSE supervisado de GRU de forma notable.

**OOD:** más disperso; GRU con L10/L40 gana +10 pp de éxito de misión; MLP baseline y variantes muestran clipping distinto entre escenarios.

### Conclusión provisional (criterio del documento de instrucciones)

> Si estos estudios no cambian la conclusión, la memoria puede presentar `hidden_dim=64` y `L=20` como configuración suficiente.

Con la evidencia actual: **ninguna variante mejora de forma clara y sistemática el bucle cerrado en `test` sin trade-offs**. La configuración v1 sigue justificable. La sensibilidad por semilla en MLP es baja.

**Matiz:** LSTM con `h128` o `L40` mejora RMSE en `test` respecto al baseline v1 local; conviene que el agente evaluador inspeccione si eso es robusto escenario a escenario (`closed_loop_comparison.csv`) o depende de pocos casos.

---

## 7. Limitaciones y trabajo pendiente

| Tema | Estado |
|------|--------|
| `neural_position` (fase 6) | No ejecutado; fallo conocido en generación de PIDs de banco |
| `results/evidence_manifest.csv` | **No actualizado** con filas de sensibilidad |
| `results/comparison_all_runs.csv` | **No actualizado**; la sensibilidad vive en `results/neural_sensitivity/` |
| Integración en memoria LaTeX | **Pendiente** (`TFG_Memoria/sections/05_control_neuronal.tex`) |
| Baseline v1 en Git | Los CSV versionados en `results/` (commit `fe2e075`) describen un snapshot anterior; el baseline **local** se regeneró en esta sesión |
| Fase 1 de campaña (`pytest`) | Fallan 2 tests preexistentes si no hay `data/`; no bloqueó este estudio |

---

## 8. Checklist para el agente evaluador

1. **Existencia:** leer `results/neural_sensitivity/study_manifest.csv` y confirmar 12 filas con `state=complete`.
2. **Cobertura:** cada variante debe tener 3 splits supervisados + 23 test + 10 ood (`study_manifest.csv`).
3. **No regresión v1:** verificar timestamps de checkpoints baseline (sección 5.5) y ausencia de sobrescritura en `*_neural_{arch}/` sin tag.
4. **Coherencia numérica:** cruzar `summary_vs_baseline.csv` con agregación manual desde `closed_loop_comparison.csv`.
5. **Interpretación:** priorizar bucle cerrado `test` sobre MSE supervisado; documentar sensibilidad OOD por separado.
6. **Decisión de memoria:** si se mantiene v1, citar este estudio como justificación; si se adopta otra variante, argumentar con `closed_loop_comparison.csv` escenario a escenario.

### Comandos de verificación sugeridos

```powershell
# Manifest y resumen
Get-Content results/neural_sensitivity/study_manifest.csv
Get-Content results/neural_sensitivity/summary_vs_baseline.csv

# Contar informes de ablación
(Get-ChildItem data/neural_ablation/reports).Count  # esperado: 18

# Reconsolidar (idempotente)
uv run python tools/summarize_neural_sensitivity.py
```

---

## 9. Referencias cruzadas

- Instrucciones originales: [`TFG_Memoria/docs/instrucciones_control_neuronal_pendiente.md`](../../TFG_Memoria/docs/instrucciones_control_neuronal_pendiente.md)
- Manifiesto de evidencia (snapshot anterior, sin sensibilidad): [`results/evidence_manifest.csv`](../../results/evidence_manifest.csv)
- Comparativa canónica anterior: [`results/comparison_summary.csv`](../../results/comparison_summary.csv)
