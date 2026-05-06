# Plan de Implementación del Simulador Cuadricóptero

## 1. Objetivo

Implementar la primera versión del simulador 6DOF de cuadricóptero definida en los documentos normativos del TFG:

- `docs/01_principios_tfg.md`
- `docs/02_requisitos_ingenieria_simulador.md`
- `docs/03_criterios_ingenieria_software.md`

Esta fase no implementa todavía el controlador neuronal ni su entrenamiento. Sí debe dejar preparados los contratos, escenarios, telemetría y métricas necesarios para comparar posteriormente el controlador clásico contra un controlador neuronal por imitación.

## 2. Alcance de esta fase

Incluido:

- Paquete Python del simulador.
- Dinámica 6DOF de cuerpo rígido.
- Sistemas de referencia ENU mundo y FRD cuerpo.
- Origen del cuerpo coincidente con el centro de gravedad.
- Actitud con cuaterniones.
- Integrador RK4.
- Drag lineal simplificado.
- Viento simple.
- Actuadores con velocidad de rotor `omega`, RPM de telemetría, lag de primer orden, retardo puro opcional y saturación.
- Relación cuadrática `T_i = k_f omega_i^2` y `Q_i = s_i k_m omega_i^2`.
- Mezclador para cuadricóptero con prioridad de actitud frente a empuje colectivo.
- Simulación multi-rate: física, control y telemetría.
- Retenedor de orden cero entre pasos de control.
- Trayectorias analíticas suaves.
- Controlador clásico en cascada.
- Escenarios YAML.
- Telemetría, métricas y condiciones de fin de episodio.
- CLI mínima para ejecutar escenarios.
- Pruebas de los puntos críticos.

No incluido:

- Entrenamiento neuronal.
- Inferencia neuronal real.
- Reinforcement learning.
- Waypoints con suavizado polinómico, minimum jerk o minimum snap.
- Aerodinámica formal más allá del drag lineal.
- Batería, sensores realistas, estimador onboard o contacto con el suelo.

## 3. Estructura propuesta

Crear una estructura simple orientada a ingeniería:

```text
src/simulador_quad/
  __init__.py
  app.py
  runner.py
  core/
    attitude.py
    contracts.py
    frames.py
  dynamics/
    rigid_body.py
    actuators.py
    mixer.py
    perturbations.py
  control/
    classic.py
    contract.py
  trajectories/
    analytic.py
    contract.py
  scenarios/
    loader.py
    schema.py
  telemetry/
    history.py
    export.py
  metrics/
    report.py
tests/
```

La estructura podrá ajustarse si simplifica el código, pero debe conservar la separación conceptual: núcleo físico, dinámica, control, trayectorias, escenarios, telemetría y métricas.

## 4. Fase 1: Base del proyecto

Entregables:

- `pyproject.toml` gestionado con `uv`.
- Dependencias iniciales: NumPy, SciPy si se justifica, Matplotlib, PyYAML y pytest.
- Paquete importable bajo `src/`.
- CLI mínima `simulador-quad` o equivalente.

Criterios:

- El proyecto debe instalarse y probarse con `uv`.
- No introducir dependencias adicionales sin documentarlas.
- El código debe usar nombres con unidades cuando aporte claridad.

## 5. Fase 2: Contratos y utilidades matemáticas

Implementar contratos de datos pasivos con `dataclasses`:

- `VehicleState`: `position_W_m`, `velocity_W_m_s`, `orientation_WB`, `angular_velocity_B_rad_s`, `time_s`.
- `VehicleParameters`: masa, inercia, gravedad, drag lineal, geometría de rotores.
- `RotorParameters`: posición, sentido de giro, `k_f`, `k_m`, `omega_max_rad_s`, constante de tiempo y retardo.
- `TrajectoryReference`: posición, velocidad, aceleración y yaw deseado.
- `ControlCommand`: empuje colectivo y momentos de cuerpo.
- `RotorCommand` y `RotorAppliedState`: comandos objetivo y valores aplicados.
- `TelemetrySample`.

Implementar en `core/attitude.py`:

- Normalización de cuaterniones.
- Producto de cuaterniones.
- Conjugado.
- Rotación cuerpo-mundo y mundo-cuerpo.
- Conversión de cuaternión a matriz de rotación.
- Error de actitud para el controlador clásico.

Pruebas:

- Norma de cuaternión conservada tras normalización.
- Rotaciones identidad.
- Signo de empuje ENU/FRD: con actitud identidad, `F_thrust_B = [0, 0, -T]` debe producir aceleración vertical positiva si `T > mg`.

## 6. Fase 3: Dinámica 6DOF e integrador RK4

Implementar la derivada del estado:

```text
dot(p_W) = v_W
m dot(v_W) = F_thrust_W + F_g_W + F_wind_W + F_drag_W
I_B dot(omega_B) = tau_B - omega_B x (I_B omega_B)
dot(q_WB) = 1/2 q_WB otimes [0, omega_B]
```

Hipótesis obligatorias:

- Mundo ENU.
- Cuerpo FRD.
- Origen cuerpo en el centro de gravedad.
- Tensor de inercia diagonal en v1, salvo que el escenario indique una matriz completa.

Implementar RK4 como único integrador oficial. Después de cada paso, normalizar o verificar el cuaternión.

Pruebas:

- Caída libre sin empuje.
- Hover ideal con `T = mg`.
- Conservación aproximada de orientación sin momentos ni velocidad angular.
- RK4 sobre un sistema simple con solución conocida.

## 7. Fase 4: Drag lineal y perturbaciones

Implementar drag lineal:

```text
v_rel_B = R_BW(q) (v_W - v_wind_W)
F_drag_B = -D_B v_rel_B
F_drag_W = R_WB(q) F_drag_B
```

Implementar viento simple:

- Viento constante por escenario.
- Opcionalmente ráfaga simple reproducible con semilla, si no complica la primera versión.

Implementar ruido de observación:

- Posición.
- Velocidad.
- Actitud o velocidad angular solo si se documentan magnitudes y unidades.

Pruebas:

- El drag debe oponerse a la velocidad relativa.
- Con velocidad relativa nula, el drag debe ser cero.
- El ruido debe ser reproducible con semilla.

## 8. Fase 5: Actuadores y mezclador

Implementar el flujo de actuadores:

1. El controlador produce `T, tau_x, tau_y, tau_z`.
2. El mezclador calcula empuje objetivo por rotor.
3. Cada empuje objetivo se convierte a `omega_cmd`.
4. Se aplica retardo puro opcional.
5. Se aplica lag de primer orden sobre `omega`.
6. Se saturan velocidades en `[0, omega_max]`.
7. Se calcula empuje y par aplicado con ley cuadrática.

El mezclador de cuadricóptero debe documentar la geometría, signos y matriz de asignación. La saturación debe priorizar roll/pitch/yaw frente al empuje colectivo cuando no sea posible cumplir todo simultáneamente.

Telemetría obligatoria:

- Comando solicitado.
- Empuje objetivo por rotor.
- `omega_cmd_rad_s`.
- `omega_applied_rad_s`.
- `rotor_speed_rpm`.
- Empuje aplicado por rotor.
- Flags de saturación y degradación.

Pruebas:

- `omega = sqrt(T/k_f)`.
- `T = k_f omega^2`.
- `Q = s k_m omega^2`.
- Saturación en `omega_max`.
- Lag de primer orden monotónico ante un escalón.
- Retardo puro de `N` pasos.

## 9. Fase 6: Multi-rate, runner y fin de episodio

Implementar un `SimulationRunner` con:

- `physics_dt_s`.
- `control_dt_s`.
- `telemetry_dt_s`.
- ZOH para mantener el último comando entre ciclos de control.
- Estado verdadero y observación separada.
- Terminación anticipada con causa explícita.

Condiciones mínimas de fin:

- `Z_W < 0`.
- Roll o pitch por encima del umbral del escenario.
- Posición o velocidad fuera de límites.
- Saturación persistente.
- Valores no finitos.

Pruebas:

- El controlador se ejecuta a `control_dt_s`, no a cada paso físico.
- La telemetría se guarda a `telemetry_dt_s`.
- ZOH mantiene comando constante entre actualizaciones.
- Cada condición de fin produce causa trazable.

## 10. Fase 7: Trayectorias analíticas suaves

Implementar trayectorias v1:

- `Hold`: mantener posición.
- `Line`: línea recta con velocidad acotada.
- `Circle`: círculo horizontal suave.
- `Lissajous` o trayectoria senoidal 3D simple.

Cada trayectoria debe devolver:

- Posición.
- Velocidad.
- Aceleración si está disponible.
- Yaw deseado.

No usar escalones de posición crudos como referencia principal. Los waypoints con suavizado quedan documentados como futuro.

Pruebas:

- Continuidad de posición y velocidad en trayectorias analíticas.
- Derivadas coherentes en casos simples.
- Referencias finitas para todo `t` dentro del escenario.

## 11. Fase 8: Control clásico

Implementar un controlador clásico en cascada:

- Bucle externo de posición: genera aceleración o fuerza deseada.
- Conversión de fuerza deseada a empuje colectivo y actitud deseada.
- Bucle interno de actitud: genera momentos de cuerpo.
- Saturaciones documentadas.

La interfaz debe ser:

```text
observación + referencia -> comando de control
```

Pruebas:

- En hover, el comando debe tender a `T = mg`.
- Errores de posición deben producir fuerzas con signo correcto.
- Momentos deben saturarse dentro de límites.

## 12. Fase 9: Escenarios YAML y CLI

Definir escenarios YAML con secciones mínimas:

```text
vehicle
initial_state
trajectory
controller
perturbations
timing
termination
output
seed
```

Crear al menos tres escenarios:

- Hover sin perturbaciones.
- Seguimiento de círculo con drag lineal.
- Seguimiento con viento simple, ruido y lag de actuador.

CLI mínima:

```text
simulador-quad run path/to/scenario.yaml
```

La CLI debe producir:

- Archivo de telemetría.
- Resumen de métricas.
- Código de salida no cero solo para errores de ejecución, no para fallo físico del episodio.

## 13. Fase 10: Telemetría, métricas y reporte

Implementar exportación a formato simple:

- JSON para trazabilidad y lectura humana.
- NPZ opcional si el volumen de datos lo requiere.

Métricas obligatorias:

- RMSE, MAE y error máximo de posición.
- Esfuerzo de control.
- Velocidades máximas de rotor.
- Porcentaje de tiempo en saturación.
- Causa y tiempo de terminación si aplica.
- Identificación de escenario, controlador, parámetros y semilla.

Pruebas:

- Métricas correctas en señales sintéticas.
- Exportación incluye metadatos suficientes para reproducir el escenario.

## 14. Criterios de aceptación global

La implementación se considerará lista cuando:

- `uv run pytest` pase.
- Existan escenarios YAML reproducibles.
- El escenario de hover se mantenga estable sin perturbaciones.
- La telemetría registre estado, referencia, observación, comando solicitado, comando aplicado y velocidades de rotor.
- Las métricas permitan comparar controladores aunque aún solo exista el clásico.
- Las convenciones ENU/FRD estén verificadas por pruebas.
- La documentación del código cubra funciones físicas importantes, no funciones triviales.

## 15. Orden recomendado de trabajo

1. Crear proyecto Python con `uv` y estructura base.
2. Implementar contratos y cuaterniones.
3. Implementar dinámica 6DOF y RK4.
4. Añadir drag lineal y perturbaciones.
5. Implementar actuadores y mezclador.
6. Implementar runner multi-rate con ZOH.
7. Añadir trayectorias analíticas.
8. Implementar controlador clásico.
9. Añadir escenarios YAML y CLI.
10. Añadir telemetría, métricas y pruebas de integración.

## 16. Riesgos principales

- Signos incorrectos por la combinación ENU/FRD.
- Saturación del mezclador que destruya autoridad de actitud.
- Comparaciones no reproducibles por semillas o escenarios incompletos.
- Trayectorias físicamente agresivas que generen saturación constante.
- Mezclar código de entrenamiento neuronal antes de estabilizar el simulador.

Cada riesgo debe cubrirse con pruebas, telemetría o documentación explícita.
