# Plan: Implementacion de Codigo para Generacion de Datos Clasicos

## Summary

Implementar la parte de codigo de `spec_generacion_datos_control_clasico.md`: soporte de ganancias explicitas del controlador clasico, generacion determinista de escenarios YAML, ajuste simple de PID por familia, ejecucion del dataset y resumen de resultados.

Queda fuera de este plan la actualizacion general de `README.md` y `docs/simulador/`; esa documentacion se hara al final cuando la interfaz real este cerrada. Tambien queda fuera cualquier red neuronal, loader de ML o entrenamiento.

## Implementation Order

### 1. Soporte de ganancias explicitas en el controlador clasico

Objetivo: permitir que los YAML declaren `Kp_pos`, `Kd_pos`, `Kp_att`, `Kd_att` y `max_body_moments_Nm`.

Cambios:

- Extender `ClassicCascadeController` para aceptar ganancias opcionales en `__init__`.
- Extender `instantiate_scenario` para leer esas ganancias desde `controller`.
- Extender `validate_scenario_config` para validar vectores de ganancias con forma `[3]`, finitos y no negativos.
- Mantener defaults actuales si no se declaran ganancias.
- Mantener `max_body_moments_Nm` como ya existe.

Verificacion:

```powershell
uv run pytest tests\test_control.py tests\test_scenarios.py tests\test_app_metadata.py
```

Acceptance:

- Un YAML sin ganancias sigue funcionando igual.
- Un YAML con ganancias explicitas instancia el controlador con esos valores.
- `metrics.metadata.controller.parameters` registra las ganancias efectivas.

### 2. Utilidades internas de dataset clasico

Objetivo: crear logica reutilizable, simple y testeable para definir familias, geometria, perturbaciones, PID y manifest.

Cambios:

- Crear modulo interno, por ejemplo `src/simulador_quad/datasets/classic.py`.
- Definir constantes de `v1`: familias, perfiles `P0`-`P5`, conteos, semillas, splits y parametros base.
- Definir funciones puras:
  - `build_pid_id(family, version)`;
  - `build_scenario_id(family, geometry_id, perturbation_id, seed)`;
  - `classic_dataset_manifest(version, output_root)`;
  - `build_scenario_config(row, pid_config)`;
  - `write_dataset_files(version, output_root, overwrite=False)`.
- Usar estructuras simples (`dict`, listas, dataclasses ligeras solo si aclaran) y nombres con unidades.

Decisiones cerradas:

- Dataset `v1`: 150 episodios.
- Splits: `70/15/15`, estratificados por familia y perfil.
- Semilla base recomendada: `1042`; derivar semillas por episodio de forma determinista desde indice/familia/perfil.
- `output.dir` siempre bajo `data/classic_dataset/v1/results/<family>/<scenario_id>`.
- No sobrescribir un dataset existente salvo flag explicito `--overwrite`.

Verificacion:

```powershell
uv run pytest tests\test_classic_dataset_generation.py
```

Acceptance:

- El manifest tiene 150 filas.
- Cada `scenario_id` es unico.
- Cada `output.dir` es unico.
- La generacion es determinista.
- Cada YAML generado pasa `validate_scenario_config`.

### 3. Script de generacion de dataset

Objetivo: exponer la generacion de YAML, `manifest.csv`, `README.md` local del dataset y PID files iniciales.

Nuevo script:

```powershell
uv run python tools/generate_classic_dataset.py --version v1 --out data\classic_dataset\v1
```

Comportamiento:

- Crear estructura `data/classic_dataset/v1/`.
- Escribir `manifest.csv`.
- Escribir 150 YAML bajo `scenarios/<family>/`.
- Escribir `pids/pid_<family>_v1.yaml` con las ganancias congeladas disponibles.
- Si aun no se ha ejecutado tuning, escribir PIDs iniciales basados en defaults actuales y marcar `source: default_initial`.
- Rechazar salida existente salvo `--overwrite`.

Verificacion:

```powershell
uv run python tools/generate_classic_dataset.py --version v1 --out data\classic_dataset\v1
uv run pytest tests\test_classic_dataset_generation.py
```

Acceptance:

- El comando genera estructura completa.
- El manifest referencia rutas existentes.
- Los YAML contienen PID, familia, geometria, perturbacion, semilla y `output.dir` coherentes.

### 4. Metricas auxiliares para seleccion PID

Objetivo: calcular el score definido por la spec sin mezclar unidades de forma opaca.

Cambios:

- Anadir helper de analisis, preferiblemente en modulo de dataset o metricas:
  - `attitude_rms_rad_from_telemetry(telemetry)`;
  - `control_effort_norm_from_metrics_or_telemetry(...)`;
  - `pid_candidate_score(metrics, telemetry, family)`.
- Usar filtros duros:
  - terminacion por tiempo;
  - sin no finitos;
  - saturacion <= 2%;
  - degradacion <= 2%;
  - `position_max_err_m` bajo umbral por familia.
- Implementar desempate del 5% a favor del PID mas conservador.

Verificacion:

```powershell
uv run pytest tests\test_classic_pid_selection.py
```

Acceptance:

- Candidatos invalidos se rechazan.
- El menor score valido gana.
- Empate relativo menor del 5% elige menores ganancias/esfuerzo.

### 5. Script de ajuste PID por familia

Objetivo: producir un `pid_<family>_v1.yaml` reproducible para cada familia usando el escenario nominal.

Nuevo script:

```powershell
uv run python tools/tune_classic_pid.py --family circle --out data\classic_dataset\v1\pids
```

Comportamiento:

- Soportar `hold`, `circle`, `lissajous`, `waypoint`.
- Construir escenario nominal de ajuste con `P0_nominal`.
- Ejecutar un barrido pequeño y explicito de ganancias alrededor de defaults.
- Evaluar candidatos con el score de la spec.
- Guardar YAML de PID con:
  - `pid_id`;
  - `family`;
  - `version`;
  - ganancias;
  - score;
  - filtros;
  - comando;
  - fecha/hora;
  - resumen de metricas nominales.
- No escribir resultados de tuning dentro del dataset final salvo bajo carpeta separada, por ejemplo `data/classic_dataset/v1/tuning/<family>/`.

Verificacion:

```powershell
uv run python tools/tune_classic_pid.py --family hold --out data\classic_dataset\v1\pids
uv run pytest tests\test_classic_pid_selection.py
```

Acceptance:

- El script genera un PID YAML valido.
- El PID ganador supera filtros duros.
- El PID queda separado por familia y version.

### 6. Script de ejecucion del dataset

Objetivo: ejecutar los YAML generados y producir resultados reproducibles.

Nuevo script:

```powershell
uv run python tools/run_classic_dataset.py --dataset data\classic_dataset\v1 --no-visualization
```

Comportamiento:

- Leer `manifest.csv`.
- Ejecutar cada `scenario_path` con `run_simulation(..., visualization=False)`.
- Permitir filtros:
  - `--family circle`;
  - `--limit 5`;
  - `--scenario-id circle_g03_p5_s1042`.
- Saltar resultados existentes salvo `--rerun`.
- Registrar fallos en un `run_report.csv` sin detener todo el lote, salvo `--fail-fast`.

Verificacion:

```powershell
uv run python tools/run_classic_dataset.py --dataset data\classic_dataset\v1 --family hold --limit 2 --no-visualization
```

Acceptance:

- Genera `telemetry.json` y `metrics.json` para escenarios ejecutados.
- El lote puede reanudarse.
- Los fallos quedan trazados.

### 7. Script de resumen del dataset

Objetivo: producir una tabla defendible de calidad del dataset.

Nuevo script:

```powershell
uv run python tools/summarize_classic_dataset.py --dataset data\classic_dataset\v1
```

Comportamiento:

- Leer manifest y resultados existentes.
- Crear `summary.csv` con metricas por episodio.
- Crear resumen agregado por familia, perfil y split.
- Marcar episodios invalidos por no finitos, terminacion inesperada, saturacion/degradacion excesiva o resultados faltantes.
- No borrar ni corregir resultados automaticamente.

Verificacion:

```powershell
uv run python tools/summarize_classic_dataset.py --dataset data\classic_dataset\v1
```

Acceptance:

- `summary.csv` existe.
- Se puede identificar cuantos episodios son validos por familia/perfil.
- Los resultados faltantes no rompen el resumen.

## Tests

Crear pruebas nuevas:

- `tests/test_classic_controller_config.py`
  - ganancias explicitas desde YAML;
  - defaults conservados;
  - metadata con ganancias efectivas.

- `tests/test_classic_dataset_generation.py`
  - manifest de 150 episodios;
  - conteos por familia;
  - determinismo;
  - YAML validos;
  - rutas unicas.

- `tests/test_classic_pid_selection.py`
  - filtros duros;
  - score;
  - desempate conservador.

- `tests/test_classic_dataset_scripts.py`
  - CLI de generacion en directorio temporal;
  - ejecucion limitada de 1 episodio nominal;
  - resumen tolerante a resultados incompletos.

Comando final esperado:

```powershell
uv run pytest
```

## Implementation Boundaries

- Always: usar `uv`; mantener ENU/FRD; mantener scripts simples; generar YAML reproducibles; no depender de `results/` historico; no sobreescribir datasets sin flag explicito.
- Ask first: cambiar el numero de episodios; cambiar valores numericos de perfiles; introducir optimizadores externos; cambiar defaults fisicos del simulador.
- Never: implementar red neuronal; crear loaders ML; entrenar modelos; reajustar PID por perturbacion; mezclar resultados historicos con el dataset `v1`.

## Suggested Task Breakdown

1. Implementar ganancias explicitas del controlador y tests.
2. Implementar modulo interno de definicion/generacion de dataset y tests.
3. Implementar `generate_classic_dataset.py` y tests CLI en temporal.
4. Implementar score/filtros de PID y tests.
5. Implementar `tune_classic_pid.py` con barrido inicial conservador.
6. Implementar `run_classic_dataset.py` con filtros, reanudacion y reporte.
7. Implementar `summarize_classic_dataset.py`.
8. Ejecutar `uv run pytest`.
9. Ejecutar una prueba manual corta: generar dataset en temporal, correr 1 episodio por familia y resumir.

La actualizacion general de `README.md` y `docs/simulador/` queda como paso posterior, una vez validados los comandos reales.
