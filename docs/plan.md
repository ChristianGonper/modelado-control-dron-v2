# Plan de implementación de NeuroFlight

**Estado:** preparado el 23 de septiembre de 2026 a partir de la [especificación aprobada](spec.md). Las unidades ejecutables y su avance se siguen en [tasks.md](tasks.md).

## Resultado y límites

Construir en este repositorio una aplicación local de concurso que permita configurar, previsualizar y ejecutar una misión con PD, MLP, GRU y LSTM; reproducir la referencia y las trayectorias obtenidas; y consultar análisis y telemetría de esa ejecución. La [especificación](spec.md) fija comportamiento y aceptación; las [decisiones de producto](decisiones-producto.md) explican el origen de las misiones y del PD. Este plan ordena la construcción sin trasladar resultados nuevos a la memoria o a `results/` históricos.

Se reutilizan el `SimulationRunner`, la carga y validación de escenarios, los controladores, las métricas y la exportación de telemetría existentes. La física, los datasets y el entrenamiento del TFG no forman parte del desarrollo de la interfaz. Los artefactos regenerados bajo `data/regenerated_2026-09-23/` son la base local de la demo; sus seis checkpoints y cuatro PD siguen identificados como nuevos. La comparación principal usa tres checkpoints `neural` outer-force; los de `neural_position` no entran en su selector.

## Estructura de la solución

- **Cliente:** aplicación React con TypeScript y Vite, dentro del repositorio, con Misión, Comparación y Análisis. Telemetría completa es una sección de Análisis. Comparte el estado de misión, ejecución y cursor temporal, pero no calcula física ni métricas. Usa el lenguaje visual de [AeroLab](../../concurso-prototipos-eiiia-2026/docs/identidad.md). La elección concreta de visor y biblioteca de gráficas se cierra tras una prueba con telemetría real, teclado, rendimiento y reflujo.
- **Servicio local:** API Python junto al paquete existente, con FastAPI y dependencias gestionadas por `uv`. Una capa de aplicación traduce misiones admitidas a escenarios declarativos, valida la envolvente de producto además del esquema del simulador y llama a `SimulationRunner` sin duplicarlo. Las cuatro simulaciones se ejecutan fuera del hilo de atención de peticiones; se publica progreso por método y se conservan los resultados válidos si otro falla. El servicio entrega telemetría, métricas y metadatos con unidades y disponibilidad explícitas.
- **Resultados y artefactos:** directorio de trabajo de NeuroFlight separado de `results/` históricos, con identificador por ejecución, configuración efectiva, semilla, versiones, hashes de artefactos, causa de terminación y archivos de salida. Un paquete local de demostración reúne los cuatro PD, los tres checkpoints outer-force y sus archivos de normalización/configuración; se verifica al arrancar. La fuente regenerada, ignorada por Git, no se supone presente en una instalación limpia: se documenta y prueba el procedimiento para producir y comprobar el paquete sin incluir datasets completos ni descargar pesos durante la demo.
- **Contrato de visualización:** la ruta nominal espacial, la referencia temporal registrada por método y las ejecuciones son conceptos distintos. En waypoint y composiciones con waypoint, la referencia depende del estado de cada simulación. El cliente sincroniza las muestras por tiempo para reproducir los vehículos, sin fabricar una referencia temporal común. Las transiciones de composición se derivan de la misma misión/ejecución que usa el simulador y se identifican al representarlas.

La estructura concreta de carpetas y el mecanismo de progreso se resolverán en la primera fase con una integración pequeña. Se preservará la ejecución por CLI del TFG. Cualquier cambio imprescindible en `src/simulador_quad` se mantendrá acotado, con prueba de compatibilidad de escenarios existentes.

## Fases y dependencias

### 1. Contratos y vertical real

Fijar los tipos de misión, ejecución, error, métricas y señal; arrancar cliente y servicio. Integrar una misión de círculo horizontal con un PD y un checkpoint regenerado, desde formulario hasta telemetría y resultado real. Probar también una ruta waypoint y una composición corta para resolver pronto el estado de la referencia, las transiciones, el progreso y el coste de simular cuatro veces. Establecer cómo se cancela una petición sin atribuir a ella resultados anteriores.

**Salida:** una ruta real pasa por todo el sistema; quedan fijados los contratos de escenario, ejecución y reproducción antes de multiplicar familias o pantallas.

### 2. Catálogo, geometría y límites

Implementar los cinco tipos simples, sus presets y la selección waypoint por identidad de ruta fuera de `train` y `test`. Añadir edición manual de puntos, amplitudes y frecuencias de Lissajous y lemniscata. Construir el círculo inclinable con posición, velocidad, aceleración y guiñada coherentes; inclinación cero conserva la referencia horizontal existente. Implementar una previsualización basada en el mismo contrato de misión y una validación de la ruta completa. Medir con ejecuciones representativas los límites aún abiertos de velocidad, longitud, duración y complejidad; fijar una envolvente que permita variedad geométrica sin exponer viento o velocidades extremos. Registrar los límites efectivos en la documentación viva.

**Salida:** cada misión simple válida se previsualiza y ejecuta; las inválidas explican la corrección. La validación de producto no sustituye las protecciones del simulador.

### 3. Composición y comparación controlada

Implementar los ejemplos de composición y el editor de dos a cuatro tramos, con duración explícita para tramos continuos y terminación propia para waypoint. Previsualizar transiciones automáticas y comprobar la duración máxima. Calcular la longitud nominal por familia antes de ejecutar y seleccionar un único PD con las reglas de empate, `hold` y lemniscata de la especificación. Ejecutar PD, MLP, GRU y LSTM con escenario, semilla y condiciones iguales; aislar el estado de cada corrida y preservar los resultados parciales. Verificar que métricas y causas de terminación proceden del simulador.

**Salida:** composiciones y misiones simples producen una comparación de cuatro métodos reproducible, con resultados separados de la evidencia histórica.

### 4. Comparación visual, análisis y telemetría

Construir el visor 3D con ruta nominal y trayectorias ejecutadas, leyenda accesible y selección de métodos. Añadir reproducción, pausa, velocidad, cursor y marcadores sincronizados; un método terminado conserva su última muestra y motivo. Presentar estado, separación media y máxima con unidades y explicación del intervalo medido. En Análisis, añadir gráficas de error, altura, viento y protecciones, junto a configuración y controladores. Generar el catálogo de Telemetría completa a partir de los campos exportados: búsqueda, grupos, componentes, unidades, gráfico y tabla por instante, y exportación con metadatos. Mantener cursor y selección al navegar entre vistas.

**Salida:** el visitante puede ver y reproducir la misión en Comparación y profundizar en Análisis sin confundir datos ausentes con ceros ni extraer una conclusión general de una corrida.

### 5. Empaquetado, experiencia y aceptación

Preparar el paquete local verificado de artefactos y un arranque reproducible sin entrenamiento ni descargas. Resolver estados de error, carga, interrupción y artefacto ausente. Revisar escritorio, móvil, teclado, foco, contraste, reflujo, movimiento reducido y alternativa textual del visor sobre la interfaz real. Ejecutar las diez [comprobaciones de aceptación](spec.md#comprobaciones-de-aceptación) con misiones simples, waypoint manual, círculo inclinado, composiciones y fallos parciales. Revisar contenido y límites académicos, medir tiempo de arranque y de corrida y ensayar la presentación sin red.

**Salida:** aplicación demostrable desde una instalación documentada, con verificación funcional, visual y técnica. Al cerrar el incremento se actualizan los documentos vivos y se compactan plan y tareas a resultado, verificaciones y deuda pendiente.

## Orden y trabajo simultáneo

La fase 1 fija los contratos. Después pueden avanzar en paralelo el catálogo/validador de misiones, el empaquetado de artefactos y la base de vistas con datos del contrato real. La composición depende de la geometría y los límites; la comparación completa depende del ejecutor de cuatro corridas. El visor puede empezar con telemetría real de la fase 1, pero la aceptación de waypoint y composición requiere los contratos finales de la fase 3. Análisis y Telemetría completa pueden crecer sobre las salidas ya fijadas mientras se termina el editor. La fase 5 cierra sobre todos los recorridos y un paquete local limpio.

## Decisiones que se resuelven con evidencia

Las librerías visuales, el formato de progreso y el almacenamiento de ejecuciones son elecciones técnicas: se registrarán al probarlas. Si las ejecuciones muestran que una parte de la envolvente aprobada produce fallos sistemáticos o esperas impropias de la demo, se documentarán casos y se revisará el límite con el autor antes de cambiar el alcance de la especificación. La recuperación de pesos no autoriza a rehacer el protocolo experimental ni a presentar sus resultados como los originales.
