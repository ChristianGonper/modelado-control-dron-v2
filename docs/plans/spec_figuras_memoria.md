# Spec: figuras cientificas para la memoria

## Estado

Propuesta pendiente de validacion antes de implementar.

## Supuestos propuestos

1. Las figuras destinadas a la memoria se insertaran principalmente al ancho
   completo del texto, aproximadamente `155 mm` segun la geometria A4 actual.
2. El artefacto principal de una figura cientifica sera PDF vectorial. Tambien
   se generara PNG a `300 dpi` para inspeccion rapida y otros usos.
3. Las figuras se generaran desde artefactos trazables (`telemetry.json`,
   `metrics.json` y tablas comparativas), no desde notebooks manuales.
4. La memoria seguira usando Latin Modern; las figuras intentaran usar Latin
   Modern Roman y tendran una alternativa portable.
5. El visor Plotly 3D seguira siendo una herramienta de inspeccion, no una
   figura citable de la memoria.
6. Los esquemas conceptuales del modelo, marcos ENU/FRD y arquitectura no se
   generaran desde telemetria ni se mezclaran con este modulo.

## Objetivo

Convertir `simulador_quad.visualization` en una fuente reproducible de figuras
cientificas aptas para la memoria, manteniendo tambien su utilidad para
diagnosticar corridas individuales.

El modulo debe:

- aplicar un lenguaje visual comun y deliberado;
- exportar PDF vectorial y PNG de alta resolucion;
- distinguir diagnostico por episodio de evidencia comparativa;
- conservar unidades, marcos ENU/FRD y significado fisico;
- evitar figuras saturadas o redundantes;
- permitir reconstruir cada figura desde resultados trazables.

## Principios editoriales

- La leyenda y los estilos visuales codifican significado, no decoracion.
- El color nunca sera el unico modo de distinguir series: se combinaran color,
  tipo de linea y, cuando proceda, marcador.
- Las figuras deben seguir siendo legibles impresas en escala de grises.
- Los titulos descriptivos se colocaran en el pie de figura de LaTeX. El perfil
  de memoria omitira normalmente titulos dentro de los ejes.
- Las magnitudes fisicas se expresaran con simbolo, marco y unidad.
- Se evitaran graficos de barras cuando una distribucion, intervalo o punto
  permita mostrar mejor los datos.
- No se mezclaran magnitudes con unidades distintas en un mismo eje.
- La precision visual no debe sugerir mas precision experimental de la real.

## Catalogo de figuras

### A. Esquemas conceptuales de la memoria

No pertenecen al modulo de telemetria, pero deben planificarse para que el
informe tenga un lenguaje visual completo:

| ID | Figura | Uso principal | Fuente |
|---|---|---|---|
| A1 | Marcos mundo ENU y cuerpo FRD | Modelo fisico | Ilustracion/TikZ |
| A2 | Fuerzas, momentos y geometria de rotores | Modelo y mixer | Ilustracion/TikZ |
| A3 | Arquitectura de control en cascada | Control clasico | Diagrama |
| A4 | Flujo de imitacion y evaluacion cerrada | Control neuronal | Diagrama |
| A5 | Protocolo experimental y splits | Metodologia | Diagrama |

Estos esquemas deben compartir tipografia y colores semanticos con las figuras
experimentales, pero no se generaran automaticamente desde `visualization`.

### B. Figuras por episodio

Sirven para explicar un escenario representativo y para diagnosticar fallos.
No todas deben aparecer para cada escenario en la memoria.

| ID | Figura | Contenido | Prioridad en memoria |
|---|---|---|---|
| B1 | Trayectoria horizontal ENU | Referencia, trayectoria, inicio y fin; ejes con escala igual | Alta |
| B2 | Trayectoria espacial ENU estatica | Referencia y trayectoria 3D en PDF | Media |
| B3 | Seguimiento de posicion | `X_W`, `Y_W`, `Z_W` frente a referencia, tres paneles | Alta |
| B4 | Error de posicion | Error euclideo y, opcionalmente, umbral relevante | Alta |
| B5 | Actitud | Roll, pitch y yaw, tres paneles | Media |
| B6 | Velocidad angular | `p`, `q`, `r`, tres paneles | Diagnostico |
| B7 | Accion de control | Empuje colectivo y momentos solicitados | Media |
| B8 | Actuadores | Omega objetivo/aplicada, saturacion y degradacion | Alta para fallos |
| B9 | Fuerza externa neuronal | Fuerza predicha, recortada y referencia experta si existe | Alta para red |
| B10 | Perturbacion y respuesta | Viento junto con error o respuesta relevante | Media |

Para la memoria se recomienda combinar B1, B3 y B4 en una figura multipanel
por escenario representativo. B6 y las cuatro curvas detalladas de rotor se
reservan principalmente para diagnostico o anejos.

### C. Figuras comparativas agregadas

Son las figuras centrales del capitulo de resultados y requieren una entrada
tabular con varias corridas, no una sola telemetria.

| ID | Figura | Pregunta que responde |
|---|---|---|
| C1 | RMSE por controlador y familia | Que controlador sigue mejor cada familia |
| C2 | Tasa de exito por controlador y condicion | Que controlador conserva estabilidad |
| C3 | Degradacion nominal a OOD | Cuanto pierde cada controlador fuera de distribucion |
| C4 | Matriz de transferencia PID | Como generaliza cada PID familiar a otras familias |
| C5 | Error frente a esfuerzo de control | Que compromiso seguimiento-esfuerzo ofrece cada controlador |
| C6 | Saturacion y clipping | Si la estabilidad depende de limites o protecciones |
| C7 | Distribucion de error por episodio | Variabilidad real entre escenarios |
| C8 | Curvas de entrenamiento | Convergencia y diferencia train/validation |
| C9 | Error supervisado frente a desempeno cerrado | Si imitar mejor implica controlar mejor |

Representaciones preferidas:

- puntos con intervalo o dispersion para metricas agregadas;
- boxplot o violin ligero con puntos individuales cuando haya suficientes
  episodios;
- mapa de calor anotado para la matriz de transferencia;
- scatter con identificacion de fallos para error frente a esfuerzo;
- barras solo para tasas o conteos discretos.

## Lenguaje visual

### Formatos y tamanos

- `report-wide`: ancho `155 mm` (`6.10 in`), pensado para `\textwidth`.
- `report-half`: ancho aproximado `75 mm` (`2.95 in`), solo para figuras
  simples.
- `diagnostic`: tamaño flexible para inspeccion en pantalla.
- PDF: vectorial, con fuentes embebidas.
- PNG: `300 dpi`; se permitira `450 dpi` cuando contenga detalles rasterizados.
- Fondo blanco y caja delimitadora ajustada.

### Tipografia

- Familia principal: `Latin Modern Roman`.
- Alternativa portable: `DejaVu Serif`.
- Matematicas: estilo compatible con Computer Modern.
- Texto base de figura `9 pt`; etiquetas y leyenda no menores de `8 pt`.
- La notacion usara simbolos como `$X_W$`, `$Z_W$`, `$\omega$` y unidades entre
  corchetes.

No se activara `text.usetex` por defecto, para evitar que generar figuras
dependa de una instalacion LaTeX completa.

### Colores semanticos

Paleta base apta para daltonismo, inspirada en Okabe-Ito:

| Rol | Color |
|---|---|
| Trayectoria/estado real | `#0072B2` azul |
| Referencia | `#4D4D4D` gris oscuro, linea discontinua |
| PID | `#0072B2` azul |
| MLP | `#E69F00` naranja |
| GRU | `#009E73` verde azulado |
| LSTM | `#D55E00` bermellon |
| Fallo/saturacion | `#CC3311` rojo |
| Inicio/estado valido | `#009E73` verde azulado |
| Informacion secundaria | `#999999` gris |

Los colores de controlador se conservaran en todas las figuras comparativas.
En figuras por episodio, azul significara estado real y gris referencia.

### Detalles graficos

- Grosor principal de linea: `1.4 pt`; referencia: `1.2 pt` discontinua.
- Ejes superior y derecho ocultos salvo que aporten informacion.
- Rejilla muy ligera, preferentemente solo en el eje de lectura principal.
- Leyendas sin marco opaco y colocadas fuera de los datos cuando sea posible.
- Paneles identificados como `(a)`, `(b)`, etc. desde LaTeX o de forma
  consistente.
- Margenes y espacios controlados con `constrained_layout`.
- Notas metricas dentro del grafico solo si explican una observacion; las
  metricas generales pertenecen al pie o a una tabla.

## Perfiles de salida

### Perfil `diagnostic`

- Conserva el conjunto amplio de figuras por episodio.
- Puede incluir titulo interno y anotaciones de metricas.
- Genera PNG y, opcionalmente, PDF.
- Se usa automaticamente tras `simulador-quad run`.

### Perfil `report`

- Omite titulos internos redundantes.
- Usa dimensiones de memoria, tipografia final y leyendas compactas.
- Genera siempre PDF y PNG.
- Genera solo figuras seleccionadas y composiciones multipanel aptas para
  citar.
- Debe poder ejecutarse desde artefactos ya existentes sin repetir simulacion.

### Perfil `comparison`

- Consume CSV/JSON agregados de la campaña experimental.
- Genera las figuras C1-C9 que sean compatibles con los datos disponibles.
- Nunca inventa grupos, intervalos ni corridas ausentes.

## Interfaz propuesta

Mantener compatible el comando actual:

```powershell
uv run simulador-quad plot results\hover_clean\telemetry.json `
  --metrics results\hover_clean\metrics.json `
  --out results\hover_clean\figures
```

Ampliarlo con opciones explicitas:

```powershell
uv run simulador-quad plot results\hover_clean\telemetry.json `
  --metrics results\hover_clean\metrics.json `
  --out results\hover_clean\figures `
  --profile report `
  --formats pdf png
```

La generacion comparativa debe tener una entrada propia, por ejemplo:

```powershell
uv run simulador-quad plot-comparison results\comparison_all_runs.csv `
  --out results\figures_report `
  --formats pdf png
```

La interfaz exacta de `plot-comparison` se cerrara cuando se confirme el
artefacto comparativo canonico del plan activo.

## Estructura propuesta

```text
src/simulador_quad/visualization/
  common.py        -> carga y validacion de datos
  style.py         -> perfiles, tamaños, paleta y contexto Matplotlib
  export.py        -> guardado multiformato y nombres de artefactos
  plots.py         -> figuras por episodio
  comparison.py    -> figuras agregadas de campaña
  three_d.py       -> visor Plotly de diagnostico

tests/
  test_visualization.py
  test_visualization_style.py
  test_visualization_comparison.py
```

No se creara un framework generico de graficos. Las funciones seguiran
representando figuras cientificas concretas.

## Estrategia de pruebas

- Verificar que cada figura solicitada genera PDF y PNG no vacios.
- Verificar la resolucion en pixeles esperada del PNG para un tamaño y DPI
  conocidos.
- Verificar que el PDF empieza con una cabecera PDF valida y no rasteriza
  innecesariamente las curvas.
- Verificar que el perfil `report` no incluye titulo interno por defecto.
- Verificar que la paleta y tamaños semanticos permanecen estables.
- Verificar escala igual en trayectorias XY.
- Verificar errores accionables ante telemetria incompleta.
- Verificar figuras comparativas con un dataset minimo controlado.
- Realizar una inspeccion visual de una corrida representativa y de una figura
  comparativa antes de dar el estilo por cerrado.

Comandos previstos:

```powershell
uv run pytest tests\test_visualization.py tests\test_visualization_style.py -q
uv run simulador-quad plot results\hover_clean\telemetry.json `
  --metrics results\hover_clean\metrics.json `
  --out results\hover_clean\figures_report `
  --profile report `
  --formats pdf png
```

## Limites

### Siempre

- Mantener ENU/FRD, unidades y trazabilidad.
- Generar las figuras desde datos exportados.
- Usar PDF vectorial como formato principal de memoria.
- Mantener legibilidad en color y escala de grises.
- Actualizar README y `docs/simulador/` al cambiar el comportamiento.

### Consultar antes

- Anadir dependencias nuevas.
- Cambiar tipografia o paleta global despues de incorporar figuras a la
  memoria.
- Generar automaticamente figuras dentro de `TFG_Memoria/Figuras/`.
- Decidir que escenarios concretos se citaran como representativos.

### Nunca

- Usar un grafico 3D como unica evidencia cuantitativa de seguimiento.
- Ocultar episodios fallidos en figuras comparativas.
- Presentar dispersion entre escenarios como incertidumbre estadistica.
- Mezclar N y Nm en un eje o llamar esfuerzo fisico al indice heuristico.
- Depender de edicion manual posterior para que una figura sea publicable.

## Criterios de aceptacion

1. Existe un estilo Matplotlib comun, documentado y no basado en defaults.
2. El mismo comando puede regenerar figuras PDF y PNG desde telemetria
   existente.
3. El PDF es el artefacto principal y conserva texto/curvas vectoriales.
4. El PNG de memoria se genera al menos a `300 dpi`.
5. Las figuras usan tipografia, colores, grosores y tamaños coherentes.
6. Hay perfiles separados para diagnostico y memoria.
7. Las figuras por episodio cubren seguimiento, error, control y actuadores.
8. Existe una ruta definida para figuras comparativas agregadas.
9. Los tests focales pasan y se ha realizado inspeccion visual.
10. README y documentacion viva describen formatos, perfiles y comandos.

## Decisiones pendientes de validacion

1. Confirmar PDF + PNG `300 dpi` como formatos por defecto del perfil
   `report`.
2. Confirmar Latin Modern/DejaVu Serif frente a una tipografia sans serif.
3. Confirmar que las figuras de memoria no lleven titulo interno.
4. Confirmar la paleta semantica propuesta para controladores.
5. Confirmar que el conjunto minimo por escenario representativo sea B1+B3+B4
   y que las figuras centrales de resultados sean C1-C7.
6. Confirmar si el perfil `report` debe escribir directamente en
   `TFG_Memoria/Figuras/` o en `results/figures_report/` para copiarse/citarse
   despues de validarlo.
