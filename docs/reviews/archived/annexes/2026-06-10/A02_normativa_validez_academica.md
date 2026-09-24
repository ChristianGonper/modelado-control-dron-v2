# Anexo A02 — Normativa y validez académica

**Fecha:** 2026-06-10 | **Owner:** A02

## Superficie revisada

`docs/01_principios_tfg.md`, `docs/02_requisitos_ingenieria_simulador.md`, `docs/03_criterios_ingenieria_software.md`.

## Invariantes y contratos comprobados

- Alcance v1: banco de ensayo, no gemelo digital (`01:5-7`).
- Trazabilidad requisito→resultado explícita (`01:11-18`).
- ENU mundo / FRD cuerpo en requisitos (`02`).
- Reproducibilidad y pruebas en `03`.

## Hallazgos del dominio

Ninguno propietario (hallazgos transversales F-001–F-005 referencian normativa de este dominio).

## Históricos revalidados

- Separación ingeniería aeroespacial / software: **vigente y coherente** con `docs/simulador/`.

## No verificable

- Cumplimiento normativa universidad (IA, extensión memoria) fuera del repo.

## Zonas sin problemas

- No contradicción entre `01–03` y README actual.
- Límites v1 (drag lineal, sin aerodinámica formal) consistentes.

## Comandos

Análisis estático READ-ONLY.

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A13 | ¿Docs viva alineada con normativa? | Sí en temas centrales |
| A14 | ¿Memoria respeta alcance? | Sí; resultados pendientes |
| A11 | ¿Tests cubren requisitos citados? | Parcial; ver A11 (F-007) |