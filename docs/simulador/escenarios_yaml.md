# Referencia de escenarios YAML

Un escenario YAML es la descripcion reproducible de un experimento. Define vehiculo, estado inicial, trayectoria, controlador, perturbaciones, tiempos, condiciones de terminacion y salida.

La estructura admitida por el cargador actual es:

```yaml
name: "Nombre del escenario"
seed: 42

vehicle: {}
initial_state: {}
trajectory: {}
controller: {}
perturbations: {}
timing: {}
termination: {}
output: {}
```

Al ejecutar un escenario con `uv run simulador-quad run <fichero.yaml>`, se generan automáticamente la telemetría, las métricas, figuras PNG y un visor 3D interactivo, a menos que se use `--no-visualization`.

## Convenciones fisicas

- Mundo `W`: ENU, con `X_W` Este, `Y_W` Norte y `Z_W` arriba.
- Cuerpo `B`: FRD, con `X_B` delante, `Y_B` derecha y `Z_B` abajo.
- El empuje sustentador de los rotores actua en direccion `-Z_B`.
- Las posiciones y velocidades lineales se expresan en mundo ENU.
- Las velocidades angulares y momentos se expresan en cuerpo FRD.
- Los cuaterniones usan formato `[w, x, y, z]`.

## Campos globales

```yaml
name: "Hover Clean"
seed: 42
```

- `name`: nombre humano del experimento. Se copia a `metrics.metadata.scenario_name`.
- `seed`: semilla usada por el ruido de observacion. Si falta, se usa `42`.

## `vehicle`

```yaml
vehicle:
  mass_kg: 1.0
  inertia_B_kg_m2: [[0.05, 0, 0], [0, 0.05, 0], [0, 0, 0.1]]
  gravity_m_s2: 9.81
  linear_drag_coefficient: [0.1, 0.1, 0.05]
  rotors:
    - {position_B_m: [0.17, 0.17, 0], turning_direction: -1, k_f: 1.0e-4, k_m: 1.0e-6, omega_max_rad_s: 1500, time_constant_s: 0.05, delay_s: 0.01}
    - {position_B_m: [0.17, -0.17, 0], turning_direction: 1, k_f: 1.0e-4, k_m: 1.0e-6, omega_max_rad_s: 1500, time_constant_s: 0.05, delay_s: 0.01}
    - {position_B_m: [-0.17, 0.17, 0], turning_direction: 1, k_f: 1.0e-4, k_m: 1.0e-6, omega_max_rad_s: 1500, time_constant_s: 0.05, delay_s: 0.01}
    - {position_B_m: [-0.17, -0.17, 0], turning_direction: -1, k_f: 1.0e-4, k_m: 1.0e-6, omega_max_rad_s: 1500, time_constant_s: 0.05, delay_s: 0.01}
```

- `mass_kg`: masa del vehiculo.
- `inertia_B_kg_m2`: matriz de inercia respecto al centro de gravedad, expresada en FRD.
- `gravity_m_s2`: gravedad positiva en magnitud. Si falta, se usa `9.81`.
- `linear_drag_coefficient`: coeficientes de drag lineal por eje de cuerpo, en `N/(m/s)`.
- `rotors`: lista de cuatro rotores. El mezclador actual exige exactamente cuatro.

Campos de cada rotor:

- `position_B_m`: posicion del rotor en cuerpo FRD respecto al centro de gravedad.
- `turning_direction`: signo `1` o `-1` para el par de reaccion de yaw.
- `k_f`: coeficiente de empuje, `N/(rad/s)^2`.
- `k_m`: coeficiente de par, `Nm/(rad/s)^2`.
- `omega_max_rad_s`: velocidad angular maxima del rotor.
- `time_constant_s`: constante de tiempo del lag de primer orden aplicado sobre `omega`.
- `delay_s`: retardo puro antes del lag. Si falta, se usa `0.0`.

## `initial_state`

```yaml
initial_state:
  position_W_m: [2, 0, 5]
  velocity_W_m_s: [0, 0, 0]
  yaw_rad: 0.0
  orientation_WB: null
  angular_velocity_B_rad_s: [0, 0, 0]
```

- `position_W_m`: posicion inicial en mundo ENU.
- `velocity_W_m_s`: velocidad inicial en mundo ENU.
- `orientation_WB`: cuaternion inicial `[w, x, y, z]`. Si es `null`, se genera una actitud nivelada.
- `yaw_rad`: guiñada usada solo cuando `orientation_WB: null`. `yaw_rad = 0` significa que el frente del dron apunta al Norte (`Y_W`).
- `angular_velocity_B_rad_s`: velocidad angular inicial en cuerpo FRD.

## `trajectory`

Toda trayectoria devuelve `position_W_m`, `velocity_W_m_s`, `acceleration_W_m_s2` y `yaw_rad`.

### Hold

Mantiene una posicion fija.

```yaml
trajectory:
  type: "hold"
  position_W_m: [0, 0, 2]
  yaw_rad: 0.0
```

- `position_W_m`: posicion deseada constante.
- `yaw_rad`: guiñada deseada constante. Si falta, se usa `0.0`.

### Circle

Circulo horizontal en el plano `X_W-Y_W`.

```yaml
trajectory:
  type: "circle"
  center_W_m: [0, 0, 5]
  radius_m: 2.0
  omega_rad_s: 0.628
  yaw_mode: "forward"
```

- `center_W_m`: centro del circulo.
- `radius_m`: radio.
- `omega_rad_s`: velocidad angular de la referencia.
- `yaw_mode`: si es `"forward"`, la guiñada sigue la direccion de avance; cualquier otro valor deja yaw en `0.0`.

La referencia implementada es:

```text
x = cx + R cos(omega t)
y = cy + R sin(omega t)
z = cz
```

### Lissajous

Trayectoria senoidal 3D.

```yaml
trajectory:
  type: "lissajous"
  center_W_m: [0, 0, 5]
  amplitudes: [1.0, 2.0, 0.5]
  omegas: [0.8, 1.2, 0.6]
```

- `center_W_m`: punto central.
- `amplitudes`: amplitudes por eje en metros.
- `omegas`: frecuencias angulares por eje en `rad/s`.
- El yaw actual de esta trayectoria es constante `0.0`.

### Line / Waypoint

Interpola waypoints con smoothstep cubico. En el YAML puede declararse como `line` o `waypoint`.

```yaml
trajectory:
  type: "line"
  waypoints:
    - [0, 0, 2]
    - [2, 0, 2]
    - [2, 2, 3]
  times: [0.0, 4.0, 8.0]
  yaw_rad: 0.0
```

- `waypoints`: lista de posiciones en mundo ENU.
- `times`: tiempo asociado a cada waypoint. Debe tener la misma longitud que `waypoints`.
- `yaw_rad`: guiñada constante de la referencia. Si falta, se usa `0.0`.

Antes del primer tiempo mantiene el primer waypoint. Despues del ultimo mantiene el ultimo waypoint. Entre waypoints usa `s(tau) = 3 tau^2 - 2 tau^3`, con velocidad cero en los extremos de cada tramo.

## `controller`

```yaml
controller:
  type: "classic"
  max_body_moments_Nm: [2.0, 2.0, 0.5]
```

- `type`: actualmente solo se acepta `"classic"`.
- `max_body_moments_Nm`: limites de momentos `[tau_x, tau_y, tau_z]` en FRD. Si falta, el controlador usa `[10.0, 10.0, 2.0]`.

El controlador clasico usa un bucle externo de posicion y un bucle interno de actitud. Sus ganancias estan fijadas en codigo en esta version.

## `perturbations`

```yaml
perturbations:
  constant_wind_W_m_s: [2.0, 1.0, 0.0]
  pos_std_m: 0.02
  vel_std_m_s: 0.05
```

- `constant_wind_W_m_s`: viento constante en mundo ENU. Campo requerido por el cargador actual.
- `pos_std_m`: desviacion tipica del ruido gaussiano de posicion. Si falta, se usa `0.0`.
- `vel_std_m_s`: desviacion tipica del ruido gaussiano de velocidad. Si falta, se usa `0.0`.

El ruido afecta a la observacion que recibe el controlador, no al estado verdadero directamente.

## `timing`

```yaml
timing:
  physics_dt_s: 0.001
  control_dt_s: 0.01
  telemetry_dt_s: 0.1
```

- `physics_dt_s`: paso del integrador RK4 y de actuadores.
- `control_dt_s`: periodo de actualizacion del controlador.
- `telemetry_dt_s`: periodo de guardado de muestras.

Entre actualizaciones del controlador se mantiene el ultimo comando mediante ZOH.

## `termination`

```yaml
termination:
  max_duration_s: 15.0
  z_min_m: 0.0
  max_attitude_angle_rad: 3.14
  max_saturation_duration_s: 5.0
```

- `max_duration_s`: duracion maxima del episodio.
- `z_min_m`: limite inferior de altura en mundo ENU.
- `max_attitude_angle_rad`: inclinacion maxima permitida. Si falta, se usa `1.256`.
- `max_saturation_duration_s`: tiempo maximo con saturacion persistente. Si falta, se usa `1.0`.

El runner tambien tiene limites internos de posicion y velocidad, pero el CLI actual no los carga desde YAML.

## `output`

```yaml
output:
  dir: "results/circle_drag"
  telemetry_file: "telemetry.json"
  metrics_file: "metrics.json"
```

- `dir`: directorio de salida.
- `telemetry_file`: nombre del JSON de telemetria.
- `metrics_file`: nombre del JSON de metricas.

## Escenarios de ejemplo disponibles

Para probar los distintos tipos de trayectorias, se proporcionan los siguientes archivos listos para usar en `scenarios/`:

- `hover_clean.yaml`: Vuelo estacionario (`hold`) a 2m, sin perturbaciones.
- `circle_drag.yaml`: Trayectoria circular (`circle`) con rozamiento lineal activo.
- `circle_noisy_wind.yaml`: Círculo con viento constante y ruido en sensores.
- `lissajous_clean.yaml`: Trayectoria en curva de Lissajous (`lissajous`) 3D.
- `waypoint_clean.yaml`: Seguimiento de una lista de puntos (`waypoint` / `line`) con paradas suaves.

## Ejemplo minimo de hover

```yaml
name: "Hover Example"
seed: 42

vehicle:
  mass_kg: 1.0
  inertia_B_kg_m2: [[0.05, 0, 0], [0, 0.05, 0], [0, 0, 0.1]]
  linear_drag_coefficient: [0, 0, 0]
  rotors:
    - {position_B_m: [0.17, 0.17, 0], turning_direction: -1, k_f: 1.0e-4, k_m: 1.0e-6, omega_max_rad_s: 1000, time_constant_s: 0.0, delay_s: 0.0}
    - {position_B_m: [0.17, -0.17, 0], turning_direction: 1, k_f: 1.0e-4, k_m: 1.0e-6, omega_max_rad_s: 1000, time_constant_s: 0.0, delay_s: 0.0}
    - {position_B_m: [-0.17, 0.17, 0], turning_direction: 1, k_f: 1.0e-4, k_m: 1.0e-6, omega_max_rad_s: 1000, time_constant_s: 0.0, delay_s: 0.0}
    - {position_B_m: [-0.17, -0.17, 0], turning_direction: -1, k_f: 1.0e-4, k_m: 1.0e-6, omega_max_rad_s: 1000, time_constant_s: 0.0, delay_s: 0.0}

initial_state:
  position_W_m: [0, 0, 1]
  velocity_W_m_s: [0, 0, 0]
  orientation_WB: null
  yaw_rad: 0.0
  angular_velocity_B_rad_s: [0, 0, 0]

trajectory:
  type: "hold"
  position_W_m: [0, 0, 2]
  yaw_rad: 0.0

controller:
  type: "classic"

perturbations:
  constant_wind_W_m_s: [0, 0, 0]
  pos_std_m: 0.0
  vel_std_m_s: 0.0

timing:
  physics_dt_s: 0.01
  control_dt_s: 0.02
  telemetry_dt_s: 0.1

termination:
  max_duration_s: 5.0
  z_min_m: 0.0
  max_attitude_angle_rad: 1.256
  max_saturation_duration_s: 1.0

output:
  dir: "results/hover_example"
  telemetry_file: "telemetry.json"
  metrics_file: "metrics.json"
```

