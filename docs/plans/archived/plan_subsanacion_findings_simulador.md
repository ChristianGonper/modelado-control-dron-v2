# Plan: Subsanacion de Findings del Simulador

## Objetivo del Plan

Implementar la subsanacion definida en `docs/plans/spec_subsanacion_findings_simulador.md` de forma incremental, verificable y acotada a los seis findings de review.

Este plan no introduce control neuronal ni nuevas dependencias. El foco es estabilizar la primera version del simulador clasico para que sea trazable, reproducible y fisicamente coherente con ENU/FRD.

## Componentes y Dependencias

### 1. Convencion fisica del mixer y actuadores

Componentes:

- `src/simulador_quad/dynamics/mixer.py`
- `src/simulador_quad/dynamics/actuators.py`
- `tests/test_mixer.py`
- `tests/test_actuators.py`

Dependencias:

- Debe cerrarse antes de ajustar telemetria y metricas, porque los campos exportados deben representar comandos fisicamente correctos.
- Debe fijar una sola convencion:

```text
F_i_B = [0, 0, -T_i]
tau_i,B = r_i,B x F_i,B + [0, 0, s_i k_m omega_i^2]
tau_x = -y_i T_i
tau_y =  x_i T_i
tau_z =  s_i (k_m / k_f) T_i
```

Resultado esperado:

- Codigo, comentarios y tests usan la misma matriz de asignacion.
- `uv run python -m pytest tests\test_mixer.py tests\test_actuators.py` pasa.

### 2. Contratos de telemetria y flags

Componentes:

- `src/simulador_quad/core/contracts.py`
- `src/simulador_quad/dynamics/mixer.py`
- `src/simulador_quad/dynamics/actuators.py`
- `src/simulador_quad/runner.py`

Dependencias:

- Requiere la convencion fisica ya fijada.
- Debe preceder a exportacion y metricas, porque esas capas dependen del contrato.

Resultado esperado:

- Se distinguen comando solicitado, empuje objetivo, omega objetivo, omega aplicada, empuje aplicado, par aplicado, RPM y flags.
- La observacion usada por el controlador queda representada en `TelemetrySample`.
- Existen flags suficientes para detectar saturacion instantanea y degradacion de empuje colectivo.

### 3. Runner y terminacion por saturacion persistente

Componentes:

- `src/simulador_quad/runner.py`
- `src/simulador_quad/scenarios/loader.py`
- `scenarios/*.yaml`
- `tests/test_runner.py`

Dependencias:

- Requiere flags de saturacion/degradacion.
- Puede implementarse antes de metricas, pero debe coordinarse con ellas para registrar causa y tiempo.

Resultado esperado:

- El runner acumula tiempo de saturacion persistente.
- El umbral se declara en segundos bajo `termination`.
- La causa de terminacion es explicita, por ejemplo `Persistent actuator saturation`.
- La telemetria conserva la causa final del episodio.

### 4. Exportacion y metricas trazables

Componentes:

- `src/simulador_quad/telemetry/export.py`
- `src/simulador_quad/metrics/report.py`
- `tests/test_metrics.py`

Dependencias:

- Requiere contratos extendidos y runner actualizado.

Resultado esperado:

- La exportacion JSON incluye todo el flujo de simulacion requerido.
- Las metricas incluyen:
  - RMSE, MAE y maximo de error de posicion;
  - esfuerzo medio y maximo de control;
  - velocidad maxima de rotor;
  - porcentaje de tiempo en saturacion;
  - causa y tiempo de terminacion;
  - escenario, controlador, semilla y parametros relevantes.

### 5. Lag, retardo y saturacion de momentos del controlador

Componentes:

- `src/simulador_quad/dynamics/actuators.py`
- `src/simulador_quad/control/classic.py`
- `src/simulador_quad/scenarios/loader.py`
- `scenarios/*.yaml`
- `tests/test_actuators.py`
- `tests/test_control.py`

Dependencias:

- El lag puede corregirse en paralelo con el mixer si no cambia contratos publicos.
- La saturacion de momentos debe integrarse con escenarios y telemetria para no quedar como constante oculta.

Resultado esperado:

- El lag usa `alpha = 1 - exp(-dt/tau)`.
- El controlador limita `body_moments_Nm` por eje.
- Los limites pueden venir de `controller.max_body_moments_Nm`; si faltan, se usan defaults conservadores documentados.

### 6. Trayectoria Line y escenarios

Componentes:

- `src/simulador_quad/trajectories/analytic.py`
- `src/simulador_quad/scenarios/loader.py`
- `tests/test_trajectories.py`
- `scenarios/circle_noisy_wind.yaml`

Dependencias:

- Puede hacerse en paralelo con telemetria si no se modifican contratos comunes.
- El ajuste de `circle_noisy_wind` debe hacerse al final, cuando mixer, actuadores y controlador ya esten corregidos.

Resultado esperado:

- Existe `LineTrajectory` con smoothstep cubico.
- El YAML acepta `trajectory.type: line`.
- `circle_noisy_wind` queda como escenario de seguimiento robusto y no como fallo prematuro.

## Orden de Implementacion

1. Fijar signos del mixer y actuadores.
2. Corregir lag de actuador.
3. Extender contratos de telemetria y flags.
4. Actualizar runner para observacion, flags y saturacion persistente.
5. Actualizar exportacion JSON y metricas.
6. Anadir saturacion de momentos al controlador y carga desde YAML.
7. Implementar `LineTrajectory` y soporte YAML.
8. Ajustar tests existentes y anadir pruebas nuevas para los criterios de aceptacion.
9. Ejecutar escenarios y ajustar `circle_noisy_wind` como escenario robusto si sigue terminando prematuramente.
10. Ejecutar verificacion global.

## Trabajo Secuencial

Por decision de planificacion, todo el trabajo se ejecutara de forma secuencial. No se haran ramas de trabajo paralelas ni subtareas simultaneas, para reducir riesgo de inconsistencias entre contratos, runner, tests y escenarios.

1. Convencion mixer/actuadores antes de metricas finales.
2. Contratos antes de runner/exportacion/metricas.
3. Runner antes de tests de integracion de telemetria.
4. Escenarios finales despues de estabilizar dinamica y controlador.

## Riesgos y Mitigaciones

### Riesgo 1: Corregir tests sin corregir la fisica

Mitigacion:

- Derivar tests desde `r x F` y la convencion documentada.
- Verificar los signos tanto en mixer como en actuadores.

### Riesgo 2: Flags de saturacion ambiguos

Mitigacion:

- Separar al menos:
  - saturacion de omega por rotor;
  - degradacion de empuje colectivo por mixer;
  - demanda de momento no realizable si aparece.

### Riesgo 3: Telemetria demasiado pesada o dificil de leer

Mitigacion:

- Mantener JSON legible.
- No anadir NPZ en esta fase salvo necesidad real.
- Usar arrays por rotor con nombres fisicos claros.

### Riesgo 4: `circle_noisy_wind` oculta inestabilidad real

Mitigacion:

- No relajar terminaciones para que pase.
- Ajustar primero signos, actuadores y saturaciones.
- Si aun falla, reducir agresividad del escenario o documentar por que no es escenario de comparacion robusta.

### Riesgo 5: Cambiar interfaz rompe muchos tests

Mitigacion:

- Actualizar contratos una vez y adaptar tests de forma agrupada.
- Mantener compatibilidad conceptual con nombres existentes cuando no contradigan requisitos.

## Checkpoints de Verificacion

### Checkpoint A: Signos y actuadores

Comando:

```powershell
uv run python -m pytest tests\test_mixer.py tests\test_actuators.py
```

Criterio:

- Todos los tests pasan.
- Los tests validan `tau_x=-yT`, `tau_y=xT`, `tau_z=s(k_m/k_f)T`.

### Checkpoint B: Runner y telemetria

Comando:

```powershell
uv run python -m pytest tests\test_runner.py tests\test_metrics.py
```

Criterio:

- La observacion esta registrada.
- La saturacion persistente termina con causa explicita.
- Las metricas reportan porcentaje de saturacion.

### Checkpoint C: Control y trayectorias

Comando:

```powershell
uv run python -m pytest tests\test_control.py tests\test_trajectories.py
```

Criterio:

- Los momentos del controlador quedan dentro de limites.
- `LineTrajectory` es finita, suave en posicion/velocidad y cargable desde YAML.

### Checkpoint D: Suite completa

Comando:

```powershell
uv run pytest
```

Criterio:

- Toda la suite pasa.

### Checkpoint E: Escenarios reproducibles

Comandos:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml
uv run simulador-quad run scenarios\circle_drag.yaml
uv run simulador-quad run scenarios\circle_noisy_wind.yaml
```

Criterio:

- Los tres escenarios generan `telemetry.json` y `metrics.json`.
- `hover_clean` y `circle_drag` llegan al limite de tiempo sin fallo fisico.
- `circle_noisy_wind` queda como seguimiento robusto y no termina prematuramente por actitud, saturacion persistente o no finitos.

## Entregables de la Fase de Implementacion

- Codigo corregido en los modulos indicados.
- Tests actualizados y ampliados.
- Escenarios YAML ajustados solo cuando sea necesario.
- Telemetria y metricas exportadas con campos trazables.
- Resultado de los comandos de verificacion en el cierre de implementacion.

## Criterio para Pasar a TASKS

Se puede pasar a la fase TASKS cuando este plan sea aprobado y no se pidan cambios en:

- orden de implementacion;
- decisiones cerradas;
- alcance de escenarios;
- formato de telemetria y metricas.
