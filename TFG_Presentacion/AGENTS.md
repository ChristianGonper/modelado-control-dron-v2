# AGENTS.md

## Proposito

Esta carpeta contiene la presentación programable de la defensa del TFG. La
memoria en `../TFG_Memoria/` se considera cerrada y se usa solo como fuente de
contenido, figuras y resultados.

## Stack

- Usa Quarto + Reveal.js para el deck principal.
- El artefacto principal es HTML; genera o prepara siempre un PDF de respaldo.
- La presentación debe poder construirse localmente sin depender de servicios web.
- Renderiza HTML con `quarto render deck.qmd` desde esta carpeta.
- Exporta el PDF de respaldo con
  `npx -y decktape reveal deck.html deck.pdf`.
- Si Quarto falta en la máquina, instalar con:
  `winget install --id Posit.Quarto --exact`.

## Fuentes de verdad

- `../TFG_Memoria/main.tex` y `../TFG_Memoria/sections/`: narrativa final cerrada.
- `../TFG_Memoria/Figuras/`: figuras finales de la memoria.
- `../results/`: CSV agregados versionados usados para resultados.
- `../docs/simulador/`: documentación viva del simulador y la ejecución.

## Reglas de assets

- No edites a mano SVG, PDF o PNG generados.
- Genera SVG desde Matplotlib cuando exista fuente de datos/código.
- Convierte PDF/TikZ vectorial a SVG con `pdftocairo` cuando la fuente cerrada
  sea una figura de la memoria.
- Usa PNG solo para contenido originalmente raster o excepciones justificadas.
- Los assets generados viven bajo `assets/generated/` y deben poder regenerarse
  con `scripts/build_assets.py`.

## Reglas narrativas
- No conviertas el deck en una versión comprimida de la memoria. Prioriza
  claridad oral, ritmo de 20 minutos y figuras legibles.
- Antes de expandir el contenido definitivo en el archivo quarto, conserva el MVP como esqueleto
  navegable sobre el framework.
