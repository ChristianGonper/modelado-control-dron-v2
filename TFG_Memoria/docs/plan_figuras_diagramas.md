# Plan de figuras, tablas y diagramas

## Principios visuales

- Cada figura debe responder una pregunta o explicar un mecanismo.
- Las comparaciones usarán colores consistentes para PD especializado, PD
  transferido, MLP, GRU y LSTM.
- No se dependerá únicamente del color: se combinarán marcadores, patrones o
  etiquetas.
- Los diagramas se conservarán en SVG como fuente editable y se exportarán a PDF
  para incluirlos con `graphicx` y `pdflatex`.
- Los snippets serán breves y usarán el estilo `codigoTFG` definido en
  `preamble.sty`.

## Diagramas explicativos previstos

| Capítulo | Diagrama | Finalidad |
|---|---|---|
| Introducción | Pregunta y estrategia experimental | Mostrar banco de PD, imitación y niveles de evaluación. |
| Estado del arte | Taxonomía de enfoques de control | Situar PD, control aprendido e híbrido. |
| Simulador | Marcos ENU y FRD | Fijar signos, ejes y dirección de empuje. |
| Simulador | Flujo multirrate | Explicar referencia, control, mezclador, actuadores, dinámica y telemetría. |
| Simulador | Arquitectura del banco propio | Contrastar control y trazabilidad con plataformas no adaptadas al objetivo. |
| Control clásico | Control PD en cascada | Mostrar lazo externo de posición y lazo interno de actitud. |
| Control clásico | Búsqueda progresiva | Mostrar diagnóstico, candidatos, filtros, refinamiento y congelación. |
| Control neuronal | Predicción de fuerza deseada | Mostrar entradas, MLP/GRU/LSTM, protecciones y lazo interno común. |
| Metodología | Flujo completo de campaña | Conectar datasets, tuneo, entrenamiento y comparaciones. |
| Metodología | Niveles de evaluación | Separar familias vistas, transferencia, composiciones y trayectorias nuevas. |
| Trabajo futuro | Paso hacia dron real | Mostrar sensores, estimación, control y percepción a bordo. |

## Gráficas y tablas previstas para resultados

1. Tabla de cobertura y validez de ejecuciones.
2. RMSE y tasa de éxito por controlador en familias vistas.
3. Mapa de calor de transferencia cruzada de controladores PD.
4. Comparación separada de variaciones o composiciones de familias conocidas.
5. Comparación separada de trayectorias completamente nuevas.
6. Gráfico seguimiento frente a esfuerzo de control.
7. Saturación, degradación y activación de protecciones.
8. Distribución del error por controlador y escenario.
9. Tabla de fidelidad supervisada de fuerza frente a rendimiento en bucle
   cerrado.
10. Tabla síntesis que responda cada pregunta experimental.

## Prompts iniciales para diagramas SVG

### Control híbrido de predicción de fuerza

> Crear un diagrama técnico vectorial, fondo blanco y estilo académico. Mostrar
> a la izquierda referencia y observación, en el centro una red seleccionable
> MLP/GRU/LSTM que predice una fuerza deseada tridimensional en ENU, después un
> bloque de límites de fuerza e inclinación, y finalmente un controlador clásico
> interno que genera empuje colectivo y momentos. Diferenciar claramente lo
> aprendido de lo clásico. Entregar SVG editable sin efectos rasterizados.

### Flujo experimental

> Crear un diagrama vectorial horizontal del flujo: escenarios declarativos,
> dataset clásico, sintonización y banco de PD, selección de demostraciones,
> entrenamiento MLP/GRU/LSTM, evaluación supervisada, evaluación en bucle
> cerrado y comparación en cuatro niveles. Usar etiquetas en español, formas
> simples y SVG editable.

### Camino hacia vuelo real

> Crear un diagrama vectorial que muestre la evolución desde simulación 6DOF
> hasta vuelo real: mejora del modelo, identificación, sensores, estimador de
> estado, controlador, validación progresiva y percepción visual con conciencia
> situacional. Presentar los pasos como trabajo futuro, sin sugerir que ya están
> implementados. Entregar SVG editable.
