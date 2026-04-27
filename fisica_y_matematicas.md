# Documentación de Ingeniería, Física y Matemáticas del Simulador Multirotor

## 1. Dinámica del Cuerpo Rígido (6 Grados de Libertad)
El simulador modela el dron como un cuerpo rígido utilizando las ecuaciones de Newton-Euler, integradas numéricamente con el método de Runge-Kutta de 4to orden (RK4).

### 1.1 Representación del Estado
- **Posición ($p$) y Velocidad Lineal ($v$)**: Referenciadas en el marco inercial (World frame).
- **Orientación ($q$)**: Representada mediante un cuaternión unitario $q = (w, x, y, z)$ para evitar el bloqueo del cardán (*gimbal lock*).
- **Velocidad Angular ($\omega$)**: Expresada en el marco del cuerpo (Body frame).

### 1.2 Ecuaciones de Movimiento Traslacional
La aceleración lineal en el marco inercial se calcula como:
$$ a = \frac{1}{m} \left( F_{empuje\_world} + F_{gravedad\_world} + F_{arrastre\_world} \right) $$
Donde:
- $m$: Masa del vehículo.
- $F_{gravedad\_world} = [0, 0, -m \cdot g]$
- El empuje efectivo incluye la pérdida inducida (explicada en aerodinámica) y es rotado al marco inercial usando el cuaternión de orientación $q$.

### 1.3 Ecuaciones de Movimiento Rotacional (Euler)
La aceleración angular en el marco del cuerpo considera el acoplamiento giroscópico:
$$ \dot{\omega} = I^{-1} \left( \tau_{cmd} - \omega \times (I \omega) \right) $$
Donde:
- $I$: Matriz de inercia diagonal $(I_{xx}, I_{yy}, I_{zz})$.
- $\tau_{cmd}$: Torques de comando aplicados sobre el cuerpo.

### 1.4 Integración Numérica (RK4)
Se utiliza el método RK4 con un paso de tiempo $dt$ sobre $p$ y $v$.
Para la **orientación**, la cinemática del cuaternión se actualiza usando el mapa exponencial:
$$ \Delta q = \left( \cos\left(\frac{||\omega|| dt}{2}\right), \frac{\vec{\omega}}{||\omega||} \sin\left(\frac{||\omega|| dt}{2}\right) \right) $$
$$ q_{t+dt} = q_t \otimes \Delta q $$

---

## 2. Sistema de Actuación y Mezclador (Rotor Mixer)

### 2.1 Modelo Dinámico del Rotor
El motor no responde instantáneamente. Se modela como un filtro de paso bajo de primer orden sobre la velocidad de rotación del motor $\omega_m$ (rad/s):
- **Cálculo de velocidad objetivo**: $\omega_{target} = \sqrt{\frac{T_{target}}{C_T}}$
- **Avance temporal discreto**: $\omega_m(t+dt) = \omega_m(t) + \alpha (\omega_{target} - \omega_m(t))$
  Donde $\alpha = 1 - e^{-dt / \tau}$ ($\tau$ es la constante de tiempo del motor).
- **Saturación**: La velocidad $\omega_m$ se satura en $[0, \omega_{m, max}]$.
- **Fuerza de Empuje generada**: $T_{real} = C_T \cdot \omega_m^2$
- **Torque de reacción**: $\tau_{reaccion} = C_Q \cdot T_{real} \cdot \text{dir\_giro}$ (donde $\text{dir\_giro} \in \{-1, 1\}$).

### 2.2 Mezclador de Control (Allocation Matrix)
El controlador pide un empuje colectivo ($F_z$) y torques ($M_x, M_y, M_z$). El mezclador distribuye esto a $N$ rotores resolviendo un sistema sobredeterminado por mínimos cuadrados (`np.linalg.lstsq`).

La matriz de asignación se construye por columnas para cada rotor $i$:
$$ \text{Col}_i = \begin{bmatrix} 1 \\ y_i \\ -x_i \\ \text{dir\_giro}_i \cdot C_Q \end{bmatrix} $$
*Nota: Los rotores asumen su eje alineado al eje $Z$ del cuerpo.*

Los empujes individuales resultantes se limitan (clamp) al empuje máximo físico de cada rotor.

---

## 3. Aerodinámica y Entorno

### 3.1 Modelo de Viento (Ornstein-Uhlenbeck)
El viento se compone de una base determinista más un proceso estocástico (ráfagas). Para asegurar que la varianza de la ráfaga sea independiente del tamaño de paso $dt$, se usa una actualización discreta exacta de Ornstein-Uhlenbeck:
$$ V_{gust}(t+dt) = V_{gust}(t) \cdot e^{-dt / \tau_w} + \sigma_w \sqrt{1 - e^{-2 dt / \tau_w}} \cdot \mathcal{N}(0, 1) $$
Donde $\tau_w$ es el tiempo de correlación del viento y $\sigma_w$ su desviación estándar estacionaria.

### 3.2 Arrastre Parasitario (Parasitic Drag)
Calculado usando la velocidad relativa del aire en el marco inercial ($V_{rel} = V_{dron} - V_{viento}$):
$$ F_{drag} = -\frac{1}{2} \rho \cdot A_{drag} \cdot ||V_{rel}|| \cdot V_{rel} $$

### 3.3 Pérdida Inducida en Vuelo Estacionario (Induced Hover Loss)
A mayor empuje generado, aumenta la pérdida inducida (efecto de deflexión del flujo). Se modela empíricamente como una fuerza opuesta al empuje ($Z$ negativo en body-frame):
$$ F_{inducida} = \left( \text{ratio\_perdida} \cdot T \cdot \frac{T}{T_{max}} \right) $$

---

## 4. Controladores en Cascada (PID)

El sistema de control básico (`cascade.py`) emplea un esquema en cascada que transforma referencias de trayectoria en comandos de motor.

### 4.1 Bucle de Posición (Translacional)
Un controlador PD toma el error de posición y velocidad:
$$ a_{deseada} = K_p (p_{ref} - p) + K_d (v_{ref} - v) + a_{ref\text{ (feedforward)}} $$
Se calcula la fuerza requerida en el espacio inercial compensando la gravedad:
$$ F_{deseada\_world} = m \cdot \begin{bmatrix} a_{des, x} \\ a_{des, y} \\ a_{des, z} + g \end{bmatrix} $$
- **Empuje colectivo comandado**: $T_{cmd} = ||F_{deseada\_world}||$
- **Actitud deseada**: La dirección del empuje es $Z_{body} = F_{deseada\_world} / T_{cmd}$. Con esto y el ángulo guiñada ($\psi_{ref}$) de la trayectoria, se extrae el cuaternión deseado resolviendo un marco ortonormal (Producto cruzado de $Z_{body}$ y la proyección de $\psi_{ref}$).

### 4.2 Bucle de Actitud (Rotacional)
Calcula el error de actitud como el arco más corto entre cuaterniones: $e_q = q_{deseado} \otimes q_{actual}^*$. Este error en cuaternión se mapea a un vector de rotación de 3 ejes.
El comando de torque resulta de otro PD:
$$ \tau_{cmd} = K_{p\_att} \cdot e_{rotacion} + K_{d\_\omega} \cdot (\omega_{deseada} - \omega_{actual}) $$
*(Actualmente la referencia de velocidad angular $\omega_{deseada} = [0,0,0]$)*

**Saturaciones**:
- El empuje $T_{cmd}$ se limita a $[0, T_{max}]$.
- Los torques $\tau_{cmd}$ se limitan independientemente a $[-\tau_{max}, \tau_{max}]$.

---

## 5. Generación Matemática de Trayectorias
La familia de trayectorias evaluadas analíticamente respecto al tiempo ($t$) incluye:

- **Línea Recta (Straight)**:
  $p(t) = p_{start} + v \cdot t$
- **Círculo (Circle)**:
  $p(t) = [c_x + R \cos(\theta), \ c_y + R \sin(\theta), \ c_z]$ con $\theta = \theta_0 + \omega t$.
  La velocidad es la derivada exacta $v(t) = [-R \omega \sin(\theta), R \omega \cos(\theta), 0]$.
- **Espiral (Spiral)**:
  Una hélice cónica con radio cambiante $R(t) = R_0 + \dot{r}t$ y ascenso constante.
- **Curva Paramétrica (ParametricCurve)**:
  Avanza a velocidad constante $v_x$, mientras oscila senoidalmente en lateral ($Y$) y vertical ($Z$) de manera independiente.
- **Lissajous**:
  Oscilaciones armónicas simples desacopladas en los tres ejes: $p_i(t) = c_i + A_i \sin(\omega_i t + \phi_i)$ para $i \in \{x,y,z\}$.

**Guiñada (Yaw)**: Para la mayoría de perfiles dinámicos, si no se especifica el ángulo deseado, éste se acopla tangencialmente a la dirección del vector de velocidad temporal $\psi(t) = \text{atan2}(v_y, v_x)$.
