# Anexo A14 — Memoria LaTeX

**Fecha:** 2026-06-10 | **Owner:** A14

## Superficie revisada

`TFG_Memoria/main.tex`, `sections/00-09_*.tex`, `appendices/a_comandos.tex`, `AGENTS.md`, `refs.bib`, `preamble.sty`. PDF generado presente localmente; no recompilado en auditoría.

## Invariantes y contratos comprobados

- ENU/FRD mencionados en estructura modular.
- **Resultados pendientes** explícito (`sections/07_resultados.tex:1-3`).
- **Conclusiones pendientes** (`sections/09_conclusiones.tex:1`).
- Discusión evita superioridad universal neuronal (`08_discusion.tex:1`).
- Dos modos neuronal documentados (`05_control_neuronal.tex:1-5`).

## Hallazgos del dominio

| ID | Sev. |
|----|------|
| F-009 | P2 |

## Históricos revalidados

- Memoria como doc código extenso: **no** — enfoque aeroespacial adecuado en índice.

## No verificable

- Compilación LaTeX sin errores en entorno local.
- Procedencia todas las figuras (carpeta Figuras mayormente institucional).

## Zonas sin problemas

- No hay afirmaciones experimentales concluyentes en resultados (prudente).
- Bibliografía `refs.bib` presente; estilo IEEE en preamble.
- Separación implementado vs pendiente en resultados coherente con F-002/F-004.

## Comandos

READ-ONLY LaTeX; sin `pdflatex`.

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A12 | ¿Tablas citables hoy? | No hasta BL-02b/BL-26 |
| A02 | ¿Alcance TFG respetado? | Sí |
| A13 | ¿AGENTS memoria vs README? | Desalineado F-009 |