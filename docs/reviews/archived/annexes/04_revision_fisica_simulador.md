# Reporte de Revisión: Física e Ingeniería del Simulador

Tras un análisis exhaustivo de los documentos proporcionados (`01_principios_tfg.md`, `02_requisitos_ingenieria_simulador.md` y `03_criterios_ingenieria_software.md`), el planteamiento general es muy sólido, claro y bien acotado. Sin embargo, desde el punto de vista del modelado físico, la dinámica y la simulación realista de sistemas de control, existen varios puntos críticos que no están cubiertos o presentan ambigüedades.

## 1. Definición y formato de los "datos" de configuración
La documentación pide que los escenarios sean "declarativos" (Doc 03, Sec 11), pero no estipula cómo. Separar el código de los parámetros es vital.

**Valoración de formatos:**
*   **JSON:** Muy estricto, no soporta comentarios (crítico para documentar unidades, ej. `mass: 1.5 // kg`). *Descartado.*
*   **Python (.py o dataclasses directamente instanciadas):** Útil porque permite usar `np.pi`, `math.radians()`, etc. Pero mezcla código y configuración, haciendo que la configuración no sea puramente declarativa y sea más difícil de parsear por herramientas externas de experimentación.
*   **TOML:** Excelente para configuraciones anidadas planas, muy popular en el ecosistema Python moderno, pero puede volverse verboso con matrices o listas multidimensionales (como matrices de inercia o secuencias de waypoints).
*   **YAML:** **Recomendado.** Soporta comentarios nativamente, es extremadamente legible para un ingeniero no informático, maneja listas y diccionarios fácilmente y es el estándar de facto en robótica (ej. ROS/ROS2 usan YAML para parámetros).

**Falta definir:** La decisión final del formato (ej. YAML) y la estructura base de este archivo (ej. sección de propiedades del vehículo, sección de condiciones iniciales, configuración del controlador).

## 2. Separación de frecuencias (Multi-rate Simulation)
Actualmente el documento asume un único paso de integración ($\Delta t$) para avanzar el sistema continuo. En un dron real (y en un simulador útil), existen al menos tres frecuencias desacopladas que deben definirse:

1.  **Frecuencia de Simulación/Física ($f_{sim}$):** Ritmo al que opera el integrador RK4. Suele ser alto (500 Hz - 1000 Hz) para mantener la estabilidad numérica.
2.  **Frecuencia de Control ($f_{ctrl}$):** Ritmo al que se ejecutan los cálculos del controlador clásico o neuronal y al que se capturan las observaciones. Un piloto automático real opera típicamente entre 100 Hz y 250 Hz.
3.  **Frecuencia de Telemetría/Log ($f_{log}$):** Frecuencia a la que se guardan los datos a disco (ej. 50 Hz). Guardar al ritmo de simulación generaría archivos inmensos y ralentizaría la simulación de episodios enteros.

**Impacto Físico:** El simulador necesitará un mecanismo de **Retenedor de Orden Cero (ZOH)**. El comando de control se calcula una vez cada ciclo de control y debe mantenerse constante para el integrador físico durante múltiples subpasos de integración RK4.

## 3. Definición de las Trayectorias
El término "Generar una referencia de trayectoria" (Doc 03, Sec 5) es excesivamente ambiguo. El control neuronal por imitación es muy sensible a referencias que son físicamente imposibles de seguir.

**Falta definir el mecanismo de generación:**
*   ¿Serán **Puntos de paso (waypoints)** independientes, formas paramétricas?
*   Si son waypoints, ¿se aplicará un **interpolador polinómico** (ej. *Minimum Snap / Minimum Jerk*) para asegurar continuidad en las derivadas (velocidad y aceleración)?
*   Alternativamente, ¿se utilizará un **Modelo de Referencia (Reference Model)** puro? Es decir, al recibir un "escalón" de comando de posición por parte del usuario, el generador lo pasa por un filtro de paso bajo de 2º orden crítico para dar referencias suaves y físicamente realizables. Si se alimenta un escalón de posición "crudo" al controlador, este generará saturaciones y el controlador neuronal aprenderá comportamientos a tirones.

---

## 4. Origen del Sistema Cuerpo y Centro de Gravedad (CG)
Las ecuaciones de la Sección 7 del Doc 02 asumen una dinámica rotacional pura ($I_B \dot{\omega}_B = \tau_B - \omega_B \times I_B \omega_B$), pero omiten una hipótesis fundamental: **¿Dónde está el origen del sistema de coordenadas del cuerpo (FRD)?**
*   **Falta especificar:** Se debe escribir explícitamente la hipótesis: *"El origen del sistema cuerpo se asume coincidente con el Centro de Gravedad (CG)"*. Si el CG estuviera desplazado respecto al origen geométrico de los rotores, la dinámica necesitaría términos de acoplamiento (momentos inducidos por aceleraciones lineales y el uso del Teorema de Steiner).

## 5. Dinámica de Rotores: Constantes y Comandos
La Sección 8 habla del "Comando solicitado", pero no concreta sus unidades ni su relación física.
*   En la realidad, un controlador PID/neuronal demanda empuje colectivo ($T$) y momentos ($\tau_x, \tau_y, \tau_z$), pero los actuadores (ESC + Motor + Hélice) operan con **RPM** o **PWM**.
*   **Falta definir:** Las constantes aerodinámicas de la hélice. El empuje y el par no son lineales respecto a la velocidad de giro del rotor, responden a las aproximaciones $T_i = k_f \omega_i^2$ y $\tau_i = k_m \omega_i^2$. Hay que dejar claro si el simulador "saltará" este nivel (comandando unidades abstractas de [0, 1] que mapean a Newtons directamente) o si calculará la velocidad de giro en RPM para cada rotor y aplicará el lag sobre las RPM. Esto afecta radicalmente a cómo responde el dron en los extremos de saturación.

## 6. Mezclador y Estrategia de Saturación (Mixer Saturation)
El Doc 02, Sec 9 menciona "Saturaciones aplicadas".
*   ¿Qué ocurre cuando la maniobra demandada requiere que un motor gire a un equivalente de 120% de su empuje máximo disponible? Si se trunca (clipping) individualmente a 100%, se rompe la proporción de los momentos y el dron volcará en vuelo agresivo.
*   **Falta definir la priorización:** La estrategia estándar en aviación no tripulada es **priorizar la actitud (Attitude over Thrust)**. Si los motores saturan, se reduce o ajusta de forma equilibrada el empuje colectivo total para asegurar que el dron mantenga los momentos de roll/pitch solicitados, sacrificando momentáneamente el seguimiento de altitud para evitar la pérdida de control.

## 7. Retardo de Transporte Puro (Dead-time) vs. Lag de Primer Orden
El modelo propone acertadamente un Lag de primer orden continuo ($\tau$) para los actuadores (Doc 02, Sec 8). Esto simula la inercia rotacional de la hélice y el motor al acelerar.
*   Sin embargo, uno de los mayores desafíos para transferir aprendizaje a la realidad (Sim2Real) o para evaluar el control neuronal es el **Dead-time (retardo de transporte puro)** de las señales, originado por los buses de comunicaciones y el tiempo de lectura de sensores/computación.
*   **Propuesta:** Además del filtro lag, introducir de forma explícita un retardo de $N$ pasos ($u_{aplicado}(t) = u_{solicitado}(t - t_{delay})$). Un filtro paso-bajo atenúa suavemente, pero un retardo puro desestabiliza drásticamente el control, siendo una perturbación crítica de añadir.

## 8. Fricción Lineal Básica (Drag aerodinámico del fuselaje)
El Doc 02 excluye la "aerodinámica formal" y el "arrastre parásito como modelo obligatorio". Es comprensible para simplificar, pero...
*   Físicamente, si a un modelo 6DOF sin ninguna fricción con el aire se le induce un ángulo constante de cabeceo (pitch), acelerará linealmente ad infinitum. Jamás alcanzará una "velocidad terminal" a menos que el controlador empiece activamente a frenar. Esto obliga al controlador neuronal a aprender dinámicas no acotadas, lo cual es inestable.
*   **Falta/Propuesta:** Añadir un modelo de amortiguamiento lineal mínimo $F_{drag} = - \mathbf{D} \cdot v_B$ (una matriz de resistencia aerodinámica que frena al dron proporcionalmente a su velocidad). Es casi coste computacional cero, pero vuelve al simulador inmensamente más razonable y "aterrizado" a la física.

## 9. Condiciones de Fin de Simulación (Límites del mundo)
El Doc 02 excluye explícitamente el "Contacto con el suelo".
*   Dado esto, ¿qué ocurre si el controlador falla y el dron colisiona o cae por debajo de $Z_W \le 0$? Matemáticamente, el simulador seguirá integrando la caída libre o enterrará el dron a -1000m.
*   **Falta definir:** Un criterio claro de "Fin de episodio" (Episode Termination). Por ejemplo, estipular que la simulación se interrumpe y se marca como fallo (importante para las métricas de penalización de RL/Imitation) si $Z_W < 0$ o si un ángulo de actitud supera un umbral de seguridad (ej. $|roll| > 80º$).
