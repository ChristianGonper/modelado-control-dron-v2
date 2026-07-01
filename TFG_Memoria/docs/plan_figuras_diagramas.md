# Plan de figuras, tablas y diagramas

## Principios visuales

- Cada figura debe responder una pregunta o explicar un mecanismo.
- Las comparaciones usarán colores consistentes para PD especializado, PD
  transferido, MLP, GRU y LSTM.
- No se dependerá únicamente del color: se combinarán marcadores, patrones o
  etiquetas.
- Los diagramas se realizarán preferentemente en TikZ standalone integrado en
  LaTeX. También podrán realizarse con Python, Matplotlib u otras librerías de
  dibujo cuando el resultado sea más claro, especialmente para representaciones
  geométricas, trayectorias, señales o esquemas que convenga generar por script.
- Cada diagrama conservará su fuente editable y una ficha reproducible con el
  mismo nombre base, según `../Figuras/diagramas/README.md`.
- Toda figura nueva requiere ficha antes de su desarrollo. Solo se procederá a
  crear o regenerar una figura cuando el usuario lo pida explícitamente en la
  instrucción de trabajo.
- Los snippets serán breves y usarán el estilo `codigoTFG` definido en
  `preamble.sty`.

## Diagramas explicativos previstos

La columna «Finalidad» fija la intención mínima. Antes de realizar cada diagrama
se ampliará en su ficha con el mensaje, elementos, relaciones, convenciones,
fuentes y método de reproducción. La ficha se mantendrá sincronizada cuando el
diagrama cambie.

| Capítulo | Diagrama | Finalidad |
|---|---|---|
| Introducción | `FIG-001` Hipótesis y estrategia experimental | Mostrar conjunto de PD, selección de expertos, imitación y comparación de las tres referencias en ID y OOD. Fuente TikZ disponible. |
| Estado del arte | `FIG-014` Arquitecturas neuronales para control | Comparar MLP, RNN básica y arquitecturas recurrentes con compuertas sin duplicar la ventana temporal de `FIG-013`. Fuente TikZ disponible y ficha actualizada. |
| Estado del arte | `FIG-015` Actuación y movimiento de un cuadricóptero | Explicar cómo cuatro rotores generan empuje colectivo y momentos, y por qué el movimiento lateral exige inclinar el vehículo. Ficha creada; fuente pendiente. |
| Metodología 3.1 | `FIG-002` Marcos ENU y FRD | Fijar signos, ejes y dirección de empuje. Fuente TikZ disponible y ficha actualizada. |
| Metodología 3.1 | `FIG-003` Flujo multirrate | Explicar referencia, control, mezclador, actuadores, dinámica y telemetría. Fuente TikZ disponible y ficha actualizada. |
| Metodología 3.1 | `FIG-011` Configuración de rotores | Mostrar configuración en X, orden de rotores y signo de giro usado por el mixer. Fuente TikZ disponible y ficha actualizada. |
| Metodología 3.1 | `FIG-009` Familias de trayectorias | Mostrar de un vistazo qué capacidad exige `hold`, `circle`, `lissajous` y `waypoint`. Ficha actualizada; en este worktree no existe todavía `FIG-009.tex`, solo generación PDF por script. |
| Metodología 3.1 | `FIG-010` Perfiles de waypoint | Explicar perfil trapezoidal/triangular y relación entre posición, velocidad y aceleración escalar. Ficha actualizada; en este worktree no existe todavía `FIG-010.tex`, solo generación PDF por script. |
| Metodología 3.1 | `FIG-012` Mixer con saturación | Mostrar flujo de reparto de mandos del mixer, desplazamiento del colectivo y recorte de momentos bajo saturación. Fuente TikZ disponible y ficha actualizada. |
| Metodología 3.2 | `FIG-004` Control PD en cascada | Mostrar lazo externo de posición y lazo interno de actitud. Fuente TikZ disponible y ficha actualizada. |
| Metodología 3.2 | `FIG-005` Búsqueda progresiva | Mostrar diagnóstico, candidatos, filtros, refinamiento y congelación. Fuente TikZ disponible y ficha actualizada. |
| Metodología 3.3 | `FIG-006` Predicción de fuerza deseada | Mostrar entradas, MLP/GRU/LSTM, protecciones y lazo interno común. Fuente TikZ disponible y ficha actualizada. |
| Metodología 3.3 | `FIG-013` Ventana deslizante recurrente | Representar la ventana deslizante temporal, el avance del lote recurrentemente y el padding por repetición al inicio. Fuente TikZ disponible y ficha actualizada. |
| Metodología 3.5 | `FIG-007` Flujo completo del procedimiento experimental | Conectar datasets, tuneo, entrenamiento y comparaciones. Fuente TikZ disponible y ficha actualizada. |
| Metodología 3.5 | `FIG-008` Niveles de evaluación | Separar familias vistas, transferencia, composiciones y trayectorias nuevas. Fuente TikZ disponible y ficha actualizada. |
| Trabajo futuro | Paso hacia dron real | Mostrar sensores, estimación, control y percepción a bordo. |

## Gráficas y tablas del capítulo de resultados

| ID archivo | Ubicación | Uso en memoria | Procedencia |
|---|---|---|---|
| `res_pid_transfer_matrix` | `TFG_Memoria/Figuras/resultados/` | Cuerpo: transferencia PD clásica | `comparison.py`, CSV consolidado |
| `res_id_rmse_family` | `TFG_Memoria/Figuras/resultados/` | Cuerpo: RMSE en condiciones conocidas | `comparison.py` |
| `res_ood_rmse_family` | `TFG_Memoria/Figuras/resultados/` | Cuerpo: figura principal OOD por familia | `comparison.py` |
| `res_ood_scenario_matrix` | `TFG_Memoria/Figuras/resultados/` | Cuerpo: desglose OOD por escenario/controlador | `comparison.py` |
| `res_ood_termination_summary` | `TFG_Memoria/Figuras/resultados/` | Cuerpo: modos de terminación OOD | `comparison.py` |
| `res_trajectory_lemniscate_mlp_lstm` | `TFG_Memoria/Figuras/resultados/` | Cuerpo: caso representativo MLP/LSTM | Telemetría `lemniscate_fast_center_yaw` |
| `res_protections_ood` | `TFG_Memoria/Figuras/resultados/` | Cuerpo: protecciones y degradación en OOD | `comparison.py` |
| `atlas_trayectorias_id` | `TFG_Memoria/Figuras/resultados/` | Anejo: muestra visual de familias conocidas | Telemetrías de dataset clásico |
| `atlas_trayectorias_ood` | `TFG_Memoria/Figuras/resultados/` | Anejo: muestra visual de trayectorias OOD | Telemetrías OOD |
| `atlas_trayectoria_helix_3d` | `TFG_Memoria/Figuras/resultados/` | Anejo: vista 3D de hélice OOD | Telemetría OOD |
| `tab:cobertura-campana` | `07_resultados.tex` | Cobertura y validez | `comparison_all_runs.csv` |
| `tab:fidelidad-supervisada` | `07_resultados.tex` | H3 fidelidad supervisada | `data/neural_control/*/metrics/test_force_metrics.json` |
| `tab:sintesis-resultados` | `07_resultados.tex` | Lecturas principales de la ejecución | Evidencia consolidada |

Comando de regeneración:

```powershell
uv run simulador-quad plot-comparison results/comparison_all_runs.csv --out TFG_Memoria/Figuras/resultados --formats pdf png
```

## Decisiones editoriales para resultados

1. El cuerpo usa alta densidad curada: siete figuras principales y tres tablas.
2. El éxito de misión no se representa en ID porque apenas discrimina; se usa
   solo para modos de fallo OOD.
3. Las figuras `atlas_*` muestran el trabajo realizado y la variedad de
   trayectorias; no sustituyen a la evidencia cuantitativa del cuerpo.
4. Las figuras antiguas `mem_*` y `c1--c7` dejan de formar parte de la línea editorial vigente.
