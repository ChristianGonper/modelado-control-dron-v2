# Plan de implementacion: tuneo PID base y pipeline experimental

## Objetivo del plan

Implementar el flujo definido en
`docs/plans/spec_tuneo_pid_base_pipeline.md` sin cambiar los filtros duros,
las convenciones ENU/FRD ni la separacion entre `train`, `val`, `test` y OOD.

El resultado debe permitir ejecutar la campaña desde un repositorio sin
resultados, diagnosticar los PIDs iniciales, tunear solamente las familias que
lo necesiten, congelar los PIDs elegidos y generar datasets neuronales
coherentes con esos PIDs.

## Decisiones tecnicas

### Busqueda de candidatos

Se implementara una busqueda progresiva determinista sin dependencias nuevas:

1. Candidato inicial con multiplicadores `[1, 1, 1, 1]`.
2. Primera ronda de 32 candidatos generados mediante muestreo log-uniforme
   estratificado con semilla fija.
3. Seleccion de los mejores candidatos validos.
4. Refinamiento de 16 candidatos alrededor de los mejores multiplicadores.
5. Seleccion final por score agregado, esfuerzo y cercania al PID inicial.

Los cuatro multiplicadores corresponden a:

- `Kp_pos`
- `Kd_pos`
- `Kp_att`
- `Kd_att`

### Conjunto de diagnostico

El conjunto se derivara del manifiesto clasico y solo usara filas `train`.
Para cada familia se seleccionaran deterministicamente:

- Una geometria representativa lenta.
- Una geometria exigente.
- Los perfiles disponibles de `P0_nominal`, `P2_wind_east` y `P5_combined`.

La seleccion concreta quedara escrita en el reporte de diagnostico.

### Artefactos

El tuneo escribira:

```text
data/classic_dataset/v1/pids/pid_<family>_v1.yaml
data/classic_dataset/v1/pid_tuning/diagnostic_report.csv
data/classic_dataset/v1/pid_tuning/candidates_<family>.csv
data/classic_dataset/v1/pid_tuning/summary.json
```

El YAML final indicara si el PID inicial fue aceptado o si fue tuneado.

## Orden de implementacion

### Fase A: contratos y utilidades de tuneo

- Extraer funciones reutilizables para:
  - Construir el conjunto de diagnostico.
  - Ejecutar un PID sobre varios escenarios.
  - Agregar metricas y comprobar criterios.
  - Generar candidatos deterministas.
  - Seleccionar el PID final.
- Mantener `passes_hard_filters` y `pid_candidate_score` como fuentes de verdad.
- No escribir artefactos hasta completar correctamente la evaluacion.

Verificacion:

```powershell
uv run pytest -q tests\test_classic_pid_tuning.py
```

### Fase B: CLI de diagnostico y tuneo

- Reemplazar la CLI actual de `tools/tune_classic_pid.py` por una CLI orientada
  al dataset completo.
- Soportar:
  - `--dataset`
  - `--out`
  - `--family`
  - `--force`
  - `--seed`
  - `--initial-candidates`
  - `--refinement-candidates`
  - umbrales RMSE configurables por familia
- Diagnosticar todas las familias por defecto.
- Tunear solo las familias que lo necesiten.
- Devolver codigo distinto de cero si ninguna configuracion segura puede
  seleccionarse.

Verificacion:

```powershell
uv run python tools\tune_classic_pid.py --help
uv run pytest -q tests\test_classic_pid_tuning.py tests\test_classic_pid_selection.py
```

### Fase C: congelacion y regeneracion del dataset clasico

- Asegurar que regenerar escenarios clasicos reutiliza los YAML de PID tuneados
  existentes en lugar de sustituirlos por defaults.
- Separar claramente:
  1. Generacion inicial.
  2. Tuneo y congelacion.
  3. Regeneracion de escenarios con PIDs congelados.
  4. Ejecucion completa del baseline.
- Validar que todos los escenarios de una familia contienen exactamente el PID
  congelado de esa familia.

Verificacion:

```powershell
uv run pytest -q tests\test_classic_dataset_generation.py tests\test_classic_dataset_scripts.py
```

### Fase D: correccion de los bancos neuronales

#### Banco `neural_position`

- Modificar `tools/generate_pid_bank.py` para variar exclusivamente `Kp_pos` y
  `Kd_pos`.
- Mantener `Kp_att`, `Kd_att` y limites internos iguales al PID base.
- Añadir variantes amortiguadas suficientes para cubrir situaciones exigentes.
- Registrar multiplicadores y PID base de origen.

#### Banco outer-force

- Ampliar variantes externas incluyendo alternativas amortiguadas.
- Mantener fijo el PID interno.
- Validar que cada escenario obtiene al menos un candidato seguro.
- Si no existe candidato seguro, abortar con un reporte completo de candidatos
  y motivos, sin dejar un dataset parcial aparentemente valido.

Verificacion:

```powershell
uv run pytest -q tests\test_outer_force_generation_integration.py tests\test_neural_position_control.py
```

### Fase E: integracion en el orquestador

- Reorganizar las primeras fases de la campaña:
  1. Sanidad.
  2. Generacion inicial clasica.
  3. Diagnostico/tuneo PID base.
  4. Regeneracion y ejecucion baseline clasico.
  5. Generacion de datasets neuronales.
- Ajustar la numeracion o documentar claramente la nueva numeracion.
- Añadir validaciones de prerequisitos antes de cada fase.
- Permitir configurar umbrales y presupuesto desde el orquestador.
- Mantener propagacion de fallos y soporte `--rerun`.

Verificacion:

```powershell
uv run python tools\run_experimental_campaign.py --dry-run
uv run pytest -q tests\test_campaign_scripts.py
```

### Fase F: documentacion reproducible

- Actualizar:
  - `README.md`
  - `docs/simulador/guia_uso.md`
  - Documentacion viva afectada en `docs/simulador/`
- Explicar el flujo desde un repositorio sin resultados.
- Diferenciar:
  - PID inicial.
  - PID base tuneado y congelado.
  - Banco `neural_position`.
  - Oraculo outer-force por escenario.
- Documentar umbrales por defecto, forma de modificarlos y efecto experimental.
- Dejar claro que cambiar umbrales o presupuesto produce una campaña distinta.

Verificacion:

```powershell
git diff --check
```

### Fase G: verificacion integral

- Ejecutar pruebas enfocadas.
- Ejecutar suite completa.
- Ejecutar una campaña reducida o fixtures equivalentes que cubran:
  - PID inicial aceptado.
  - Familia retuneada.
  - Congelacion y regeneracion.
  - Generacion de ambos bancos.
  - Aborto limpio ante ausencia de experto seguro.
- Revisar artefactos generados y trazabilidad.

Verificacion:

```powershell
uv run pytest -q
git diff --check
```

## Tareas implementables

- [ ] Tarea 1: añadir pruebas del criterio de diagnostico y activacion de tuneo.
  - Aceptacion: una familia se retunea por RMSE o por cualquier fallo duro.
  - Verificar: `uv run pytest -q tests\test_classic_pid_tuning.py`
  - Archivos: `tests/test_classic_pid_tuning.py`

- [ ] Tarea 2: implementar generacion reproducible y seleccion de candidatos.
  - Aceptacion: misma semilla produce mismos candidatos y seleccion.
  - Verificar: pruebas unitarias del buscador.
  - Archivos: `tools/tune_classic_pid.py`, `tests/test_classic_pid_tuning.py`

- [ ] Tarea 3: implementar evaluacion agregada y escritura atomica de artefactos.
  - Aceptacion: no quedan PIDs finales parciales ante fallo.
  - Verificar: pruebas de fallo y artefactos.
  - Archivos: `tools/tune_classic_pid.py`, `tests/test_classic_pid_tuning.py`

- [ ] Tarea 4: preservar PIDs congelados al regenerar dataset clasico.
  - Aceptacion: escenarios regenerados usan exactamente el YAML tuneado.
  - Verificar: pruebas de generacion clasica.
  - Archivos: `src/simulador_quad/datasets/classic.py`, pruebas asociadas.

- [ ] Tarea 5: corregir banco `neural_position`.
  - Aceptacion: ninguna variante modifica ganancias internas.
  - Verificar: pruebas del banco y dataset position-gain.
  - Archivos: `tools/generate_pid_bank.py`, pruebas asociadas.

- [ ] Tarea 6: ampliar y robustecer banco outer-force.
  - Aceptacion: los escenarios bloqueantes obtienen candidato seguro y los
    fallos generan reporte completo.
  - Verificar: integración outer-force.
  - Archivos: `tools/generate_outer_force_pid_bank.py`,
    `tools/generate_outer_force_dataset.py`, pruebas asociadas.

- [ ] Tarea 7: integrar tuneo y prerequisitos en el orquestador.
  - Aceptacion: campaña desde cero ejecuta el orden correcto y una fase aislada
    falla temprano con mensaje accionable si faltan artefactos.
  - Verificar: `tests/test_campaign_scripts.py`.
  - Archivos: `tools/run_experimental_campaign.py`,
    `tests/test_campaign_scripts.py`.

- [ ] Tarea 8: actualizar documentacion viva.
  - Aceptacion: existe un procedimiento completo desde clon limpio hasta tablas
    finales.
  - Verificar: revision documental y `git diff --check`.
  - Archivos: `README.md`, `docs/simulador/guia_uso.md` y documentos afectados.

- [ ] Tarea 9: ejecutar verificacion integral y revisar resultados.
  - Aceptacion: suite completa pasa y los artefactos muestran trazabilidad.
  - Verificar: `uv run pytest -q` y `git diff --check`.

## Riesgos y mitigaciones

### Coste computacional

El tuneo puede requerir hasta 48 candidatos por familia multiplicados por los
casos de diagnostico. Se limita el conjunto de diagnostico y se evita ejecutar
tuneo cuando el PID inicial ya cumple.

### Sobreajuste al diagnostico

Se usan varias geometrías y perturbaciones de `train`, manteniendo `test` y OOD
fuera. La evaluacion final sigue realizandose sobre conjuntos separados.

### Cambios silenciosos de condicion experimental

Todos los umbrales, semillas, presupuestos y escenarios deben persistirse en
los artefactos de tuneo.

### Dataset parcial

Los generadores deben escribir manifiestos finales solo tras completar y
validar todos los escenarios, o escribir explicitamente un reporte de fallo.

## Punto de control antes de implementar

La implementacion comenzara por las pruebas y el motor de diagnostico/tuneo.
No se modificaran los resultados existentes ni se ejecutara la campaña pesada
completa hasta que las pruebas de seleccion y congelacion sean correctas.
