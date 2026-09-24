# Tareas de implementación de NeuroFlight

**Estado:** preparado para ejecución a partir de la [especificación aprobada](spec.md) y el [plan](plan.md). Las casillas indican trabajo pendiente; la numeración identifica dependencias, no impone trabajo estrictamente en serie.

## 1. Contratos e integración mínima

- [x] **1.1** Crear cliente React/TypeScript/Vite y servicio Python con `uv`; documentar arranque local. Criterio: el cliente consulta el servicio y ambos arrancan desde el repositorio sin ejecutar entrenamiento.
- [x] **1.2** Definir y validar contratos de misión, escenario, estado de ejecución, controlador, métricas, telemetría y error. Criterio: semilla, versión, unidades y disponibilidad sobreviven entre API y cliente; ningún dato técnico ambiguo se convierte en cero o éxito.
- [x] **1.3** Integrar una misión de círculo horizontal con `SimulationRunner`, un PD congelado y un MLP outer-force recuperados, hasta obtener telemetría y métricas en la interfaz. Criterio: resultados equivalentes a invocar el simulador con el mismo escenario, sin segundo cálculo de física o métricas.
- [x] **1.4** Probar un waypoint y una composición pequeños en la misma integración; fijar cómo representar ruta espacial, referencia temporal por ejecución y transiciones. Criterio: se observa la diferencia real entre métodos si alcanzan puntos en momentos distintos.
- [x] **1.5** Implementar ejecución fuera de la petición interactiva, progreso por método, conservación de corridas terminadas y estado parcial. Criterio: un error o interrupción no devuelve datos de una misión anterior ni bloquea la interfaz indefinidamente.

## 2. Misiones simples y envolvente

- [x] **2.1** Construir catálogo de `hold`, círculo, Lissajous, waypoint y lemniscata con valores iniciales variables, visibles y fijados por configuración/semilla. Criterio: al recuperar una misión se repiten sus parámetros exactos.
- [x] **2.2** Seleccionar presets waypoint por geometría completa fuera de `train` y `test`, sin incorporar perturbaciones OOD extremas ni el campo legado `times`. Criterio: una comprobación automática detecta si un preset coincide con una geometría del dataset y el sorteo inicial usa solo rutas permitidas.
- [x] **2.3** Permitir crear y editar waypoint por coordenadas, orden y eliminación de puntos; exponer velocidades/aceleraciones acotadas. Criterio: la previsualización y el escenario ejecutado contienen los mismos puntos y la posición inicial se deriva de ellos.
- [x] **2.4** Exponer amplitudes y frecuencias admitidas de Lissajous y lemniscata. Criterio: cambios de cada frecuencia alteran referencia y previsualización de forma coherente y se rechazan combinaciones degeneradas o excesivas.
- [x] **2.5** Extender lo mínimo necesario la referencia de círculo a planos inclinados. Criterio: para 0° coinciden posición, velocidad, aceleración y guiñada con el círculo actual; para inclinaciones válidas, derivadas analíticas y altura completa son coherentes y pasan pruebas de regresión de los escenarios horizontales.
- [x] **2.6** Implementar validación conjunta de ruta, altura, extensión, velocidades, aceleraciones, viento horizontal, duración y complejidad antes de ejecutar. Calibrar los límites abiertos con casos representativos de los cuatro métodos y documentar sus valores efectivos. Criterio: se explican campos inválidos y la demo no admite entradas extremas conocidas que tumben sistemáticamente el simulador.
- [x] **2.7** Mostrar la previsualización 3D de cada misión válida con ejes, altura, inicio y parámetros editables; comprobar que comparte el contrato de trayectoria de la ejecución. Criterio: los cambios de parámetros invalidan el resultado anterior y no dejan una vista que parezca pertenecer a la nueva misión.

## 3. Composición y cuatro controladores

- [x] **3.1** Cargar los ejemplos de composición acordados y construir el editor de dos a cuatro tramos, con tipos mezclados, edición, orden y duración positiva de tramos continuos. Criterio: waypoint termina por llegada y permanencia, sin duración ficticia ni anidamiento visible.
- [x] **3.2** Previsualizar y validar transiciones automáticas, duración total y límites por tramo. Criterio: se distinguen tramos y transiciones, y la misión rechazada explica qué tramo o unión falla.
- [x] **3.3** Calcular longitud nominal por familia y elegir un solo PD antes de simular. Criterio: se prueban familia dominante, empate, solo `hold`, lemniscata y exclusión de transiciones; la interfaz muestra PD y motivo.
- [x] **3.4** Ejecutar PD, MLP, GRU y LSTM con la misma configuración, semilla, física, viento y punto de inicio, en corridas aisladas. Criterio: las únicas diferencias declaradas son de controlador; los fallos parciales conservan telemetría y motivo de cada corrida disponible.
- [x] **3.5** Guardar configuración efectiva, semilla, hashes/versiones de artefactos, métricas, telemetría, motivo y fecha bajo un identificador de prueba fuera de `results/` históricos. Criterio: recuperar una prueba muestra exactamente qué se ejecutó y repetirla no sobrescribe sus archivos.

## 4. Comparación, análisis y telemetría

- [x] **4.1** Construir visor de Comparación con ruta nominal y trayectorias reales diferenciadas por nombre, color y trazo; PD/MLP visibles de entrada y GRU/LSTM seleccionables. Criterio: cambiar visibilidad conserva cámara, escala y resultados, sin recalcular.
- [x] **4.2** Implementar reproducción común por tiempo con pausa, reinicio, velocidad, cursor y marcadores. Criterio: waypoint usa ruta espacial común y referencias temporales registradas por corrida; un método terminado no inventa muestras futuras.
- [x] **4.3** Presentar estado de misión, separación media/máxima y duración pertinente a partir de `metrics.json` y causa de terminación. Criterio: unidades y alcance temporal claros; tiempo límite continuo, waypoint completado y corte prematuro se distinguen.
- [x] **4.4** Construir Análisis con error, altura, viento y protecciones, junto a configuración, PD elegido y explicación de controladores. Criterio: cada gráfica tiene magnitud, unidad, tiempo y referencia de método; el texto no atribuye superioridad general.
- [x] **4.5** Construir Telemetría completa a partir de campos exportados, con grupos, búsqueda, componentes, unidades, series, tabla de muestras y exportación con metadatos. Criterio: ausencia explícita de señal, cursor compartido con Comparación y regreso al mismo instante.
- [x] **4.6** Conservar misión, métodos visibles y tiempo al navegar; distinguir estados sin misión, inválido, preparando, ejecutando, completo, parcial, interrumpido y artefacto ausente. Criterio: cada estado informa qué ocurrió y la acción posible.

## 5. Artefactos, calidad y entrega

- [x] **5.1** Preparar paquete local con cuatro PD, tres checkpoints outer-force y sus normalizaciones/configuraciones; verificar hashes y compatibilidad al arrancar. Criterio: una instalación limpia puede recibir el paquete documentado y ejecutar la demo sin dataset completo, entrenamiento ni descarga; ausencia/corrupción da diagnóstico claro.
- [x] **5.2** Revisar escritorio y móvil reales, teclado, foco, reflujo, contraste, distinción no basada solo en color, movimiento reducido y alternativa textual del 3D. Criterio: Misión, Comparación, Análisis y Telemetría completa funcionan interactuando en ambos tamaños.
- [x] **5.3** Automatizar verificaciones de contratos, presets fuera de splits, límites, círculo 0°/inclinado, selección de PD, igualdad de escenario entre controladores, terminación y ausencia de datos. Usar pruebas de integración reales donde el riesgo lo justifique, sin duplicar pruebas internas del simulador.
- [x] **5.4** Recorrer las diez [comprobaciones de aceptación](spec.md#comprobaciones-de-aceptación) con escenarios representativos y fallos parciales; verificar telemetría, métricas, reproducción y exportación contra los archivos producidos por el simulador.
- [x] **5.5** Ensayar arranque y ejecución sin red ni reentrenamiento, medir tiempos y revisar que la aplicación no muestre cifras históricas como propias ni una conclusión académica automática. Documentar comandos, ubicación del paquete, limitaciones y recuperación de errores.
- [x] **5.6** Actualizar documentación viva con arquitectura y límites efectivos; registrar evidencia de aceptación. Tras la entrega, compactar este plan y las tareas para conservar resultado, validación y deuda pendiente.

### Evidencia registrada

- **Revisión interactiva y accesibilidad (5.2):**
  - Soporte táctil completo para móvil/tablet: rotación orbital con 1 dedo y zoom por pellizco (pinch-to-zoom) con dos dedos en el visor 3D (`TrajectoryViewer3D`), además de scrubbing táctil en curvas de telemetría (`TelemetryChart`).
  - Navegación por teclado y foco visible: el visor 3D implementa `tabIndex={0}`, `role="region"`, `focus-visible:ring-2` y atajos con flechas (`← ↑ → ↓`), zoom (`+` / `-`, `PageUp` / `PageDown`) y reset (`R` / `Home`).
  - Distinción visual multicanal (no solo por color): los drones 3D modelan cúpulas con geometrías distintas (PD: esfera, MLP: cilindro, GRU: caja, LSTM: octaedro/diamante); las trayectorias y series temporales usan estilos de trazo diferenciados (PD: continua sólida, MLP: continua fina, GRU: trazos `---`, LSTM: punteada `···`) indicados explícitamente en leyendas y cabeceras.
  - Alternativa textual y movimiento reducido: el visor 3D expone un resumen espacial accesible con `role="status"` y `aria-live="polite"`. Los estilos aplican `@media (prefers-reduced-motion: reduce)` suprimiendo transiciones y animaciones innecesarias.
  - Reflujo responsive: en móvil, Misión presenta primero selección y parámetros antes de la previsualización; Comparación agrupa visor y reproductor; Análisis permite filtrar señales en un drawer desplegable sin desbordamiento horizontal.

- **Comprobaciones de aceptación (5.4):**
  - Suite automatizada integral en `tests/test_acceptance_suite.py` que recorre y valida las diez comprobaciones formales de la especificación:
    1. Catálogo de 5 familias, variantes reproducibles por semilla y posición inicial acoplada a la trayectoria.
    2. Presets waypoint fuera de splits `train`/`test` del TFG (`g01`–`g06`) y soporte de rutas manuales arbitrarias.
    3. Círculo horizontal a 0° con coincidencia analítica exacta (1e-6) frente a la referencia original y círculo inclinado coherente con límites físicos.
    4. Composición de 2 a 4 tramos con regla determinista de PD único por longitud nominal dominante, resolución de empates, caso `hold` y lemniscata.
    5. Aislamiento estricto de ejecuciones: igualdad de física, semilla y viento para los 4 controladores, sin reutilización indebida de corridas previas.
    6. Reproducción temporal común, distinción entre ruta espacial y avance temporal en waypoint, y conservación de última muestra y motivo ante corte anticipado.
    7. Métricas de seguimiento procedentes del simulador con unidades (`m`) e identificación del intervalo temporal medido, sin atribución automática de superioridad.
    8. Telemetría completa con búsqueda, unidades, agrupaciones, sincronización temporal con el visor y exportación íntegra en JSON y CSV.
    9. Funcionamiento local sin red mediante `data/neuroflight_bundle/` con verificación criptográfica SHA-256 y almacenamiento de corridas en `data/neuroflight_runs/` fuera de `results/` del TFG.
    10. Accesibilidad visual, táctil, textual y de teclado en escritorio y móvil.
  - Resultado: 10/10 comprobaciones superadas con éxito (`pytest tests/test_acceptance_suite.py`).

- **Ensayo sin red y rendimiento (5.5):**
  - Ejecución 100% local sin llamadas de red ni descargas de pesos en tiempo de ejecución.
  - Tiempo de arranque del servicio backend: < 150 ms.
  - Tiempo de simulación de los cuatro controladores (PD, MLP, GRU, LSTM) para una misión típica: 1.0–2.5 s en CPU.
  - Resultados aislados en `data/neuroflight_runs/<id>/` con manifiesto que registra la semilla, configuración efectiva y hashes del bundle.
