# Requisitos de Ingeniería del Simulador Cuadricóptero

## 1. Objetivo del simulador

El simulador debe modelar el movimiento de un cuadricóptero como un cuerpo rígido de seis grados de libertad y servir como banco de comparación entre un controlador clásico y un controlador neuronal entrenado por imitación.

El simulador debe ser suficientemente fiel para estudiar seguimiento de trayectorias, estabilidad, esfuerzo de control y sensibilidad ante perturbaciones simples. No pretende representar todos los efectos aerodinámicos de un vehículo real.

## 2. Alcance físico de la primera versión

La primera versión incluirá:

- Cuerpo rígido 6DOF.
- Orientación mediante cuaterniones unitarios.
- Integración numérica RK4.
- Simulación multi-rate con paso de física, control y telemetría separados.
- Actuadores de rotor con velocidad de giro, saturación, retardo puro opcional y lag de primer orden.
- Relación cuadrática entre velocidad de rotor y empuje/par.
- Perturbaciones simples: ruido de observación, viento externo simplificado, retardo o lag de actuadores y drag lineal.
- Control clásico de referencia.
- Control neuronal por imitación.
- Registro de telemetría y métricas.

La primera versión no incluirá:

- Aerodinámica formal detallada más allá del drag lineal simplificado.
- Flapping de rotores.
- Arrastre parásito cuadrático o modelo aerodinámico identificado.
- Pérdidas inducidas.
- Dinámica de batería.
- Contacto con el suelo.
- Estimador onboard completo.

## 3. Sistemas de referencia

El simulador adoptará dos sistemas de referencia principales.

### 3.1 Sistema inercial mundo: ENU

El Sistema mundo será ENU:

- Eje `X_W`: Este.
- Eje `Y_W`: Norte.
- Eje `Z_W`: arriba.

La posición y la velocidad lineal del vehículo se expresarán en este Sistema.

### 3.2 Sistema cuerpo: FRD

El Sistema cuerpo será FRD:

- Eje `X_B`: hacia delante del vehículo.
- Eje `Y_B`: hacia la derecha del vehículo.
- Eje `Z_B`: hacia abajo del vehículo.

La velocidad angular del vehículo se expresará en el Sistema cuerpo.

### 3.3 Convención de empuje

Como el eje `Z_B` apunta hacia abajo, el empuje sustentador de los rotores actúa en dirección `-Z_B`. Esta convención debe aparecer de forma explícita en las ecuaciones, en la implementación y en las pruebas.

Si `T` es el empuje colectivo positivo, la fuerza de empuje en cuerpo será:

```text
F_thrust_B = [0, 0, -T]
```

La fuerza en mundo se obtendrá mediante la matriz de rotación asociada al cuaternión:

```text
F_thrust_W = R_WB(q) F_thrust_B
```

### 3.4 Origen del sistema cuerpo

El origen del sistema cuerpo se asumirá coincidente con el centro de gravedad del cuadricóptero. Esta hipótesis permite usar directamente las ecuaciones de Newton-Euler para un cuerpo rígido con dinámica rotacional alrededor del CG.

Si en una versión futura el origen geométrico del vehículo y el centro de gravedad no coinciden, deberán añadirse los términos de acoplamiento correspondientes y documentarse el uso del teorema de ejes paralelos.

## 4. Estado del vehículo

El estado físico mínimo del vehículo será:

```text
x = (p_W, v_W, q_WB, omega_B)
```

donde:

- `p_W` es la posición en Sistema mundo, en metros.
- `v_W` es la velocidad lineal en Sistema mundo, en m/s.
- `q_WB` es el cuaternión unitario que representa la orientación cuerpo respecto al mundo.
- `omega_B` es la velocidad angular en Sistema cuerpo, en rad/s.

El tiempo de simulación se tratará como parte del estado extendido o como variable del integrador, pero siempre deberá quedar registrado en telemetría.

## 5. Cinemática de actitud

La actitud se representará mediante cuaterniones unitarios para evitar singularidades asociadas a ángulos de Euler.

La ecuación cinemática de actitud será:

```math
\dot{q}_{WB} = \frac{1}{2} q_{WB} \otimes [0, \omega_B]
```

donde `\otimes` representa el producto de cuaterniones y `[0, omega_B]` es el cuaternión puro asociado a la velocidad angular.

Después de cada paso de integración, el cuaternión deberá normalizarse o verificarse para conservar la condición:

```math
\|q_{WB}\| = 1
```

## 6. Dinámica translacional

La dinámica translacional se expresará en Sistema mundo:

```math
\dot{p}_W = v_W
```

```math
m \dot{v}_W = F_{thrust,W} + F_{g,W} + F_{wind,W} + F_{drag,W}
```

donde:

- `m` es la masa del vehículo.
- `F_thrust,W` es la fuerza de empuje transformada al Sistema mundo.
- `F_g,W = [0, 0, -mg]` en ENU.
- `F_wind,W` representa perturbaciones externas simplificadas asociadas al viento.
- `F_drag,W` representa un drag lineal simple.

El drag lineal se calculará como amortiguamiento proporcional a la velocidad relativa respecto al aire. En marco cuerpo:

```math
v_{rel,B} = R_{BW}(q)(v_W - v_{wind,W})
```

```math
F_{drag,B} = -D_B v_{rel,B}
```

donde `D_B` será una matriz diagonal positiva o semidefinida positiva con unidades de `N/(m/s)`. La fuerza se transformará al marco mundo mediante:

```math
F_{drag,W} = R_{WB}(q)F_{drag,B}
```

Este término se considera un modelo de amortiguamiento lineal simplificado. No deberá presentarse como aerodinámica formal ni como arrastre identificado experimentalmente.

## 7. Dinámica rotacional

La dinámica rotacional se expresará en Sistema cuerpo:

```math
I_B \dot{\omega}_B = \tau_B - \omega_B \times (I_B \omega_B)
```

donde:

- `I_B` es el tensor de inercia en Sistema cuerpo.
- `tau_B` es el vector de momentos aplicados en cuerpo.
- `omega_B` es la velocidad angular del cuerpo.

La primera versión podrá asumir tensor de inercia diagonal si esta hipótesis se declara en el escenario y en la documentación.

La ecuación anterior asume que el origen del sistema cuerpo coincide con el centro de gravedad. Bajo esta hipótesis, los momentos `tau_B` se aplican alrededor del CG.

## 8. Modelo de actuadores

El simulador deberá distinguir entre:

- Intención solicitada por el controlador: empuje colectivo y momentos.
- Empuje objetivo por rotor tras el mezclador.
- Velocidad objetivo de rotor.
- Velocidad de rotor efectivamente aplicada tras retardo, lag y saturación.
- Empuje y par realmente aplicados.

Cada rotor tendrá al menos:

- Posición en Sistema cuerpo.
- Sentido de giro.
- Coeficiente de empuje `k_f`, en `N/(rad/s)^2`.
- Coeficiente de par `k_m`, en `Nm/(rad/s)^2`.
- Velocidad máxima `omega_max`, en `rad/s`.
- Constante de tiempo o modelo de lag de primer orden.
- Retardo puro opcional, expresado como tiempo o número de pasos de control.

El mezclador calculará un empuje objetivo por rotor `T_{cmd,i}`. A partir de ese empuje se obtendrá una velocidad angular objetivo:

```math
\omega_{cmd,i} = \sqrt{\max(T_{cmd,i}, 0)/k_f}
```

La velocidad objetivo se saturará en:

```math
0 \leq \omega_{cmd,i} \leq \omega_{max,i}
```

El lag de primer orden se aplicará sobre la velocidad angular del rotor, no directamente sobre el empuje:

Se usará un modelo de lag de actuador discreto de primer orden:

```math
\omega_{k+1} = \omega_k + \alpha (\omega_{cmd,k} - \omega_k)
```

con:

```math
\alpha = 1 - e^{-\Delta t / \tau}
```

El empuje y el par aplicados por cada rotor serán:

```math
T_i = k_f \omega_i^2
```

```math
Q_i = s_i k_m \omega_i^2
```

donde `s_i` es el sentido de giro del rotor. Si se registra la velocidad en RPM, se usará únicamente como magnitud de telemetría o visualización:

```math
RPM_i = \omega_i \frac{60}{2\pi}
```

El valor solicitado, objetivo y aplicado debe registrarse en telemetría para medir esfuerzo real de control, saturaciones y efecto de los retardos.

## 9. Mezclador de control

El controlador podrá generar una intención de alto nivel:

```text
u = (T, tau_x, tau_y, tau_z)
```

El mezclador convertirá esa intención en comandos de rotor. La matriz de asignación deberá documentar:

- Posición de cada rotor.
- Signo de los momentos de roll, pitch y yaw.
- Convención de empuje compatible con FRD.
- Saturaciones aplicadas.

Cuando el número de rotores o la geometría lo requiera, podrá resolverse mediante mínimos cuadrados o pseudoinversa, siempre que la formulación quede documentada.

La estrategia de saturación deberá quedar fijada. En la primera versión se priorizará mantener los momentos de actitud frente al empuje colectivo cuando no sea posible satisfacer simultáneamente todos los comandos. Si una demanda requiere superar `omega_max`, el mezclador deberá reducir o redistribuir el empuje colectivo antes de aceptar una pérdida severa de autoridad en roll o pitch. Las saturaciones y cualquier degradación de comando deberán registrarse en telemetría.

## 10. Integración numérica

El integrador oficial será Runge-Kutta de cuarto orden (RK4).

La simulación tendrá tres escalas temporales explícitas:

- `physics_dt_s`: paso del integrador RK4.
- `control_dt_s`: periodo de actualización del controlador y de la observación usada por este.
- `telemetry_dt_s`: periodo de guardado de muestras de telemetría.

El integrador podrá ejecutar varios subpasos de física por cada paso de control. Entre dos actualizaciones del controlador, el comando aplicado al modelo físico se mantendrá mediante un retenedor de orden cero (ZOH). Esta separación permite estudiar efectos de muestreo y retardo sin cambiar el integrador oficial.

Para una ecuación diferencial:

```math
\dot{x} = f(t, x, u)
```

el paso RK4 se define como:

```math
k_1 = f(t_k, x_k, u_k)
```

```math
k_2 = f(t_k + \Delta t/2, x_k + \Delta t k_1/2, u_k)
```

```math
k_3 = f(t_k + \Delta t/2, x_k + \Delta t k_2/2, u_k)
```

```math
k_4 = f(t_k + \Delta t, x_k + \Delta t k_3, u_k)
```

```math
x_{k+1} = x_k + \frac{\Delta t}{6}(k_1 + 2k_2 + 2k_3 + k_4)
```

No se incluirán otros integradores como rutas oficiales de simulación en la primera versión. Si se usan cálculos auxiliares o pruebas simples, no deberán confundirse con el integrador del simulador.

## 11. Perturbaciones de la primera versión

Las perturbaciones admitidas inicialmente serán:

### 11.1 Ruido de observación

El controlador podrá recibir una observación distinta del estado verdadero. El ruido deberá documentar:

- Variables afectadas.
- Distribución usada.
- Magnitud o desviación típica.
- Semilla aleatoria si aplica.

### 11.2 Retardo o lag de actuadores

El comando aplicado podrá retrasarse o filtrarse respecto al comando calculado por el controlador. Deberá registrarse tanto el comando solicitado como el aplicado.

El retardo puro y el lag de primer orden se tratarán como fenómenos distintos:

- Retardo puro: `u_aplicado(t) = u_solicitado(t - t_delay)`.
- Lag de primer orden: respuesta dinámica suave del rotor sobre `omega`.

El retardo puro podrá implementarse como una cola de `N` pasos de control. Si está desactivado, deberá indicarse explícitamente en el escenario.

### 11.3 Viento simple

El viento podrá modelarse como perturbación externa simplificada. En la primera versión no deberá presentarse como aerodinámica completa. Deberá documentarse si actúa como velocidad externa, fuerza equivalente o perturbación directa.

### 11.4 Drag lineal

El drag lineal será parte del modelo base de la primera versión. Su objetivo es evitar dinámicas translacionales no acotadas en maniobras sostenidas y representar una disipación mínima del movimiento relativo con el aire.

Este término deberá parametrizarse por escenario mediante `D_B` o coeficientes equivalentes por eje. No se considerará una identificación aerodinámica real del fuselaje.

## 12. Control clásico

El control clásico será el controlador de referencia para:

- Generar datos de entrenamiento por imitación.
- Servir como baseline experimental.
- Proporcionar una comparación interpretable.

El diseño esperado será un controlador en cascada, con un bucle externo de posición y un bucle interno de actitud, salvo modificación posterior justificada.

El documento final deberá incluir:

- Ecuaciones del controlador.
- Ganancias usadas.
- Saturaciones.
- Relación entre referencia, error y comando.
- Limitaciones del controlador.

## 13. Control neuronal por imitación

El controlador neuronal se entrenará para imitar acciones generadas por el controlador clásico.

El conjunto de datos deberá documentar:

- Escenarios usados para generar muestras.
- Variables de entrada.
- Variables objetivo.
- Normalización.
- División entrenamiento/validación/test.
- Semillas.
- Métrica de entrenamiento.

La evaluación no deberá limitarse a error supervisado de entrenamiento. El controlador neuronal deberá evaluarse cerrando el bucle dentro del simulador.

## 14. Escenarios de simulación

Cada escenario deberá definir:

- Estado inicial.
- Trayectoria o referencia.
- Parámetros físicos del vehículo.
- Parámetros de control.
- Perturbaciones activadas.
- Duración.
- `physics_dt_s`, `control_dt_s` y `telemetry_dt_s`.
- Semilla aleatoria si aplica.

Los escenarios deberán ser suficientemente claros para comparar ambos controladores bajo las mismas condiciones.

El formato recomendado para escenarios será YAML, por legibilidad, soporte de comentarios y facilidad para declarar configuraciones jerárquicas. Un escenario deberá separar, como mínimo, las secciones de vehículo, condiciones iniciales, trayectoria, controlador, perturbaciones, tiempos de simulación y salida de resultados.

Las trayectorias de la primera versión deberán ser analíticas y suaves, o referencias explícitamente filtradas, de forma que incluyan posición y, cuando aplique, velocidad y aceleración de referencia. No se usarán escalones de posición crudos como referencia principal para entrenamiento o comparación. Las trayectorias por waypoints con suavizado polinómico, minimum jerk o minimum snap quedan como extensión posterior.

## 15. Condiciones de fin de episodio

Aunque la primera versión no modele contacto con el suelo, el simulador deberá detener un episodio y marcarlo como fallo si se cumplen condiciones de seguridad o validez.

Condiciones mínimas:

- Altura no válida: `Z_W < 0`.
- Actitud excesiva: roll o pitch por encima de un umbral documentado.
- Divergencia de posición o velocidad fuera de límites del escenario.
- Saturación persistente de actuadores durante un intervalo definido.
- Valores no finitos en estado, comandos o métricas.

Cada terminación anticipada deberá registrarse en telemetría con una causa explícita.

## 16. Métricas obligatorias

La comparación entre control clásico y control neuronal deberá incluir, como mínimo:

- Error de seguimiento: RMSE, MAE y error máximo de posición.
- Esfuerzo de control: magnitud media y máxima de empuje, momentos, velocidades de rotor y saturaciones.
- Estabilidad: detección de divergencia, vuelco, pérdida de seguimiento o saturación persistente.
- Terminación de episodio: causa, instante y estado asociado si se produce fallo.
- Trazabilidad: identificación del escenario, controlador, parámetros y semilla usados.

Las métricas deberán presentarse junto con las condiciones experimentales que las generan.

## 17. Límites de validez

Los resultados del simulador serán válidos dentro del marco de hipótesis documentado:

- Cuerpo rígido.
- Parámetros físicos definidos por escenario.
- Sin aerodinámica formal más allá de drag lineal simplificado.
- Perturbaciones simplificadas.
- Ausencia de sensores reales y estimador onboard completo.

El TFG deberá evitar extrapolar conclusiones a vuelo real si no se ha validado contra datos experimentales.

## 18. Trazabilidad mínima

Cada requisito de ingeniería deberá poder vincularse con:

- Una sección del documento técnico.
- Una parte del software.
- Al menos una prueba o escenario de validación.
- Una métrica o criterio de aceptación.

Ejemplo de trazabilidad:

```text
Requisito: usar cuaterniones para actitud.
Justificación: evitar singularidades de Euler.
Software: módulo de actitud / estado del vehículo.
Prueba: conservación de norma del cuaternión.
Resultado: simulaciones sin singularidad de orientación.
```

## 19. Referencias iniciales

- Stevens, B. L., Lewis, F. L., & Johnson, E. N. (2015). *Aircraft Control and Simulation: Dynamics, Controls Design, and Autonomous Systems*. Wiley.
- Beard, R. W., & McLain, T. W. (2012). *Small Unmanned Aircraft: Theory and Practice*. Princeton University Press.
- Diebel, J. (2006). *Representing Attitude: Euler Angles, Unit Quaternions, and Rotation Vectors*. Stanford University.
- Hairer, E., Nørsett, S. P., & Wanner, G. (1993). *Solving Ordinary Differential Equations I: Nonstiff Problems*. Springer.
- Ross, S., Gordon, G., & Bagnell, D. (2011). A reduction of imitation learning and structured prediction to no-regret online learning. *Proceedings of AISTATS*.
