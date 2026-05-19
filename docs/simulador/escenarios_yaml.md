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

Al ejecutar un escenario con `uv run simulador-quad run <fichero.yaml>`, el YAML se valida antes de instanciar la simulacion. Si un parametro fisico es invalido, el cargador falla temprano con un `ValueError` que indica el campo afectado. Si la configuracion es valida, se generan automaticamente la telemetria, las metricas, figuras PNG y un visor 3D interactivo, a menos que se use `--no-visualization`.

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

- `mass_kg`: masa del vehiculo. Debe ser positiva.
- `inertia_B_kg_m2`: matriz de inercia respecto al centro de gravedad, expresada en FRD. Debe ser 3x3, finita, simetrica y definida positiva.
- `gravity_m_s2`: gravedad positiva en magnitud. Si falta, se usa `9.81`; si se proporciona, debe ser positiva.
- `linear_drag_coefficient`: coeficientes de drag lineal por eje de cuerpo, en `N/(m/s)`. Puede ser escalar o vector de tres componentes; todos los valores deben ser finitos y no negativos.
- `rotors`: lista de cuatro rotores. El mezclador actual exige exactamente cuatro.

Campos de cada rotor:

- `position_B_m`: posicion del rotor en cuerpo FRD respecto al centro de gravedad. Debe tener tres componentes finitas.
- `turning_direction`: signo `1` o `-1` para el par de reaccion de yaw.
- `k_f`: coeficiente de empuje, `N/(rad/s)^2`. Debe ser positivo.
- `k_m`: coeficiente de par, `Nm/(rad/s)^2`. Debe ser finito y no negativo.
- `omega_max_rad_s`: velocidad angular maxima del rotor. Debe ser positiva.
- `time_constant_s`: constante de tiempo del lag de primer orden aplicado sobre `omega`. Debe ser finita y no negativa.
- `delay_s`: retardo puro antes del lag. Si falta, se usa `0.0`; si se proporciona, debe ser finito y no negativo.

## `initial_state`

```yaml
initial_state:
  position_W_m: [2, 0, 5]
  velocity_W_m_s: [0, 0, 0]
  yaw_rad: 0.0
  orientation_WB: null
  angular_velocity_B_rad_s: [0, 0, 0]
```

- `position_W_m`: posicion inicial en mundo ENU. Debe tener tres componentes finitas.
- `velocity_W_m_s`: velocidad inicial en mundo ENU. Debe tener tres componentes finitas.
- `orientation_WB`: cuaternion inicial `[w, x, y, z]`. Si es `null`, se genera una actitud nivelada. Si se proporciona, debe ser finito y unitario dentro de una tolerancia pequena; el cargador no normaliza cuaterniones iniciales invalidos.
- `yaw_rad`: guiñada usada solo cuando `orientation_WB: null`. `yaw_rad = 0` significa que el frente del dron apunta al Norte (`Y_W`).
- `angular_velocity_B_rad_s`: velocidad angular inicial en cuerpo FRD. Debe tener tres componentes finitas.

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

### Lemniscate

Trayectoria en forma de ocho (Lemniscata de Gerono) en el plano horizontal `X_W-Y_W` con altura constante. Incluye un mecanismo de suavizado (warmup) para evitar discontinuidades de velocidad y orientación al inicio de la simulación.

```yaml
trajectory:
  type: "lemniscate"
  center_W_m: [0, 0, 2.0]
  a: 2.0
  b: 1.0
  omega_rad_s: 0.5
  yaw_mode: "forward"
  warmup_s: 3.0
```

- `center_W_m`: centro de la trayectoria.
- `a`: semi-eje mayor en `X_W`.
- `b`: semi-eje menor en `Y_W`.
- `omega_rad_s`: velocidad angular de avance de la referencia.
- `yaw_mode`: si es `"forward"`, la guiñada sigue la dirección de avance (tangente a la trayectoria); cualquier otro valor la mantiene en `0.0`.
- `warmup_s`: duración en segundos de la fase de calentamiento/suavizado (default: `3.0`). Durante esta fase, la referencia se interpola suavemente usando un polinomio cúbico de Hermite desde el estado estacionario inicial hasta la trayectoria nominal.

### Line / Waypoint

Misión discreta de alcanzar puntos con parada controlada en cada uno. En el YAML puede declararse como `line` o `waypoint`; ambos nombres cargan el mismo comportamiento `waypoint_stop`.

Esta trayectoria es **state-aware**: la referencia no avanza por tiempo global, sino que planifica un perfil de movimiento (trapezoidal o triangular) hacia el siguiente punto y espera a que el vehículo se asiente antes de saltar al siguiente tramo.

```yaml
trajectory:
  type: "line"
  waypoints:
    - [0, 0, 0]
    - [0, 0, 2]
    - [2, 0, 2]
  yaw_rad: 0.0
  max_speed_m_s: 0.6
  max_acceleration_m_s2: 0.5
  waypoint_tolerance_m: 0.20
  waypoint_speed_tolerance_m_s: 0.20
  dwell_time_s: 0.40
```

- `waypoints`: lista de posiciones en mundo ENU.
- `yaw_rad`: guiñada constante de la referencia. Si falta, se usa `0.0`.
- `max_speed_m_s`: velocidad máxima del perfil (default: `0.6`).
- `max_acceleration_m_s2`: aceleración máxima del perfil (default: `0.5`).
- `waypoint_tolerance_m`: distancia máxima al objetivo para considerar llegada (default: `0.20`).
- `waypoint_speed_tolerance_m_s`: velocidad máxima permitida para considerar asentamiento (default: `0.20`).
- `dwell_time_s`: tiempo que debe permanecer dentro de las tolerancias antes de avanzar (default: `0.40`).
- `times`: **deprecated**. Lista legacy de tiempos asociada a waypoints. Si aparece, debe tener la misma longitud que `waypoints`; se acepta por compatibilidad pero no gobierna el avance entre waypoints.

**Comportamiento:**
1. **MOVE_TO_WAYPOINT**: Genera un perfil de velocidad suave hacia el siguiente waypoint.
2. **HOLD_AT_WAYPOINT**: Una vez que el perfil llega al destino, la referencia se queda fija y espera a que el vehículo cumpla los criterios de posición, velocidad y tiempo de permanencia (`dwell`).
3. **SWITCH_SEGMENT**: Solo tras cumplir `dwell`, se avanza al siguiente tramo.

**Terminación:** Cuando se completa el último waypoint de la lista, el episodio termina automáticamente con la causa `"Trajectory completed"`.

El avance de `line` / `waypoint` no depende de `times` ni de `termination.max_duration_s`; si el vehículo no consigue asentarse en un waypoint, la referencia permanece en ese punto hasta que cumpla las tolerancias o hasta que otra condición de terminación corte el episodio.

## `controller`

### Controlador clasico

```yaml
controller:
  type: "classic"
  Kp_pos: [2.0, 2.0, 5.0]
  Kd_pos: [1.0, 1.0, 2.0]
  Kp_att: [4.0, 4.0, 1.0]
  Kd_att: [1.5, 1.5, 0.5]
  max_body_moments_Nm: [2.0, 2.0, 0.5]
```

- `type`: `"classic"` para el controlador en cascada.
- `Kp_pos`: ganancias proporcionales de posicion por eje ENU. Si falta, se usa `[2.0, 2.0, 5.0]`.
- `Kd_pos`: ganancias derivativas de posicion por eje ENU. Si falta, se usa `[1.0, 1.0, 2.0]`.
- `Kp_att`: ganancias proporcionales de actitud por eje de cuerpo FRD. Si falta, se usa `[4.0, 4.0, 1.0]`.
- `Kd_att`: ganancias derivativas de actitud por eje de cuerpo FRD. Si falta, se usa `[1.5, 1.5, 0.5]`.
- `max_body_moments_Nm`: limites de momentos `[tau_x, tau_y, tau_z]` en FRD. Si falta, el controlador usa `[10.0, 10.0, 2.0]`.

El controlador clasico usa un bucle externo de posicion y un bucle interno de actitud. Las ganancias declaradas en YAML permiten fijar PIDs por familia de trayectoria para datasets clasicos; si se omiten, se conservan los defaults del controlador.

### Controlador neuronal

```yaml
controller:
  type: "neural"
  architecture: "gru"
  checkpoint_path: "data/neural_control/gru_v1/checkpoints/gru_best.pt"
  normalization_path: "data/neural_control/gru_v1/normalization.json"
  sequence_length: 20
  clip_to_classic_limits: true
  max_body_moments_Nm: [10.0, 10.0, 2.0]
  device: "auto"
```

- `type`: `"neural"` para cargar un modelo entrenado por imitacion.
- `architecture`: arquitectura del checkpoint. Debe ser `"mlp"`, `"gru"` o `"lstm"`.
- `checkpoint_path`: ruta al `.pt` entrenado.
- `normalization_path`: ruta al `normalization.json` guardado durante entrenamiento. Debe corresponder a la misma version de features que el checkpoint.
- `sequence_length`: longitud de ventana para GRU/LSTM. Si falta, se usa `20`. Para MLP se ignora.
- `clip_to_classic_limits`: si es `true`, limita las salidas de la red antes de pasarlas al mixer. Si falta, se usa `true`.
- `max_body_moments_Nm`: limites de momentos `[tau_x, tau_y, tau_z]` en FRD. Si falta, se usa `[10.0, 10.0, 2.0]`.
- `device`: `"auto"`, `"cpu"` o `"cuda"`. Si falta, `auto` usa CUDA cuando PyTorch la detecta.

El controlador neuronal devuelve el mismo contrato que el clasico: `collective_thrust_N` y `body_moments_Nm`. El empuje se limita a `0..mass_kg*gravity_m_s2*2.5` cuando `clip_to_classic_limits` esta activo. GRU/LSTM mantienen memoria interna; el runner llama a `reset()` al inicio de cada simulacion.

### Controlador neuronal en lazo externo

```yaml
controller:
  type: "neural_position"
  architecture: "gru"
  checkpoint_path: "data/neural_control/position_gru_v1/checkpoints/gru_best.pt"
  normalization_path: "data/neural_control/position_gru_v1/normalization.json"
  sequence_length: 20
  base_Kp_pos: [2.0, 2.0, 5.0]
  base_Kd_pos: [1.0, 1.0, 2.0]
  multiplier_clip: [0.25, 4.0]
  max_body_moments_Nm: [10.0, 10.0, 2.0]
  device: "auto"
```

- `type`: `"neural_position"` para usar una red como programador de ganancias del lazo externo.
- `architecture`, `checkpoint_path`, `normalization_path` y `sequence_length`: mismos criterios que en el controlador neuronal directo.
- `base_Kp_pos` y `base_Kd_pos`: ganancias base sobre las que se aplican los multiplicadores predichos. Si faltan, se usan los defaults mostrados.
- `multiplier_clip`: rango `[min, max]` aplicado a los multiplicadores tras `exp`. Si falta, se usa `[0.25, 4.0]`.
- `device`: `"auto"`, `"cpu"` o `"cuda"`. Si falta, `auto` usa CUDA cuando PyTorch la detecta.

En este modo la red no predice empuje ni momentos. Predice multiplicadores de `Kp_pos` y `Kd_pos`; el lazo interno de actitud sigue siendo clasico.

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

Los tres tiempos deben ser positivos. Entre actualizaciones del controlador se mantiene el ultimo comando mediante ZOH.

## `termination`

```yaml
termination:
  max_duration_s: 15.0
  z_min_m: 0.0
  max_attitude_angle_rad: 3.14
  max_saturation_duration_s: 5.0
```

- `max_duration_s`: duracion maxima del episodio. Debe ser positiva.
- `z_min_m`: limite inferior de altura en mundo ENU. Debe ser finito.
- `max_attitude_angle_rad`: inclinacion maxima permitida. Si falta, se usa `1.256`; si se proporciona, debe ser positiva.
- `max_saturation_duration_s`: tiempo maximo con saturacion persistente. Si falta, se usa `1.0`; si se proporciona, debe ser positivo.

El runner tambien tiene limites internos de posicion y velocidad, pero el CLI actual no los carga desde YAML.

## Validacion fisica v1

La validacion implementada en `src/simulador_quad/scenarios/schema.py` cubre parametros que pueden invalidar un resultado del TFG antes de simular:

- masa y gravedad positivas;
- inercia 3x3 finita, simetrica y definida positiva;
- drag escalar o vector `[3]`, finito y no negativo;
- exactamente cuatro rotores;
- posicion de rotor `[3]`, `turning_direction` en `{-1, 1}`, `k_f > 0`, `k_m >= 0`, `omega_max_rad_s > 0`, `time_constant_s >= 0` y `delay_s >= 0`;
- tiempos `physics_dt_s`, `control_dt_s`, `telemetry_dt_s` y `max_duration_s` positivos;
- estado inicial con vectores `[3]` finitos y cuaternion `orientation_WB` nulo o unitario;
- controlador clasico con ganancias `Kp_pos`, `Kd_pos`, `Kp_att`, `Kd_att` opcionales como vectores `[3]` finitos y no negativos;
- controlador neuronal con `checkpoint_path`, `normalization_path` y `architecture` validos;
- limites `controller.max_body_moments_Nm` opcionales como vector `[3]` finito y no negativo para controladores clasicos y neuronales.
- trayectorias `line` / `waypoint` con `waypoints` no vacio, cada waypoint como vector `[3]` finito, `times` legacy con longitud compatible si aparece, y parametros opcionales de velocidad/aceleracion/tolerancia/dwell fisicamente validos.

Ejemplo de error:

```text
Invalid vehicle.mass_kg: expected positive kg value, got -1.0
```

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
- `waypoint_clean.yaml`: Misión secuencial de puntos (`waypoint` / `line`) con perfil de velocidad limitado y parada controlada en cada waypoint.
- `neural_ood_lemniscate.yaml`: Trayectoria de lemniscata (`lemniscate`) para evaluacion OOD. Por defecto usa controlador clasico; puede ejecutarse con un checkpoint neuronal mediante `tools\run_neural_scenario.py`.

La clasificacion de estos escenarios como nominales, robustez o demostracion, junto con sus criterios de aceptacion, esta en `docs/simulador/validacion.md`.

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
