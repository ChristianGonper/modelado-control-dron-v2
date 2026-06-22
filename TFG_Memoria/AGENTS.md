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
- Evita convertir la memoria en documentación extensa de software.
- No inventes resultados, referencias, decisiones ni capacidades. Distingue
  hechos verificados, interpretaciones, propuestas y contenido pendiente.
- Justifica las decisiones relevantes y mantén trazabilidad entre objetivos,
  modelo, implementación, escenarios, métricas y resultados.
- Cita fuentes reales y verificadas e identifica la procedencia de figuras,
  tablas, datos y resultados.
- Los diagramas pueden realizarse en SVG, TikZ u otro formato original integrado
  en LaTeX. Conserva la fuente editable y una ficha que describa su intención,
  contenido, convenciones y procedimiento de reproducción.
- Introduce los términos técnicos primero en español y registra los nuevos
  acrónimos en `sections/00_abreviaturas.tex`.
- Registra referencias aún inestables en
  `docs/referencias_cruzadas_pendientes.md`.
- No modifiques la declaración de uso de IA hasta la revisión final.
- No hagas commits salvo petición explícita del usuario.

## Herramientas de exploración

- Usa Context7 para documentación actualizada de LaTeX, paquetes y herramientas,
  priorizando fuentes oficiales compatibles con la configuración del proyecto.

## Flujo de redacción

Trabaja apartado por apartado según `docs/metodologia_redaccion.md`. Parte de las
decisiones del usuario y de evidencia verificable; usa las herramientas
anteriores solo como apoyo. Señala la información o justificación que falte y
revisa la coherencia local antes de avanzar.

Salvo que el usuario indique lo contrario, cada verbalización se entiende como
una revisión autoral apoyada en una versión preliminar redactada previamente por
un agente. Usa esa versión como base de estructura y contraste, pero da prioridad
a las decisiones, correcciones y preferencias expresadas en la verbalización; no
la trates como una transcripción literal ni como una redacción desde cero.
