# Auditoria de control e ingenieria aeroespacial

Fecha: 2026-05-04  
Alcance: revision del repositorio desde la perspectiva de un TFG cuyo objetivo es comparar control clasico y futuro control neuronal por imitacion.  
Restriccion aplicada: no se modifica codigo fuente ni tests; solo se crea este reporte.

## Base normativa revisada

- `AGENTS.md`: mantiene el foco en simulador 6DOF de cuadricoptero, comparativa clasico-neuronal por imitacion, trazabilidad y codigo cientifico simple.
- `docs/01_principios_tfg.md`: exige comparacion trazable y reproducible, separacion entre ingenieria fisica/control e ingenieria software, alcance limitado y declaracion de limitaciones.
- `docs/02_requisitos_ingenieria_simulador.md`: fija ENU/FRD, empuje en `-Z_B`, estado 6DOF, RK4 multi-rate, actuadores con lag sobre `omega`, mixer, escenarios, terminacion y metricas obligatorias.
- `docs/03_criterios_ingenieria_software.md`: exige contratos de datos claros, escenarios YAML, telemetria suficiente, pruebas de puntos fisicos criticos y preparacion para controlador neuronal en igualdad de condiciones.

## Verificacion ejecutada

- `uv run pytest`
- Resultado: 29 tests pasados.

Esto confirma que la base actual no esta rota funcionalmente, pero no elimina los riesgos de validez fisica, trazabilidad experimental y preparacion de la comparativa neuronal descritos abajo.

## Dictamen ejecutivo

El repositorio ya tiene una base razonable para una primera fase del TFG: separa estado, actitud, dinamica, actuadores, mixer, controlador clasico, escenarios, runner, telemetria y metricas. Tambien implementa convenciones ENU/FRD de forma visible, RK4, multi-rate, ruido de observacion, viento constante, drag lineal, saturacion de actuadores y terminacion de episodios.

El principal riesgo no es de estructura, sino de validez academica de la comparativa: el controlador clasico tiene ganancias fijadas en codigo, la interfaz de escenarios solo admite `classic`, no existe todavia dataset ni controlador neuronal cargable, y algunas metricas agregan magnitudes fisicamente heterogeneas. Ademas, hay puntos de control y trayectoria que necesitan documentacion o ajustes antes de usar sus salidas como "experimento defendible" en memoria.

## Hallazgos priorizados

### P1 - La comparativa clasico-neuronal aun no es ejecutable ni cerrada en bucle

**Evidencia.**

- El contrato comun existe como `Controller.compute_control(time_s, obs_state, reference) -> ControlCommand` en `src/simulador_quad/control/contract.py:4`.
- El cargador de escenarios solo acepta `controller.type == "classic"` y rechaza cualquier otro tipo en `src/simulador_quad/scenarios/loader.py:81`.
- La documentacion viva declara explicitamente que el controlador neuronal, dataset, entrenamiento y evaluacion en bucle cerrado no estan implementados en `docs/simulador/README.md:23`.
- La busqueda en `src/` no muestra modulos de dataset, entrenamiento, normalizacion ni inferencia neuronal.

**Riesgo academico/tecnico.**  
El TFG puede defender la fase de simulador clasico, pero todavia no puede defender la comparacion final que el objetivo normativo exige. Si se generan resultados ahora, solo son baseline clasico, no comparativa. Si se introduce una red despues sin fijar antes entradas, salidas, normalizacion y escenarios, habra riesgo de comparacion no reproducible o sesgada.

**Recomendacion concreta.**

- Mantener el alcance: no introducir entrenamiento neuronal hasta estabilizar baseline.
- Antes de entrenar, congelar un contrato de imitacion: observacion usada, referencia usada, accion objetivo (`collective_thrust_N`, `body_moments_Nm` o comandos de rotor), normalizacion, frecuencia de muestreo, semillas, escenarios train/val/test y evaluacion cerrada.
- Extender el cargador con un tipo neuronal solo cuando exista un artefacto cargable y evaluable por el mismo `SimulationRunner`, no como script aparte.

### P1 - Las ganancias del controlador clasico no son trazables por escenario

**Evidencia.**

- `Kp_pos`, `Kd_pos`, `Kp_att`, `Kd_att`, `max_thrust` y valores por defecto de momentos estan fijados en `src/simulador_quad/control/classic.py:12`.
- El YAML solo permite `type` y opcionalmente `max_body_moments_Nm`, documentado en `docs/simulador/escenarios_yaml.md:172`.
- El cargador solo pasa `max_body_moments_Nm` al controlador en `src/simulador_quad/scenarios/loader.py:81`.

**Riesgo academico/tecnico.**  
Las metricas exportan el escenario completo, pero no las ganancias reales salvo por inspeccion del codigo. Esto debilita la reproducibilidad experimental: una ejecucion no queda completamente definida por el YAML si las ganancias relevantes viven solo en la implementacion. Tambien complica comparar una red entrenada para imitar un experto concreto, porque el "experto" no queda identificado como configuracion experimental.

**Recomendacion concreta.**

- Declarar ganancias y saturaciones del controlador clasico en YAML o exportarlas siempre a `metrics.metadata`.
- Versionar el baseline experto usado para generar dataset de imitacion.
- Documentar ecuaciones y ganancias en la memoria, vinculadas a escenarios concretos.

### P1 - La trayectoria waypoint usa smoothstep C1, pero la aceleracion es discontinua entre tramos

**Evidencia.**

- `LineTrajectory` usa `s = 3 tau^2 - 2 tau^3`, con velocidad cero en waypoints, en `src/simulador_quad/trajectories/analytic.py:81`.
- La aceleracion se calcula como `dds = 6 - 12*tau` y cambia de signo bruscamente en los extremos de cada tramo en `src/simulador_quad/trajectories/analytic.py:104`.
- El requisito normativo pide trayectorias analiticas suaves o referencias filtradas y no escalones crudos como referencia principal para entrenamiento/comparacion.

**Riesgo academico/tecnico.**  
La trayectoria no es un escalon crudo, pero tampoco es suave en aceleracion. Para control en cascada con feedforward de aceleracion y para imitacion neuronal, esa discontinuidad puede generar acciones expertas con saltos, saturaciones o muestras dificilmente interpretables como comportamiento deseable.

**Recomendacion concreta.**

- Usar `hold`, `circle` y `lissajous` como escenarios principales de comparacion inicial.
- Mantener `waypoint` como escenario secundario o cambiarlo a minimum-jerk/quintico antes de usarlo para dataset o comparativa principal.
- Documentar explicitamente que la variante actual es C1, no C2.

### P2 - Las metricas de esfuerzo mezclan unidades fisicas en una sola magnitud

**Evidencia.**

- `control_effort = abs(thrust_N) + norm(body_moments_Nm)` en `src/simulador_quad/metrics/report.py:25`.
- Se registran maxima velocidad de rotor, saturacion y degradacion, pero no medias/maximos separados de empuje colectivo, momentos por eje, empuje aplicado total o energia/proxy fisico.

**Riesgo academico/tecnico.**  
Sumar newtons y newton-metro produce un indicador sin unidad fisica clara. Puede ser util como proxy interno, pero no debe presentarse como metrica aeroespacial principal. Para comparar clasico contra neuronal, una red podria parecer "mejor" o "peor" por una magnitud agregada arbitraria.

**Recomendacion concreta.**

- Mantener RMSE/MAE/max error de posicion.
- Separar esfuerzo en: empuje colectivo medio/max, norma de momentos media/max, momentos por eje, rotor speed media/max, porcentaje de saturacion y degradacion.
- Si se usa una magnitud compuesta, declararla como indice adimensional normalizado por limites fisicos.

### P2 - La estrategia de saturacion del mixer necesita validacion fisica mas fuerte

**Evidencia.**

- El mixer documenta que prioriza actitud frente a empuje en `src/simulador_quad/dynamics/mixer.py:5`.
- La asignacion usa `tau_x = -y_i T_i`, `tau_y = x_i T_i`, `tau_z = s_i (k_m/k_f) T_i` en `src/simulador_quad/dynamics/mixer.py:16`.
- La degradacion se marca con un booleano `degraded_collective_thrust` en `src/simulador_quad/dynamics/mixer.py:79`.
- Las pruebas cubren hover, pitch y un caso de saturacion en `tests/test_mixer.py:21`.

**Riesgo academico/tecnico.**  
La matriz de asignacion es interpretable, pero la politica de degradacion no cuantifica cuanto empuje o momento se pierde. Para un TFG, no basta con saber que "degrado": conviene medir el comando solicitado frente al alcanzable. Esto afecta directamente a estabilidad y esfuerzo de control.

**Recomendacion concreta.**

- Registrar comando alcanzado reconstruido desde los empujes objetivo: `M @ T_req`.
- Exportar error de asignacion: empuje solicitado-aplicado objetivo y momentos solicitados-aplicados objetivo.
- Ampliar validacion con casos de roll, yaw, combinaciones de ejes y saturacion extrema.

### P2 - El controlador clasico es interpretable, pero su formulacion debe cerrarse en documentacion de control

**Evidencia.**

- La cascada posicion-actitud esta implementada en `src/simulador_quad/control/classic.py:27`.
- El feedforward de aceleracion se suma en `src/simulador_quad/control/classic.py:32`.
- La actitud deseada se construye alineando `-Z_B` con la fuerza deseada en `src/simulador_quad/control/classic.py:47`.
- La guiñada usa la convencion `yaw=0 -> Front = Norte` en `src/simulador_quad/control/classic.py:59`, coherente con `src/simulador_quad/core/frames.py:16`.
- Los momentos incluyen realimentacion PD y feedforward giroscopico `omega x I omega` en `src/simulador_quad/control/classic.py:95`.

**Riesgo academico/tecnico.**  
El controlador parece defendible como baseline, pero la memoria debera explicar claramente signos, yaw, construccion de ejes deseados y limitaciones. Sin esa explicacion, la comparativa neuronal imitaria una caja negra clasica con convenciones no evidentes.

**Recomendacion concreta.**

- Documentar ecuaciones del controlador en una seccion tecnica: error de posicion, fuerza deseada, construccion de `R_des`, error de cuaternion, ley de momentos y saturaciones.
- Anadir una tabla de convenciones de signo para roll, pitch, yaw y relacion con ENU/FRD.
- Declarar limitaciones: no hay integral, no hay planificador dinamico, no hay feedforward de yaw rate, no hay estimador.

### P2 - Los limites de episodio no son completamente configurables desde YAML

**Evidencia.**

- `SimulationRunner` admite `max_position_m` y `max_velocity_m_s` en `src/simulador_quad/runner.py:21`.
- El CLI/cargador solo pasa `max_duration_s`, `z_min_m`, `max_attitude_angle_rad` y `max_saturation_duration_s` en `src/simulador_quad/app.py:21`.
- La documentacion lo declara como limite actual en `docs/simulador/escenarios_yaml.md:230`.

**Riesgo academico/tecnico.**  
Una comparativa puede terminar por limites implicitos que no estan en el YAML. Esto reduce reproducibilidad y dificulta explicar por que un controlador falla en una trayectoria agresiva.

**Recomendacion concreta.**

- Pasar todos los criterios de terminacion usados por el runner desde YAML o exportarlos siempre como metadatos efectivos.
- En tablas de resultados, reportar causa, instante y estado final asociado.

### P2 - El ruido de observacion solo afecta posicion/velocidad; actitud y velocidad angular quedan ideales

**Evidencia.**

- `ObservationNoise.apply_noise` solo perturba `position_W_m` y `velocity_W_m_s` en `src/simulador_quad/dynamics/perturbations.py:42`.
- En el runner, la orientacion y velocidad angular observadas se copian del estado verdadero en `src/simulador_quad/runner.py:153`.

**Riesgo academico/tecnico.**  
Esto esta dentro del alcance simplificado si se declara, pero es relevante para aprendizaje por imitacion: la red recibira una observacion parcialmente ideal, y los resultados no deben presentarse como robustez ante sensores reales.

**Recomendacion concreta.**

- Declarar en escenarios y memoria que el ruido actual afecta solo posicion/velocidad.
- No extraer conclusiones de robustez sensorial general.
- Si se amplia, hacerlo como perturbacion simple documentada, no como estimador onboard.

### P3 - La telemetria es buena, pero falta trazabilidad de codigo/artefacto de ejecucion

**Evidencia.**

- `TelemetrySample` agrupa estado, observacion, referencia, comando, rotor objetivo y rotor aplicado en `src/simulador_quad/core/contracts.py:57`.
- `app.py` guarda `scenario_name`, `seed` y `config` completa en `metrics.metadata` en `src/simulador_quad/app.py:48`.
- No se observa registro de version del paquete, commit git, comando CLI ni version de Python/uv.

**Riesgo academico/tecnico.**  
Para una memoria de TFG puede ser suficiente en fase inicial, pero una comparativa final con entrenamiento neuronal necesita trazabilidad mas fuerte: dataset, modelo, normalizacion, commit y entorno.

**Recomendacion concreta.**

- Incluir en metricas: version del paquete, commit git si esta disponible, comando ejecutado y versiones principales.
- Para neuronal: guardar ruta/hash del modelo, arquitectura, normalizacion y dataset de entrenamiento.

### P3 - Dependencias: `plotly` aporta visualizacion pero no aparece en la politica normativa inicial

**Evidencia.**

- `pyproject.toml:10` incluye `plotly>=6.7.0`.
- La politica normativa lista NumPy, SciPy, Matplotlib, PyTorch y PyYAML como base aceptable.
- La documentacion viva indica visor 3D interactivo basado en Plotly en `docs/simulador/arquitectura.md:37`.

**Riesgo academico/tecnico.**  
No es un problema fisico ni de control, pero conviene justificar la dependencia para no parecer desviacion de alcance.

**Recomendacion concreta.**

- Documentar Plotly como dependencia de visualizacion postproceso, no del nucleo de simulacion/control.
- Mantener resultados y metricas independientes de Plotly.

## Aspectos solidos observados

- Convenciones fisicas explicitas en contratos: posicion/velocidad en ENU, velocidad angular y momentos en FRD, cuaternion `[w, x, y, z]` (`src/simulador_quad/core/contracts.py:5`).
- Actitud nivelada ENU/FRD documentada en codigo, con `yaw=0` apuntando al Norte (`src/simulador_quad/core/frames.py:16`).
- Dinamica 6DOF con gravedad ENU, fuerza de cuerpo a mundo, drag lineal y ecuacion rotacional Newton-Euler (`src/simulador_quad/dynamics/rigid_body.py:5`).
- RK4 con normalizacion de cuaternion al final del paso (`src/simulador_quad/dynamics/rigid_body.py:52`).
- Actuadores aplican saturacion, retardo y lag sobre `omega`, despues calculan `T_i = k_f omega_i^2` y `Q_i = s_i k_m omega_i^2` (`src/simulador_quad/dynamics/actuators.py:43`).
- Runner multi-rate con ZOH: el controlador se actualiza a `control_dt_s` y la fisica avanza a `physics_dt_s` (`src/simulador_quad/runner.py:151`).
- Escenarios YAML incluyen vehiculo, estado inicial, trayectoria, controlador, perturbaciones, tiempos, terminacion y salida (`scenarios/hover_clean.yaml:1`).
- Tests cubren puntos criticos: actitud, dinamica, actuadores, mixer, runner, perturbaciones, metricas y trayectorias.

## Recomendaciones por area auditada

### Arquitectura de control

- Mantener la interfaz conceptual actual `observacion + referencia -> ControlCommand`.
- Hacer configurables las ganancias del experto clasico antes de generar dataset.
- Documentar el controlador como baseline academico, no como autopiloto industrial.

### Contratos de controlador

- Definir ya el vector de observacion neuronal aunque no se implemente la red: estado observado, referencia instantanea, posibles errores relativos y unidades.
- Decidir si la red imita comandos de alto nivel `(T, tau_B)` o salidas ya mezcladas. Para comparacion justa y trazable, se recomienda imitar `(T, tau_B)` y reutilizar el mismo mixer/actuadores.
- Registrar frecuencia de inferencia neuronal igual a `control_dt_s`.

### Mixer

- Mantener la formulacion fisica actual, pero exportar el comando reconstruido desde rotores objetivo.
- Documentar signos de `tau_x`, `tau_y`, `tau_z` con un esquema FRD.
- No ampliar a geometrias arbitrarias salvo necesidad real del TFG; el cuadricoptero de 4 rotores es suficiente.

### Actuadores

- La decision de aplicar lag sobre `omega` es correcta respecto a los requisitos.
- Registrar saturacion como "comando objetivo recortado" y "estado aplicado cerca del limite" de forma separada si se van a analizar saturaciones finas.
- Mantener retardo puro opcional como cola discreta; documentar el redondeo `delay_s / dt_s`.

### Escenarios y reproducibilidad

- Usar un conjunto pequeno y estable de escenarios canonicos: hover, circulo con drag, circulo con viento/ruido, lissajous suave.
- Separar escenarios de entrenamiento, validacion y test cuando llegue la imitacion neuronal.
- Evitar `waypoint` actual como fuente principal de entrenamiento hasta suavizar aceleracion.
- Exportar todos los limites efectivos de terminacion, no solo los definidos en YAML.

### Trayectorias

- `hold`, `circle` y `lissajous` son adecuadas para baseline inicial.
- `line/waypoint` necesita aclaracion de suavidad C1 o sustitucion por minimum jerk/quintica si se usa como caso principal.
- Mantener referencias con posicion, velocidad y aceleracion como ya hace `TrajectoryReference`.

### Metricas

- Separar metricas con unidades fisicas claras.
- Incluir error por eje ademas de norma de posicion si se quieren analizar efectos de viento lateral o acoplamientos.
- Incluir resumen de fallo: causa, tiempo, posicion, velocidad, actitud/inclinacion y saturacion acumulada.
- Para neuronal, exigir evaluacion cerrada en el simulador, no solo perdida supervisada.

### Preparacion para imitacion neuronal

- Congelar el experto clasico y sus escenarios antes de generar datos.
- Guardar cada muestra con: observacion, referencia, accion experta, accion objetivo de rotor opcional, accion aplicada opcional, semilla, escenario y tiempo.
- Calcular normalizacion solo con train y guardar estadisticas.
- Dividir por escenarios o episodios completos, no por muestras mezcladas aleatoriamente, para evitar fuga temporal.
- Evaluar la red en los mismos escenarios de test que el clasico, con mismas perturbaciones y semillas.

## Riesgos academicos si se usa el estado actual como resultado final

1. Presentar una comparativa neuronal inexistente o solo supervisada, incumpliendo el objetivo de evaluacion en bucle cerrado.
2. No poder reproducir exactamente el experto clasico por tener ganancias fijadas solo en codigo.
3. Usar metricas de esfuerzo sin unidad fisica clara como argumento principal.
4. Entrenar imitacion con trayectorias no suficientemente suaves o con discontinuidades de aceleracion.
5. Concluir robustez ante perturbaciones cuando el ruido solo afecta posicion/velocidad y no hay sensores/estimador realistas.

## Cierre

El repositorio esta bien encaminado como simulador clasico trazable de primera version. Para convertirlo en un TFG solido de comparacion entre control clasico y control neuronal por imitacion, el siguiente paso no deberia ser ampliar fisica ni introducir aerodinamica compleja, sino cerrar trazabilidad experimental: ganancias del experto, contratos de datos neuronales, escenarios canonicos, metricas con unidades fisicas y evaluacion cerrada comun.
