# Anexo A13 — Ecosistema documental

**Fecha:** 2026-06-10 | **Owner:** A13

## Superficie revisada

`README.md`, `docs/simulador/*`, `docs/reviews/*`, `docs/plans/archived/*`, ausencia `docs/preliminary/`, `docs/reviews/README.md`.

## Invariantes y contratos comprobados

- `docs/simulador/trazabilidad.md` matriz 28 requisitos operativa.
- `docs/simulador/validacion.md` comandos y separación OOD.
- `docs/reviews/README.md` prioriza jun-02 y marca mayo histórico.
- `docs/preliminary/` eliminado (SPEC hipótesis confirmada refutada).

## Hallazgos del dominio

| ID | Sev. |
|----|------|
| F-010 | P2 |
| F-013 | P2 |
| F-015 | P2 |
| F-016 | P2 |
| F-018 | P3 |

## Históricos revalidados

- README vacío (mayo): **cerrado**.
- preliminar sobrerreclama: **cerrado** (carpeta ausente).

## No verificable

- Calidad textual exhaustiva de 28 specs archived (muestreo).

## Zonas sin problemas (sin contradicción con F-016)

- **`docs/simulador/`** coherente con código y 151 tests: arquitectura, control_neuronal, dataset_clasico, guia_uso alineados junio 2026.
- **`docs/reviews/README.md`** etiqueta correctamente multivista mayo como histórica y jun-02 como diagnóstico previo.
- **`docs/plans/archived/README.md`** declara explícitamente que planes activos no están en archived como vigentes.
- Enlaces rutas en README a herramientas existentes verificados por `--help` dry-run.
- F-016 afecta **ficheros individuales mayo sin banner**, no el índice README ni docs/simulador/ (zona limpia).

## Comandos

Análisis estático; listado `docs/plans/` → solo `archived/`.

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A02 | ¿Normativa reflejada en simulador/? | Sí |
| A14 | ¿Memoria AGENTS alineado? | No F-009 |
| A01 | ¿README reproducibilidad? | Parcial F-001 |