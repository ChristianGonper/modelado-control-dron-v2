# Fuentes reproducibles de los diagramas

Los diagramas pueden realizarse en SVG, TikZ u otro formato original compatible
con el flujo LaTeX. Debe conservarse siempre la fuente editable, no solo la
exportación incluida en la memoria.

Cada diagrama tendrá además una ficha Markdown con el mismo nombre base. La ficha
permitirá repetirlo o revisarlo sin depender de recordar cómo se creó. Se partirá
de `PLANTILLA.md`:

```text
control_hibrido.svg
control_hibrido.pdf
control_hibrido.md

flujo_multirrate.tex
flujo_multirrate.md
```

La ficha debe registrar como mínimo:

1. intención y pregunta que responde;
2. mensaje que debe obtener el lector;
3. elementos, relaciones y jerarquía visual;
4. convenciones físicas, símbolos, unidades, colores y etiquetas;
5. fuentes de datos o afirmaciones representadas;
6. herramienta y procedimiento de generación;
7. prompt, código o pasos manuales necesarios para reproducirlo;
8. forma de inclusión o exportación y comprobaciones visuales.

Para SVG se conservarán el `.svg` editable y, cuando se use `pdflatex`, su
exportación `.pdf`. Para TikZ u otro diagrama nativo se conservará el `.tex`
incluido o compilable. Las gráficas derivadas de resultados deben registrar
también el script, comando, datos de entrada y revisión Git de procedencia.

Los diagramas deben usar etiquetas en español, fondo claro, tipografía legible y
un significado que no dependa únicamente del color.
