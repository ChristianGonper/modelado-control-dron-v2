# Apéndice de hallazgos — Contrato SPEC §14

**Fecha:** 2026-06-10  
**Registro maestro:** `auditoria_integral_tfg_2026-06-10_hallazgos.csv`

---

## F-001

```text
ID: F-001
Titulo: Evidencia experimental local ignorada por Git
Severidad: P1
Dominio propietario: A01
Tipo: evidencia
Estado historico: persiste
Fuente normativa: docs/03_criterios_ingenieria_software.md (reproducibilidad); AGENTS.md
Causa raiz: Politica .gitignore con comodín (*) en data/ y results/ sin manifiesto versionado sustituto
Impacto tecnico: Artefactos experimentales no transferibles con el repositorio
Impacto academico: Terceros no pueden verificar resultados citados sin copia manual del autor
Evidencia primaria: data/.gitignore:1; results/.gitignore:1
Contraevidencia revisada: README.md:25-26 documenta que data/ está ignorado y describe regeneración
Confianza: alta
Decision propuesta: Publicar manifiesto versionado de evidencia de memoria (hashes, commit, comandos)
Remediacion minima: Crear data/manifest_evidencia_memoria.json versionado o política formal tutor
Archivos probablemente afectados: data/.gitignore; results/.gitignore; README.md; docs/simulador/validacion.md
Dependencias: BL-01
Criterio verificable de cierre: Manifiesto versionado referenciado en memoria y coherente con artefactos locales inspeccionados
```

## F-002

```text
ID: F-002
Titulo: Matriz comparativa de controladores incompleta
Severidad: P1
Dominio propietario: A10
Tipo: evidencia
Estado historico: nuevo
Fuente normativa: docs/01_principios_tfg.md; docs/simulador/validacion.md:56-60
Causa raiz: Campaña experimental ejecutada parcialmente; consolidación incompleta
Impacto tecnico: CSV agregados no cubren diseño experimental documentado
Impacto academico: No se puede defender comparación baseline/oráculo/neural/neural_position/transfer
Evidencia primaria: results/comparison_all_runs.csv (controladores: classic_family_pid, neural_outer_force_mlp/gru/lstm); ausencia results/comparison_closed_loop_v1.csv; tools/summarize_comparison.py:99-126
Contraevidencia revisada: summarize_comparison.py implementa oracle, transfer y position; outer-force sí en CSV
Confianza: alta
Decision propuesta: Completar fases 9-11 campaña y regenerar tablas
Remediacion minima: BL-02a summarize completo + BL-02b build_comparison_closed_loop
Archivos probablemente afectados: results/comparison_*.csv; tools/summarize_comparison.py
Dependencias: BL-02a; BL-02b; BL-04; BL-05
Criterio verificable de cierre: comparison_all_runs.csv incluye outer_force_oracle, classic_transfer_*, neural_position_* y existe comparison_closed_loop_v1.csv
```

## F-003

```text
ID: F-003
Titulo: Metadata de reproducibilidad desalineada con HEAD
Severidad: P1
Dominio propietario: A01
Tipo: evidencia
Estado historico: nuevo
Fuente normativa: docs/03_criterios_ingenieria_software.md; docs/simulador/trazabilidad.md:36
Causa raiz: Corridas generadas con working tree sucio y commit anterior al HEAD auditado
Impacto tecnico: metrics.json no fingerprint del código actual
Impacto academico: Afirmación de reproducibilidad desde 560c5a8 es falsa para evidencia almacenada
Evidencia primaria: data/classic_dataset/v1/results/hold/hold_g01_P0_nominal_s1042/metrics.json:428-429; git rev-parse HEAD → 560c5a879fbc7cf307607d8a4721624a999638a3
Contraevidencia revisada: src/simulador_quad/app.py:53-54 implementa git_commit y git_dirty correctamente
Confianza: alta
Decision propuesta: Re-ejecutar corridas citadas con árbol limpio y fijar HEAD en memoria
Remediacion minima: Campaña --rerun tras commit limpio (BL-03)
Archivos probablemente afectados: data/**/metrics.json; TFG_Memoria/sections/07_resultados.tex
Dependencias: BL-03; BL-06
Criterio verificable de cierre: Muestra representativa de metrics.json con git_commit==HEAD y git_dirty==false
```

## F-004

```text
ID: F-004
Titulo: Pipeline neural_position sin artefactos locales
Severidad: P1
Dominio propietario: A09
Tipo: evidencia
Estado historico: persiste
Fuente normativa: docs/simulador/control_neuronal.md; README.md:79-88
Causa raiz: Fases 6-9 de campaña no ejecutadas para línea position
Impacto tecnico: Segunda hipótesis de lazo externo sin dataset ni checkpoints
Impacto academico: Comparación dual neuronal incompleta en memoria
Evidencia primaria: ausencia data/position_gain_dataset/; ausencia data/neural_control/position_*; tools/summarize_comparison.py:30
Contraevidencia revisada: tests/test_neural_position_control.py (7 tests); control/neural.py:202-239 operativo
Confianza: alta
Decision propuesta: Ejecutar generate_position_gain_* → train → run_neural_position_dataset
Remediacion minima: BL-04 fase 6-9 campaña
Archivos probablemente afectados: data/position_gain_dataset/; data/neural_control/position_*
Dependencias: BL-04; BL-07
Criterio verificable de cierre: manifest position_gain_dataset/v1 y checkpoints position_* con run_report_neural_position_*.csv
```

## F-005

```text
ID: F-005
Titulo: Transferencia cruzada de PID no materializada
Severidad: P1
Dominio propietario: A07
Tipo: evidencia
Estado historico: nuevo
Fuente normativa: docs/simulador/dataset_clasico.md; README.md:109-110
Causa raiz: Fase 11 campaña (run_classic_transfer_dataset) no ejecutada
Impacto tecnico: Sin métricas PID familia A en trayectoria B
Impacto academico: Hipótesis transferencia no cuantificada
Evidencia primaria: ausencia data/classic_dataset/v1/results_transfer/; tools/summarize_comparison.py:72-73
Contraevidencia revisada: tools/run_classic_transfer_dataset.py existe; tests/test_campaign_scripts.py valida flujo
Confianza: alta
Decision propuesta: Ejecutar run_classic_transfer_dataset.py e integrar en summarize
Remediacion minima: BL-05
Archivos probablemente afectados: data/classic_dataset/v1/results_transfer/; results/comparison_all_runs.csv
Dependencias: BL-05; BL-02b
Criterio verificable de cierre: results_transfer/ poblado y filas classic_transfer_* en comparison_all_runs.csv
```

## F-006

```text
ID: F-006
Titulo: test_ideal_hover no ejercita convención ENU/FRD nivel
Severidad: P2
Dominio propietario: A03
Tipo: prueba
Estado historico: persiste
Fuente normativa: docs/02_requisitos_ingenieria_simulador.md; docs/simulador/trazabilidad.md:15
Causa raiz: Test histórico usa cuaternión identidad en lugar de get_level_quaternion
Impacto tecnico: Cobertura redundante/confusa en suite dinámica
Impacto academico: Menor confianza en detección de regresiones de signo
Evidencia primaria: tests/test_dynamics.py:59
Contraevidencia revisada: tests/test_dynamics.py:27-48 test_hover_level_frd_thrust_sign
Confianza: alta
Decision propuesta: Unificar criterio hover FRD en un test canónico
Remediacion minima: BL-08
Archivos probablemente afectados: tests/test_dynamics.py
Dependencias: BL-08
Criterio verificable de cierre: test_ideal_hover usa get_level_quaternion o se elimina duplicando cobertura
```

## F-007

```text
ID: F-007
Titulo: Ausencia de estudio sensibilidad a physics_dt_s
Severidad: P2
Dominio propietario: A03
Tipo: fisica
Estado historico: persiste
Fuente normativa: docs/02_requisitos_ingenieria_simulador.md; SPEC.md §11.1
Causa raiz: No hay tests ni documentación de convergencia temporal
Impacto tecnico: Error de discretización no acotado experimentalmente
Impacto academico: Claims de precisión numérica requieren reservas
Evidencia primaria: ausencia casos dt/dt2/dt4 en tests/
Contraevidencia revisada: RK4 y multi-rate verificados en tests/test_runner.py
Confianza: media
Decision propuesta: Añadir test convergencia en caso analítico
Remediacion minima: BL-09
Archivos probablemente afectados: tests/test_dynamics.py
Dependencias: BL-09
Criterio verificable de cierre: Test compara estados finales dt vs dt/2 vs dt/4 bajo tolerancia declarada
```

## F-008

```text
ID: F-008
Titulo: Descripción plantilla en pyproject.toml
Severidad: P2
Dominio propietario: A01
Tipo: documentacion
Estado historico: persiste
Fuente normativa: docs/03_criterios_ingenieria_software.md
Causa raiz: Plantilla uv sin personalizar
Impacto tecnico: Metadatos paquete incompletos
Impacto academico: Percepción de rigor software menor
Evidencia primaria: pyproject.toml:4
Contraevidencia revisada: README.md describe el proyecto correctamente
Confianza: alta
Decision propuesta: Actualizar description
Remediacion minima: BL-10
Archivos probablemente afectados: pyproject.toml
Dependencias: BL-10
Criterio verificable de cierre: description != "Add your description here"
```

## F-009

```text
ID: F-009
Titulo: TFG_Memoria referencia plan archivado como fuente de verdad
Severidad: P2
Dominio propietario: A14
Tipo: narrativa
Estado historico: persiste
Fuente normativa: TFG_Memoria/AGENTS.md; docs/plans/archived/README.md:5
Causa raiz: AGENTS memoria no actualizado tras archivado de planes
Impacto tecnico: Redactores siguen ruta no vigente
Impacto academico: Metodología memoria desalineada con docs/simulador/
Evidencia primaria: TFG_Memoria/AGENTS.md:14
Contraevidencia revisada: Plan existe en archived/plan_experimental_y_memoria_tfg_2026-06.md como histórico
Confianza: alta
Decision propuesta: Actualizar fuentes de verdad en AGENTS memoria
Remediacion minima: BL-11
Archivos probablemente afectados: TFG_Memoria/AGENTS.md
Dependencias: BL-11
Criterio verificable de cierre: AGENTS.md lista docs/simulador/ y README sin plan solo-en-archived como vigente
```

## F-010

```text
ID: F-010
Titulo: README afirma planes activos bajo docs/plans/ inexistentes
Severidad: P2
Dominio propietario: A13
Tipo: documentacion
Estado historico: nuevo
Fuente normativa: README.md; docs/plans/archived/README.md:5
Causa raiz: README no actualizado tras mover specs a archived/
Impacto tecnico: Ruta docs/plans/ vacía de specs vigentes
Impacto academico: Confusión gobernanza documental
Evidencia primaria: README.md:141; listado solo docs/plans/archived/*
Contraevidencia revisada: docs/simulador/ contiene especificación operativa
Confianza: alta
Decision propuesta: Corregir sección planes en README
Remediacion minima: BL-12
Archivos probablemente afectados: README.md
Dependencias: BL-12
Criterio verificable de cierre: README distingue archived vs documentación viva sin afirmar specs activas en docs/plans/ raíz
```

## F-011

```text
ID: F-011
Titulo: Métricas control_effort_heuristic y alias sin deprecación fuerte
Severidad: P2
Dominio propietario: A06
Tipo: contrato
Estado historico: persiste
Fuente normativa: docs/simulador/guia_uso.md:163-164
Causa raiz: Compatibilidad legacy en export JSON
Impacto tecnico: Mezcla N y Nm en campos exportados
Impacto academico: Riesgo uso indebido en tablas
Evidencia primaria: src/simulador_quad/metrics/report.py:66-71
Contraevidencia revisada: guia_uso.md advierte no usar como métrica física principal
Confianza: alta
Decision propuesta: Marcar deprecated o reforzar guía memoria
Remediacion minima: BL-13
Archivos probablemente afectados: metrics/report.py; guia_uso.md
Dependencias: BL-13
Criterio verificable de cierre: Memoria usa solo métricas con unidades N/Nm explícitas
```

## F-012

```text
ID: F-012
Titulo: Entrenamiento neuronal con semilla única por defecto
Severidad: P2
Dominio propietario: A08
Tipo: evidencia
Estado historico: persiste
Fuente normativa: docs/03_criterios_ingenieria_software.md
Causa raiz: Default seed=42 sin repetición documentada
Impacto tecnico: Una sola realización por arquitectura
Impacto academico: Incertidumbre de selección no cuantificada
Evidencia primaria: tools/train_neural_controller.py:29; data/neural_control/outer_force_mlp_min_v1/config.yaml:13
Contraevidencia revisada: seed registrado; reproducible dentro de una semilla
Confianza: media
Decision propuesta: Documentar limitación o ejecutar ≥2 semillas
Remediacion minima: BL-14
Archivos probablemente afectados: tools/train_neural_controller.py; memoria
Dependencias: BL-14
Criterio verificable de cierre: Memoria declara semillas y criterio de selección
```

## F-013

```text
ID: F-013
Titulo: Filas Parcial en trazabilidad sin plan de cierre fechado
Severidad: P2
Dominio propietario: A13
Tipo: documentacion
Estado historico: persiste
Fuente normativa: docs/simulador/trazabilidad.md:54-62
Causa raiz: Matriz sin gestión de deuda por fila Parcial
Impacto tecnico: Incertidumbre sobre requisitos «casi completos»
Impacto academico: Auditoría requisito-prueba incompleta
Evidencia primaria: docs/simulador/trazabilidad.md:20; :23; :26; :27
Contraevidencia revisada: Implementación existe para filas Parcial
Confianza: media
Decision propuesta: Tabla cierre con criterio/fecha
Remediacion minima: BL-15
Archivos probablemente afectados: docs/simulador/trazabilidad.md
Dependencias: BL-15
Criterio verificable de cierre: Cada fila Parcial tiene criterio verificable y fecha objetivo
```

## F-014

```text
ID: F-014
Titulo: rmse_std en tablas LaTeX no es incertidumbre experimental
Severidad: P2
Dominio propietario: A10
Tipo: documentacion
Estado historico: nuevo
Fuente normativa: SPEC.md §11.2 (interpretación estadística)
Causa raiz: Agregación pandas std entre escenarios formateada como ±
Impacto tecnico: Salida LaTeX potencialmente engañosa
Impacto academico: Sobreinterpretación estadística en memoria
Evidencia primaria: tools/summarize_comparison.py:342; :376
Contraevidencia revisada: Agregación útil para exploración interna
Confianza: alta
Decision propuesta: Etiquetar dispersión entre escenarios
Remediacion minima: BL-16
Archivos probablemente afectados: tools/summarize_comparison.py; memoria tablas
Dependencias: BL-16
Criterio verificable de cierre: Tablas LaTeX sin notación ± como IC sin repetición por semilla
```

## F-015

```text
ID: F-015
Titulo: Auditoría junio 2026 con hallazgos P0 obsoletos respecto a evidencia local
Severidad: P2
Dominio propietario: A13
Tipo: documentacion
Estado historico: persiste
Fuente normativa: docs/reviews/README.md
Causa raiz: Informe 2026-06-02 generado sin inspeccionar evidencia local regenerada
Impacto tecnico: Diagnóstico histórico contradice estado tardío junio
Impacto academico: Decisiones basadas en P0 ya cerrados localmente
Evidencia primaria: docs/reviews/auditoria_integral_tfg_2026-06.md:47-53; data/outer_force_dataset/v1 presente localmente
Contraevidencia revisada: README.md:20-26 matiza evidencia pendiente
Confianza: alta
Decision propuesta: Priorizar informe 2026-06-10 y errata en README reviews
Remediacion minima: BL-17
Archivos probablemente afectados: docs/reviews/README.md; auditoria_integral_tfg_2026-06.md (banner)
Dependencias: BL-17
Criterio verificable de cierre: README reviews cita 2026-06-10 como vigente con delta explícito vs jun-02
```

## F-016

```text
ID: F-016
Titulo: Auditorías mayo sin etiquetado histórico individual uniforme
Severidad: P2
Dominio propietario: A13
Tipo: documentacion
Estado historico: persiste
Fuente normativa: SPEC.md §12.1
Causa raiz: Índice README etiqueta pero ficheros individuales no
Impacto tecnico: Apertura aislada de auditoria_*.md mayo parece vigente
Impacto academico: Aplicación de findings ya cerrados
Evidencia primaria: docs/reviews/auditoria_fisica_modelado_6dof.md:1 (sin banner); docs/reviews/README.md:9-18 (sí contextualiza)
Contraevidencia revisada: README mitiga al listar como referencia histórica
Confianza: media
Decision propuesta: Banner histórico en cabecera de cada review mayo
Remediacion minima: BL-18
Archivos probablemente afectados: docs/reviews/auditoria_*.md (mayo)
Dependencias: BL-18
Criterio verificable de cierre: Cada fichero mayo tiene banner fecha y enlace a diagnóstico vigente
```

## F-017

```text
ID: F-017
Titulo: Escenarios manuales con límites de actitud excesivamente permisivos
Severidad: P2
Dominio propietario: A05
Tipo: contrato
Estado historico: persiste
Fuente normativa: docs/simulador/validacion.md:64-71
Causa raiz: Escenarios demo con max_attitude_angle_rad ≈ π
Impacto tecnico: Terminación por actitud poco exigente
Impacto academico: Evidencia de estabilidad débil si se citan como oficiales
Evidencia primaria: scenarios/circle_drag.yaml:43; scenarios/circle_noisy_wind.yaml:45
Contraevidencia revisada: hover_clean.yaml:41 usa 1.256 rad coherente con dataset
Confianza: media
Decision propuesta: Etiquetar como demo o endurecer límites en escenarios de memoria
Remediacion minima: BL-19
Archivos probablemente afectados: scenarios/circle_drag.yaml; validacion.md
Dependencias: BL-19
Criterio verificable de cierre: Escenarios citados en memoria cumplen umbrales validacion.md o etiqueta demo
```

## F-018

```text
ID: F-018
Titulo: Plotly sin justificación en documentos normativos
Severidad: P3
Dominio propietario: A13
Tipo: documentacion
Estado historico: persiste
Fuente normativa: docs/03_criterios_ingenieria_software.md
Causa raiz: Dependencia añadida solo en documentación viva
Impacto tecnico: Stack con dependencia no normada
Impacto academico: Justificación de herramientas incompleta
Evidencia primaria: pyproject.toml:14; docs/01_principios_tfg.md (sin plotly); docs/simulador/arquitectura.md:42
Contraevidencia revisada: Visualización aislada en postproceso
Confianza: alta
Decision propuesta: Párrafo justificación en arquitectura o 03_criterios
Remediacion minima: BL-20
Archivos probablemente afectados: docs/03_criterios_ingenieria_software.md o arquitectura.md
Dependencias: BL-20
Criterio verificable de cierre: Normativa o arquitectura menciona Plotly como postproceso opcional
```

## F-019

```text
ID: F-019
Titulo: requires-python >=3.13 reduce portabilidad
Severidad: P3
Dominio propietario: A01
Tipo: documentacion
Estado historico: persiste
Fuente normativa: docs/03_criterios_ingenieria_software.md
Causa raiz: Elección uv/Python moderno sin justificación en memoria
Impacto tecnico: uv sync falla en 3.11-3.12
Impacto academico: Fricción reproducibilidad tribunal
Evidencia primaria: pyproject.toml:9
Contraevidencia revisada: uv.lock y entorno auditado funcionan
Confianza: media
Decision propuesta: Documentar requisito mínimo
Remediacion minima: BL-21
Archivos probablemente afectados: pyproject.toml; README.md
Dependencias: BL-21
Criterio verificable de cierre: README y memoria declaran Python mínimo y motivo
```

## F-020

```text
ID: F-020
Titulo: pytest en dependencias principales no dev group
Severidad: P3
Dominio propietario: A01
Tipo: documentacion
Estado historico: persiste
Fuente normativa: docs/03_criterios_ingenieria_software.md
Causa raiz: Plantilla uv con pytest en dependencies
Impacto tecnico: Entorno runtime incluye test runner
Impacto academico: Separación dev/prod imperfecta
Evidencia primaria: pyproject.toml:15
Contraevidencia revisada: No afecta validez científica
Confianza: alta
Decision propuesta: Mover a dependency-group dev
Remediacion minima: BL-22
Archivos probablemente afectados: pyproject.toml
Dependencias: BL-22
Criterio verificable de cierre: pytest en grupo dev documentado
```

## F-021

```text
ID: F-021
Titulo: Transiciones composite basadas en referencia no en estado del vehículo
Severidad: P3
Dominio propietario: A05
Tipo: fisica
Estado historico: persiste
Fuente normativa: docs/simulador/trazabilidad.md:30
Causa raiz: Diseño v1: LineTrajectory entre puntos de referencia al finalizar sub-trayectoria por duration
Impacto tecnico: Transición no exige asentamiento dinámico del vehículo
Impacto academico: OOD composite puede mostrar fallos cerrados; narrativa debe ser cautelosa
Evidencia primaria: src/simulador_quad/trajectories/composite.py:148-174
Contraevidencia revisada: tests/test_composite_trajectory.py valida contrato implementado
Confianza: media
Decision propuesta: Documentar limitación en validacion.md y memoria OOD
Remediacion minima: BL-23
Archivos probablemente afectados: docs/simulador/validacion.md; TFG_Memoria/sections/07_resultados.tex
Dependencias: BL-23
Criterio verificable de cierre: Limitación declarada explícitamente en documentación y memoria
```