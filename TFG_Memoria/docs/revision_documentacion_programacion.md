# Revisión de la documentación de programación

## Alcance de la revisión

Se han contrastado `README.md`, `docs/02_requisitos_ingenieria_simulador.md`,
`docs/03_criterios_ingenieria_software.md` y la documentación viva de
`docs/simulador/`. La exploración dirigida del código se ha realizado mediante
la CLI `grok` y se han verificado los elementos necesarios en las rutas
señaladas.

## Correspondencia general

La documentación describe correctamente el flujo principal:

1. Un escenario YAML define vehículo, trayectoria, controlador, perturbaciones,
   tiempos y salidas.
2. `app.run_simulation()` carga y valida el escenario.
3. `SimulationRunner` ejecuta el ciclo multirrate de referencia, observación,
   control, mezclador, actuadores, telemetría e integración RK4.
4. La ejecución exporta telemetría, métricas y metadatos reproducibles.
5. Las herramientas de campaña generan datasets, ajustan controladores,
   entrenan redes y consolidan comparaciones.

Las convenciones ENU/FRD, las ecuaciones 6DOF, los actuadores, el mezclador, las
perturbaciones y las métricas mantienen una trazabilidad clara entre requisitos,
código, pruebas y escenarios.

## Aspectos especialmente útiles para la memoria

- `docs/02_requisitos_ingenieria_simulador.md` contiene la formulación física y
  las ecuaciones que deben desarrollarse en el apartado metodológico del
  simulador.
- `docs/simulador/arquitectura.md` ofrece el flujo real de una simulación y los
  contratos de datos principales.
- `docs/simulador/trazabilidad.md` permite justificar cada decisión mediante
  código, pruebas, escenarios y métricas.
- `docs/simulador/dataset_clasico.md` y `control_neuronal.md` describen la cadena
  experimental desde los controladores congelados hasta la comparación de
  predicción de fuerza deseada.
- `results/comparison_summary.csv` contiene la comparación consolidada de
  controladores clásicos y redes MLP, GRU y LSTM en prueba y fuera de la
  distribución de entrenamiento.

## Riesgos y decisiones narrativas

### Hipótesis experimental y niveles de evaluación

La hipótesis central debe formularse como la posibilidad de condensar un banco
de controladores PD especializados en una política neuronal común, mantener un
desempeño competitivo y mejorar la transferencia frente a los PD aplicados fuera
de su familia. La evidencia implementada permite separar cuatro niveles:

1. prueba en familias conocidas;
2. transferencia cruzada de los controladores PD;
3. variaciones y composiciones de capacidades conocidas;
4. trayectorias completamente nuevas.

La memoria y las visualizaciones no deben agrupar los dos últimos niveles bajo
una única media fuera de la distribución de entrenamiento.

### Denominación PID frente a implementación PD

El controlador clásico se denomina PID en escenarios, herramientas y resultados,
pero su formulación actual utiliza términos proporcionales y derivativos, sin
término integral. Se ha acordado describirlo técnicamente como PD en cascada y
conservar PID solo al identificar nombres heredados de escenarios, herramientas
o artefactos.

### Alcance de los controladores neuronales

La comparación principal incluye controladores de predicción de fuerza deseada
MLP, GRU y LSTM; las tres arquitecturas forman parte del trabajo.
`neural_position`, que predice
log-multiplicadores, y el entrenamiento `outer_force_full_v1` con 31 variables
están implementados, pero quedan fuera del alcance experimental principal por
ahora.

### Experto de fuerza deseada

El experto seleccionado genera las demostraciones y sirve como referencia
supervisada, pero no aparece como baseline cerrado en
`results/comparison_all_runs.csv`. No debe presentarse como controlador de la
tabla comparativa principal salvo que se regenere la evidencia correspondiente.

### Evidencia local y estado Git

Los datasets masivos, checkpoints y telemetrías se conservan localmente, mientras
que Git contiene manifiestos y tablas consolidadas. Antes de cerrar resultados se
debe verificar que los artefactos finales proceden de una misma revisión y que
los metadatos no registran un árbol sucio o un commit distinto.

### Generalización

Los splits `train`, `val` y `test` mantienen las mismas familias de trayectorias;
por tanto, `test` mide rendimiento dentro de la distribución de entrenamiento.
Las afirmaciones de generalización deben apoyarse en la batería separada fuera
de distribución.

### Éxito de misión y seguridad

La documentación distingue correctamente `mission_success` de
`safety_success`. La memoria debe conservar esta separación, especialmente en
trayectorias finitas donde alcanzar el límite temporal no implica completar la
misión.

## Decisiones implementadas que todavía requieren justificación

La documentación y el código permiten describir las siguientes decisiones, pero
no aportan todavía una defensa académica o una explicación suficiente del
autor:

- masa, inercia, geometría y coeficientes de propulsión del vehículo;
- número concreto de geometrías, perfiles, episodios y ratios de partición;
- pesos, umbrales, multiplicadores y presupuesto de la búsqueda progresiva;
- límite de actitud de terminación, inclinación neuronal máxima, factor de
  empuje y componente vertical mínima;
- elección de nueve variables frente a las 31 disponibles;
- tamaño oculto, longitud de secuencia, tamaño de lote, tasa de aprendizaje y
  paciencia de parada temprana.

Estos elementos deben tratarse como preguntas explícitas del guion y no como
constantes que puedan presentarse sin explicación.

## Fragmentos de código recomendados

Los siguientes fragmentos son suficientemente breves y explicativos para el
cuerpo de la memoria:

- `src/simulador_quad/dynamics/rigid_body.py`: correspondencia entre ecuaciones
  6DOF y marcos ENU/FRD.
- `src/simulador_quad/control/classic.py::compute_desired_force_W`: lazo externo
  clásico y compensación gravitatoria.
- `src/simulador_quad/ml/dataset.py`: definición de entradas mínimas y objetivo
  de fuerza deseada.
- `tools/generate_outer_force_dataset.py`: criterio reproducible de selección
  del experto.
- `src/simulador_quad/metrics/success.py`: diferencia entre completar una misión
  y terminar de forma segura.

El resto de la implementación debe referenciarse mediante el repositorio, sin
convertir la memoria en documentación exhaustiva del código.

## Visualizaciones comparativas disponibles

El repositorio permite generar comparaciones de RMSE, tasa de éxito,
transferencia cruzada, seguimiento frente a esfuerzo, saturación, clipping y
distribuciones de error. La selección final debe incluir además:

- un mapa de calor de transferencia de controladores PD;
- resultados separados para composiciones y trayectorias nuevas;
- una comparación entre error supervisado de fuerza y rendimiento de posición
  en bucle cerrado;
- una tabla síntesis que responda cada pregunta experimental.
