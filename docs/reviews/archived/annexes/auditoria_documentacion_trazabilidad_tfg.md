# Auditoria de documentacion, trazabilidad y adecuacion a TFG

Fecha de auditoria: 2026-05-04  
Alcance: documentacion, trazabilidad y adecuacion academica del repositorio. No se ha modificado codigo fuente ni tests.

## Resumen ejecutivo

El repositorio ya contiene una base normativa solida para un TFG: `docs/01_principios_tfg.md`, `docs/02_requisitos_ingenieria_simulador.md` y `docs/03_criterios_ingenieria_software.md` definen con claridad el objetivo, el alcance fisico, la politica de reproducibilidad y la necesidad de trazabilidad entre requisitos, codigo, escenarios y metricas.

La documentacion viva en `docs/simulador/` esta bastante alineada con el estado actual del codigo y separa bien lo implementado de lo no implementado. Sin embargo, el repositorio no esta aun listo para ser defendido como memoria tecnica sin una depuracion documental: el `README.md` raiz esta vacio, los informes preliminares contienen afirmaciones obsoletas o aspiracionales como si fueran implementadas, los planes/revisiones no reflejan el estado actual, y no existe una matriz de trazabilidad verificable requisito-modelo-codigo-prueba-escenario-metrica.

Verificacion ejecutada:

```powershell
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
```

Resultado observado: `uv run pytest` pasa con 29 tests; `hover_clean` termina por `Time limit reached` y genera telemetria/metricas. Esta verificacion solo confirma funcionamiento basico, no valida la suficiencia documental para tribunal.

## Criterios auditados

- Documentos normativos obligatorios: leidos y usados como referencia.
- README raiz y documentacion de uso.
- `docs/simulador/`: estado implementado, arquitectura, escenarios, guia y mantenimiento.
- `docs/preliminar/`: coherencia con codigo actual y utilidad para memoria.
- `docs/plans/` y `docs/reviews/`: trazabilidad historica y estado de tareas.
- Coherencia entre requisitos normativos y codigo.
- Claridad para tribunal de TFG.
- Comentarios/docstrings necesarios en puntos con impacto fisico.
- Separacion entre alcance actual y futuro control neuronal.

## Hallazgos priorizados

### P0 - Los informes preliminares documentan funcionalidad inexistente o fuera de alcance como si estuviera implementada

Referencias:

- `docs/preliminar/fisica_y_matematicas.md:17` introduce perdida inducida.
- `docs/preliminar/fisica_y_matematicas.md:58` documenta viento Ornstein-Uhlenbeck.
- `docs/preliminar/fisica_y_matematicas.md:63` documenta arrastre parasitario cuadratico.
- `docs/preliminar/arquitectura_software.md:41` usa el paquete `simulador_multirotor`, no `simulador_quad`.
- `docs/preliminar/arquitectura_software.md:50` afirma que existen modelos neuronales MLP/RNN/GRU/LSTM.
- `docs/preliminar/arquitectura_software.md:69` documenta un CLI `multirotor-sim` que no coincide con `simulador-quad`.
- `docs/preliminar/informe_software_simulador.tex:94` incluye una capa de control con PD, MLP, GRU y LSTM.
- `docs/preliminar/informe_software_simulador.tex:119`-`120` lista `mlp.py` y `recurrent.py`.
- `docs/preliminar/informe_fisica_simulador.tex:48` afirma perturbaciones aerodinamicas con viento OU e inducido.
- `docs/preliminar/informe_fisica_simulador.tex:344`-`369` desarrolla controladores neuronales MLP/GRU/LSTM.

Contraste:

- `docs/simulador/README.md:23`-`28` declara correctamente que el controlador neuronal real, entrenamiento, dataset y evaluacion neuronal en bucle cerrado no estan implementados.
- `src/simulador_quad/scenarios/loader.py:81`-`90` solo acepta `controller.type: classic`.
- `src/simulador_quad/dynamics/perturbations.py:23`-`29` implementa viento constante, no OU.
- `src/simulador_quad/dynamics/perturbations.py:5`-`21` y `src/simulador_quad/dynamics/rigid_body.py:31`-`34` implementan drag lineal, no aerodinamica formal cuadratica.

Riesgo academico: alto. Un tribunal podria interpretar que la memoria exagera el alcance, mezcla versiones del sistema o presenta trabajo futuro como resultado. Esto afecta directamente a la defendibilidad del TFG y contradice el principio de alcance limitado de `docs/01_principios_tfg.md:90`-`99` y los limites de validez de `docs/02_requisitos_ingenieria_simulador.md:409`-`419`.

Recomendacion: marcar estos documentos como "historicos/no normativos" o reescribirlos para que reflejen el estado real. Todo contenido sobre OU, perdida inducida, MLP/GRU/LSTM, dataset neuronal y CLI antiguo debe pasar a una seccion explicita de trabajo futuro o eliminarse del material que vaya a memoria.

### P0 - Falta una matriz de trazabilidad minima de requisitos a codigo, pruebas, escenarios y metricas

Referencias normativas:

- `docs/01_principios_tfg.md:11`-`20` exige seguir cada decision desde objetivo academico hasta resultado experimental.
- `docs/02_requisitos_ingenieria_simulador.md:427` exige vinculo con prueba o escenario de validacion.
- `docs/03_criterios_ingenieria_software.md:222` exige vincular resultados con escenario y controlador.

Estado observado:

- `docs/simulador/arquitectura.md:22`-`37` mapea modulos principales.
- `docs/simulador/guia_uso.md:101` indica que `metrics.json` conserva el YAML en `metadata.config`.
- `src/simulador_quad/app.py:49`-`53` efectivamente incluye `scenario_name`, `seed` y `config` en metadatos.

Brecha: no hay un documento o tabla que conecte cada requisito critico con implementacion, prueba, escenario y metrica. Por ejemplo: ENU/FRD, signo de empuje, RK4, ZOH multi-rate, retardo/lag, saturacion, drag lineal, terminacion de episodio y metricas aparecen repartidos, pero no auditables en una matriz unica.

Riesgo academico: alto. La trazabilidad es un criterio central del TFG; sin matriz, la memoria dependera de explicaciones narrativas y sera mas dificil demostrar cumplimiento sistematico.

Recomendacion: crear una tabla `docs/simulador/trazabilidad.md` o una seccion equivalente con columnas: requisito, justificacion fisica, documento normativo, codigo, prueba, escenario, metrica/criterio de aceptacion, estado. No hace falta que sea extensa; debe cubrir requisitos con impacto en validez.

### P1 - El README raiz esta vacio y no orienta al tribunal ni a nuevos revisores

Referencias:

- `README.md` tiene longitud 0.
- `pyproject.toml:4` mantiene `description = "Add your description here"`.
- `pyproject.toml:5` apunta a `README.md` como readme del paquete.

Riesgo academico: medio-alto. La primera entrada al repositorio no explica objetivo, alcance, comandos reproducibles, estructura documental ni estado del control neuronal. Esto perjudica claridad para tribunal y reproducibilidad inicial.

Recomendacion: completar `README.md` con: objetivo TFG, estado actual, limites de alcance, comandos `uv sync`, `uv run pytest`, ejecucion de escenarios, mapa de documentacion y aviso claro de que el control neuronal aun no esta implementado. Actualizar tambien la descripcion del paquete.

### P1 - La separacion entre alcance actual y futuro control neuronal es buena en `docs/simulador/`, pero inconsistente en `docs/preliminar/`

Referencias positivas:

- `docs/simulador/README.md:10`-`21` enumera lo implementado.
- `docs/simulador/README.md:23`-`28` enumera lo no implementado.
- `docs/plans/plan_implementacion_simulador.md:11` declara que esta fase no implementa todavia control neuronal.
- `docs/plans/spec_subsanacion_findings_simulador.md:6` excluye ampliar hacia control neuronal.

Referencias conflictivas:

- `docs/preliminar/arquitectura_software.md:190`-`197` describe controladores neuronales como componentes existentes.
- `docs/preliminar/informe_software_simulador.tex:199`-`230` describe pipeline de datos y entrenamiento.
- `docs/preliminar/informe_fisica_simulador.tex:374`-`382` presenta teoria seguida para controladores neuronales.

Riesgo academico: alto si los preliminares se usan como base de memoria. Puede crear una incoherencia central: el objetivo final es comparar controlador clasico y neuronal, pero el repositorio actual solo implementa baseline clasico.

Recomendacion: mantener dos etiquetas documentales visibles: "implementado en v1 clasica" y "pendiente para fase neuronal". Cualquier texto neuronal debe declarar entradas necesarias, criterios futuros y dependencias no presentes, sin usar lenguaje de implementacion realizada.

### P1 - Las ganancias y limites del controlador clasico no son totalmente trazables desde escenarios

Referencias:

- `docs/simulador/arquitectura.md:82`-`83` reconoce que solo hay controlador clasico y que las ganancias estan fijadas en codigo.
- `docs/simulador/escenarios_yaml.md:180`-`183` documenta que solo se acepta `classic` y que sus ganancias estan fijadas en codigo.
- `src/simulador_quad/control/classic.py:12`-`18` fija `Kp_pos`, `Kd_pos`, `Kp_att` y `Kd_att` en codigo.
- `src/simulador_quad/control/classic.py:20`-`25` fija empuje maximo y limites por defecto de momentos.
- `src/simulador_quad/scenarios/loader.py:82`-`88` solo carga `max_body_moments_Nm`, no ganancias.

Riesgo academico: medio-alto. El controlador clasico sera baseline y generador futuro de datos de imitacion. Si las ganancias no estan declaradas por escenario o recogidas explicitamente en metadatos, la reproducibilidad experimental depende de la version exacta del codigo, no solo del YAML.

Recomendacion: documentar una tabla de ganancias nominales con justificacion y registrar esas ganancias en `metrics.metadata` o en un bloque de escenario/controlador. No es imprescindible hacerlas configurables de inmediato, pero si deben quedar trazadas como parametro experimental.

### P1 - Los planes y revisiones historicas no reflejan el estado actual y pueden inducir a error

Referencias:

- `docs/plans/tasks_subsanacion_findings_simulador.md:9`-`102` mantiene todas las tareas sin marcar, aunque varias estan implementadas.
- `docs/reviews/05_revision_subsanacion_findings_simulador.md:33`-`47` afirma que falta `LineTrajectory` y que el loader no soporta `line/waypoint`.
- `src/simulador_quad/trajectories/analytic.py:81`-`113` contiene `LineTrajectory` con smoothstep cubico.
- `src/simulador_quad/scenarios/loader.py:74`-`77` acepta `line` o `waypoint`.

Riesgo academico: medio. La trazabilidad historica pierde fiabilidad: un lector no sabe si un finding sigue abierto, fue resuelto o quedo reemplazado por otro.

Recomendacion: no borrar revisiones historicas, pero anadir cabecera de estado: "obsoleto", "parcialmente resuelto" o "vigente". Alternativamente, crear un indice `docs/reviews/README.md` con estado de cada auditoria y enlace al reporte mas reciente.

### P1 - Las condiciones de terminacion y metricas no documentan todavia todo lo necesario para explicar fallos con rigor

Referencias:

- `docs/02_requisitos_ingenieria_simulador.md:385`-`397` exige terminacion por seguridad/validez y causa explicita.
- `docs/02_requisitos_ingenieria_simulador.md:399`-`407` exige metricas de error, esfuerzo, estabilidad, terminacion y trazabilidad.
- `src/simulador_quad/runner.py:46`-`96` implementa causas de terminacion.
- `src/simulador_quad/telemetry/export.py:53` exporta `termination_cause` por muestra.
- `src/simulador_quad/metrics/report.py:43`-`59` calcula metricas agregadas y `termination_reason`.

Brecha: las metricas no incluyen estado asociado al fallo, instante exacto de terminacion separado de duracion, limites activos de posicion/velocidad, ni un resumen explicito de condiciones de validez usadas. `docs/simulador/arquitectura.md:86` reconoce ademas que el CLI no carga limites de posicion o velocidad desde YAML.

Riesgo academico: medio. Si un escenario falla por saturacion, actitud o limites internos, el tribunal necesitara reconstruir la causa desde telemetria en vez de verla como resultado auditable.

Recomendacion: documentar claramente que, en la version actual, ciertos limites viven en `SimulationRunner` y no en YAML. Para memoria, incluir en metricas o reporte experimental: causa, tiempo, estado final, limites activos y porcentaje de saturacion/degradacion.

### P2 - La documentacion viva es util, pero no contiene aun una justificacion fisico-matematica completa defendible

Referencias:

- `docs/simulador/arquitectura.md:5`-`20` describe flujo de simulacion.
- `docs/simulador/escenarios_yaml.md:23`-`30` documenta convenciones ENU/FRD.
- `docs/simulador/escenarios_yaml.md:42`-`71` documenta campos de vehiculo y rotores.

Brecha: `docs/simulador/` explica como usar el sistema, pero no desarrolla con suficiente formalidad las ecuaciones clave, limites de validez, convencion de signos del mezclador, derivacion del controlador clasico y bibliografia aplicable. Esa informacion existe en parte en los documentos normativos, pero los preliminares actuales no son fiables por las contradicciones ya citadas.

Riesgo academico: medio. El codigo puede ser correcto, pero la memoria necesita una explicacion autonoma y consistente de por que el modelo es aceptable para un banco de ensayo academico.

Recomendacion: crear una version revisada de `docs/preliminar/fisica_y_matematicas.md` basada solo en lo implementado: ENU/FRD, `F_thrust_B=[0,0,-T]`, Newton-Euler, cuaterniones, RK4, drag lineal, actuadores, mezclador, controlador clasico y limites de validez.

### P2 - Comentarios y docstrings en puntos fisicos criticos son insuficientes o muestran incertidumbre

Referencias:

- `src/simulador_quad/control/classic.py:47`-`57` contiene comentarios de duda sobre `Z_B` y valor por defecto.
- `src/simulador_quad/runner.py:75`-`84` contiene comentarios de razonamiento sobre inclinacion ENU/FRD.
- `src/simulador_quad/dynamics/rigid_body.py:18`-`21` documenta la derivada de forma muy breve para una funcion central.
- `src/simulador_quad/dynamics/mixer.py:6`-`10` documenta el objetivo del mezclador, pero no remite a un requisito o ecuacion normativa.
- `src/simulador_quad/core/contracts.py:5`-`66` usa comentarios de unidades utiles, pero no valida dimensiones ni finitud.

Riesgo academico: medio. Los comentarios con "Wait" o dudas no son adecuados en codigo que implementa convenciones fisicas defendibles; pueden sugerir que el signo de ejes no esta cerrado.

Recomendacion: sustituir comentarios de duda por docstrings afirmativos con unidades, marcos y ecuacion usada. Documentar especialmente controlador clasico, calculo de actitud deseada, tilt, drag lineal, RK4, mezclador y actuadores. No hace falta comentar funciones triviales.

### P2 - Dependencias y visualizacion necesitan justificacion documental

Referencias:

- `docs/01_principios_tfg.md:130`-`137` limita dependencias aceptables y exige justificar adicionales.
- `docs/03_criterios_ingenieria_software.md:151`-`162` permite PyYAML y pide justificar librerias adicionales.
- `pyproject.toml:10`-`17` incluye `plotly>=6.7.0`.
- `docs/simulador/guia_uso.md:63`-`67` documenta el visor 3D basado en Plotly.

Riesgo academico: bajo-medio. Plotly parece razonable para visualizacion 3D, pero no esta justificado como dependencia adicional en los documentos normativos o de arquitectura.

Recomendacion: anadir una nota de dependencia en `docs/simulador/arquitectura.md` o `docs/simulador/guia_uso.md`: problema que resuelve, alternativa simple, coste y efecto sobre reproducibilidad.

### P2 - Escenarios de ejemplo cubren trayectorias, pero falta clasificarlos como validacion, demostracion o caso de fallo

Referencias:

- `docs/simulador/escenarios_yaml.md:245`-`253` lista escenarios disponibles.
- `scenarios/hover_clean.yaml:1`-`2`, `scenarios/circle_drag.yaml:1`-`2`, `scenarios/circle_noisy_wind.yaml:1`-`2`, `scenarios/lissajous_clean.yaml:1`-`2`, `scenarios/waypoint_clean.yaml:1`-`2` tienen nombre y semilla.
- `docs/simulador/guia_uso.md:91`-`101` propone flujo de comparacion manual.

Brecha: no se declara que representa cada escenario para el TFG: smoke test, validacion de requisito, demostracion de perturbacion, caso robusto, caso de fallo esperado o escenario de comparacion futuro clasico-neuronal.

Riesgo academico: medio. Sin clasificacion, los resultados pueden parecer arbitrarios y no conectados a una pregunta experimental.

Recomendacion: crear una tabla de escenarios con objetivo, requisito cubierto, perturbaciones, criterio de aceptacion y metricas principales. Esto tambien prepara la comparacion futura con control neuronal bajo igualdad de condiciones.

## Fortalezas observadas

- Los documentos normativos son claros y academicos. Definen trazabilidad, alcance limitado, reproducibilidad y limites de validez.
- `docs/simulador/README.md:8`-`28` separa muy bien implementado/no implementado.
- `docs/simulador/escenarios_yaml.md` es util para usuarios tecnicos y documenta unidades, marcos y campos.
- El codigo usa nombres con unidades y marcos en muchos contratos, por ejemplo `position_W_m`, `velocity_W_m_s`, `orientation_WB`, `angular_velocity_B_rad_s` en `src/simulador_quad/core/contracts.py:7`-`11`.
- La telemetria distingue estado verdadero, observacion, referencia, comando, objetivo de rotor y aplicado (`src/simulador_quad/telemetry/export.py:20`-`53`).
- La ejecucion con `uv` es reproducible en lo basico y la suite de tests pasa.

## Riesgos academicos principales

1. Sobrerreclamo de alcance: documentos preliminares presentan control neuronal y aerodinamica avanzada inexistentes.
2. Trazabilidad incompleta: no hay matriz unica que permita auditar cumplimiento requisito-codigo-prueba-escenario-metrica.
3. Reproducibilidad parcial: escenarios guardan configuracion, pero parametros internos del controlador y limites internos del runner no quedan suficientemente visibles como condiciones experimentales.
4. Claridad insuficiente para tribunal: README raiz vacio y documentos preliminares contradictorios.
5. Evidencia experimental aun basica: hay tests y escenarios, pero falta clasificacion formal de escenarios y criterios de aceptacion por requisito.

## Recomendaciones concretas

1. Completar `README.md` raiz con objetivo, alcance, estado, comandos, mapa documental y aviso de control neuronal pendiente.
2. Crear una matriz de trazabilidad en `docs/simulador/trazabilidad.md`.
3. Marcar `docs/preliminar/*` como historico o reescribirlo antes de usarlo para la memoria.
4. Crear una tabla de escenarios: objetivo, requisito, parametros clave, perturbaciones, semilla, criterio de exito/fallo y metricas.
5. Documentar ganancias del controlador clasico y limites internos del runner como condiciones experimentales.
6. Sustituir comentarios de incertidumbre en convenciones fisicas por docstrings afirmativos y referencias a la ecuacion/documento correspondiente.
7. Justificar Plotly como dependencia adicional para visualizacion 3D, o mover esa justificacion a la documentacion de uso.
8. Crear un indice de `docs/reviews/` y `docs/plans/` con estado de cada documento para evitar que findings antiguos parezcan vigentes.
9. Separar explicitamente en toda la documentacion: "v1 clasica implementada" frente a "fase futura neuronal por imitacion".
10. Antes de redactar memoria final, ejecutar y registrar un set minimo de escenarios con artefactos: YAML, version/commit, metricas, figuras y conclusion tecnica breve.

## Conclusion

El proyecto esta bien encaminado como simulador 6DOF clasico con documentacion viva razonable, pero la adecuacion a TFG depende de corregir la capa documental. La prioridad no es anadir mas codigo, sino hacer defendible lo que ya existe: limpiar preliminares obsoletos, completar el README, formalizar trazabilidad y convertir escenarios/metricas en evidencia academica conectada a requisitos.
