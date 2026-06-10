# Backlog de subsanación — Auditoría integral TFG (2026-06-10)

**Origen:** `auditoria_integral_tfg_2026-06-10.md` y CSV de hallazgos.  
**Estado:** decision-complete; no implementado en esta auditoría.

---

## Fase 1 — Correcciones invalidantes de contrato, física o metodología

*Ninguna acción P0 en el snapshot auditado. No iniciar fase 2 sin confirmar ausencia de regresiones físicas.*

| ID | Problema | Decisión | Resultado esperado | Áreas | Verificación |
|----|----------|----------|-------------------|-------|--------------|
| — | — | Mantener invariantes ENU/FRD y contrato neural 3 salidas | Sin cambio de severidad | `src/simulador_quad/core/`, `control/neural.py` | `uv run pytest tests/test_attitude.py tests/test_neural_outer_force.py -q` |

---

## Fase 2 — Refuerzo de pruebas y validación

| ID | Problema | Decisión | Resultado esperado | Áreas | Dependencias | Verificación |
|----|----------|----------|-------------------|-------|--------------|--------------|
| BL-08 | F-006 `test_ideal_hover` no FRD | Reescribir test con `get_level_quaternion` o consolidar con `test_hover_level_frd_thrust_sign` | Un test canónico de hover FRD en dinámica | `tests/test_dynamics.py` | — | `uv run pytest tests/test_dynamics.py -q` |
| BL-09 | F-007 sin sensibilidad `physics_dt_s` | Añadir test de convergencia caída libre u hover con dt, dt/2, dt/4 | Tolerancia documentada en test | `tests/test_dynamics.py` o nuevo módulo | BL-08 opcional | Test nuevo pasa con umbrales declarados |

---

## Fase 3 — Coherencia de pipelines y reproducibilidad

| ID | Problema | Decisión | Resultado esperado | Áreas | Dependencias | Verificación |
|----|----------|----------|-------------------|-------|--------------|--------------|
| BL-01 | F-001 evidencia ignorada por Git | Publicar `data/manifest_evidencia_memoria.json` versionado con hashes, commit, comando y rutas locales | Trazabilidad externa sin versionar telemetrías masivas | `docs/simulador/validacion.md`, nuevo manifiesto | — | Manifiesto referenciado en memoria y coherente con artefactos locales |
| BL-03 | F-003 metadata desalineada | Re-ejecutar corridas citadas con `git status` limpio y anotar HEAD en memoria | `git_commit==HEAD`, `git_dirty==false` | Campaña fases 4-10 | BL-01 | Muestreo ≥5 `metrics.json` cumple |
| BL-04 | F-004 sin neural_position | Ejecutar fases 6-9 campaña para `position_gain_dataset` y `position_*` | Artefactos locales completos | `tools/generate_position_gain_*`, `train_neural_position_*` | BL-03 | Existen `data/position_gain_dataset/v1/manifest.csv` y checkpoints |
| BL-05 | F-005 sin transferencia PID | Ejecutar `tools/run_classic_transfer_dataset.py` | `results_transfer/` poblado | `tools/run_classic_transfer_dataset.py` | BL-03 | Directorio existe con metrics por escenario |
| BL-02a | F-002 matriz incompleta (consolidación) | Ejecutar `tools/summarize_comparison.py` tras BL-04 y BL-05 | `comparison_all_runs.csv` con oracle, transfer, position | `tools/summarize_comparison.py`, `results/` | BL-04; BL-05 | CSV contiene controladores faltantes |
| BL-02b | F-002 CSV unificado memoria | Ejecutar `tools/build_comparison_closed_loop.py` | `results/comparison_closed_loop_v1.csv` | `tools/build_comparison_closed_loop.py` | BL-02a | Archivo existe y columnas documentadas en validacion.md |
| BL-06 | F-003 política re-ejecución | Documentar en README que evidencia local debe regenerarse tras cambios de commit | Procedimiento explícito | `README.md` | BL-03 | Párrafo reproducibilidad actualizado |
| BL-07 | F-004 cierre trazabilidad position | Actualizar fila `neural_position` en trazabilidad cuando exista evidencia | Estado «Implementado» con evidencia | `docs/simulador/trazabilidad.md` | BL-04 | Fila 40 sin «pendiente evidencia» |

---

## Fase 4 — Saneamiento de documentación viva

| ID | Problema | Decisión | Resultado esperado | Áreas | Dependencias | Verificación |
|----|----------|----------|-------------------|-------|--------------|--------------|
| BL-10 | F-008 pyproject plantilla | Actualizar `description` | Metadatos coherentes con TFG | `pyproject.toml` | — | Campo no vacío ni plantilla |
| BL-12 | F-010 README plans | Corregir sección planes: vigente = `docs/simulador/`; histórico = `archived/` | Sin ruta activa vacía | `README.md` | — | Texto alineado con listado real |
| BL-13 | F-011 control_effort alias | Añadir nota `deprecated` en export o guía memoria | Memoria no usa heuristic | `metrics/report.py`, `guia_uso.md` | — | Memoria revisada |
| BL-15 | F-013 filas Parcial | Tabla cierre con criterio/fecha por fila Parcial | Deuda trazable | `trazabilidad.md` | — | 4 filas Parcial con criterio |
| BL-16 | F-014 rmse_std | Cambiar etiqueta LaTeX a «dispersión entre escenarios» | Sin símbolo ± como IC | `summarize_comparison.py`, memoria | BL-02a | Tabla LaTeX corregida |

---

## Fase 5 — Etiquetado o depuración histórica

| ID | Problema | Decisión | Resultado esperado | Áreas | Dependencias | Verificación |
|----|----------|----------|-------------------|-------|--------------|--------------|
| BL-17 | F-015 auditoría jun-02 obsoleta | Actualizar `docs/reviews/README.md` para citar **este** informe 2026-06-10 como vigente | Una sola fuente diagnóstica | `docs/reviews/README.md` | — | README apunta a 2026-06-10 |
| BL-18 | F-016 reviews mayo | Banner histórico en cabecera de cada `auditoria_*` mayo | Apertura aislada no confunde | `docs/reviews/auditoria_*.md` (mayo) | BL-17 | Banner en ≥6 ficheros mayo |
| BL-11 | F-009 memoria AGENTS | Sustituir referencia a plan archivado por fuentes vigentes | AGENTS memoria alineado | `TFG_Memoria/AGENTS.md` | BL-17 | Línea 14 corregida |
| BL-19 | F-017 límites actitud | Etiquetar `circle_drag`/`circle_noisy_wind` como demo o endurecer si se citan | Escenarios memoria coherentes | `scenarios/`, `validacion.md` | — | Documentación o YAML actualizado |

---

## Fase 6 — Regeneración experimental futura

| ID | Problema | Decisión | Resultado esperado | Áreas | Dependencias | Verificación |
|----|----------|----------|-------------------|-------|--------------|--------------|
| BL-14 | F-012 semilla única | Opcional: segunda semilla en MLP outer-force o declarar limitación en memoria | Limitación explícita o repetición | Campaña fase 7, memoria | BL-03 | config.yaml documenta semillas |
| BL-24 | OOD batería completa | Ejecutar fase 10 campaña para 4 controladores × battery_v1 | Métricas OOD para classic, outer-force×3, position×3 | `run_experimental_campaign.py` | BL-04; BL-02a | `data/neural_ood/battery_v1/results/` completo |
| BL-25 | Oráculo en comparativa | Verificar que `outer_force_dataset/v1/results/` alimenta filas oracle en summarize | Oráculo por escenario tabulado | `summarize_comparison.py` | BL-02a | `outer_force_oracle` en CSV |

*Comando orquestador (fuera de esta auditoría):*

```powershell
uv run python tools\run_experimental_campaign.py --rerun --workers 8 --device auto
```

---

## Fase 7 — Actualización posterior de la memoria

| ID | Problema | Decisión | Resultado esperado | Áreas | Dependencias | Verificación |
|----|----------|----------|-------------------|-------|--------------|--------------|
| BL-20 | F-018 Plotly | Párrafo en metodología software o anexo sobre visualización 3D | Justificación académica breve | `TFG_Memoria/sections/06_metodologia.tex` o `docs/03_*` | Fase 4 opcional | Texto presente |
| BL-21 | F-019 Python 3.13 | Declarar versión mínima en memoria y README | Reproducibilidad declarada | `README.md`, memoria anexo comandos | — | Versión documentada |
| BL-22 | F-020 pytest deps | Mover a dev group (opcional pre-defensa) | Separación dependencias | `pyproject.toml` | — | `uv sync` sin pytest en runtime si aplica |
| BL-23 | F-021 composite | Declarar limitación transiciones por referencia en memoria resultados OOD | Claim proporcional | `TFG_Memoria/sections/07_resultados.tex`, `validacion.md` | BL-24 | Limitación explícita |
| BL-26 | Sección resultados | Redactar tablas desde `comparison_closed_loop_v1.csv` con commit y comando | Resultados defendibles | `TFG_Memoria/sections/07_resultados.tex` | BL-02b; BL-03 | Tablas con metadata trazable |

---

## Orden recomendado de ejecución

1. BL-17, BL-18, BL-11, BL-10, BL-12 (documentación rápida, sin GPU).
2. BL-03 → campaña `--rerun` (BL-04, BL-05, BL-24, BL-14).
3. BL-02a, BL-02b, BL-01, BL-06, BL-07.
4. BL-08, BL-09 (tests).
5. BL-16, BL-13, BL-15, BL-19, BL-20–BL-23, BL-26 (memoria).