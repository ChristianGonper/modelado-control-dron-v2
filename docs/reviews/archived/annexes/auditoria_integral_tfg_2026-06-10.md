# Auditoría integral TFG — Simulador quad 6DOF

**Fecha:** 2026-06-10  
**Alcance:** diagnóstico READ-ONLY con ejecución permitida (pytest, dry-run campaña, inspección `data/`/`results/` local). Sin commits, sin regeneración experimental, sin cambios fuera de `docs/reviews/`.  
**Especificación:** `SPEC.md` (raíz, no versionado en snapshot; aplicada como contrato de auditoría).  
**Baseline histórico:** `docs/reviews/auditoria_integral_tfg_2026-06.md` (2026-06-02, sin pytest).

---

## 1. Dictamen global

### **APTO CON RESERVAS MATERIALES**

El repositorio es **defendible como banco de ensayo académico** para un TFG que compara control clásico y control neuronal por imitación. El núcleo 6DOF, la normativa (`docs/01–03`), la documentación viva (`docs/simulador/`), la suite de pruebas (151 tests) y el tooling de campaña están en nivel adecuado para ingeniería de software científico.

Las **reservas materiales** no invalidan la física ni el código neuronal vigente (contrato 3 salidas outer-force), sino la **brecha entre evidencia local regenerada parcialmente y el paquete comparativo completo** exigido por el diseño experimental del TFG: faltan `neural_position`, transferencia PID cruzada, CSV unificado `comparison_closed_loop_v1.csv`, alineación commit/metadata y versionado de evidencia bajo `.gitignore`.

| Severidad | Cantidad |
|-----------|----------|
| P0 | 0 |
| P1 | 5 |
| P2 | 12 |
| P3 | 4 |
| **Total** | **21** |

---

## 2. Snapshot auditado (Ronda 0)

| Campo | Valor |
|-------|-------|
| **HEAD** | `560c5a879fbc7cf307607d8a4721624a999638a3` |
| **Autor / fecha** | Christian, 2026-06-10 13:26:09 +0200 — «Documenta paralelizacion de pipelines PID» |
| **git status --short** | `?? SPEC.md` (único no rastreado) |
| **Archivos versionados** | 179 (`git ls-files`) |
| **Evidencia local inspeccionada** | `data/classic_dataset/v1`, `data/outer_force_*`, `data/neural_control/outer_force_*`, `data/neural_ood/battery_v1`, `results/comparison_*.csv` |
| **Delta vs auditoría 2026-06-02** | Outer-force y checkpoints 3-salidas **existen localmente** (antes P0 en informe jun-02); persisten lagunas comparativa completa, neural_position, transfer, reproducibilidad commit |

### Comandos base ejecutados

| Comando | Resultado |
|---------|-----------|
| `git status --short` | `?? SPEC.md` |
| `git rev-parse HEAD` | `560c5a879fbc7cf307607d8a4721624a999638a3` |
| `git log -1 --format=fuller` | commit 560c5a8, 2026-06-10 |
| `uv run pytest -q` | **151 passed** en 74.77s |
| `uv run pytest --collect-only -q` | **151 tests**, 33 ficheros |
| `uv run python tools\run_experimental_campaign.py --dry-run` | OK, 11 fases listadas sin ejecutar |

### Comandos prohibidos (no ejecutados)

- `run_experimental_campaign.py` sin `--dry-run` (regeneración masiva).
- `train_neural_controller.py` / entrenamientos completos.
- `generate_classic_dataset.py --overwrite` y regeneración de datasets.
- Commits o cambios fuera de `docs/reviews/`.

### Comandos permitidos adicionales usados

- Inspección estática de `data/`, `results/`, memoria LaTeX, anexos por dominio.
- Conteo de tests por fichero vía pytest collect.

---

## 3. Matriz de ownership (R0)

| Dominio | Propietario primario | Superficie principal |
|---------|---------------------|----------------------|
| A01 | Gobierno, entorno | `AGENTS.md`, `.gitignore`, `pyproject.toml`, `uv.lock`, `data/.gitignore`, `results/.gitignore` |
| A02 | Normativa | `docs/01_principios_tfg.md`, `docs/02_requisitos_ingenieria_simulador.md`, `docs/03_criterios_ingenieria_software.md` |
| A03 | Marcos / dinámica | `src/simulador_quad/core/`, `dynamics/rigid_body.py`, `tests/test_dynamics.py`, `tests/test_attitude.py` |
| A04 | Actuadores / control clásico | `dynamics/actuators.py`, `mixer.py`, `control/classic.py`, `tests/test_actuators.py`, `tests/test_mixer.py`, `tests/test_control.py` |
| A05 | Trayectorias / escenarios | `trajectories/`, `scenarios/`, `tests/test_trajectories.py`, `tests/test_scenarios.py`, `tests/test_composite_trajectory.py` |
| A06 | Ejecución / telemetría | `app.py`, `runner.py`, `telemetry/`, `metrics/`, `visualization/` |
| A07 | Dataset clásico / PID | `datasets/classic.py`, `tools/generate_classic_dataset.py`, `tune_classic_pid.py`, `run_classic_transfer_dataset.py` |
| A08 | ML supervisado | `src/simulador_quad/ml/`, `tools/train_neural_controller.py`, `evaluate_neural_controller.py` |
| A09 | Control neuronal cerrado | `control/neural.py`, `tools/run_neural_*`, `tests/test_neural_*` |
| A10 | Oráculo / campañas | `tools/generate_outer_force_*`, `run_experimental_campaign.py`, `summarize_comparison.py`, `build_comparison_closed_loop.py` |
| A11 | Pruebas / validación numérica | `tests/` (33 ficheros, 151 tests) |
| A12 | Evidencia local | `data/`, `results/` (muestras) |
| A13 | Ecosistema documental | `README.md`, `docs/simulador/`, `docs/reviews/`, `docs/plans/archived/` |
| A14 | Memoria | `TFG_Memoria/` |

**Gate G0:** Todos los archivos versionados asignados; `SPEC.md` sin owner (no versionado).

---

## 4. Metodología y limitaciones

- **Rondas:** R0 congelación → R1 revisión por dominio (anexos A01–A14) → R2 contraste cruzado → R3 red team (§8) → R4 consolidación (este informe).
- **Precedencia:** `AGENTS.md` > `docs/01–03` > código/pruebas > `docs/simulador/` > evidencia local > memoria > reviews históricas.
- **Limitación:** Evidencia en `data/`/`results/` existe localmente pero **no es auditable desde Git** (F-001). Conclusiones sobre comparativa completa requieren regeneración (F-002, F-004, F-005).
- **No verificable en alcance:** entrenamientos multi-semilla masivos, campaña GPU completa, compilación LaTeX PDF.

---

## 5. Resumen por dominio

| Dom. | Veredicto breve | Hallazgos |
|------|-----------------|-----------|
| A01 | Entorno funcional; reproducibilidad documental débil | F-001, F-003, F-008, F-019, F-020 |
| A02 | Normativa sólida y coherente con alcance v1 | — |
| A03 | Física 6DOF defendible; validación numérica incompleta | F-006, F-007 |
| A04 | Control clásico y actuadores OK | — |
| A05 | Escenarios y composite operativos; límites demo permisivos | F-017, F-021 |
| A06 | Runner, telemetría y métricas con unidades | F-011 |
| A07 | Dataset clásico v1 local completo; sin transfer | F-005 |
| A08 | Pipeline ML outer-force OK; semilla única | F-012 |
| A09 | Código neural_position OK; sin artefactos | F-004 |
| A10 | Tooling campaña maduro; comparativa parcial | F-002, F-014 |
| A11 | 151 tests; trazabilidad documentada | ver anexo A11 |
| A12 | Evidencia outer-force local; no versionada | F-001, F-003 |
| A13 | Docs viva alineada; históricos y README mezclan vigencia | F-010, F-013, F-015, F-016, F-018 |
| A14 | Memoria prudente (resultados pendientes); AGENTS desalineado | F-009 |

---

## 6. Hallazgos consolidados

### P1 — Bloqueantes académicos (5)

| ID | Título | Evidencia primaria |
|----|--------|-------------------|
| F-001 | Evidencia local ignorada por Git | `data/.gitignore:1`, `results/.gitignore:1` |
| F-002 | Matriz comparativa incompleta | `results/comparison_all_runs.csv` (solo classic + neural_outer_force_*); falta `comparison_closed_loop_v1.csv` |
| F-003 | Metadata desalineada (commit/dirty) | `metrics.json:428-429` → `0cee096…`, `git_dirty: true` vs HEAD `560c5a8` |
| F-004 | Sin artefactos neural_position | Ausencia `data/position_gain_dataset/`, `data/neural_control/position_*` |
| F-005 | Sin transferencia PID cruzada | Ausencia `data/classic_dataset/v1/results_transfer/` |

### P2 — Mejoras materiales (12)

F-006 test_ideal_hover · F-007 sensibilidad dt · F-008 pyproject plantilla · F-009 memoria AGENTS plan archivado · F-010 README plans · F-011 control_effort alias · F-012 semilla única · F-013 trazabilidad Parcial · F-014 rmse_std LaTeX · F-015 auditoría jun-02 obsoleta · F-016 etiquetado mayo · F-017 límites actitud demo

### P3 — Pulido (4)

F-018 Plotly · F-019 Python 3.13 · F-020 pytest deps · F-021 transiciones composite

Detalle SPEC §14: `auditoria_integral_tfg_2026-06-10_hallazgos_appendix.md`. Registro tabular: `_hallazgos.csv`.

---

## 7. Contraste cruzado R2 (resumen)

| Revisión cruzada | Owner → Revisor | Hallazgo reforzado | Contraevidencia revisada |
|------------------|-----------------|--------------------|-------------------------|
| Dinámica ↔ control | A03 → A04 | F-006 hover test | `test_hover_level_frd_thrust_sign` mitiga pero no cierra F-006 |
| Escenarios ↔ runner | A05 → A06 | F-021 composite | Tests composite validan contrato, no asentamiento estado |
| Clásico ↔ tuneo/datasets | A07 → A10 | F-005 transfer | `summarize_comparison.py:72` listo; sin datos |
| ML features ↔ inferencia | A08 → A09 | F-004 position | Outer-force usa observation; position sin dataset |
| Neuronal ↔ campañas/evidencia | A09 → A12 | F-002, F-004 | Outer-force local existe; position no |
| Pruebas ↔ requisitos | A11 → A02 | F-007 dt | Matriz trazabilidad no exige dt-study |
| Normativa ↔ memoria | A02 → A14 | F-009, resultados pendientes | `07_resultados.tex:1-3` prudente |
| Tooling ↔ artefactos | A10 → A12 | F-002 | `comparison_summary.csv` parcial (249 filas agregadas, 4 controladores en raw) |

**Gate G2:** Ningún P1 aceptado con una sola perspectiva.

---

## 8. Red team (R3)

| ID | Intento de refutación | Resultado |
|----|----------------------|-----------|
| F-001 | «README documenta regeneración» | **Mantiene P1:** ignorar `*` impide defensa reproducible sin manifiesto versionado |
| F-002 | «Existen comparison_*.csv» | **Mantiene P1:** faltan oracle, transfer, position y CSV unificado citado en validacion.md |
| F-003 | «Diseño metadata en app.py correcto» | **Mantiene P1:** evidencia almacenada es de otro commit y dirty |
| F-004 | «Tests position pasan» | **Mantiene P1:** verificación ≠ validez experimental sin artefactos |
| F-005 | «Transfer es opcional» | **Mantiene P1:** diseño TFG y README:109 lo incluyen en comparativa |
| F-006 | «Existe test FRD separado» | **Rebaja impacto, mantiene P2:** deuda de claridad en suite |
| F-015 | «Jun-02 es histórico» | **Mantiene P2:** sin errata explícita en el propio fichero |

**Gate G3:** P1 conservan contraevidencia documentada en CSV.

---

## 9. Mapa E1–E6 (afirmaciones centrales)

| Afirmación | E1 | E2 | E3 | E4 | E5 | E6 | Brecha |
|------------|----|----|----|----|----|----|--------|
| Simulador 6DOF ENU/FRD coherente | docs/02, requisitos marcos | `core/frames.py`, `rigid_body.py` | `test_attitude.py`, `test_dynamics.py` | `hover_clean.yaml` | pytest + metadata diseño | Limitaciones v1 declaradas | E4 numérica dt (F-007) |
| Dataset clásico 150 episodios | docs/simulador/dataset_clasico.md | `datasets/classic.py` | `test_classic_dataset_*` | manifest v1 | local summary.csv | Uso académico baseline | E5 commit (F-003) |
| Control neural outer-force 3 salidas | control_neuronal.md | `NeuralOuterForceController` | `test_neural_outer_force.py` | checkpoints min_v1 | config.yaml local | Comparación vs clásico | E5-E6 incompletos (F-002) |
| Control neural_position | control_neuronal.md | `NeuralPositionController` | `test_neural_position_control.py` | — | — | Hipótesis alternativa | **E4-E6 ausentes** (F-004) |
| Generalización OOD | validacion.md | `generate_ood_battery.py` | `test_evaluate_ood_split.py` | battery_v1 local | parcial neural OOD | Claims proporcionales | E6 sin position/transfer (F-002) |
| Reproducibilidad fuerte | docs/03 | `app.py:53-54` | `test_app_metadata.py` | cualquier run | **evidencia 0cee096 dirty** | — | **E5 roto** (F-003) |

---

## 10. Brechas de trazabilidad requisito → evidencia memoria

1. **Comparación cuádruple** (docs/01, README): sin filas oracle/position/transfer en CSV actual.
2. **neural_position** (trazabilidad.md:40): implementado en código, sin manifest/checkpoints locales.
3. **Transferencia PID** (README:109): tooling sin `results_transfer/`.
4. **comparison_closed_loop_v1.csv** (validacion.md:59): documentado, archivo ausente en `results/`.
5. **Commit reproducible** (trazabilidad.md:36): metadata local ≠ HEAD auditado.
6. **Manifiesto evidencia versionado** (F-001): no sustituye `.gitignore` global.

---

## 11. Afirmaciones permitidas y no permitidas (memoria)

### Permitidas (con evidencia actual o diseño verificado)

- El simulador implementa dinámica 6DOF con mundo ENU, cuerpo FRD y empuje en `-Z_B` (E1–E3).
- Existe dataset clásico v1 generado localmente con 150 episodios y PIDs congelados por familia (inspección `summary.csv`; E5 con reserva F-003).
- El contrato `neural` outer-force rechaza checkpoints legacy 4 salidas y acepta 3 salidas (tests).
- Checkpoints `outer_force_mlp/gru/lstm_min_v1` existen localmente bajo contrato vigente (inspección `config.yaml`: `output_dim: 3`).
- La memoria puede declarar **metodología** de dos lazos neuronales y comparación honesta (texto actual prudente en `07_resultados.tex`).
- Suite de 151 tests automatizados pasa en el snapshot auditado.

### No permitidas (hasta subsanar P1)

- Afirmar **reproducibilidad plena desde solo Git** sin copiar `data/`/`results/` (F-001).
- Publicar **tabla comparativa cerrada** baseline / oráculo / neural / neural_position / transfer sin regenerar (F-002, F-004, F-005).
- Citar **resultados como generados en commit 560c5a8** usando metrics con `0cee096` y `git_dirty: true` (F-003).
- Concluir **superioridad general** del control neuronal o de una arquitectura (diseño memoria lo evita; datos agregados parciales no bastan).
- Presentar `rmse_std` en tablas como **intervalo de confianza experimental** (F-014).
- Usar escenarios `circle_drag` con `max_attitude_angle_rad: 3.14` como evidencia fuerte de estabilidad sin calificar (F-017).

---

## 12. Delta vs auditoría 2026-06-02

| Hallazgo jun-02 | Estado 2026-06-10 |
|-----------------|-------------------|
| P0 sin outer-force en data/ | **Cerrado localmente** — existen `outer_force_dataset/v1`, `outer_force_pid_bank/v1`, checkpoints 3-out |
| P0 checkpoints legacy 4-out | **Mitigado** — rechazo en código; legacy no usado en comparativa actual |
| P0 sin tabla comparativa | **Parcial** — `comparison_all_runs.csv` sin matriz completa |
| P1 OOD WIP | **Cerrado tooling** — `generate_ood_battery.py` trackeado y testeado |
| P1 sin batch outer-force | **Cerrado** — `run_neural_outer_force_dataset.py` |
| P1 neural_position obs/state | **Refutado** — outer-force usa observation; position sin dataset |
| P1 test_ideal_hover | **Persiste** F-006 |
| P2 composite transición | **Persiste** F-021 (limitación) |
| ~29 tests | **Superado** — 151 tests |

**Regresión documental:** `auditoria_integral_tfg_2026-06.md` sigue listando P0 obsoletos (F-015).

---

## 13. Riesgos residuales

- Tribunal solicita reproducir resultados solo desde clone Git → **bloqueo** sin manifiesto (F-001).
- Mezcla de informes jun-02 y jun-10 → decisiones contradictorias (F-015).
- Interpretación de ± en tablas LaTeX generadas por `summarize_comparison.py` (F-014).
- OOD composite con transiciones cinemáticas puede fallar cerrado (evidencia `neural_outer_force_mlp` OOD composite 0% éxito en summary) — requiere narrativa cautelosa, no invalidación del modelo.

---

## 14. Orden recomendado de subsanación

Ver `auditoria_integral_tfg_2026-06-10_backlog.md`: documentación rápida (BL-17–BL-12) → re-ejecución campaña (BL-03–BL-05, BL-04) → consolidación (BL-02a/b) → tests (BL-08–09) → memoria (BL-26).

---

## 15. Entregables de esta auditoría

| # | Archivo |
|---|---------|
| 1 | `docs/reviews/auditoria_integral_tfg_2026-06-10.md` (este) |
| 2 | `docs/reviews/auditoria_integral_tfg_2026-06-10_hallazgos.csv` |
| 3 | `docs/reviews/auditoria_integral_tfg_2026-06-10_backlog.md` |
| 4 | `docs/reviews/auditoria_integral_tfg_2026-06-10_hallazgos_appendix.md` |
| 5–18 | `docs/reviews/annexes/2026-06-10/A01_*.md` … `A14_*.md` |

---

*Auditoría integral según SPEC.md. Coordinación R0–R4. Sin modificaciones fuera de `docs/reviews/`.*