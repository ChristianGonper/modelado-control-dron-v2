# Auditoría integral TFG — Simulador quad 6DOF (junio 2026)

**Fecha:** 2 junio 2026  
**Alcance:** análisis READ-ONLY de código y documentación (sin `pytest`, sin regeneración de datasets ni simulaciones).  
**Método:** cuatro ejes en paralelo (científico/TFG, simulador, neuronal, documentación) + síntesis consolidada.  
**Informes parciales:** integrados desde revisión de `docs/01–03`, `docs/simulador/*`, `src/simulador_quad/`, `tools/`, `tests/`, `scenarios/` y contraste con `docs/reviews/auditoria_sintesis_multivista.md` (2026-05-04).

---

## 1. Dictamen global

**Aptitud del repositorio como base de TFG: sí, con reservas.**

El repositorio cumple el rol de **banco de ensayo académico trazable** para un TFG que compara control clásico y control neuronal por imitación. La ingeniería de software, la documentación normativa y viva, la matriz de trazabilidad y el núcleo 6DOF están en un nivel defendible ante tribunal.

La reserva principal no es la ausencia de código neuronal ni la falta de modelo físico, sino la **brecha entre contrato documentado e implementado** y **evidencia experimental versionada** bajo el contrato vigente (`neural` outer-force, oráculo por escenario, OOD compuesto). Los artefactos en `data/neural_control/*_v1` y resultados OOD en `results/` pertenecen a una **fase legacy** (4 salidas directas) incompatible con `controller.type: neural` actual.

**Líneas neuronales:** la coexistencia de `neural` (fuerza externa ENU) y `neural_position` (programación de ganancias) es coherente con el TFG y debe mantenerse en la narrativa de la memoria como **dos hipótesis de lazo externo neuronal**, no como redundancia accidental.

---

## 2. Resumen por eje

| Eje | Veredicto breve |
| --- | --- |
| **A — Científico / TFG** | Marco normativo y trazabilidad sólidos; comparación de controladores **bien diseñada en docs**, **no materializada** en datos versionados. |
| **B — Simulador** | Modelo 6DOF, integración multi-rate, validación YAML y control clásico defendibles; deudas en tests ENU/FRD y drag duplicado. |
| **C — Neuronal** | Pipeline outer-force y `neural_position` implementados y testeados; **cero** artefactos `outer_force_*` en `data/`; evidencia cerrada legacy no usable para conclusiones finales. |
| **D — Documentación** | README, `docs/simulador/` y `docs/reviews/README.md` alineados con junio 2026; las auditorías multivista de mayo quedan como referencia histórica. |

---

## 3. Fortalezas para la memoria (consolidadas)

1. **Objetivo y alcance v1 explícitos** en `docs/01_principios_tfg.md`, `docs/02_requisitos_ingenieria_simulador.md` y `docs/simulador/README.md` (sin pretender gemelo digital ni aerodinámica formal).
2. **Matriz de trazabilidad** en `docs/simulador/trazabilidad.md` que enlaza requisito, código, prueba, escenario y métrica, incluyendo neuronal, dataset outer-force y OOD (estado Parcial donde corresponde).
3. **Convención ENU/FRD y empuje en `-Z_B`** con pruebas de signo y arquitectura documentada en `docs/simulador/arquitectura.md`.
4. **Dataset clásico v1** reproducible (`data/classic_dataset/v1/`: manifest, PIDs por familia, telemetría, filtros duros).
5. **Diseño experimental neuronal híbrido** (fuerza externa + PID interno fijo) con spec activa `docs/plans/spec_control_neuronal_fuerza_externa.md`, oráculo por escenario en diseño de `tools/generate_outer_force_*`, y línea alternativa `neural_position` documentada en `docs/simulador/control_neuronal.md`.
6. **Reproducibilidad en metadata** (`git_commit`, hash de escenario, `uv.lock` en `metrics.metadata` según `validacion.md` y `app.py`).
7. **Validación por escenario** en `docs/simulador/validacion.md` con umbrales iniciales para escenarios oficiales (adecuado para sanidad del banco y baseline clásico).

---

## 4. Hallazgos consolidados (P0 / P1 / P2)

### P0 — Bloquean o invalidan conclusiones en memoria sin acción previa

| ID | Hallazgo | Evidencia |
| --- | --- | --- |
| **P0-1** | No hay artefactos versionados del pipeline **outer-force** (`outer_force_pid_bank`, `outer_force_dataset`, checkpoints `outer_force_*`). | Sin coincidencias `outer_force` bajo `data/`; rutas documentadas en README y `control_neuronal.md`. |
| **P0-2** | Checkpoints en `data/neural_control/{mlp,gru,lstm}_v1` son **legacy** (`output_dim: 4`); incompatibles con `NeuralOuterForceController` (`control/neural.py`, `scenarios/loader.py`). | `config.yaml` en esos directorios; rechazo explícito en carga. |
| **P0-3** | No existe **tabla experimental unificada** para la sección «comparación de controladores»: baseline, oráculo, `neural`, `neural_position`, por trayectoria y OOD. | Spec § comparativas; ausencia de CSV/manifiesto de corridas pareadas junio 2026. |

### P1 — Debilitan el argumento; corregir antes de tribunal

| ID | Hallazgo | Evidencia |
| --- | --- | --- |
| **P1-1** | OOD neuronal: batería `tools/generate-ood-batery.py` WIP, sin trackear, typo; `data/neural_ood/` ausente; evaluador puede filtrar split `ood` como `train`. | Script en `tools/`; `evaluate_neural_controller.py`. |
| **P1-2** | Sin herramienta batch de bucle cerrado para **`neural` outer-force** (solo `run_neural_scenario.py` por escenario; existe `run_neural_position_dataset.py` para la otra línea). | `tools/`. |
| **P1-3** | **Transferencia cruzada de PID** (experto/ganancias de familia A en trayectoria B) no protocolizada; relevante para comparar «mejor por trayectoria» vs «optimizado para otra». | `dataset_clasico.md`; ausencia de diseño experimental en docs. |
| **P1-4** | `neural_position`: features en inferencia desde **estado verdadero**, no `observation` ruidosa del runner (desalineación train/deploy si el dataset usa observación). | `control/neural.py`, `ml/dataset.py`. |
| **P1-5** | Tests de dinámica (`test_ideal_hover`) no ejercitan hover ENU/FRD real; enmascaran regresiones de signo. | `tests/test_dynamics.py` vs `get_level_quaternion` en otros tests. |
| **P1-6** | Drag lineal duplicado en `rigid_body.py` y `perturbations.py`; import no usado en `runner.py`. | Código citado en auditoría física mayo; persiste. |
| **P1-7** | Resultados OOD legacy (p. ej. GRU lemniscate) con crash y RMSE alto; no sustituyen evaluación outer-force. | `results/neural_ood_lemniscate_neural_gru/metrics.json` (si presente). |

### P2 — Mejoras recomendadas (v1 acotado)

| ID | Hallazgo |
| --- | --- |
| **P2-1** | Filas «Parcial» en `trazabilidad.md` sin plan de cierre documental con fecha/criterio. |
| **P2-2** | `pyproject.toml`: `description = "Add your description here"`. |
| **P2-3** | Métricas `control_effort_*` legacy vs campos con unidad explícita; riesgo de uso indebido en memoria. |
| **P2-4** | Telemetría sin `desired_force_W_N` ni fuerzas de perturbación por muestra (auditoría difícil en bucle cerrado neuronal). |
| **P2-5** | Composite: fin de sub-trayectoria por `duration` sin asentamiento del vehículo; transición desde referencia, no estado. |
| **P2-6** | Plotly sin párrafo de justificación normativa (dependencia adicional). |

---

## 5. Comparación de controladores — marco para la memoria

La memoria debe articular **cuatro referencias** donde el diseño lo permita (spec outer-force), más **dos líneas neuronales** en paralelo:

| Referencia | Rol | Evidencia hoy |
| --- | --- | --- |
| PID baseline por familia | Suelo clásico congelado (`pid_<family>_v1`) | `data/classic_dataset/v1/pids/`, `summary.csv` |
| Oráculo por escenario | Techo de imitación (PID externo elegido en banco outer-force) | Pipeline documentado; **no generado** en `data/` |
| `neural` outer-force | Lazo externo = fuerza ENU; PID interno fijo | Código + tests; **sin checkpoints** vigentes |
| `neural_position` | Lazo externo = multiplicadores de ganancias | Código + tools; **sin** `position_gain_dataset` en `data/` |

**Comparaciones exigidas por el autor (estado documental / experimental):**

| Comparación | Diseño | Evidencia en repo |
| --- | --- | --- |
| Neuronales entre sí (MLP/GRU/LSTM; min vs full features; outer-force vs position) | Spec y `control_neuronal.md` | Sin corridas bajo contrato 3-salidas |
| Neuronal vs clásico **por trayectoria** | Mismas métricas en `metrics/report.py` | Clásico: 150 episodios; neuronal: CSV/resultados legacy limitados |
| vs **mejor/oráculo por trayectoria** | Selección RMSE en `generate_outer_force_dataset.py` | Tests de integración; sin manifest outer-force |
| vs PID **de otra trayectoria** (transferencia) | No protocolizado | Cambio manual YAML posible; sin matriz experimental |

**Regla metodológica para tribunal:** no presentar el split `test` del dataset clásico como generalización fuerte; usar OOD declarado (`neural_ood_*`, `composite_ood`, batería generada) y documentar semillas y commit en `metrics.metadata`.

---

## 6. Mapa de evidencias a regenerar antes de la memoria

Orden recomendado (solo documentación de comandos; ejecución fuera de esta auditoría):

### Fase 1 — Datos y oráculo

1. `uv run python tools/generate_outer_force_pid_bank.py --dataset data/classic_dataset/v1 --out data/outer_force_pid_bank/v1`
2. `uv run python tools/generate_outer_force_dataset.py --source-dataset data/classic_dataset/v1 --pid-bank data/outer_force_pid_bank/v1 --out data/outer_force_dataset/v1`
3. (Línea position) `generate_pid_bank.py` → `generate_position_gain_dataset_from_bank.py` → `run_classic_dataset.py` sobre manifest resultante.

### Fase 2 — Entrenamiento

4. Outer-force: MLP `outer_force_min_v1` (prioritaria) + al menos GRU o LSTM; opcional `outer_force_full_v1` como ablation.
5. Position: entrenar arquitectura elegida (p. ej. GRU) sobre `position_gain_dataset/v1`.
6. Archivar o etiquetar como histórico `data/neural_control/*_v1` (4 salidas).

### Fase 3 — Evaluación

7. Supervisada: `evaluate_neural_controller.py` / `evaluate_neural_position_controller.py` por split.
8. Cerrada in-distribution: batch test (script nuevo o procedimiento documentado para outer-force).
9. OOD: verificar `composite_ood` con estado inicial coincidente con el primer punto de ruta; generar batería (`generate-ood-batery.py` renombrado e integrado); ejecutar 4 controladores × escenarios OOD representativos.

### Fase 4 — Paquete para memoria

10. CSV único `comparison_closed_loop_v1.csv`: `scenario_id`, controlador, `position_rmse_m`, `termination_reason`, saturación, degradación, clipping de fuerza (outer-force).
11. Figuras desde `telemetry.json` versionadas; tabla que cite commit, comando y cumplimiento de `validacion.md`.
12. Subsección en `validacion.md`: «Comparación de controladores» + criterios OOD neuronal.

---

## 7. Delta vs. auditoría multivista (mayo 2026)

| Hallazgo mayo 2026 | Estado junio 2026 |
| --- | --- |
| README raíz vacío | **Cerrado** — `README.md` completo |
| Falta `trazabilidad.md` | **Cerrado** — matriz en `docs/simulador/` |
| Comparativa neuronal inexistente | **Parcial** — implementada en código/docs; falta evidencia regenerada |
| Ganancias PID no en YAML | **Cerrado** |
| Validación física YAML insuficiente | **Mayormente cerrado** — `schema.py` ampliado |
| Metadata sin commit/lock | **Cerrado** en diseño |
| Métricas esfuerzo sin unidades | **Mejorado** — campos N y Nm; persisten alias legacy |
| `docs/preliminar/` sobrerreclama | **Cerrado** — carpeta eliminada |
| ~29 tests, sin neuronal | **Superado** — suite amplia; cifra en reviews **obsoleta** |
| Sin regresiones escenario completo | **Parcial** — `test_model_regressions.py`; sin bandas CI por YAML oficial |
| Auditorías mayo = vigentes | **Cerrado** — `docs/reviews/README.md` prioriza este informe y marca mayo como referencia histórica con errata |

**Regresión nueva respecto a mayo:** riesgo de **confundir** filas «Implementado» en trazabilidad con **artefactos listos** en `data/`; artefactos legacy que contradicen el contrato vigente si no se segregan.

**Ajuste posterior incorporado:** `composite_ood` pasa a iniciar en el primer punto de ruta y queda recogido en `docs/simulador/validacion.md`; ya no se considera hallazgo abierto, solo escenario a verificar cuando se ejecuten evidencias.

---

## 8. Roadmap priorizado (máx. 6 ítems, v1)

1. **Regenerar cadena outer-force completa** y un checkpoint MLP mínimo defendible; excluir conclusiones basadas en `*_v1` de 4 salidas.
2. **Validar `composite_ood.yaml`** (estado inicial igual al primer punto de ruta) dentro de la batería OOD.
3. **Producir matriz comparativa cerrada** (test + OOD): baseline, oráculo, `neural`, `neural_position`, con CSV y metadata de commit.
4. **Actualizar gobernanza documental:** subsección comparación en `validacion.md`, estado de evidencias en README y criterios de cierre en trazabilidad.
5. **Cerrar OOD:** integrar batería de escenarios, corregir split en evaluador, ejecutar las cuatro referencias en al menos 3 escenarios OOD.
6. **Reforzar pruebas físicas** (`test_ideal_hover` ENU/FRD) y unificar drag; opcional: batch `run_neural_outer_force_dataset.py`.

---

## 9. Respuestas directas para redactar la memoria

| Pregunta | Respuesta breve |
| --- | --- |
| ¿Por qué ENU/FRD? | Convención fijada en requisitos y código; limitaciones v1 (drag lineal, sin aerodinámica formal) en `docs/02` y README. |
| ¿Cómo se compara clásico vs neuronal? | Mismo simulador, mismos escenarios y métricas; dos lazos externos neuronales; oráculo por escenario en outer-force; **falta ejecutar y tabular**. |
| ¿Qué pruebas respaldan cada requisito? | `docs/simulador/trazabilidad.md` + `validacion.md` § tests. |
| ¿Qué regenerar? | Sección 6 de este informe. |
| ¿Qué riesgos declarar? | Artefactos legacy, OOD parcial y posible leakage observation/state en `neural_position`. |

---

## 10. Uso de este informe

- **Diagnóstico vigente (junio 2026):** este documento sustituye a la síntesis multivista de mayo para decisiones de memoria, sin borrar historiales.
- **Auditorías por área (mayo):** conservar como historial; contrastar siempre con `docs/simulador/` y este informe.
- **Próximo paso opcional:** fase de verificación con `uv run pytest` y smoke de 2–3 escenarios para validar hallazgos P0 físicos (fuera del alcance acordado de esta auditoría).

---

*Informe generado por análisis integral en cuatro ejes (científico, simulador, neuronal, documentación). Restricción: sin ejecución experimental.*
