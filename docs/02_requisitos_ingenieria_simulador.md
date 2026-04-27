# Requisitos de Ingeniería del Simulador Cuadricóptero

## 1. Objetivo del simulador

El simulador debe modelar el movimiento de un cuadricóptero como un cuerpo rígido de seis grados de libertad y servir como banco de comparación entre un controlador clásico y un controlador neuronal entrenado por imitación.

El simulador debe ser suficientemente fiel para estudiar seguimiento de trayectorias, estabilidad, esfuerzo de control y sensibilidad ante perturbaciones simples. No pretende representar todos los efectos aerodinámicos de un vehículo real.

## 2. Alcance físico de la primera versión

La primera versión incluirá:

- Cuerpo rígido 6DOF.
- Orientación mediante cuaterniones unitarios.
- Integración numérica RK4.
- Actuadores de rotor con saturación y retardo o lag de primer orden.
- Perturbaciones simples: ruido de observación, viento externo simplificado y retardo o lag de actuadores.
- Control clásico de referencia.
- Control neuronal por imitación.
- Registro de telemetría y métricas.

La primera versión no incluirá:

- Aerodinámica formal detallada.
- Flapping de rotores.
- Arrastre parásito como modelo obligatorio.
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
m \dot{v}_W = F_{thrust,W} + F_{g,W} + F_{pert,W}
```

donde:

- `m` es la masa del vehículo.
- `F_thrust,W` es la fuerza de empuje transformada al Sistema mundo.
- `F_g,W = [0, 0, -mg]` en ENU.
- `F_pert,W` agrupa perturbaciones externas simplificadas.

En la primera versión, `F_pert,W` podrá representar viento simple o fuerzas externas equivalentes, pero no se documentará como modelo aerodinámico detallado.

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

## 8. Modelo de actuadores

El simulador deberá distinguir entre:

- Comando solicitado por el controlador.
- Comando efectivamente aplicado por los actuadores.

Cada rotor tendrá al menos:

- Posición en Sistema cuerpo.
- Sentido de giro.
- Empuje máximo.
- Constante de tiempo o modelo de lag de primer orden.

Se usará un modelo de lag de actuador discreto de primer orden:

```math
u_{k+1} = u_k + \alpha (u_{cmd,k} - u_k)
```

con:

```math
\alpha = 1 - e^{-\Delta t / \tau}
```

El valor aplicado debe registrarse en telemetría para medir esfuerzo real de control y saturaciones.

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

## 10. Integración numérica

El integrador oficial será Runge-Kutta de cuarto orden (RK4).

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

### 11.3 Viento simple

El viento podrá modelarse como perturbación externa simplificada. En la primera versión no deberá presentarse como aerodinámica completa. Deberá documentarse si actúa como velocidad externa, fuerza equivalente o perturbación directa.

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
- Paso de integración.
- Semilla aleatoria si aplica.

Los escenarios deberán ser suficientemente claros para comparar ambos controladores bajo las mismas condiciones.

## 15. Métricas obligatorias

La comparación entre control clásico y control neuronal deberá incluir, como mínimo:

- Error de seguimiento: RMSE, MAE y error máximo de posición.
- Esfuerzo de control: magnitud media y máxima de empuje y momentos, o comandos de rotor si están disponibles.
- Estabilidad: detección de divergencia, vuelco, pérdida de seguimiento o saturación persistente.
- Trazabilidad: identificación del escenario, controlador, parámetros y semilla usados.

Las métricas deberán presentarse junto con las condiciones experimentales que las generan.

## 16. Límites de validez

Los resultados del simulador serán válidos dentro del marco de hipótesis documentado:

- Cuerpo rígido.
- Parámetros físicos definidos por escenario.
- Sin aerodinámica formal en la primera versión.
- Perturbaciones simplificadas.
- Ausencia de sensores reales y estimador onboard completo.

El TFG deberá evitar extrapolar conclusiones a vuelo real si no se ha validado contra datos experimentales.

## 17. Trazabilidad mínima

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

## 18. Referencias iniciales

- Stevens, B. L., Lewis, F. L., & Johnson, E. N. (2015). *Aircraft Control and Simulation: Dynamics, Controls Design, and Autonomous Systems*. Wiley.
- Beard, R. W., & McLain, T. W. (2012). *Small Unmanned Aircraft: Theory and Practice*. Princeton University Press.
- Diebel, J. (2006). *Representing Attitude: Euler Angles, Unit Quaternions, and Rotation Vectors*. Stanford University.
- Hairer, E., Nørsett, S. P., & Wanner, G. (1993). *Solving Ordinary Differential Equations I: Nonstiff Problems*. Springer.
- Ross, S., Gordon, G., & Bagnell, D. (2011). A reduction of imitation learning and structured prediction to no-regret online learning. *Proceedings of AISTATS*.
