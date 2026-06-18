# AGENTS.md

## Propósito

Esta carpeta contiene la memoria LaTeX del TFG sobre un simulador 6DOF de
cuadricóptero para comparar control clásico y control neuronal por imitación.
La redacción debe mantener criterio académico y corresponderse con la evidencia
del repositorio.

## Fuentes de verdad

- `../README.md` y `../docs/`: alcance, requisitos y estado del simulador.
- `../src/`, `../scenarios/`, `../tests/`, `../tools/`, `../data/` y
  `../results/`: implementación y evidencia experimental.
- `docs/requisitos_reglamento.md`: requisitos formales del TFG.
- `docs/indice_detallado_memoria.md`: estructura prevista de la memoria.
- `docs/metodologia_redaccion.md`: proceso para redactar y revisar apartados.
- `docs/criterios_redaccion_y_decisiones.md`: criterios académicos y decisiones.
- `docs/plan_fuentes.md`, `docs/plan_figuras_diagramas.md` y
  `docs/referencias_cruzadas_pendientes.md`: planificación de fuentes, material
  gráfico y referencias pendientes.

No uses `../docs/html/` como fuente de verdad.

## Reglas esenciales

- Escribe en español correcto y respeta la estructura, macros y estilo LaTeX.
- Prioriza dinámica, control, escenarios, datasets, entrenamiento y resultados;
  evita convertir la memoria en documentación extensa de software.
- No inventes resultados, referencias, decisiones ni capacidades. Distingue
  hechos verificados, interpretaciones, propuestas y contenido pendiente.
- Justifica las decisiones relevantes y mantén trazabilidad entre objetivos,
  modelo, implementación, escenarios, métricas y resultados.
- Mantén mundo ENU y cuerpo FRD, con unidades, signos e hipótesis explícitos.
- Cita fuentes reales y verificadas e identifica la procedencia de figuras,
  tablas, datos y resultados.
- Introduce los términos técnicos primero en español y registra los nuevos
  acrónimos en `sections/00_abreviaturas.tex`.
- Registra referencias aún inestables en
  `docs/referencias_cruzadas_pendientes.md`.
- Compila y revisa el PDF después de cambios relevantes.
- No modifiques la declaración de uso de IA hasta la revisión final.
- No hagas commits salvo petición explícita del usuario.

## Herramientas de exploración

- Para localizar código, seguir flujos e identificar archivos concretos, usa la
  CLI `grok` mediante `grok --model grok-composer-2.5-fast "..."`.
  Formula preguntas dirigidas y verifica después los archivos señalados.
- Cuando la exploración requiera mayor criterio, una revisión crítica o una
  opinión razonada, usa `agy`. Contrasta sus
  conclusiones con la implementación y la evidencia del repositorio.
- Usa Context7 para documentación actualizada de LaTeX, paquetes y herramientas,
  priorizando fuentes oficiales compatibles con la configuración del proyecto.

## Flujo de redacción

Trabaja apartado por apartado según `docs/metodologia_redaccion.md`. Parte de las
decisiones del usuario y de evidencia verificable; usa las herramientas
anteriores solo como apoyo. Señala la información o justificación que falte y
revisa la coherencia local antes de avanzar.
