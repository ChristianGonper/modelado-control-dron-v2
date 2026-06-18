# Diagramas vectoriales de la memoria

Guardar aquí el archivo SVG editable de cada diagrama y su exportación PDF con
el mismo nombre base:

```text
control_hibrido.svg
control_hibrido.pdf
```

La memoria incluirá la versión PDF mediante `\includegraphics`, mientras que el
SVG conservará la fuente vectorial editable. Este flujo mantiene una compilación
estable con `pdflatex` y evita depender de conversiones automáticas o de
`shell-escape`.

Los diagramas deben usar etiquetas en español, fondo claro, tipografía legible y
un significado que no dependa únicamente del color.
