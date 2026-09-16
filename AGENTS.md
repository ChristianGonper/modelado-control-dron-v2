# AGENTS.md

## Propósito activo

Este repositorio alberga el TFG y, como trabajo activo, la aplicación interactiva
para presentar sus resultados en el concurso de prototipos. El simulador y la
investigación existente son la base validada de la aplicación, no un área de
rediseño.

Consulta primero [ESTADO.md](ESTADO.md). Lee sólo la documentación que corresponda a la
tarea actual:

| Si la tarea afecta a... | Consulta... |
|---|---|
| Alcance o experiencia de producto | [docs/producto/vision.md](docs/producto/vision.md) |
| Relato y demostración | [docs/producto/storytelling.md](docs/producto/storytelling.md) |
| Límites técnicos del trabajo nuevo | [docs/producto/constitucion.md](docs/producto/constitucion.md) |
| Arquitectura o comportamiento existente | [docs/simulador/README.md](docs/simulador/README.md) y su documento específico |
| Evidencia y conclusiones del TFG | [TFG_Memoria/](TFG_Memoria/) o [TFG_Report/](TFG_Report/), sólo cuando sea necesario |
| Identidad, candidatura o metodología común | el documento concreto indicado en [ESTADO.md](ESTADO.md) o la tarea |
| Implementación futura | la spec activa y, sólo en la fase correspondiente, su plan y tareas |

No leas por defecto toda la memoria, los planes archivados, las auditorías ni el
repositorio compartido.

## Autoridad y actualización

| Si cambia... | Modificar primero... | Actualizar además... |
|---|---|---|
| Un límite del trabajo nuevo o un invariante del TFG | [docs/producto/constitucion.md](docs/producto/constitucion.md) | La visión o spec afectada sólo si necesita concretarlo |
| El alcance o comportamiento global de la aplicación | [docs/producto/vision.md](docs/producto/vision.md) | La spec afectada cuando exista |
| El relato o recorrido de demostración | [docs/producto/storytelling.md](docs/producto/storytelling.md) | La spec de interfaz afectada cuando exista |
| Una capacidad concreta | Su `spec.md` | Su `plan.md` y `tasks.md` sólo en las fases autorizadas |
| El foco, fase, spec activa o bloqueo local | [ESTADO.md](ESTADO.md) | [TAREAS.md](TAREAS.md) sólo si cambia trabajo abierto |
| Una intención futura todavía sin spec | [TAREAS.md](TAREAS.md) | Nada más hasta que se decida especificarla |
| Metodología o identidad compartida | El documento canónico enlazado del repositorio común | La documentación local sólo si cambia una concreción de la aplicación |

No actualices el estado ni las tareas del repositorio común por un cambio exclusivo de esta aplicación.

## Invariantes

- Están congelados el modelo físico 6DOF, los lazos de control, los controladores,
  el dataset, el entrenamiento, los modelos entrenados y los resultados del TFG.
- No se reentrenan redes ni se altera el pipeline para construir la aplicación.
- El código nuevo puede ocuparse de interfaz, adaptación, orquestación,
  reproducción, visualización y construcción de trayectorias dentro de los
  límites aprobados.
- El comportamiento nuevo aprobado pertenece a la aplicación del concurso; no
  se atribuye a los resultados científicos originales ni obliga a reescribir la
  documentación histórica del TFG.

## Forma de trabajo

- La especificación define intención y comportamiento; el plan define cómo se
  implementa; las tareas dividen la ejecución. Son autorizaciones separadas.
- Terminar una fase no autoriza comenzar la siguiente.
- Un cambio sustancial se refleja primero en su spec gobernante. Los cambios
  inequívocamente cosméticos o mecánicos no requieren ceremonia documental.
- No añadas comportamiento no especificado ni dupliques información que ya tenga
  una fuente canónica: enlázala.
- Tras validar un incremento, condensa plan y tareas para conservar decisiones,
  resultado, comprobaciones y deuda real sin mantener ruido transitorio.
- Los comandos, verificaciones y criterios técnicos viven en el plan activo, no
  se acumulan en este archivo.
- Las referencias a archivos, rutas o documentos deben escribirse siempre como enlaces markdown funcionales (`[docs/producto/vision.md](docs/producto/vision.md)`), no como texto plano entre comillas ni comillas invertidas.
- Si entre dos turnos de trabajo aparecen modificaciones manuales realizadas por el usuario en el repositorio, nunca deben revertirse de forma automática. Si alguna modificación es crítica, altera sustancialmente la funcionalidad o entra en contradicción directa con los criterios gobernantes del proyecto, se debe consultar primero al usuario antes de actuar sobre ella.

Las instrucciones locales de los subdirectorios prevalecen dentro de su ámbito.
