# Validacion de escenarios y resultados

Este documento define como usar los escenarios actuales como evidencia experimental del simulador clasico. No sustituye a los YAML ni a las metricas exportadas: fija el papel de cada escenario, los criterios iniciales de aceptacion y las evidencias minimas que deben conservarse para la memoria del TFG.

La capa neuronal queda fuera de esta fase. Cuando exista controlador neuronal, sus escenarios y criterios deberan documentarse en una ampliacion separada y compararse con las mismas condiciones.

## Comandos oficiales

Ejecutar desde la raiz del repositorio:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
uv run simulador-quad run scenarios\circle_drag.yaml --no-visualization
uv run simulador-quad run scenarios\circle_noisy_wind.yaml --no-visualization
uv run simulador-quad run scenarios\lissajous_clean.yaml --no-visualization
uv run simulador-quad run scenarios\waypoint_clean.yaml --no-visualization
```

Para generar figuras despues de una ejecucion:

```powershell
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
```

## Criterios generales

Un escenario se considera valido como evidencia de la version clasica si cumple:

- El YAML usado esta versionado en `scenarios/`.
- La ejecucion termina por la causa esperada.
- `metrics.json` y `telemetry.json` se generan desde ese YAML.
- No aparecen valores no finitos en estado, comandos, rotores o metricas.
- Las saturaciones y degradaciones se reportan, no se ocultan.
- Las figuras se generan desde la telemetria exportada, no desde datos editados manualmente.

Los umbrales numericos de RMSE y error maximo son iniciales. Deben revisarse cuando se implemente metadata reproducible fuerte y regresiones automaticas de escenarios.

## Escenarios oficiales

| Escenario | Tipo | Objetivo | Perturbaciones | Semilla | Criterio inicial de exito |
| --- | --- | --- | --- | --- | --- |
| `scenarios/hover_clean.yaml` | Nominal | Verificar despegue corto y mantenimiento de hover con referencia fija. | Sin viento, sin ruido, sin drag. | `42` | `termination_reason == "Time limit reached"`, `saturation_percentage == 0`, `degradation_percentage == 0`, `position_rmse_m <= 0.40`. |
| `scenarios/circle_drag.yaml` | Nominal con disipacion | Verificar seguimiento circular con drag lineal activo. | Drag lineal `[0.1, 0.1, 0.05]`, sin viento ni ruido. | `42` | `termination_reason == "Time limit reached"`, `saturation_percentage == 0`, `degradation_percentage <= 1`, `position_rmse_m <= 0.45`. |
| `scenarios/circle_noisy_wind.yaml` | Robustez | Verificar seguimiento circular con viento constante, ruido de observacion, retardo y lag. | Viento `[2, 1, 0]`, ruido pos/vel, drag, retardo y lag. | `123` | `termination_reason == "Time limit reached"`, `saturation_percentage == 0`, `degradation_percentage <= 5`, `position_rmse_m <= 0.60`. |
| `scenarios/lissajous_clean.yaml` | Nominal dinamico | Verificar seguimiento suave 3D sin perturbaciones externas. | Sin viento, sin ruido, sin drag. | `42` | `termination_reason == "Time limit reached"`, `saturation_percentage == 0`, `degradation_percentage <= 1`, `position_rmse_m <= 0.70`. |
| `scenarios/waypoint_clean.yaml` | Demostracion de trayectoria suavizada | Verificar carga y seguimiento de waypoints con smoothstep cubico. | Sin viento, sin ruido, sin drag. | `42` | `termination_reason == "Time limit reached"`, sin fallo por actitud/no finitos/saturacion persistente, `position_rmse_m <= 0.50`. |

## Resultados historicos

Los directorios actuales en `results/` son utiles para inspeccion y comparacion durante desarrollo, pero no deben tratarse como evidencia final de memoria sin regenerarlos desde los YAML actuales.

Motivos:

- Los artefactos no registran todavia commit, estado del arbol, comando exacto ni hash de `uv.lock`.
- Algunos resultados pueden proceder de versiones anteriores de escenarios o codigo.
- Por ejemplo, el resultado historico de `results/waypoint_clean/metrics.json` registra una duracion de 60 s, mientras el YAML actual `scenarios/waypoint_clean.yaml` declara `max_duration_s: 15.0`.

Para usar un resultado en memoria:

1. Ejecutar el YAML oficial desde el estado de codigo que se quiere defender.
2. Guardar `metrics.json`, `telemetry.json`, figuras y visor 3D si aplica.
3. Registrar manualmente, hasta que exista metadata automatica fuerte, el comando, fecha, commit, estado limpio/sucio y version de Python/uv.
4. Referenciar el escenario y los criterios de este documento.

## Evidencias minimas por escenario

Cada escenario usado en la memoria debe conservar:

- YAML versionado en `scenarios/`.
- `metrics.json`.
- `telemetry.json`.
- Figuras estandar:
  - `trajectory_xy.png`
  - `position_time.png`
  - `tracking_error.png`
  - `rotor_speeds.png`
  - `control_effort.png`
- Conclusion tecnica breve:
  - causa de terminacion;
  - error de seguimiento;
  - saturacion/degradacion;
  - perturbaciones activas;
  - limitaciones del resultado.

## Escenarios de fallo y estres

Los escenarios de estres o fallo esperado no deben mezclarse con escenarios nominales. Si se anaden, deben declararse con:

- objetivo del fallo o estres;
- condicion esperada de terminacion;
- motivo fisico o de validacion;
- criterio para considerar correcto el fallo.

Los resultados historicos `results/stress_*` o `results/test_line` no son escenarios oficiales si no existe YAML reproducible correspondiente en `scenarios/`.

## Relacion con pruebas automaticas

Esta fase define validacion documental. La automatizacion futura debera:

- ejecutar escenarios cortos en directorios temporales;
- comprobar `termination_reason`;
- verificar RMSE, saturacion, degradacion y ausencia de no finitos;
- validar esquema minimo de `metrics.json` y `telemetry.json`;
- evitar usar `results/` historico como oraculo unico.

## Limites de validez

Estos escenarios validan el simulador dentro del alcance actual:

- cuerpo rigido 6DOF;
- cuaterniones;
- RK4;
- control clasico;
- drag lineal simplificado;
- viento constante y ruido de observacion simple;
- actuadores simplificados con saturacion, retardo y lag.

No validan vuelo real, aerodinamica formal, sensores realistas, estimador onboard ni control neuronal.
