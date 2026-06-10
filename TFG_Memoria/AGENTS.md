# AGENTS.md — Memoria LaTeX del TFG

## Proposito

Esta carpeta contiene la memoria del TFG. La memoria debe explicar el trabajo como un proyecto de ingenieria aeroespacial: modelado 6DOF, sistemas de referencia, ecuaciones, control, escenarios, datasets, entrenamiento neuronal, evaluacion y resultados.

No debe convertirse en una documentacion interna del codigo. La implementacion software se menciona solo cuando ayuda a entender como se materializan las ecuaciones, los escenarios o la reproducibilidad.

## Fuentes de verdad

- `../docs/01_principios_tfg.md`
- `../docs/02_requisitos_ingenieria_simulador.md`
- `../docs/simulador/`
- `../docs/plans/SPEC.md`
- Resultados regenerados con `metrics.metadata` trazable a commit.

## Reglas de redaccion

- Escribir en espanol academico, claro y sobrio.
- Mantener ENU para mundo y FRD para cuerpo en texto, ecuaciones, figuras y tablas.
- Explicar hipotesis y limitaciones junto a cada modelo: cuerpo rigido, drag lineal, perturbaciones simples, sin validacion con vuelo real.
- Evitar prometer que la red neuronal es siempre mejor: formular la tesis como comparacion honesta de generalizacion, robustez y degradacion frente a PID especificos.
- Declarar el uso de asistencia de IA si lo exige la normativa o la guia de la universidad.

## Reglas LaTeX

- No commitear artefactos generados: `*.aux`, `*.log`, `*.toc`, `*.lof`, `*.lot`, `*.out`, `*.pdf`, `*.synctex*`, `*.bbl`, `*.blg`, `*.run.xml`.
- Preferir estructura modular (`sections/*.tex`, `figures/`, `tables/`, `refs.bib`) cuando se empiece a redactar en serio.
- Usar referencias no rompibles: `Figura~\ref{...}`, `Tabla~\ref{...}`, `Ecuacion~\eqref{...}` o macros equivalentes.
- No insertar capturas o figuras sin procedencia. Cada figura experimental debe poder trazarse a un comando, escenario y telemetria.
- Para ecuaciones, escribir simbolos con unidades y marcos de referencia explicitos. Evitar bloques de codigo largos; si hace falta, usar pseudocodigo o fragmentos muy breves.

## Bibliografia

- Usar estilo IEEE salvo indicacion contraria del tutor.
- Toda afirmacion de estado del arte o metodologia general debe tener cita: dinamica de vuelo, quaterniones, RK4, PID, aprendizaje por imitacion, redes recurrentes.
- No inventar referencias. Si falta una fuente, dejar marcador claro para buscarla.

## IA y autoria

- La IA puede ayudar a estructurar, revisar y proponer redaccion, pero el texto final debe ser revisado y asumido por el autor.
- No introducir citas, resultados o afirmaciones experimentales que no esten verificadas en el repositorio o en fuentes consultadas.
