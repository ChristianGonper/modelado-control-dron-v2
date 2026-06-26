# Fuentes reproducibles de los diagramas

Los diagramas de la memoria se mantienen preferentemente como fuentes TikZ
standalone (`FIG-xxx.tex`) para que la figura sea editable, versionable y
coherente con el flujo LaTeX. Solo se usará otro formato cuando la figura sea
una gráfica generada a partir de datos o cuando TikZ no sea razonable para el
contenido. En todos los casos debe conservarse la fuente reproducible, no solo
la exportación incluida en la memoria.

Cada diagrama tendrá además una ficha Markdown con el mismo nombre base. La ficha
permitirá repetirlo o revisarlo sin depender de recordar cómo se creó. Se partirá
de `PLANTILLA.md`:

```text
FIG-003.tex
FIG-003.md

FIG-010.py
FIG-010.pdf
FIG-010.md
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

Para TikZ se conservará el `.tex` standalone o incluido. Si el documento usa la
figura mediante `\includegraphics`, la exportación PDF generada desde esa fuente
no sustituye al `.tex`. Para gráficas derivadas de scripts o resultados se
registrarán también el script, el comando, los datos de entrada y la revisión Git
de procedencia. Si se incorpora un SVG por necesidad puntual, se conservarán el
`.svg` editable y la exportación `.pdf`.

Los diagramas deben usar etiquetas en español, fondo claro, tipografía legible y
un significado que no dependa únicamente del color. Cuando el diagrama representa
marcos, fuerzas, momentos o señales de control, la ficha debe declarar
explícitamente el marco de referencia, las unidades y la relación con el código o
la ecuación de la memoria.
