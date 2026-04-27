# Documentación de Arquitectura y Diseño de Software del Simulador Multirotor

Este documento mapea la estructura de software, las decisiones de arquitectura, los contratos de datos y la orquestación del simulador. El objetivo es ofrecer una guía clara de cómo está construido el sistema a nivel de ingeniería de software, complementando la documentación física y matemática.

## 1. Filosofía de Arquitectura

El simulador está diseñado bajo los siguientes principios:
- **Inmutabilidad y Seguridad de Tipos**: El estado y los comandos se transmiten usando `@dataclass(frozen=True, slots=True)`. Esto previene efectos secundarios indeseados durante el bucle de simulación y reduce el uso de memoria.
- **Desacoplamiento estricto**: La física (`dynamics`), el control (`control`), y la generación de referencias (`trajectories`) no se conocen entre sí directamente. Se comunican a través de contratos puramente de datos definidos en el módulo `core`.
- **Telemetría Diferida (Decoupled Visualization)**: El bucle de simulación no renderiza en tiempo real. En su lugar, genera una traza de eventos (`SimulationHistory`) que el módulo de telemetría persiste. El módulo de visualización lee estas trazas a posteriori para generar gráficos, aislando el rendimiento computacional de la carga gráfica.
- **Configuración basada en Datos (Data-driven Scenarios)**: Los escenarios de simulación se definen como cargas útiles estructuradas (diccionarios/JSON) que instancian todos los componentes (controlador, trayectoria, físicas y perturbaciones) antes de inyectarlos al orquestador.

## 2. Contratos Base (`core/contracts.py`)

Todos los módulos dependen de `core` para evitar dependencias circulares. Los objetos más importantes son:

- `VehicleState`: Representa el estado físico absoluto (Posición, Orientación en cuaternión, Velocidad Lineal, Velocidad Angular, Tiempo).
- `VehicleObservation`: Es un contenedor que expone al controlador el estado observado (potencialmente con ruido inyectado) separándolo del estado verdadero (`true_state`) del integrador físico.
- `TrajectoryReference`: La muestra de la referencia deseada en un instante `time_s` específico (Posición, Velocidad, Aceleración feedforward, Guiñada).
- `VehicleIntent`: Abstracción de la orden del controlador, compuesta por el empuje colectivo (`collective_thrust_newton`) y los torques del cuerpo (`body_torque_nm`).
- `VehicleCommand`: El comando emitido al vehículo, que agrupa el `VehicleIntent` y las señales específicas mapeadas a cada rotor (`RotorCommand`).

## 3. Orquestación y Bucle de Simulación (`runner.py`)

El componente central que ata todo es el `SimulationRunner`.
Flujo lógico por cada paso (step) de simulación:

1. **Inyección de Perturbaciones**: A partir del estado físico verdadero, el escenario inyecta ruido/retrasos devolviendo un `VehicleObservation`.
2. **Referencia de Trayectoria**: Se consulta el objeto trayectoria en el instante de tiempo actual para obtener un `TrajectoryReference`.
3. **Acción de Control**: El controlador (`ControllerContract`) recibe la observación y la referencia para generar un `VehicleCommand`.
4. **Avance Dinámico**: El motor de físicas (`RigidBody6DOFDynamics`) avanza el `VehicleState` usando RK4 con el tamaño de paso físico (`physics_dt_s`).
5. **Captura de Telemetría**: Todos estos objetos (`true_state`, `observed_state`, `reference`, `command`) se empaquetan en un `TelemetrySample` que se añade al `SimulationHistory`.

Existen diferentes frecuencias de actualización (multi-rate):
- Frecuencia física (`physics_dt_s`).
- Frecuencia de control (`control_dt_s`).
- Frecuencia de telemetría (`telemetry_dt_s`).

## 4. Estructura de Módulos

### 4.1 `simulador_multirotor.dynamics`
Contiene la integración de RK4 y la resolución de fuerzas aerodinámicas y de actuadores.
- `RigidBody6DOFDynamics`: Integrador principal de estados.
- `AerodynamicEnvironment`: Proveedor de vientos, modelo de ráfagas estocásticas y arrastre.
- `RotorMixer`: Matriz matemática que resuelve la conversión de intención de vuelo (Torque/Thrust) a comandos individuales por motor.

### 4.2 `simulador_multirotor.control`
Provee las estrategias de control que deben cumplir con `ControllerContract` (`compute_action`).
- Modelos Clásicos: Controlador PID en cascada (`cascade.py`).
- Modelos Neuronales: Definiciones y arquitecturas de control usando redes (MLP, RNN/GRU/LSTM).

### 4.3 `simulador_multirotor.trajectories`
Provee generadores analíticos que implementan `TrajectoryContract` (`reference_at`).
Generadores nativos disponibles: *Hold, Straight, Circle, Spiral, ParametricCurve, Lissajous*.
Utiliza un registro (`TRAJECTORY_FACTORIES`) para parsear las configuraciones en objetos de trayectoria.

### 4.4 `simulador_multirotor.scenarios`
Parsea configuraciones externas (generalmente en formato JSON) en un objeto `SimulationScenario`. Este objeto es una fábrica que construye e inyecta la dinámica, la perturbación, el controlador y la trayectoria de acuerdo a los esquemas de configuración (`schema.py`).

### 4.5 `simulador_multirotor.telemetry`
Se encarga de transformar la memoria temporal de un vuelo (`SimulationHistory`) y exportarla a un almacenamiento en disco de forma optimizada (`export_history_to_json`, soporte a formatos NPZ/CSV/JSON).

### 4.6 `simulador_multirotor.visualization`
Toma el artefacto persistido de telemetría mediante un modelo desacoplado (`TelemetryArchive` en `archive.py`).
Usa Matplotlib para renderizar vistas estáticas (Trayectorias 3D/2D y gráficos de error) sobre los datos históricos (`render.py`).

### 4.7 Interfaz de Línea de Comandos (`app.py`)
El módulo principal utiliza `argparse` para exponer las utilidades del sistema de forma segmentada. Sub-comandos destacados:
- `multirotor-sim`: Ejecuta un escenario y muestra métricas básicas.
- `multirotor-sim --analysis-dir`: Corre la simulación, guarda telemetría e invoca el visualizador.
- `multirotor-sim neural ...`: Acceso a los flujos de creación de datasets, entrenamiento de redes neuronales, evaluación de benchmarks y generación de reportes automáticos.
- `multirotor-sim validation ...`: Batería de validación de referencia (smoke tests base).

## 5. Extensibilidad
La arquitectura está montada para ser un entorno plug-and-play:
- **Para añadir un controlador nuevo**: Implementar la interfaz `ControllerContract` e inyectarla en el `SimulationScenario`.
- **Para añadir un modelo físico**: Reemplazar o extender `RigidBody6DOFDynamics` conservando la firma del método `step`.
- **Para cambiar el comportamiento del simulador**: Modificar el esquema JSON del escenario, que la aplicación automáticamente interpretará sin modificar el código fuente base.