# Spec: Generacion de Datos Clasicos por Familia de Trayectoria

## Objective

Definir la fase previa al control neuronal: generacion reproducible de datos con el simulador clasico. La red neuronal queda fuera de alcance en esta spec: no se implementan loaders de ML, entrenamiento, inferencia ni evaluacion neuronal.

El objetivo academico es construir un dataset defendible para entrenar posteriormente una red por imitacion. Para ello se ajustara un controlador clasico por familia de trayectoria en un caso nominal, se congelaran esas ganancias y se generaran variantes geometricas y perturbadas usando siempre el PID congelado de su familia.

El escenario nominal de ajuste no es fisica ideal: incluye drag lineal y dinamica de actuadores. Nominal significa sin viento y sin ruido de observacion.

## Dataset v1

La version inicial sera `v1` y tendra escala media: 150 episodios de dataset, mas escenarios separados para ajuste PID nominal.

| Familia | Episodios | PID congelado | Papel |
| --- | ---: | --- | --- |
| `hold` | 18 | `pid_hold_v1` | Hover, cambios de posicion fija y estabilizacion. |
| `circle` | 48 | `pid_circle_v1` | Seguimiento circular horizontal ENU. |
| `lissajous` | 48 | `pid_lissajous_v1` | Seguimiento 3D suave sinusoidal. |
| `waypoint` | 36 | `pid_waypoint_v1` | Seguimiento por puntos con smoothstep cubico. |

### Ajuste PID por familia

Para cada familia se definira un escenario nominal de ajuste:

- drag lineal activado;
- dinamica de actuadores activada segun parametros base, incluyendo retardo si el perfil base lo declara;
- viento constante nulo: `constant_wind_W_m_s: [0, 0, 0]`;
- ruido de observacion nulo: `pos_std_m: 0.0`, `vel_std_m_s: 0.0`;
- misma masa, inercia, geometria de rotores y limites que el vehiculo base;
- estado inicial coherente con la trayectoria en `t = 0`, para medir seguimiento y no captura inicial;
- duracion suficiente para observar el regimen de la familia.

El PID ajustado para una familia no se reajustara para variantes geometricas, viento, ruido, drag alto ni combinaciones. Cualquier cambio posterior de ganancias creara un nuevo identificador de PID, por ejemplo `pid_circle_v2`.

### Repertorio por familia

`hold`: 6 referencias por 3 perfiles, total 18 episodios.

- Alturas: `1.5`, `2.0`, `3.0` m.
- Posiciones XY: centro, desplazamiento Este y desplazamiento Norte.
- Yaw: `0` y `pi/4` donde aplique.
- Perfiles usados: `P0_nominal`, `P2_wind_east`, `P5_combined`.

`circle`: 8 geometria por 6 perfiles, total 48 episodios.

- Radios candidatos: `1.0`, `1.5`, `2.0`, `2.5` m.
- Velocidades angulares candidatas: `0.35`, `0.5`, `0.65` rad/s.
- Alturas candidatas: `2.0`, `3.0`, `4.0` m.
- `yaw_mode: forward`.
- Las 8 geometria se escogeran como combinaciones representativas, evitando duplicados casi identicos y manteniendo aceleraciones compatibles con saturacion razonable.

`lissajous`: 8 geometria por 6 perfiles, total 48 episodios.

- Amplitudes XY entre `0.75` y `2.5` m.
- Amplitud Z entre `0.2` y `0.8` m.
- Frecuencias no identicas para evitar trayectorias degeneradas.
- Centro con `Z_W >= 2.0 m` para conservar margen vertical.
- Yaw nominal constante `0.0` salvo decision documentada posterior.

`waypoint`: 6 patrones por 6 perfiles, total 36 episodios.

- Cuadrado.
- Rectangulo.
- Zigzag.
- Escalera vertical suave.
- Diagonal 3D.
- Recorrido cerrado con retorno.
- Los tiempos se definiran para mantener velocidades razonables y evitar saltos agresivos en aceleracion.

### Perfiles de entorno

Los perfiles se aplican a las variantes de dataset, no al proceso de reajuste PID. `P0_nominal` coincide con el entorno de ajuste.

| Perfil | Definicion |
| --- | --- |
| `P0_nominal` | Drag nominal + actuadores nominales, sin viento, sin ruido. |
| `P1_drag_high` | Drag mayor que nominal, actuadores nominales, sin viento, sin ruido. |
| `P2_wind_east` | Drag nominal + actuadores nominales, viento constante Este. |
| `P3_wind_ne` | Drag nominal + actuadores nominales, viento constante Este/Norte. |
| `P4_noise_low` | Drag nominal + actuadores nominales, ruido bajo en posicion y velocidad. |
| `P5_combined` | Viento + ruido + drag alto + actuadores con dinamica completa. |

Valores numericos fijados para `v1`:

| Perfil | Drag `[x,y,z]` | Viento ENU `[m/s]` | Ruido pos `[m]` | Ruido vel `[m/s]` | Actuadores |
| --- | --- | --- | ---: | ---: | --- |
| `P0_nominal` | `[0.10, 0.10, 0.05]` | `[0, 0, 0]` | `0.0` | `0.0` | `time_constant_s: 0.03`, `delay_s: 0.01` |
| `P1_drag_high` | `[0.20, 0.20, 0.10]` | `[0, 0, 0]` | `0.0` | `0.0` | nominal |
| `P2_wind_east` | nominal | `[1.0, 0, 0]` | `0.0` | `0.0` | nominal |
| `P3_wind_ne` | nominal | `[1.0, 1.0, 0]` | `0.0` | `0.0` | nominal |
| `P4_noise_low` | nominal | `[0, 0, 0]` | `0.02` | `0.03` | nominal |
| `P5_combined` | `[0.20, 0.20, 0.10]` | `[1.5, 1.0, 0]` | `0.05` | `0.08` | `time_constant_s: 0.05`, `delay_s: 0.02` |

En todos los escenarios del dataset `v1`, usar `omega_max_rad_s: 1500` para evitar que la saturacion sea el comportamiento dominante. La saturacion debe existir como metrica y criterio de rechazo, pero no debe definir el dataset base.

Estos valores deben quedar exportados en cada YAML y en `metrics.metadata.config_resolved`.

### Inicializacion de escenarios generados

Los escenarios de tuning y dataset clasico deben empezar en la referencia de su trayectoria en `t = 0`:

```text
initial_state.position_W_m = trajectory.get_reference(0.0).position_W_m
initial_state.yaw_rad = trajectory.get_reference(0.0).yaw_rad
initial_state.velocity_W_m_s = [0.0, 0.0, 0.0]
initial_state.orientation_WB = null
initial_state.angular_velocity_B_rad_s = [0.0, 0.0, 0.0]
```

Esta decision evita que `position_rmse_m`, `position_max_err_m` y el score de seleccion PID queden dominados por un error inicial artificial. La evaluacion de captura desde una posicion lejana queda fuera de `v1` y debera definirse como escenario o familia separada si se necesita.

## Interfaces and Artifacts

### YAML de controlador

El YAML de escenarios debera poder declarar ganancias explicitas:

```yaml
controller:
  type: "classic"
  Kp_pos: [2.0, 2.0, 5.0]
  Kd_pos: [1.0, 1.0, 2.0]
  Kp_att: [4.0, 4.0, 1.0]
  Kd_att: [1.5, 1.5, 0.5]
  max_body_moments_Nm: [2.0, 2.0, 0.5]
```

Si faltan ganancias, se mantendran los valores por defecto actuales. La metadata debe registrar siempre las ganancias efectivas, tanto si vienen del YAML como si vienen de defaults.

### Estructura de salida

```text
data/classic_dataset/v1/
  README.md
  manifest.csv
  pids/
    pid_hold_v1.yaml
    pid_circle_v1.yaml
    pid_lissajous_v1.yaml
    pid_waypoint_v1.yaml
  scenarios/
    hold/
    circle/
    lissajous/
    waypoint/
  results/
    hold/
    circle/
    lissajous/
    waypoint/
```

Campos minimos de `manifest.csv`:

- `scenario_id`
- `family`
- `geometry_id`
- `perturbation_id`
- `pid_id`
- `seed`
- `split`
- `scenario_path`
- `result_dir`

`scenario_id` sera estable y legible, por ejemplo `circle_g03_p5_s1042`. `split` se reservara para uso posterior y debera ser uno de `train`, `val`, `test`, aunque esta fase no implemente ningun loader neuronal.

## Commands

Comandos implementados para esta fase:

```powershell
uv run python tools/tune_classic_pid.py --family hold --out data\classic_dataset\v1\pids
uv run python tools/tune_classic_pid.py --family circle --out data\classic_dataset\v1\pids
uv run python tools/tune_classic_pid.py --family lissajous --out data\classic_dataset\v1\pids
uv run python tools/tune_classic_pid.py --family waypoint --out data\classic_dataset\v1\pids

uv run python tools/generate_classic_dataset.py --version v1 --out data\classic_dataset\v1
uv run python tools/run_classic_dataset.py --dataset data\classic_dataset\v1 --no-visualization
uv run python tools/summarize_classic_dataset.py --dataset data\classic_dataset\v1
```

Los scripts deben ser sencillos y trazables, con estilo de software cientifico: funciones pequenas, nombres con unidades, datos explicitos y sin frameworks de experimentacion.

## Project Structure

- `tools/`: scripts ejecutables de ajuste, generacion, ejecucion y resumen.
- `src/simulador_quad/control/`: soporte para ganancias explicitas del controlador clasico.
- `src/simulador_quad/scenarios/`: carga y validacion de YAML generados.
- `tests/`: pruebas de generacion determinista, loader, metadata y manifiesto.
- `data/classic_dataset/v1/`: dataset generado versionado localmente.
- `docs/simulador/`: documentacion viva si cambian comandos, YAML, salidas o metadata.

## Testing Strategy

### Generacion determinista

- Mismo `version`, familia y semilla producen los mismos YAML.
- Cada YAML generado pasa `validate_scenario_config`.
- Cada `output.dir` es unico.
- `manifest.csv` contiene exactamente 150 episodios.
- Cada fila del manifiesto apunta a un YAML existente y a un directorio de resultado unico.
- Cada YAML generado inicializa `initial_state.position_W_m` y `initial_state.yaw_rad` desde la referencia en `t = 0`.

### Controlador y metadata

- El loader acepta `Kp_pos`, `Kd_pos`, `Kp_att`, `Kd_att` y `max_body_moments_Nm`.
- Si faltan ganancias, se conservan defaults actuales.
- `metrics.metadata.controller.parameters` registra ganancias efectivas y limites.
- Los `pid_id` usados en YAML, metadata y manifest son consistentes.

### Validacion ligera del dataset

- Ejecutar al menos un episodio nominal por familia.
- Comprobar que se generan `telemetry.json` y `metrics.json`.
- Comprobar ausencia de no finitos en telemetria y metricas.
- Comprobar que metadata contiene PID, semilla, configuracion original y configuracion efectiva.

## PID Selection Criterion

El ajuste de cada PID por familia se hara solo sobre el escenario nominal de ajuste. Antes de comparar candidatos, aplicar filtros duros:

- Rechazar si `termination_reason != "Time limit reached"`.
- Rechazar si aparece cualquier valor no finito.
- Rechazar si `saturation_percentage > 2.0`.
- Rechazar si `degradation_percentage > 2.0`.
- Rechazar si `position_max_err_m` supera:
  - `hold`: `0.40 m`;
  - `circle`: `0.75 m`;
  - `lissajous`: `0.90 m`;
  - `waypoint`: `0.80 m`.

Entre candidatos validos, seleccionar el menor score:

```text
score =
  1.00 * position_rmse_m
+ 0.50 * position_max_err_m
+ 0.20 * attitude_rms_rad
+ 0.10 * control_effort_norm
+ 2.00 * saturation_fraction
+ 2.00 * degradation_fraction
```

Definiciones:

- `attitude_rms_rad`: RMS de la norma de roll/pitch/yaw calculados desde `orientation_WB` con convenio ENU/FRD.
- `control_effort_norm`: esfuerzo de control normalizado para comparar candidatos dentro de la misma familia. Debe derivarse de empuje colectivo y momentos con escalas explicitas, no de una suma dimensional sin normalizar.
- `saturation_fraction = saturation_percentage / 100`.
- `degradation_fraction = degradation_percentage / 100`.

Si dos candidatos tienen score parecido, con diferencia relativa menor del `5%`, elegir el PID mas conservador: menor `Kp`, menor `Kd` y menor esfuerzo de control. Para dataset de imitacion se prioriza una referencia clasica estable y defendible sobre un PID agresivo que reduzca poco el RMSE.

## Boundaries

- Always: mantener mundo ENU y cuerpo FRD; ajustar PID por familia solo en nominal con drag y actuadores; congelar el PID antes de generar variantes perturbadas; registrar semilla, PID, familia, geometria, perturbacion y configuracion efectiva; separar escenarios de ajuste PID de episodios de dataset.
- Ask first: aumentar el dataset por encima de 150 episodios; anadir nuevas familias de trayectoria; cambiar modelo fisico o sensores; anadir dependencias externas para optimizacion; cambiar el significado de nominal.
- Never: implementar red neuronal, loaders ML o entrenamiento; reajustar PID por perturbacion; mezclar resultados historicos de `results/` con el dataset versionado; sobrescribir datasets versionados existentes.

## Success Criteria

- Existe `docs/plans/spec_generacion_datos_control_clasico.md` como spec vigente.
- La spec fija familias, escala, numero de episodios, perturbaciones, artefactos y comandos.
- La spec declara explicitamente que nominal incluye drag y actuadores, pero no viento ni ruido.
- La spec define un PID congelado por familia y prohibe reajustar por perturbacion.
- La spec deja criterios de prueba suficientes para implementar la fase sin decisiones sustanciales adicionales.

## Open Questions

- No hay preguntas abiertas.
