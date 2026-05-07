# Arquitectura actual

El simulador esta organizado como codigo cientifico simple. Las carpetas separan conceptos fisicos y experimentales, no capas abstractas.

## Flujo de simulacion

1. `app.py` recibe `simulador-quad run <escenario.yaml>`.
2. `scenarios.loader` lee el YAML e instancia vehiculo, rotores, estado inicial, trayectoria, controlador, viento y ruido.
3. `SimulationRunner` inicializa tiempos de fisica, control y telemetria.
4. En cada ciclo:
   - obtiene la referencia de trayectoria para `time_s`;
   - genera la observacion, con ruido si aplica;
   - llama al controlador cuando toca `control_dt_s`;
   - convierte empuje/momentos a comandos de rotor mediante el mezclador;
   - aplica retardo, lag y saturacion en actuadores;
   - guarda telemetria cuando toca `telemetry_dt_s`;
   - avanza el estado con RK4 usando `physics_dt_s`.
5. El episodio termina por limite de tiempo o por una condicion de seguridad/validez.
6. Se exportan `telemetry.json` y `metrics.json`.
7. Se generan automáticamente figuras PNG y el visor interactivo `visualization_3d.html`.

## Modulos principales

- `core/contracts.py`: dataclasses de estado, parametros, referencias, comandos, rotores y telemetria.
- `core/attitude.py`: operaciones de cuaterniones y rotacion entre cuerpo y mundo.
- `core/frames.py`: actitud nivelada inicial ENU/FRD.
- `dynamics/rigid_body.py`: derivada 6DOF e integrador RK4.
- `dynamics/actuators.py`: retardo, lag, saturacion, empuje y par aplicado por rotores.
- `dynamics/mixer.py`: asignacion de empuje colectivo y momentos a empujes de rotor.
- `dynamics/perturbations.py`: drag lineal, viento constante y ruido de observacion.
- `trajectories/analytic.py`: referencias `hold`, `circle`, `lissajous` y `line`.
- `control/classic.py`: controlador clasico en cascada.
- `runner.py`: orquestacion multi-rate, ZOH, telemetria y terminacion.
- `telemetry/export.py`: exportacion JSON.
- `metrics/report.py`: metricas agregadas con magnitudes fisicas separadas por unidades.
- `visualization/plots.py`: figuras PNG a partir de `telemetry.json`.
- `visualization/three_d.py`: visor interactivo HTML 3D basado en Plotly.

## Contratos de datos

Los contratos relevantes para interpretar resultados son:

- `VehicleState`: estado verdadero u observacion del controlador.
- `TrajectoryReference`: referencia instantanea de posicion, velocidad, aceleracion y yaw.
- `ControlCommand`: empuje colectivo y momentos de cuerpo solicitados por el controlador.
- `RotorCommand`: empuje y `omega` objetivo por rotor, mas bandera de degradacion.
- `RotorAppliedState`: `omega`, RPM, empuje, par y saturacion realmente aplicados.
- `TelemetrySample`: muestra que agrupa estado, observacion, referencia, control y rotores.

La telemetria distingue comando solicitado, comando objetivo de rotor y estado aplicado. Esta separacion es importante para estudiar saturacion, retardos y lag de actuadores.

## Telemetria

Cada muestra de `telemetry.json` contiene:

- `time_s`
- `state`
- `observation`
- `reference`
- `control`
- `rotors`
- `termination_cause`

`state` es el estado verdadero del simulador. `observation` es lo que vio el controlador; puede diferir por ruido. `reference` es la trayectoria deseada. `control` es la salida del controlador. `rotors` separa objetivo y aplicado.

## Metricas

`metrics.json` resume:

- error de posicion: RMSE, MAE, maximo y desviacion tipica;
- empuje colectivo solicitado por el controlador en N: media, maximo, minimo y desviacion tipica;
- norma de momentos de cuerpo solicitados en Nm: media, maximo y desviacion tipica;
- indice heuristico de esfuerzo `|T| + ||tau||`, conservado por compatibilidad y solo apto para diagnostico;
- maxima velocidad de rotor en `rad/s` y RPM;
- tiempo y porcentaje de saturacion;
- tiempo y porcentaje de degradacion de empuje colectivo;
- causa de terminacion y duracion;
- metadatos de reproducibilidad: escenario, semilla, controlador, comando, version del paquete, Python/plataforma, estado Git, hashes de escenario/`uv.lock`, configuracion original y configuracion efectiva con defaults.

Las metricas no sustituyen a la inspeccion de telemetria. Para explicar un resultado en la memoria, conviene combinar `metrics.json` con las figuras generadas automaticamente y el visor 3D interactivo. Las comparaciones fisicas deben apoyarse en campos con unidades explicitas; el indice heuristico no debe presentarse como esfuerzo fisico total porque suma N y Nm.

## Limites actuales

- Solo hay controlador clasico estable en la interfaz de escenarios.
- Las ganancias del controlador clasico estan fijadas en codigo.
- El viento es constante.
- El ruido de observacion afecta solo a posicion y velocidad.
- El CLI no carga limites de posicion o velocidad desde YAML.
- La visualización es postproceso y automática tras cada ejecución exitosa.
