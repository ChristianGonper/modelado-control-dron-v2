# Especificacion de auditoria integral del repositorio

## 1. Objetivo

Realizar una auditoria profunda y exclusivamente diagnostica del repositorio para
identificar mejoras claras que aumenten su rigor, coherencia, trazabilidad y
calidad como Trabajo de Fin de Grado.

La auditoria debe:

- detectar errores tecnicos, riesgos cientificos y contradicciones;
- identificar deuda con impacto material en el TFG;
- revisar codigo, pruebas, tooling, documentacion, memoria y evidencia local;
- detectar contenido documental obsoleto, redundante, aspiracional o generico;
- distinguir entre comportamiento implementado, tooling disponible, evidencia
  experimental generada y afirmaciones defendibles;
- producir un backlog de subsanacion suficientemente concreto para ser
  implementado posteriormente sin repetir la investigacion.

La auditoria no debe implementar correcciones.

## 2. Principios rectores

- Priorizar la validez y defensa academica del TFG sobre el pulido puramente
  software.
- Mantener como invariantes mundo ENU, cuerpo FRD y empuje sustentador en
  direccion `-Z_B`.
- Contrastar toda afirmacion con evidencia primaria del repositorio.
- No asumir que una prueba aprobada demuestra validez fisica o experimental.
- No confundir codigo implementado con evidencia experimental disponible.
- No confundir evidencia local ignorada por Git con evidencia versionada.
- No tratar documentos historicos como fuentes del estado actual.
- No eliminar referencias legacy mientras exista codigo, pruebas, escenarios,
  artefactos o contratos que las utilicen.
- Evaluar la calidad de los textos, no atribuir su autoria a IA.
- Mantener el alcance cientifico limitado definido para el TFG; una propuesta
  que amplie innecesariamente dicho alcance no constituye una mejora.

## 3. Fuentes de verdad y precedencia

Usar esta precedencia para resolver contradicciones:

1. `AGENTS.md` y reglas locales aplicables.
2. `docs/01_principios_tfg.md`.
3. `docs/02_requisitos_ingenieria_simulador.md`.
4. `docs/03_criterios_ingenieria_software.md`.
5. Codigo, pruebas, escenarios y contratos ejecutables.
6. `docs/simulador/` y `README.md` como documentacion viva.
7. Evidencia experimental local trazable.
8. `TFG_Memoria/` como narrativa academica.
9. `docs/reviews/` como diagnosticos fechados.
10. `docs/plans/archived/` y otros documentos historicos.

Los documentos historicos pueden explicar decisiones anteriores, pero no
demuestran por si mismos el estado vigente.

## 4. Alcance

### 4.1 Superficies versionadas

La auditoria debe cubrir:

- configuracion, dependencias, entorno y reproducibilidad;
- normativa y requisitos;
- nucleo fisico, marcos, actitud y dinamica 6DOF;
- actuadores, mixer y control clasico;
- trayectorias, escenarios, carga y terminaciones;
- runner, integracion multirate, telemetria, metricas y visualizacion;
- dataset clasico, tuneo PID, bancos y transferencia;
- datasets ML, features, targets, normalizacion, entrenamiento y evaluacion;
- control neuronal en bucle cerrado;
- oraculo outer-force, OOD, campañas y comparaciones;
- pruebas y correspondencia requisito-prueba;
- README, documentacion viva, reviews, planes e informes preliminares;
- memoria LaTeX y bibliografia local.

### 4.2 Evidencia local ignorada

Inspeccionar de forma seleccionada `data/` y `results/`:

- manifests;
- configuraciones;
- checkpoints y metadata;
- reportes CSV;
- metricas agregadas;
- muestras concretas necesarias para validar un hallazgo.

No revisar telemetrias masivas muestra a muestra salvo que sea imprescindible
para confirmar un hallazgo concreto.

### 4.3 Fuera de alcance

- Implementar correcciones.
- Crear commits.
- Regenerar datasets completos.
- Entrenar modelos.
- Ejecutar campañas experimentales completas.
- Consultar fuentes externas.
- Introducir nuevas dependencias o ampliar el alcance cientifico.

## 5. Ejecucion permitida

La auditoria puede ejecutar:

- analisis estatico;
- suite de pruebas;
- validadores;
- compilacion o chequeos de documentacion;
- comandos `--help`;
- smokes ligeros y escenarios pequeños;
- scripts de inspeccion que no modifiquen archivos versionados ni regeneren
  evidencia pesada.

Toda ejecucion debe registrar comando, resultado y limitaciones.

### 5.1 Comandos base recomendados

Ejecutar al inicio, siempre que no modifiquen archivos versionados:

```powershell
git status --short
git rev-parse HEAD
git log -1 --format=fuller
git ls-files
uv run pytest -q
uv run python tools\run_experimental_campaign.py --dry-run
```

Los revisores de herramientas deben comprobar los CLI relevantes mediante
`--help`. Los revisores de escenarios pueden ejecutar smokes concretos cuando
sean necesarios para confirmar comportamiento, pero deben evitar cualquier
comando que regenere campañas o sobrescriba evidencia local.

## 6. Modelo de evidencia y aceptacion

La auditoria debe separar tres niveles:

1. **Verificacion:** el codigo implementa correctamente las ecuaciones y
   contratos declarados.
2. **Validacion:** el simulador representa adecuadamente el modelo 6DOF
   simplificado definido para el TFG.
3. **Validez experimental:** el protocolo y la evidencia permiten sostener las
   conclusiones academicas.

Una afirmacion central necesita, cuando aplique:

- **E1 - Definicion:** requisito, hipotesis, ecuacion, unidades y limites.
- **E2 - Implementacion:** codigo identificable coherente con E1.
- **E3 - Verificacion:** prueba, invariante o caso analitico.
- **E4 - Validacion:** escenario, metrica y criterio de aceptacion.
- **E5 - Reproducibilidad:** commit, entorno, comando, configuracion y semillas.
- **E6 - Inferencia academica:** conclusion proporcional, comparacion justa y
  limitaciones.

Una afirmacion principal sin E1-E5 no debe aceptarse. Una conclusion comparativa
necesita tambien E6.

## 7. Dominios de revision y ownership

Usar la siguiente asignacion primaria. Si la plataforma empleada requiere menos
agentes, puede agrupar dominios, pero no omitirlos ni cambiar sus fronteras sin
registrarlo en la metodologia.

| ID | Dominio primario | Superficie principal |
|---|---|---|
| A01 | Gobierno, entorno y reproducibilidad | `AGENTS.md`, `.gitignore`, `pyproject.toml`, `uv.lock`, configuracion del repo y artefactos generados |
| A02 | Normativa y validez academica | `docs/01_*`, `docs/02_*`, `docs/03_*` |
| A03 | Marcos, actitud y dinamica 6DOF | `src/simulador_quad/core/`, dinamica de cuerpo rigido y pruebas fisicas asociadas |
| A04 | Actuadores, mixer y control clasico | actuadores, mixer, `control/classic.py`, contrato de control y pruebas asociadas |
| A05 | Trayectorias y escenarios | `trajectories/`, `scenarios/`, escenarios oficiales, loader, schema y pruebas asociadas |
| A06 | Ejecucion, telemetria y metricas | `app.py`, `runner.py`, telemetria, metricas, visualizacion y pruebas asociadas |
| A07 | Dataset clasico y PID | `datasets/classic.py`, generacion/ejecucion/resumen clasico, tuneo, bancos PID y transferencia |
| A08 | ML supervisado | `src/simulador_quad/ml/`, entrenamiento, evaluacion, features, targets, normalizacion y pruebas |
| A09 | Control neuronal cerrado | `control/neural.py`, runners neuronales, inferencia y pruebas de control neuronal |
| A10 | Oraculo y campañas | outer-force, OOD, campaña experimental, comparaciones y pruebas de integracion |
| A11 | Pruebas y validacion numerica | conjunto completo de `tests/`, trazabilidad requisito-prueba y suficiencia de criterios |
| A12 | Evidencia local | `data/` y `results/`, limitada a manifests, configs, metadata, metricas y muestras justificadas |
| A13 | Ecosistema documental | `README.md`, `docs/simulador/`, `docs/reviews/`, `docs/plans/`, `docs/preliminary/` |
| A14 | Memoria | `TFG_Memoria/`, narrativa, tablas, figuras, referencias y claims |

Cada archivo debe tener un unico propietario primario. Otros revisores pueden
citarlo o realizar contraste cruzado, pero no duplicar su auditoria principal.

Los ficheros de prueba tienen ownership primario en A11, pero los especialistas
de dominio deben evaluarlos como evidencia y comunicar a A11 cualquier carencia.

## 8. Proceso operativo obligatorio

### Ronda 0 - Congelacion y cobertura

El coordinador debe registrar:

- commit, rama y estado Git;
- diferencia respecto a la ultima auditoria integral;
- inventario de archivos versionados por dominio;
- inventario resumido de `data/` y `results/`;
- comandos permitidos y comandos prohibidos;
- matriz de ownership sin archivos sin asignar.

**Gate G0:** ningun especialista comienza sin declarar dominio, archivos,
fuentes normativas aplicables y limitaciones.

### Ronda 1 - Revision independiente

Cada especialista debe entregar:

1. Superficie revisada.
2. Contratos, invariantes y claims comprobados.
3. Hallazgos candidatos.
4. Hallazgos historicos revalidados.
5. Aspectos no verificables.
6. Zonas revisadas sin problemas encontrados.
7. Comandos ejecutados y resultados.

**Gate G1:** todos los dominios tienen cobertura explicita y no quedan archivos
versionados sin owner.

### Ronda 2 - Contraste cruzado

Ejecutar las revisiones cruzadas definidas en la siguiente seccion. Cada
revisor secundario debe intentar encontrar contraevidencia, no limitarse a
confirmar al owner.

**Gate G2:** ningun P0 o P1 transversal se acepta con una sola perspectiva.

### Ronda 3 - Red team

Un revisor no propietario debe intentar:

- refutar cada P0 y P1;
- detectar severidades exageradas;
- distinguir error de limitacion ya declarada;
- detectar recomendaciones que amplian innecesariamente el alcance;
- comprobar que un hallazgo no dependa de una auditoria antigua;
- comprobar que “implementado”, “validado” y “con evidencia final” no se
  confundan.

**Gate G3:** cada P0/P1 conserva contraevidencia revisada, impacto academico y
confianza justificada.

### Ronda 4 - Consolidacion

El integrador debe:

- fusionar sintomas con la misma causa raiz;
- resolver o documentar disputas;
- clasificar el delta historico;
- construir el mapa requisito-codigo-prueba-escenario-metrica-evidencia;
- producir informe, CSV, anexos y backlog.

**Gate G4:** todo hallazgo final tiene evidencia, owner, decision propuesta y
criterio verificable de cierre.

## 9. Revisiones cruzadas obligatorias

Contrastar de forma independiente:

- marcos y dinamica con actuadores y control;
- escenarios y trayectorias con runner, terminaciones y telemetria;
- control clasico con tuneo PID, datasets y splits;
- features y targets de entrenamiento con datos usados en inferencia;
- control neuronal con campañas, OOD y evidencia local;
- pruebas con los requisitos que supuestamente verifican;
- normativa con documentacion viva y memoria;
- tooling documentado con comandos, artefactos y resultados realmente
  disponibles.

Un hallazgo transversal grave no debe aceptarse con una unica perspectiva.

## 10. Hipotesis iniciales que deben confirmarse o refutarse

Estas observaciones proceden de una exploracion preliminar. No deben copiarse
como hallazgos finales sin verificarlas contra el snapshot auditado:

- `docs/preliminary/` podria seguir versionado pese a que una review afirma que
  fue retirado.
- Podrian no existir planes activos directamente bajo `docs/plans/`, aunque
  algunas superficies los presenten como vigentes.
- `TFG_Memoria/AGENTS.md` podria referenciar como fuente de verdad un plan ya
  archivado.
- Los planes archivados y reviews historicas podrian carecer de etiquetado
  individual suficiente.
- `pyproject.toml` podria conservar descripcion de plantilla.
- Existen referencias legacy que parecen operativas y no deben eliminarse solo
  por ser antiguas.
- La evidencia experimental local podria existir sin estar preservada en Git ni
  vinculada de forma suficiente a la memoria.
- Algunos escenarios manuales podrian usar limites de actitud demasiado
  permisivos para servir como evidencia fuerte de estabilidad.
- La validacion numerica podria carecer de estudio de sensibilidad a
  `physics_dt_s`.
- El entrenamiento neuronal podria depender de una sola semilla o no registrar
  suficiente variabilidad.
- Algunas estadisticas agregadas podrian representar dispersion entre
  escenarios, no incertidumbre experimental ni intervalos de confianza.
- Podrian existir TODO, placeholders, comentarios de compatibilidad o fallbacks
  cuyo estado operativo/documental no este claro.

Cada hipotesis debe acabar clasificada como:

- confirmada y convertida en hallazgo;
- refutada con evidencia;
- limitacion aceptada y correctamente declarada;
- no verificable dentro del alcance.

## 11. Criterios tecnicos y academicos

### 11.1 Fisica y simulacion

Comprobar:

- coherencia ENU/FRD, signos, unidades y convenciones;
- correspondencia entre ecuaciones declaradas e implementacion;
- validez de parametros fisicos y limites;
- integracion RK4, ZOH y frecuencias multirate;
- actuacion solicitada frente a actuacion aplicada;
- terminaciones, saturacion, degradacion y no finitos;
- limitaciones declaradas del modelo simplificado;
- necesidad de estudios de sensibilidad numerica.

Comprobar expresamente si existen casos analiticos o comparaciones con pasos
`dt`, `dt/2` y `dt/4`. Su ausencia no implica automaticamente un error fisico,
pero puede constituir un bloqueo para claims sensibles a precision numerica.

### 11.2 Control y experimentacion

Comprobar:

- trazabilidad y congelacion de ganancias;
- ausencia de uso de `test` u OOD para tuneo o seleccion;
- comparaciones pareadas bajo condiciones equivalentes;
- tratamiento explicito de fallos y terminaciones;
- criterios de seguridad y filtros duros;
- interpretacion fisica correcta de metricas de esfuerzo;
- separacion entre rendimiento supervisado y rendimiento cerrado.

Comprobar tambien:

- si los fallos cerrados se incluyen en los agregados;
- si las comparaciones informan diferencias frente al baseline;
- si una desviacion estandar entre escenarios se presenta incorrectamente como
  incertidumbre experimental;
- si metricas que combinan magnitudes con unidades distintas se interpretan
  solo como heuristicas.

### 11.3 Aprendizaje por imitacion

Comprobar:

- separacion por episodios y splits;
- normalizacion basada exclusivamente en `train`;
- correspondencia entre experto, targets y controlador desplegado;
- alineacion entre features de entrenamiento e inferencia;
- tratamiento y cuantificacion del clipping;
- reproducibilidad de entrenamientos;
- suficiencia de semillas y comparaciones;
- uso correcto de OOD y ausencia de leakage.

Comprobar expresamente:

- numero de semillas de entrenamiento realmente ejecutadas;
- semillas y generadores configurados;
- separacion por episodios completos;
- cuantificacion del uso de clipping;
- seleccion de arquitectura e hiperparametros sin consultar test u OOD;
- diferencia entre perdida supervisada y estabilidad cerrada.

### 11.4 Reproducibilidad

Comprobar que cada resultado relevante pueda vincularse con:

- commit y estado Git;
- `uv.lock` y entorno;
- comando;
- configuracion;
- semillas;
- manifest;
- escenario;
- metricas y artefactos.

### 11.5 Validez para la memoria

Comprobar:

- que cada conclusion responda a una pregunta explicita;
- que las afirmaciones sean proporcionales a la evidencia;
- que no se extrapole a vuelo real ni a robustez general;
- que se declaren limitaciones, fallos y dependencia del experto;
- que tablas, cifras y figuras sean trazables;
- que resultados pendientes no se presenten como concluyentes.

## 12. Politica documental

Clasificar cada documento como:

- normativo;
- documentacion viva;
- memoria;
- review historica;
- plan archivado;
- legacy operativo;
- borrador o informe preliminar.

### 12.1 Decisiones posibles

- **Conservar:** correcto, normativo, operativo o necesario para trazabilidad.
- **Etiquetar:** historicamente util, pero no vigente.
- **Reescribir:** tema necesario mezclado con errores, aspiraciones o
  contradicciones.
- **Eliminar:** incorrecto o duplicado, sin valor historico, tecnico u
  operativo.

La politica general para historicos es conservar y etiquetar.

### 12.2 Calidad textual

Marcar como candidato a saneamiento cuando un texto:

- repita informacion sin aportar decision, evidencia o contexto;
- use calificativos no medibles;
- presente intencion futura como comportamiento implementado;
- describa capacidades inexistentes;
- mezcle estado actual, historico y propuesta;
- carezca de unidades o marcos cuando sean necesarios;
- contenga recomendaciones genericas sin accion verificable;
- sea tan deficiente estructuralmente que impida su mantenimiento.

Antes de proponer eliminar un texto, identificar y conservar cualquier:

- ecuacion correcta;
- hipotesis fisica;
- decision de diseño;
- criterio de aceptacion;
- limitacion conocida;
- evidencia o contexto historico relevante.

No usar “AI slop” como etiqueta de autoria.

### 12.3 Legacy operativo

Solo proponer retirar una referencia legacy cuando se cumplan conjuntamente:

1. No existe codigo que la acepte o produzca.
2. No existen escenarios, datos o resultados que la necesiten.
3. No existen pruebas de compatibilidad asociadas.
4. La documentacion viva deja de prometer soporte.
5. La ruptura o migracion queda explicitamente documentada.

### 12.4 Validaciones documentales especificas

Comprobar:

- enlaces y rutas mencionadas;
- comandos documentados frente a sus `--help`;
- campos YAML documentados frente al loader y schema;
- metricas documentadas frente a su implementacion;
- claims sensibles como `implementado`, `vigente`, `retirado`, `garantiza` y
  `resultado`;
- referencias LaTeX, citas y bibliografia local;
- procedencia de figuras, tablas y resultados;
- estado y sucesor de cada documento historico.

## 13. Severidades

### P0 - Invalidante

Invalida la fisica, metodologia, evidencia o conclusiones centrales.

Ejemplos:

- incoherencia de marcos o signos;
- leakage de test u OOD;
- comparaciones bajo condiciones diferentes;
- memoria que describe experimentos distintos de los ejecutados;
- resultados seleccionados u ocultacion de fallos.

### P1 - Bloqueante academico

Impide sostener o reproducir una conclusion principal hasta resolverlo.

Ejemplos:

- ausencia de evidencia reproducible;
- validacion numerica insuficiente;
- falta de correspondencia entrenamiento-despliegue;
- conclusiones generales sin repeticiones suficientes;
- tooling correcto pero artefactos finales ausentes o incompatibles.

### P2 - Mejora material

Debilita claridad, trazabilidad, mantenibilidad o calidad del TFG, pero permite
usar resultados con reservas explicitas.

### P3 - Pulido

Mejora localizada sin impacto material sobre conclusiones o reproducibilidad.

Las preferencias estilisticas sin impacto verificable no son hallazgos.

## 14. Contrato obligatorio de hallazgo

Cada hallazgo debe usar este formato:

```text
ID:
Titulo:
Severidad: P0 | P1 | P2 | P3
Dominio propietario:
Tipo: codigo | fisica | contrato | prueba | documentacion | evidencia | narrativa
Estado historico: nuevo | persiste | cerrado | regresion | obsoleto
Fuente normativa:
Causa raiz:
Impacto tecnico:
Impacto academico:
Evidencia primaria: archivo:linea
Contraevidencia revisada:
Confianza: alta | media | baja
Decision propuesta:
Remediacion minima:
Archivos probablemente afectados:
Dependencias:
Criterio verificable de cierre:
```

No aceptar hallazgos:

- sin evidencia primaria;
- basados solo en auditorias antiguas;
- basados solo en busquedas textuales;
- que confundan limitacion declarada con error;
- que propongan ampliar alcance sin justificar su necesidad academica.

Los sintomas con la misma causa raiz y comportamiento observable deben
consolidarse en un unico hallazgo.

### 14.1 Registro y resolucion de conflictos

El registro central debe asignar IDs definitivos y deduplicar usando la firma:

```text
<requisito afectado, comportamiento observable, causa raiz>
```

Si revisores discrepan:

- el owner decide los hechos locales de su dominio;
- el integrador decide severidad e impacto transversal;
- el red team puede bloquear o rebajar aportando contraevidencia;
- una disputa no resuelta debe aparecer explicitamente en el informe.

## 15. Backlog de subsanacion

El backlog final debe ser decision-complete. Cada accion debe indicar:

- problema que resuelve;
- decision concreta recomendada;
- resultado esperado;
- archivos o areas afectadas;
- dependencias y orden;
- pruebas o verificaciones necesarias;
- cambios documentales asociados;
- criterio objetivo de cierre;
- impacto esperado en la defensa del TFG.

Separar claramente:

- correcciones de codigo;
- refuerzo de pruebas;
- saneamiento documental;
- regeneracion experimental;
- cambios de memoria.

No mezclar una correccion de comportamiento con la regeneracion de evidencia o
la redaccion de conclusiones.

## 16. Entregables

Crear los siguientes archivos bajo `docs/reviews/`, sin commits:

```text
docs/reviews/auditoria_integral_tfg_<fecha>.md
docs/reviews/auditoria_integral_tfg_<fecha>_hallazgos.csv
docs/reviews/auditoria_integral_tfg_<fecha>_backlog.md
docs/reviews/annexes/<fecha>/
```

### Informe maestro

Debe contener:

- snapshot auditado;
- metodologia y limitaciones;
- dictamen sobre aptitud para defensa;
- resumen por dominio;
- hallazgos consolidados por severidad;
- delta respecto a auditorias anteriores;
- riesgos residuales;
- afirmaciones permitidas y no permitidas para la memoria;
- orden recomendado de subsanacion.

### Anexos

Cada dominio debe entregar:

- superficie revisada;
- invariantes y contratos comprobados;
- hallazgos candidatos;
- hallazgos historicos revalidados;
- aspectos no verificables;
- zonas sin problemas encontrados;
- comandos ejecutados y resultados.

### CSV de hallazgos

Debe incluir al menos estas columnas:

```text
id,titulo,severidad,dominio,tipo,estado_historico,fuente_normativa,
evidencia_primaria,impacto_tecnico,impacto_academico,confianza,
decision_propuesta,dependencias,criterio_cierre,estado_disputa
```

### Backlog

Ordenar las acciones en fases:

1. Correcciones invalidantes de contrato, fisica o metodologia.
2. Refuerzo de pruebas y validacion.
3. Coherencia de pipelines y reproducibilidad.
4. Saneamiento de documentacion viva.
5. Etiquetado o depuracion historica.
6. Regeneracion experimental futura.
7. Actualizacion posterior de la memoria.

## 17. Criterios de finalizacion

La auditoria solo se considera completa cuando:

- todos los archivos versionados tienen propietario primario;
- la evidencia local seleccionada esta diferenciada del estado versionado;
- todos los dominios han entregado cobertura explicita;
- todo P0 y P1 ha sido contrastado de forma cruzada;
- todo hallazgo contiene evidencia primaria y criterio de cierre;
- las contradicciones entre agentes se han resuelto o documentado;
- reviews y planes historicos no se presentan como estado actual;
- legacy operativo no se propone eliminar sin demostrar ausencia de
  consumidores;
- documentacion viva, memoria y evidencia han sido contrastadas;
- el backlog final es decision-complete;
- no se ha modificado ninguna superficie fuera de `docs/reviews/`;
- no se han creado commits.

## 18. Resultado esperado

El resultado no debe ser una coleccion de opiniones ni una lista extensa de
micro-mejoras. Debe permitir responder, con evidencia:

1. Que partes del repositorio son tecnicamente correctas y defendibles.
2. Que afirmaciones puede realizar actualmente la memoria.
3. Que problemas invalidan o debilitan esas afirmaciones.
4. Que contenido esta obsoleto, es historico o sigue siendo operativo.
5. Que acciones concretas deben ejecutarse, en que orden y con que criterio de
   cierre, antes de considerar el TFG listo para defensa.
