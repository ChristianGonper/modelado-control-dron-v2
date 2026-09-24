# Póster NeuroFlight · EIIIA 2026

El entregable para enviar es [`poster-neuroflight.pdf`](poster-neuroflight.pdf): una página vertical de **75 × 105 cm**. La cabecera conserva el fondo, la línea institucional y los logos de la plantilla oficial. Solo se sustituyen los campos del título, autor y titulación. El cuerpo se organiza en apartados editables con texto, figuras del TFG y una captura real de NeuroFlight.

## Fuentes del contenido

- **Cabecera:** `assets/header-template.png` es una exportación a 300 ppp de los primeros 13 cm de `C:\Users\chris\Downloads\poster tipo para alumnos exposicion-concurso 2026.pptx`, abierta en modo de solo lectura. El HTML coloca esa imagen sin cambiar su geometría y cubre únicamente los marcadores editables de título, autor y titulación con el color original `#DBEEF4`. La línea institucional y ambos logos permanecen en la imagen original. Las copias separadas de los logos se conservan en `assets/`.
- **TFG:** `assets/tfg-control-hibrido.pdf` copia `TFG_Memoria/Figuras/diagramas/FIG-006.pdf`; `assets/tfg-rmse-test.pdf` copia `TFG_Memoria/Figuras/resultados/res_id_rmse_family.pdf`. Los SVG se derivan de esos PDF para incrustarlos como vectores. La interpretación de la gráfica sigue `TFG_Memoria/sections/07_resultados.tex`, especialmente el texto y pie de la figura en las líneas 100–119.
- **Aplicación:** `assets/app-comparison.png` es una captura auténtica de la vista de comparación, tomada tras ejecutar una misión Lissajous con el paquete local de NeuroFlight. Muestra la reproducción a los 9,80 s de una misión de 20 s. El archivo `assets/app-comparison-full.png` conserva la vista completa. Es una ejecución nueva de la aplicación, separada de la evaluación académica del TFG.
- **Contacto y enlace:** el correo figura en `README.md` del proyecto; el QR apunta al repositorio público `https://github.com/ChristianGonper/modelado-control-dron-v2`.

## Reproducir el PDF

Con Chrome instalado en la ruta configurada en el script:

```powershell
uv run --script docs\poster-neuroflight\render.py
```

El texto del cuerpo y los campos del proyecto en la cabecera se editan en `poster.html`. La captura se puede renovar con el servicio local funcionando y el paquete de modelos disponible:

```powershell
uv run neuroflight
uv run --script docs\poster-neuroflight\capture_app.py
```

`capture_app.py` vuelve a ejecutar la misión; por eso los resultados de una captura nueva pueden variar si cambia el paquete local o el preset. Si se renueva la imagen, hay que revisar también el pie de figura del cartel.

## Verificación realizada

Antes de esta revisión se guardaron `poster-neuroflight_original.pdf` y `poster_original.html`. El PDF nuevo se exportó en una sola página de 2125,92 × 2976 pt (75 × 105 cm). Se comprobó que todas las imágenes cargan, que cada apartado cabe en su espacio y que la página renderizada no presenta recortes ni superposiciones. `poster-preview.png` es una vista reducida para revisar la composición; el PDF conserva las figuras del TFG y el QR en vector.
