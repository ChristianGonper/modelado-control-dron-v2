# AGENTS.md

## Propósito

Esta carpeta contiene la memoria LaTeX del TFG sobre un simulador 6DOF de
cuadricóptero para comparar control clásico y control neuronal por imitación.
Toda tarea de redacción, revisión o integración de contenido académico en esta
carpeta debe usar la skill `redactar-latex-academico`.

## Fuentes de verdad

- [../README.md](../README.md) y [../docs/](../docs/): alcance, requisitos y estado del simulador.
- [../src/](../src/), [../scenarios/](../scenarios/), [../tests/](../tests/), [../tools/](../tools/), [../data/](../data/) y
  [../results/](../results/): implementación y evidencia experimental.
- [docs/requisitos_reglamento.md](docs/requisitos_reglamento.md): requisitos formales del TFG.
- [docs/indice_detallado_memoria.md](docs/indice_detallado_memoria.md): estructura prevista de la memoria.
- [docs/metodologia_redaccion.md](docs/metodologia_redaccion.md): proceso para redactar y revisar apartados.
- [docs/criterios_redaccion_y_decisiones.md](docs/criterios_redaccion_y_decisiones.md): criterios académicos, decisiones
  técnicas que deben justificarse y frontera entre contenido técnico y software.
- [docs/plan_fuentes.md](docs/plan_fuentes.md), [docs/plan_figuras_diagramas.md](docs/plan_figuras_diagramas.md) y
  [docs/referencias_cruzadas_pendientes.md](docs/referencias_cruzadas_pendientes.md): planificación de fuentes, material
  gráfico y referencias pendientes.
- [docs/citas_pendientes_redaccion.md](docs/citas_pendientes_redaccion.md): afirmaciones que requieren fuente
  bibliográfica antes de cerrar la memoria.
- [Figuras/diagramas/](Figuras/diagramas/): fichas y fuentes editables de diagramas previstos.

No uses [../docs/html/](../docs/html/) como fuente de verdad.

## Reglas esenciales

- Respeta la estructura, macros, bibliografía, convenciones y herramienta de
  compilación existentes.
- No inventes resultados, referencias, decisiones ni capacidades; contrasta con
  evidencia del repositorio antes de cerrar afirmaciones técnicas.
- Si cambian narrativa, estructura, bibliografía, figuras o resultados usados en
  la memoria, actualiza también los documentos de planificación afectados en
  `docs/`.
- Mantén trazabilidad entre objetivos, modelo, implementación, escenarios,
  métricas, resultados y conclusiones.
- Conserva las fuentes editables de figuras y diagramas, junto con su ficha de
  intención, convenciones y reproducción cuando proceda.
- No elimines comentarios editoriales de `CITA PENDIENTE`, `FIGURA PENDIENTE`
  o notas de autor salvo petición explícita; si una cita o figura se resuelve,
  actualiza la planificación correspondiente antes de retirar la marca.
- Registra nuevas referencias cruzadas inestables en
  [docs/referencias_cruzadas_pendientes.md](docs/referencias_cruzadas_pendientes.md) y nuevas necesidades bibliográficas
  en [docs/citas_pendientes_redaccion.md](docs/citas_pendientes_redaccion.md).
- No modifiques la declaración de uso de IA hasta la revisión final.
- No hagas commits salvo petición explícita del usuario.
- Las referencias a archivos, rutas o documentos deben escribirse siempre como enlaces markdown funcionales (`[docs/metodologia_redaccion.md](docs/metodologia_redaccion.md)`), no como texto plano entre comillas ni comillas invertidas.
- Si entre dos turnos de trabajo aparecen modificaciones manuales realizadas por el usuario en el repositorio, nunca deben revertirse de forma automática. Si alguna modificación es crítica, altera sustancialmente la funcionalidad o entra en contradicción directa con los criterios gobernantes del proyecto, se debe consultar primero al usuario antes de actuar sobre ella.

## Herramientas de exploración

- Usa Context7 para documentación actualizada de LaTeX, paquetes y herramientas,
  priorizando fuentes oficiales compatibles con la configuración del proyecto.

## Interpretación de peticiones

- Si el usuario pide redactar, revisar, reestructurar, integrar verbalizaciones,
  corregir estilo o trabajar sobre `.tex`, aplica la skill
  `redactar-latex-academico` y edita los archivos correspondientes.
- Si el usuario está verbalizando ideas para la memoria, trátalas como criterio
  autoral que debe integrarse o clasificarse, no como una transcripción literal.
- Si el usuario propone una idea sin pedir edición inmediata, contrástala con la
  estructura y evidencia disponibles; devuelve una recomendación concreta y
  actualiza planificación solo si lo pide o si forma parte natural de la tarea.
- Si el usuario pide a la vez propuesta y ejecución, explica brevemente el
  criterio aplicado y realiza los cambios coherentes sin detenerte en decisiones
  menores.
- Pregunta solo cuando falte una decisión autoral no inferible o haya varias
  opciones con consecuencias narrativas, técnicas o reglamentarias relevantes.

## Gestión de documentación

- Los archivos `.tex` contienen la memoria compilable.
- `docs/` contiene planificación, requisitos, metodología, decisiones,
  bibliografía pendiente, figuras previstas y referencias cruzadas; actualízalo
  cuando una edición cambie esas piezas.
- `Figuras/` contiene material gráfico final o en preparación; conserva fuentes
  editables y no sustituyas fichas por archivos exportados.
- Los archivos auxiliares generados por LaTeX no son fuente de verdad y no deben
  editarse manualmente.

## Documentación que consultar según la tarea

- Para redactar o revisar un apartado: [docs/metodologia_redaccion.md](docs/metodologia_redaccion.md),
  [docs/criterios_redaccion_y_decisiones.md](docs/criterios_redaccion_y_decisiones.md) e
  [docs/indice_detallado_memoria.md](docs/indice_detallado_memoria.md).
- Para comprobar alcance, hipótesis, trazabilidad y criterios académicos:
  [../docs/01_principios_tfg.md](../docs/01_principios_tfg.md) y los documentos vivos de [../docs/simulador/](../docs/simulador/).
- Para explicar simulador, dinámica, control, redes neuronales, campañas,
  métricas o resultados: contrasta con [../src/](../src/), [../scenarios/](../scenarios/), [../tools/](../tools/),
  [../data/](../data/), [../results/](../results/) y la documentación relacionada en [../docs/](../docs/).
- Para bibliografía: usa [docs/plan_fuentes.md](docs/plan_fuentes.md) y registra nuevas necesidades en
  [docs/citas_pendientes_redaccion.md](docs/citas_pendientes_redaccion.md); no añadas citas no verificadas.
- Para figuras o diagramas: revisa [docs/plan_figuras_diagramas.md](docs/plan_figuras_diagramas.md) y las fichas
  de [Figuras/diagramas/](Figuras/diagramas/); si propones una figura nueva, crea o actualiza su
  ficha con intención, contenido, convenciones y fuente de reproducción. No
  registres descripciones de figuras en documentos laterales si ya existe una
  ficha `Figuras/diagramas/FIG-xxx.md`; usa la ficha y sincroniza el plan.
- Para referencias cruzadas todavía inestables: registra o actualiza
  [docs/referencias_cruzadas_pendientes.md](docs/referencias_cruzadas_pendientes.md).
