# Criterios de Ingeniería de Software del TFG

## 1. Objetivo del documento

Este documento fija cómo debe tratarse la ingeniería de software en el TFG. El objetivo no es imponer una arquitectura compleja, sino asegurar que el código sea claro, reproducible, trazable y adecuado para un proyecto de ingeniería aeroespacial.

El software debe servir al objetivo del TFG: simular un cuadricóptero 6DOF y comparar control clásico frente a control neuronal por imitación.

## 2. Filosofía general

El proyecto seguirá una filosofía de código científico simple:

- Claridad antes que abstracción.
- Funciones y módulos con responsabilidad física o experimental reconocible.
- Unidades y sistemas de referencia explícitos.
- Dependencias externas limitadas y justificadas.
- Documentación suficiente para entender el sistema a nivel de ingeniería.

No se buscará aplicar patrones de software avanzados si no aportan claridad real al TFG.

## 3. Nivel de documentación software

La documentación software deberá cubrir:

- Arquitectura del sistema.
- Responsabilidad de cada módulo.
- Flujo de datos de una simulación.
- Contratos de datos principales.
- Funciones importantes.
- Puntos de extensión.
- Relación entre código, escenarios y resultados.

No deberá cubrir de forma exhaustiva:

- Cada línea de código.
- Funciones auxiliares evidentes.
- Detalles internos sin impacto en el modelo, la reproducibilidad o la comparación experimental.

## 4. Arquitectura esperada

La estructura del software deberá separar, al menos conceptualmente:

- Núcleo físico: estado, actitud, dinámica e integración.
- Control: controlador clásico y controlador neuronal.
- Escenarios: definición de condiciones iniciales, parámetros y perturbaciones.
- Simulación: orquestación del bucle temporal.
- Telemetría: registro de estados, comandos, referencias y métricas.
- Análisis: cálculo de métricas y generación de figuras.

La separación debe ayudar a razonar sobre el sistema, no crear capas artificiales.

## 5. Flujo de datos de simulación

El flujo básico de una simulación deberá documentarse y mantenerse estable:

1. Se carga o define un escenario.
2. Se inicializa el estado verdadero del vehículo.
3. Se genera una referencia de trayectoria.
4. Se obtiene una observación, posiblemente perturbada.
5. El controlador calcula un comando.
6. El modelo de actuadores transforma el comando solicitado en comando aplicado.
7. La dinámica avanza el estado con RK4.
8. Se registra telemetría.
9. Se calculan métricas al finalizar.

Este flujo será la base para comparar control clásico y neuronal en igualdad de condiciones.

## 6. Contratos de datos

Se permitirá el uso de `dataclasses` para representar datos pasivos y contratos claros. Ejemplos:

- Estado del vehículo.
- Referencia de trayectoria.
- Comando de control.
- Parámetros físicos.
- Configuración de escenario.
- Muestra de telemetría.
- Resultado de métricas.

Las `dataclasses` deberán tener nombres y campos relacionados con conceptos físicos o experimentales. No se usarán para ocultar lógica compleja ni para crear jerarquías innecesarias.

Cuando sea útil, se podrán usar:

- `frozen=True` para datos que no deban mutarse.
- `slots=True` si reduce memoria sin perjudicar la claridad.
- Validaciones simples en `__post_init__` para unidades, dimensiones o valores no finitos.

## 7. Funciones importantes

Se consideran funciones importantes aquellas que afectan directamente a la validez del TFG. Deberán estar documentadas con docstrings o documentación técnica externa.

Ejemplos:

- Conversión entre cuaterniones y matrices de rotación.
- Propagación de actitud.
- Cálculo de la derivada del estado.
- Paso RK4.
- Mezclador de control.
- Aplicación de saturaciones.
- Generación de observaciones perturbadas.
- Cálculo del comando del controlador clásico.
- Inferencia del controlador neuronal.
- Cálculo de métricas.
- Exportación de telemetría.

Para estas funciones se deberá documentar:

- Qué representa cada entrada.
- Unidades.
- Sistema de referencia.
- Qué devuelve.
- Supuestos principales.
- Condiciones de error o saturación si aplica.

## 8. Convenciones de nombres

Los nombres deberán favorecer la interpretación física:

- Usar sufijos de unidades cuando sea práctico: `_m`, `_m_s`, `_rad`, `_rad_s`, `_newton`, `_nm`, `_s`.
- Indicar marco de referencia cuando sea relevante: `_W` para mundo y `_B` para cuerpo, o nombres equivalentes en el estilo del código.
- Evitar abreviaturas ambiguas.
- Usar nombres distintos para comando solicitado y comando aplicado.

Ejemplos recomendados:

```text
position_W_m
velocity_W_m_s
angular_velocity_B_rad_s
collective_thrust_newton
body_torque_nm
applied_rotor_thrusts_newton
```

## 9. Política de dependencias

Se permiten como base:

- NumPy.
- SciPy cuando esté justificado.
- Matplotlib.
- PyTorch.

El gestor de paquetes y entornos será `uv`.

Cualquier librería adicional deberá justificar:

- Qué problema resuelve.
- Qué alternativa simple existiría.
- Qué coste introduce.
- Si afecta a reproducibilidad o portabilidad.

La incorporación de librerías no estándar deberá discutirse antes de hacerse parte estable del proyecto.

## 10. Control clásico y control neuronal

Ambos controladores deberán compartir una interfaz conceptual común:

```text
observación + referencia -> comando de control
```

El controlador clásico será:

- Baseline de comparación.
- Generador de datos para imitación.
- Referencia interpretable.

El controlador neuronal será:

- Entrenado con datos trazables generados por el controlador clásico.
- Evaluado en bucle cerrado dentro del simulador.
- Comparado con las mismas métricas y escenarios.

No se aceptará una comparación basada únicamente en pérdida de entrenamiento.

## 11. Escenarios y configuración

Los escenarios deberán ser declarativos siempre que sea razonable. Un escenario debe permitir reconstruir:

- Vehículo.
- Condición inicial.
- Trayectoria.
- Perturbaciones.
- Controlador.
- Duración.
- Paso temporal.
- Semilla.

El objetivo es que los experimentos puedan repetirse sin depender de cambios manuales en el código.

## 12. Telemetría y resultados

La telemetría deberá registrar, como mínimo:

- Tiempo.
- Estado verdadero.
- Observación usada por el controlador si difiere del estado verdadero.
- Referencia.
- Comando solicitado.
- Comando aplicado.
- Indicadores de saturación o fallo si existen.

Los resultados deberán vincularse con el escenario y el controlador que los generaron. Esta relación es obligatoria para mantener trazabilidad.

## 13. Pruebas y validación software

Las pruebas deberán cubrir especialmente los elementos con impacto físico o experimental:

- Conservación de norma del cuaternión.
- Signo del empuje en convención ENU/FRD.
- Paso RK4 en casos simples conocidos.
- Saturación de actuadores.
- Registro correcto de telemetría.
- Cálculo de métricas.
- Ejecución mínima de un escenario con controlador clásico.
- Ejecución mínima de un escenario con controlador neuronal cargado o simulado.

Las pruebas no deben sustituir a la validación de ingeniería, pero deben evitar errores de implementación que invaliden los resultados.

## 14. Reproducibilidad

El software deberá permitir reproducir:

- Generación de datos.
- Entrenamiento neuronal.
- Evaluación de controladores.
- Cálculo de métricas.
- Figuras o tablas usadas en la memoria.

Cuando haya aleatoriedad, se registrarán semillas. Cuando haya artefactos entrenados, se registrarán parámetros de entrenamiento, arquitectura y normalización.

## 15. Trazabilidad software

Cada componente importante deberá poder relacionarse con un requisito o sección de ingeniería.

Ejemplo:

```text
Componente: integrador RK4.
Requisito: el simulador usa RK4 como integrador oficial.
Documento: requisitos de ingeniería del simulador.
Prueba: integración de sistema simple y simulación mínima.
Resultado: trayectoria y métricas generadas en escenario trazable.
```

## 16. Estilo de implementación

Se seguirán estas reglas:

- Preferir funciones puras cuando el cálculo no necesite estado interno.
- Mantener clases solo cuando representen entidades con estado o responsabilidad clara.
- Evitar herencia profunda.
- Evitar configuraciones implícitas globales.
- Validar dimensiones y valores físicos críticos.
- Escribir errores comprensibles para un usuario técnico.
- Mantener los notebooks, si existen, como exploración, no como fuente principal del sistema.

## 17. Gestión de documentación en el código

Las docstrings deberán usarse en:

- Módulos principales.
- Clases de contrato.
- Funciones físicas o matemáticas importantes.
- Funciones de entrenamiento y evaluación.

Los comentarios en línea se reservarán para explicar decisiones no evidentes. No deben repetir literalmente lo que ya hace el código.

## 18. Criterio de aceptación del software

El software será aceptable para el TFG si:

- Ejecuta escenarios reproducibles.
- Registra telemetría suficiente.
- Permite comparar controladores con métricas comunes.
- Mantiene la convención de ejes documentada.
- Se puede leer y modificar razonablemente por un ingeniero aeroespacial.
- Tiene pruebas para los puntos críticos.
- Está documentado a nivel de sistema y funciones importantes.

## 19. Referencias iniciales

- Wilson, G., Aruliah, D. A., Brown, C. T., et al. (2014). Best practices for scientific computing. *PLOS Biology*.
- Wilson, G., Bryan, J., Cranston, K., et al. (2017). Good enough practices in scientific computing. *PLOS Computational Biology*.
- Hunt, A., & Thomas, D. (1999). *The Pragmatic Programmer*. Addison-Wesley.
- Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning*. MIT Press.
