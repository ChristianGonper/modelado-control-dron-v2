# Anexo A01 — Gobierno, entorno y reproducibilidad

**Fecha:** 2026-06-10 | **Owner:** A01

## Superficie revisada

`AGENTS.md`, `SPEC.md` (no versionado), `.gitignore`, `pyproject.toml`, `uv.lock`, `data/.gitignore`, `results/.gitignore`, `src/simulador_quad/app.py` (metadata), muestra `data/classic_dataset/v1/results/**/metrics.json`.

## Invariantes y contratos comprobados

- Metadata de ejecución incluye `git_commit` y `git_dirty` (`app.py:53-54`).
- `uv.lock` presente y coherente con dependencias torch/cuda.
- Regla AGENTS: commits solo bajo indicación explícita.

## Hallazgos del dominio

| ID | Sev. |
|----|------|
| F-001 | P1 |
| F-003 | P1 |
| F-008 | P2 |
| F-019 | P3 |
| F-020 | P3 |

## Históricos revalidados

- Metadata commit/lock: **cerrado en diseño** (mayo 2026); **abierto en evidencia almacenada** (F-003).

## No verificable

- Hash `uv.lock` en todos los metrics.json locales (no presente en muestra).

## Zonas sin problemas

- `uv sync` / entorno `.venv` operativo para pytest.
- HEAD único y rama limpia salvo `?? SPEC.md`.

## Comandos y resultados

| Comando | Resultado |
|---------|-----------|
| `git status --short` | `?? SPEC.md` |
| `git rev-parse HEAD` | `560c5a879fbc7cf307607d8a4721624a999638a3` |
| `git log -1 --format=fuller` | 2026-06-10, «Documenta paralelizacion de pipelines PID» |
| `git ls-files` | 179 archivos |

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A12 | ¿Evidencia local compensa .gitignore? | No: F-001 P1 confirmado |
| A10 | ¿Campaña dry-run coherente con paths? | Sí; fase 6 position_gain esperada |
| A14 | ¿Memoria exige commit trazable? | Sí; conflicto F-003 |