# Especificación de NeuroFlight para el concurso

**Estado:** aprobada por el autor el 23 de septiembre de 2026. Concreta el [concepto](concepto-aplicacion.md) y las [decisiones de producto](decisiones-producto.md). La [identidad visual de AeroLab](../../concurso-prototipos-eiiia-2026/docs/identidad.md) fija el lenguaje compartido. Esta especificación describe lo que debe hacer la aplicación y cómo se comprobará; la ejecución se organiza en el [plan](plan.md) y las [tareas](tasks.md).

## Resultado esperado y frontera académica

NeuroFlight permite configurar una misión de vuelo, verla antes de ejecutarla, simular el mismo escenario con un controlador clásico y tres redes neuronales, reproducir las trayectorias obtenidas y examinar las señales necesarias para entenderlas. Una persona sin experiencia en control de vuelo puede completar el primer recorrido; quien quiera profundizar encuentra los parámetros, las gráficas y la telemetría de **esa ejecución**.

La comparación principal emplea el PD clásico congelado que corresponda a la misión y los modelos **MLP, GRU y LSTM del modo `neural` outer-force**. Las redes sustituyen el control externo de posición por una fuerza deseada; el lazo interno clásico conserva la estabilización de actitud y las protecciones existentes. Los modelos `neural_position` regenerados permanecen como artefactos técnicos, pero no son otros tres métodos del selector principal. La aplicación no reentrena ni modifica el dataset del TFG.

Los seis checkpoints y los cuatro PD regenerados el 23 de septiembre de 2026 son artefactos ejecutables nuevos. Su manifiesto local está en `data/regenerated_2026-09-23/recovery_manifest.json`, bajo una carpeta ignorada por Git. Sus pesos y las métricas de las nuevas simulaciones no se presentan como los originales ni reemplazan las cifras de la memoria del TFG. La aplicación tampoco muestra resultados agregados, conclusiones académicas o un enlace a la memoria; el autor puede enseñarla por separado si se la piden.

## Recorrido y vistas

1. **Misión.** El visitante elige una familia de trayectoria con una variante inicial lista para usar o abre el editor de composición. Ve la ruta, ejes, altura, punto de inicio y condiciones antes de ejecutar. Puede modificar geometría y un viento horizontal moderado; los parámetros menos frecuentes quedan cerca de su familia, en opciones avanzadas.
2. **Ejecución.** Una acción ejecuta PD, MLP, GRU y LSTM con la misma misión configurada. El progreso distingue preparación, simulación de cada método, resultado disponible y fallo. Si uno falla, las ejecuciones terminadas siguen disponibles y el fallo conserva su motivo; la interfaz no lo sustituye por un resultado anterior.
3. **Comparación.** Se muestran la ruta espacial prevista y, inicialmente, las ejecuciones de PD y MLP. GRU y LSTM están visibles y pueden añadirse o quitarse sin recalcular. Un reproductor común permite observar dónde está cada dron simulado en el mismo tiempo de la misión.
4. **Análisis.** Muestra unas pocas gráficas explicadas junto a los resultados, la configuración utilizada, los controladores y las protecciones. Una subsección **Telemetría completa** permite elegir señales, unidades, componentes y métodos, consultar muestras por instante y exportar los datos de esta ejecución.

El visitante puede volver de Análisis a Comparación conservando misión, métodos visibles y tiempo seleccionado. Cambiar parámetros de la misión invalida el resultado anterior como resultado de la nueva configuración: queda claro que hay que volver a ejecutar.

## Catálogo de misiones y valores iniciales

El selector principal ofrece **mantener posición**, **círculo**, **Lissajous**, **ruta por puntos** y **lemniscata**. Las cuatro primeras familias estuvieron en el entrenamiento; la lemniscata sirve para explorar una geometría nueva. Estos rótulos describen formas de vuelo, sin exigir al visitante entender `train`, `test` u OOD. `line` es un alias del simulador para waypoint y no aparece como una sexta opción.

Al elegir una familia se genera una variante inicial dentro de una envolvente conservadora. Una nueva elección puede proponer otra variante, pero los valores nunca cambian solos en una misión ya configurada. El visitante ve todos los valores concretos antes de ejecutar y puede repetir la prueba con la misma configuración. La aplicación guarda con cada ejecución la configuración efectiva y su semilla; al recuperar o compartir esa configuración se reproduce el mismo escenario, sujeto al mismo conjunto de artefactos y versión del simulador.

| Familia | Propuesta inicial y ajustes disponibles |
| --- | --- |
| Mantener posición | Partir de alturas de 1,5–3 m y desplazamientos horizontales pequeños ya representados en las variantes del dataset. Ajustar posición y orientación admitida, con altura dentro de la envolvente de vuelo de la aplicación. |
| Círculo | Proponer un círculo horizontal conocido; permitir radio de 0,75–3,5 m, centro, velocidad angular, inclinación de 0–30° y orientación horizontal del plano. La última aparece en opciones avanzadas. La combinación cumple `radio × velocidad angular ≤ 1,5 m/s` y `radio × velocidad angular² ≤ 1,0 m/s²`; toda la ruta queda entre 0,5 y 6 m de altura. |
| Lissajous | Partir de las ocho geometrías del dataset; ajustar centro, amplitud y frecuencia por eje dentro de la envolvente de esas variantes. Rechazar frecuencias degeneradas y combinaciones que excedan los límites de movimiento validados. |
| Ruta por puntos | Proponer alternativamente `waypoint_clean.yaml` o las hélices ascendente y descendente definidas en la batería OOD. Ninguna de estas rutas se incorpora a `train` o `test`; la hélice más exigente queda como ejemplo adicional. Permitir introducir, editar, quitar y reordenar coordenadas `(X, Y, Z)` en metros. Se ven los puntos y la ruta resultante. |
| Lemniscata | Partir de las tres variantes OOD existentes; ajustar centro, semiejes, frecuencia de avance, amplitud y frecuencia vertical cuando proceda. La selección inicial omite las perturbaciones extremas del ensayo original. |

Los presets waypoint se seleccionan por **identidad de la ruta completa**, no por pertenecer al tipo `waypoint`: las seis geometrías `g01`–`g06` del dataset aparecen al menos una vez en `train` y no entran en ese sorteo. `waypoint_clean.yaml` añade un ascenso y no coincide con ellas. Al importar su geometría se descarta `times`, que el simulador admite solo por compatibilidad y que no gobierna la llegada a puntos. Crear una ruta manual es siempre una prueba nueva de inferencia, no un elemento del dataset.

La posición inicial del vehículo se calcula a partir de la trayectoria elegida y se muestra como dato fijo. La previsualización usa la misma configuración declarativa que pasará a la simulación; incluye desnivel y transiciones si las hay. Si una trayectoria no supera la validación, se explican los campos y combinaciones afectados antes de habilitar «Ejecutar».

### Círculos inclinados

El simulador actual solo define círculos en el plano horizontal. La aplicación podrá construir una referencia circular en un plano inclinado mediante inclinación y orientación del plano, conservando posición, velocidad y aceleración analíticas coherentes y el mismo contrato de trayectoria. La inclinación cero reproduce exactamente el comportamiento horizontal existente. La guiñada sigue la proyección horizontal de la tangente, con continuidad angular al cerrar la vuelta; para inclinación cero debe coincidir con la regla actual. Se dará preferencia a una capa de integración; si hace falta ampliar `CircleTrajectory` y su esquema, el cambio será mínimo y se comprobará que no altera los escenarios horizontales ni los resultados históricos. Los círculos inclinados solo se usan para inferencia y demostración.

### Envolvente de demostración

El visitante puede variar más la **geometría** que la exigencia dinámica. El viento se ajusta en magnitud y dirección horizontal, con máximo de 1,4 m/s y componente vertical nula. El waypoint parte de 0,6 m/s y 0,5 m/s²; el rango superior expuesto no superará el validado con las cuatro estrategias. Se comprueba la ruta completa, incluidas altura, extensión, duración prevista, velocidad y aceleración, no solo que cada número sea finito o positivo. Las combinaciones fuera de la envolvente se rechazan antes de simular y se explica cómo corregirlas. La misma regla se aplica a cada tramo de una composición.

La validación de producto complementa la validación física del YAML. Una misión válida puede aun así terminar por una protección o por el tiempo máximo; ese resultado se muestra como tal, sin ocultarlo ni presentar el caso como un fallo total de la aplicación.

Límites efectivos de la demostración, aplicados antes de previsualizar o simular:

- Viento horizontal de 0 a 1,4 m/s. Una magnitud negativa se rechaza; la componente vertical del escenario es nula.
- Duración de una misión continua, o de la composición con sus transiciones, como máximo 60 s. Cada tramo continuo dura como máximo 30 s y debe ser positivo. Waypoint no recibe una duración de interfaz: su tiempo nominal es el perfil trapezoidal más la permanencia, y ese tiempo también entra en el tope de 60 s.
- Waypoint: velocidad de 0,2 a 1,0 m/s, aceleración de 0,2 a 0,8 m/s², como máximo 16 puntos y 40 m de longitud.
- Lissajous: amplitud por eje hasta 3,5 m, frecuencia de 0,1 a 1,2 rad/s, velocidad de eje A·ω hasta 1,5 m/s y aceleración A·ω² hasta 1,1 m/s². La extensión horizontal, igual que en el círculo, queda dentro de 12 m desde el origen.
- En familias continuas el tope de simulación es la duración pedida. En waypoint y composición se suma un margen de 10 s de llegada, sin pasar de 60 s.

## Composición por tramos

La composición vive en un panel propio de Misión y ofrece los dos ejemplos de la batería OOD y `composite_ood.yaml` como puntos de partida. El visitante puede crear también una composición de **dos a cuatro tramos**, elegir para cada uno cualquiera de los cinco tipos anteriores y modificarlo con los mismos controles que en una misión simple. Puede añadir, eliminar y reordenar tramos. La interfaz inicial no ofrece anidamiento, aunque el motor lo admita.

Cada tramo `hold`, círculo, Lissajous o lemniscata tiene una duración positiva explícita. Un tramo waypoint avanza y termina cuando se cumplen sus condiciones de llegada y permanencia; la interfaz no le asigna una duración ficticia. Las transiciones automáticas que inserta el simulador se representan en la previsualización y en la reproducción. Si una discontinuidad o una duración hace inviable la misión dentro de la envolvente, se informa antes de ejecutar.

Se usa **un solo PD congelado para toda la composición**. La familia representativa es la que suma más longitud de ruta nominal entre sus tramos. Las transiciones automáticas no cuentan; `hold` aporta longitud cero y, si toda la composición es estacionaria, se usa el PD de `hold`. Los empates se resuelven por la primera familia empatada en la secuencia. La lemniscata se asocia al PD de Lissajous después de calcular la familia predominante. El PD elegido y el motivo se muestran junto a la misión. Esta regla es propia de NeuroFlight: el experimento OOD histórico usó Lissajous como referencia fija para las composiciones.

## Condiciones de ejecución y artefactos

Las cuatro estrategias reciben la misma geometría de misión, vehículo, perturbación, semilla, límites y discretización de física, control y telemetría. Solo cambia el controlador externo seleccionado. Se emplea el `SimulationRunner` y su contrato de escenarios y resultados; la interfaz no reproduce por su cuenta la física ni calcula métricas alternativas. Los YAML o datos declarativos se validan antes de instanciar una simulación.

La distribución de la aplicación incorpora localmente los **cuatro PD** y, para la comparación principal, los **tres checkpoints outer-force**, junto a la normalización y configuración que necesita cada uno. Comprueba su presencia y compatibilidad al iniciar y muestra un diagnóstico si falta alguno. El paquete de demostración no requiere los datasets completos, reentrenamiento ni descargas de gran tamaño en directo. El manifiesto de regeneración queda en el entorno técnico para identificar artefactos y versiones; no se convierte en un panel de resultados académicos para el visitante.

Cada ejecución conserva su configuración efectiva, semilla, identidad de artefactos, telemetría, métricas, causa de terminación y fecha de la prueba. Esta información permite repetir e interpretar **esa prueba**, sin atribuirle los resultados agregados del TFG. Los archivos se separan de `results/` históricos y no se sobrescriben al cambiar la misión.

## Comparación y reproducción

La ruta nominal espacial aparece con trazo propio y las ejecuciones seleccionadas con nombres, colores y trazos distintos. Se comienza con PD y MLP visibles; GRU y LSTM se pueden incorporar o quitar sin repetir la simulación. La cámara, los ejes y la escala no saltan al cambiar visibilidad. Reproducir, pausar, reiniciar, ajustar velocidad y mover el cursor temporal actúa sobre todas las ejecuciones. Un marcador muestra la posición de cada vehículo en el tiempo seleccionado; el instante y el estado de reproducción permanecen legibles fuera del visor 3D.

En waypoint, la **ruta geométrica** es común, pero la referencia temporal del simulador avanza cuando cada vehículo cumple las condiciones de asentamiento. Por ello, el visor no inventa un único objetivo móvil idéntico para todos: muestra la ruta espacial común y los vehículos sincronizados en tiempo; Análisis puede mostrar la referencia temporal registrada para cada ejecución. Esta distinción se mantiene en composiciones con waypoint. Si un método termina antes, su trayectoria y motivo siguen visibles y su marcador no avanza más allá de la última muestra. La interpolación usada para mover marcadores entre muestras es solo visual y no modifica telemetría ni métricas.

La primera lectura muestra por controlador: **estado de la misión**, **separación media de la referencia en metros** y **mayor separación en metros**. Corresponden a `termination_reason`, `position_mae_m` y `position_max_err_m` del simulador. En waypoint, la separación se calcula frente a la referencia temporal propia de esa ejecución; se explica ese alcance junto a la métrica. La duración observada acompaña al estado cuando ayuda a interpretar una terminación anticipada. Alcanzar el tiempo límite es un final previsto para trayectorias continuas y no equivale a completar todos los waypoint. Una ejecución incompleta conserva sus medidas, identificadas como medidas del intervalo disponible; no se comparan como si cubrieran toda la misma misión.

## Análisis y telemetría completa

El resumen de Análisis responde primero a preguntas concretas: cuánto se apartó el vehículo de la referencia a lo largo del tiempo, cómo siguió la altura, qué viento se aplicó y si actuaron las protecciones. Cada gráfica muestra magnitud, unidades, tiempo y métodos visibles. El texto próximo explica qué mide, sin deducir una superioridad general de una corrida. Se puede consultar configuración, controlador clásico elegido, papel del lazo interno, normalización del modelo neuronal y motivo de parada.

**Telemetría completa** está dentro de Análisis y ofrece búsqueda y grupos basados en los campos realmente exportados: estado y referencia, observación del controlador, velocidad, actitud, fuerza deseada y limitada cuando exista, órdenes y respuesta de rotores, viento y protecciones. El visitante elige señales, componentes y controladores, ve sus series temporales con unidades y consulta en tabla las muestras del instante seleccionado. El cursor puede seguir el tiempo de Comparación y existe un regreso directo a «Ver misión». Se pueden exportar las muestras de la ejecución, conservando nombres, unidades y metadatos suficientes para interpretarlas. Un campo ausente se indica como no disponible, nunca como cero medido.

El funcionamiento de PD, MLP, GRU y LSTM y el entrenamiento por imitación se explican con la profundidad necesaria para interpretar la ejecución. La aplicación no añade una página de conclusiones del TFG ni un veredicto automático sobre qué controlador es mejor.

## Presentación, accesibilidad y estados

La aplicación aplica el [sistema visual común](../../concurso-prototipos-eiiia-2026/docs/identidad.md#sistema-visual-común): jerarquía luminosa, tipografía, colores con significado, unidades próximas al valor y distinción de series además del color. Las referencias visuales de Misión, Composición, Comparación, Análisis y Telemetría completa orientan la composición; sus cifras y curvas ilustrativas no son datos del producto.

En escritorio, la trayectoria o gráfica ocupa la zona principal y los controles se agrupan junto a ella. En móvil, Misión muestra primero elección y ajustes esenciales y después previsualización; Comparación mantiene juntos visor y reproductor; Análisis permite elegir señales antes de mostrar gráfica y tabla. No se reduce simplemente una pantalla de escritorio. La experiencia admite teclado, foco visible, nombres accesibles, zoom y reflujo; el visor 3D tiene un resumen textual y las métricas son legibles fuera de él. La reproducción se puede pausar y respeta la preferencia de movimiento reducido.

Se distinguen de forma visible los estados **sin misión**, **configuración inválida**, **preparando**, **ejecutando**, **resultado completo**, **resultado parcial**, **interrumpido** y **artefacto no disponible**. Los mensajes explican qué ocurrió y qué acción puede tomar el visitante. Una interrupción de un controlador no borra la telemetría de los demás ni convierte un límite de seguridad en «misión completada».

## Comprobaciones de aceptación

1. El visitante puede elegir cada una de las cinco familias, recibir variantes iniciales que pueden cambiar en sucesivas elecciones, ajustar sus parámetros admitidos y recuperar exactamente la configuración de una prueba. El punto de inicio aparece y no se edita de forma independiente.
2. Los presets waypoint propuestos por defecto no corresponden a rutas de `train` ni `test`; un visitante puede introducir coordenadas nuevas y ver la ruta antes de ejecutarla. El entrenamiento regenerado conserva las geometrías y divisiones originales, sin incorporar estos presets de aplicación.
3. Un círculo horizontal con inclinación cero conserva la referencia del simulador existente. Un círculo inclinado válido muestra y ejecuta posición, velocidad, aceleración y orientación coherentes; sus límites de altura, velocidad tangencial y aceleración se comprueban antes de ejecutar.
4. El editor crea una composición de dos a cuatro tramos de tipos mezclados, permite orden y duración de los tramos continuos, muestra transiciones y aplica un único PD según la mayor longitud nominal. Empates, solo `hold` y presencia de lemniscata tienen resultado determinista y visible.
5. PD, MLP, GRU y LSTM ejecutan la misma configuración y semilla. La comparación no cambia física, viento o punto de inicio entre controladores y no se alimenta con una ejecución anterior cuando una nueva falla.
6. La comparación reproduce ruta nominal y ejecuciones con un cursor común; pausar, mover el cursor, cambiar velocidad y activar GRU/LSTM mantienen la sincronía. Una ejecución cortada se detiene en su última muestra y expone la causa. En waypoint se distingue ruta común de referencia temporal propia.
7. Estado, separación media y separación máxima proceden de las métricas del simulador y se muestran con unidades y alcance temporal. Un tiempo límite de trayectoria continua y una terminación por waypoint se explican de manera distinta; no aparece una clasificación universal.
8. Análisis muestra gráficas con unidades y explicación. Telemetría completa permite localizar y representar campos presentes, consultar el mismo instante que en la reproducción y exportar muestras; no inventa valores donde una señal falta.
9. La demostración arranca con PD, checkpoints outer-force, normalización y configuración disponibles localmente, sin red ni entrenamiento. Un artefacto ausente o incompatible produce un diagnóstico claro. Los nuevos resultados quedan separados de la memoria y `results/` históricos.
10. El primer recorrido y el detalle funcionan en escritorio y móvil, con teclado, reflujo, foco visible, significado no dependiente solo del color y alternativa textual al visor. Se revisan visualmente e interactuando, además de comprobar que la aplicación arranca.

## Fuera de esta versión

No hay vuelo físico, datos de sensores reales, garantía de seguridad operacional, dibujo libre de trayectorias, reentrenamiento desde la interfaz ni incorporación de misiones creadas por el visitante al dataset. La comparación principal no añade `neural_position` como otros tres controladores. No se recalculan los resultados académicos del TFG ni se publica una conclusión general a partir de un ensayo puntual. Las composiciones anidadas del motor no se exponen en la primera interfaz.

## Fuentes de comportamiento existentes

- [Capacidades del simulador](simulador/README.md), [escenarios y trayectorias YAML](simulador/escenarios_yaml.md) y [control neuronal](simulador/control_neuronal.md).
- [Decisiones de producto](decisiones-producto.md) y [referencias visuales](../../concurso-prototipos-eiiia-2026/docs/identidad.md).
- [Memoria del TFG](../TFG_Memoria/) y [resultados históricos](../results/) para el alcance académico, separados de las ejecuciones de NeuroFlight.
