# Auditoria de documentacion frente a la implementacion

**Fecha de corte:** 2026-06-18
**Alcance:** documentacion tecnica viva, contratos publicos del codigo, CLI,
configuracion YAML y evidencia versionada.
**Exclusiones:** `docs/plans/archived/`, auditorias historicas y `docs/html/` no
se modificaron ni se usaron como fuente de verdad.

## Resultado

La documentacion viva queda contrastada con `pyproject.toml`, `src/`, `tools/`,
`scenarios/`, `tests/`, las ayudas ejecutables y los CSV admitidos por
`results/.gitignore`. No se modificaron la dinamica ni los controladores; el
unico cambio ejecutable retira dos campos YAML ignorados y los rechaza al validar.

La auditoria corrigio cuatro clases de desajuste:

1. limites YAML retirados porque no se aplicaban por la CLI;
2. recuentos experimentales presentados sin identificar su snapshot;
3. referencias a planes vigentes que no existen fuera de `plans/archived/`;
4. descripciones imprecisas de la transferencia PID y del alcance de protecciones
   neuronales.

## Evidencia ejecutada

| Comprobacion | Resultado |
| --- | --- |
| `uv run pytest -q` | `215 passed in 105.73s` (verificacion final) |
| `uv run pytest --collect-only -q` | 215 pruebas recolectadas |
| `uv run simulador-quad --help` y subordenes | `run`, `plot` y `plot-comparison` disponibles |
| `uv run python tools/<script>.py --help` | Los 21 scripts cargan y terminan con codigo 0 |
| Carga de `scenarios/*.yaml` | Los 9 escenarios versionados validan y cargan |
| Inspeccion de CSV con `uv run python` | Conteos y columnas indicados en la seccion siguiente |

No se ejecutaron campanas, entrenamientos ni escenarios para producir resultados
nuevos. Los valores de RMSE locales no se usan como evidencia de esta auditoria.

## Evidencia experimental versionada

`results/evidence_manifest.csv`, `comparison_all_runs.csv`,
`comparison_all_runs_full.csv` y `comparison_summary.csv` fueron incorporados en
el commit `fe2e075` el 2026-06-10. El snapshot contiene:

- 264 corridas comparables: 184 `test` y 80 `ood`;
- 518 filas completas: 210 `train`, 44 `val`, 184 `test` y 80 `ood`;
- 64 agregados en `comparison_summary.csv`;
- una matriz de transferencia clasica declarada por el manifiesto de 92 corridas
  `test` y 40 OOD.

Los conteos 92/40 describen solo la matriz de transferencia; no son el total de
la comparacion consolidada. Los CSV no incluyen checkpoints ni telemetria pesada.
Su regeneracion debe actualizar fecha, procedencia y conteos.

## Hallazgos y correcciones

### A-01. Limites de terminacion retirados del YAML

`termination.max_position_m` y `termination.max_speed_m_s` se validaban pero
`app.run_simulation` no los transferia a `SimulationRunner`. Se retiraron del
contrato YAML y el esquema ahora los rechaza explicitamente. El runner conserva
sus limites internos de 100 m y 50 m/s por componente.

### A-02. Recuentos experimentales ambiguos

`README.md` presentaba 92 corridas `test` y 40 OOD como si fueran toda la
comparacion. Se identificaron como matriz de transferencia y se añadieron los
conteos fechados de los CSV versionados. `docs/simulador/README.md` y
`validacion.md` reflejan el mismo snapshot.

### A-03. Planes archivados citados como especificacion vigente

`docs/plans/` no contiene documentos vigentes; solo existe el contenido
historico bajo `docs/plans/archived/`. Se retiraron del README y de la guia del
dataset las referencias a planes actuales como fuente de parametros.

### A-04. Transferencia PID descrita de forma incompleta

La transferencia excluye por defecto el PID nativo, pero `--include-native` lo
incluye y la fase 11 usa esa opcion. `guia_uso.md` ahora distingue ambos casos.

### A-05. Comentarios que excedian el alcance implementado

Un docstring de `NeuralOuterForceController` justificaba el limite vertical por
seguridad del vehiculo real. El repositorio no implementa vuelo real. El texto
se limito al efecto verificable en el convertidor de actitud del simulador. Los
comentarios de exportacion de clipping en `app.py` tambien se desligaron de un
plan historico.

### A-06. Ayuda CLI imprecisa para entrenamiento

`train_neural_controller.py --dataset` decia siempre "classic dataset". El
script acepta el dataset compatible con la version de features seleccionada;
la ayuda publica ahora exige raiz con `manifest.csv` y telemetria compatible.

### A-07. Recuento obsoleto de figuras base

`plot_telemetry` genera ocho figuras base, incluida `trajectory_3d_static`, y
hasta dos figuras condicionales. Se sincronizaron `docs/simulador/README.md`,
`validacion.md` y `mantenimiento.md`.

### A-08. Referencias temporales a especificaciones no vigentes

Se sustituyeron "new contract", "per spec" y "nueva comparacion" por contratos
descriptivos en `schema.py`, `datasets/classic.py` y `control_neuronal.md`.

### A-09. Campo global YAML omitido

Tres escenarios OOD versionados usan `description`. El cargador lo conserva en
la configuracion incluida en metadata, aunque no cambia la simulacion. Se añadio
a `escenarios_yaml.md` como campo global opcional.

## Archivos vivos revisados

| Grupo | Archivos | Clasificacion |
| --- | --- | --- |
| Entrada | `README.md`, `pyproject.toml` | Revisado; README corregido |
| Documentacion viva | Los 9 Markdown de `docs/simulador/` | Revisados; se corrigieron README, arquitectura, escenarios, guia, dataset, validacion y mantenimiento; control neuronal y trazabilidad no requirieron cambios |
| CLI | `src/simulador_quad/app.py`, 21 scripts de `tools/` | Ayudas verificadas; dos textos publicos corregidos |
| YAML | `scenarios/*.yaml`, `scenarios/loader.py`, `scenarios/schema.py` | 9 escenarios cargados; desacoplamiento documentado |
| Contratos | `core/contracts.py`, `control/`, `runner.py`, `telemetry/`, `metrics/` | Revisados; un docstring y comentarios corregidos |
| Datos y ML | `datasets/`, `ml/` y herramientas asociadas | Revisados frente a datasets, features, targets, normalizacion y entrenamiento |
| Pruebas | `tests/` | 215 pruebas pasan en el snapshot fechado |
| Evidencia | Cuatro CSV versionados en `results/` | Revisados por columnas, splits y conteos |
| Memoria | `TFG_Memoria/` | Revisada por afirmaciones tecnicas relevantes; no se alteraron resultados ni narrativa experimental |

Los cambios preexistentes encontrados en `TFG_Memoria/` y en las dos notas de
limites YAML se conservaron y se revisaron en vez de revertirse.

## Contratos confirmados

- Marcos: mundo ENU y cuerpo FRD; cuaternion `[w, x, y, z]`.
- CLI principal: `run`, `plot` y `plot-comparison`.
- Controladores YAML: `classic`, `neural` outer-force y `neural_position`.
- Trayectorias: `hold`, `circle`, `lissajous`, `line`/`waypoint`, `lemniscate`
  y `composite`.
- Telemetria: estado, observacion, referencia, control, comando/aplicacion de
  rotores, viento, causa de terminacion y fuerzas neuronales opcionales.
- Metricas comunes: errores de posicion, magnitudes de control, velocidades de
  rotor, saturacion, degradacion, terminacion, duracion y metadata.
- Outer-force: 9 o 31 features desde `observation`, target de fuerza ENU de tres
  componentes y normalizacion ajustada solo con `train`.
- Dataset clasico `v1`: generador determinista de 150 episodios, con recuentos
  verificados por las pruebas del generador, no por datos locales ignorados.
- Campana: 11 fases; las fases aisladas no resuelven dependencias previas.

## Pendientes e incertidumbres

- **Pendiente de evidencia:** checkpoints, telemetria y datasets de `data/` no
  estan versionados; el manifiesto aporta trazabilidad declarativa, pero esta
  auditoria no pudo recomputar los CSV desde esos artefactos.
- **Pendiente de evidencia:** no se verifico entrenamiento CUDA ni competencia
  de varios workers sobre una GPU.
- **Pendiente experimental:** `neural_position` tiene pipeline y pruebas, pero
  `evidence_manifest.csv` declara cero corridas consolidadas.
- **Pendiente experimental:** cualquier cifra que se regenere despues del
  snapshot del 2026-06-10 debe actualizar documentos, manifiesto y tablas.

## Cierre

La comprobacion automatica y el contraste estatico cubren los contratos
documentados. La trazabilidad experimental completa sigue dependiendo de
conservar o regenerar los artefactos pesados indicados en el manifiesto; por eso
no se eleva esa evidencia declarativa a verificacion experimental independiente.
