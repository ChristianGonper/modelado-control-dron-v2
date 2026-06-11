# Especificacion de subsanacion posterior a la auditoria integral

## 1. Objetivo

Pulir el repositorio y cerrar su cadena de evidencia experimental para que el
TFG pueda defender, de forma clara y trazable, la comparacion entre control
clasico y control neuronal `outer_force`.

La implementacion debe:

- endurecer los generadores de datasets y bancos PID para impedir artefactos
  incompletos o aparentemente validos;
- inventariar la campana experimental ejecutada manualmente y completar solo
  los pasos realmente pendientes;
- producir una comparacion final canonica coherente con el alcance defendido;
- alinear documentacion, trazabilidad y memoria con el estado real;
- corregir deuda menor que pueda inducir a interpretaciones academicas
  incorrectas.

Esta especificacion sustituye a la especificacion de auditoria anterior como
plan activo. La auditoria ya esta realizada; el siguiente agente debe
implementar sus conclusiones.

## 2. Decisiones y hechos aceptados

Estas decisiones no deben reabrirse durante la implementacion:

1. `docs/preliminary/` ya ha sido eliminado. No queda trabajo pendiente sobre
   esa carpeta.
2. Los datasets, checkpoints, metricas y resultados generados manualmente la
   manana del 10 de junio de 2026 se consideran correctos y utilizables.
3. Que esos artefactos referencien un commit anterior o indiquen
   `git_dirty=true` no invalida sus resultados y no obliga a regenerarlos.
4. La campana se ejecuto manualmente, no mediante las fases 1-11 de
   `run_experimental_campaign.py`.
5. Antes de ejecutar trabajo experimental pesado debe inventariarse lo ya
   generado y determinar exactamente que falta.
6. No se debe regenerar una campana completa solo para ajustarla al
   orquestador de fases.
7. La linea principal defendible del TFG compara `neural_outer_force` contra
   los cuatro PID expertos familiares congelados.
8. La transferencia cruzada de los PID familiares es parte obligatoria del
   trabajo experimental:
   - cada PID experto familiar debe evaluarse sobre escenarios `test` de su
     propia familia y de las demas familias;
   - cada PID experto familiar debe poder evaluarse sobre cualquier escenario
     de la bateria OOD;
   - la comparacion debe permitir estudiar generalizacion y transferencia de
     cada PID frente a la red.
9. `neural_position` y el oraculo outer-force por escenario solo deben
   incluirse en la comparacion final si ya existe evidencia suficiente o si
   completarlos requiere un coste razonable. En caso contrario deben
   declararse como extensiones o tooling disponible.
10. Mantener mundo ENU, cuerpo FRD y el contrato neuronal `outer_force` de tres
   salidas.
11. En esta especificacion, `PID experto familiar` significa uno de los cuatro
    PID congelados del dataset clasico. No significa el oraculo outer-force
    seleccionado especificamente por escenario.

## 3. Fuentes de verdad

Resolver contradicciones usando esta precedencia:

1. `AGENTS.md` y reglas locales.
2. Esta especificacion.
3. `docs/01_principios_tfg.md`.
4. `docs/02_requisitos_ingenieria_simulador.md`.
5. `docs/03_criterios_ingenieria_software.md`.
6. Codigo, pruebas, escenarios y artefactos ejecutables.
7. `docs/simulador/` y `README.md`.
8. Evidencia local en `data/` y `results/`.
9. `TFG_Memoria/`.
10. Auditorias y planes archivados.

Las auditorias anteriores son diagnosticos historicos. No deben mantenerse sus
afirmaciones cuando contradigan el estado actual o esta especificacion.

## 4. Alcance de implementacion

### 4.1 Obligatorio

- Endurecer `generate_outer_force_dataset.py`.
- Hacer seguras las operaciones `--overwrite` de los generadores afectados.
- Anadir pruebas de integridad y regresion para esos cambios.
- Inventariar la evidencia experimental manual existente.
- Determinar y ejecutar solo las operaciones pendientes necesarias para cerrar
  la comparacion principal.
- Generar o designar un artefacto comparativo canonico.
- Implementar y ejecutar la matriz cruzada de los cuatro PID familiares sobre
  `test` y OOD.
- Corregir documentacion viva, trazabilidad, indice de reviews y reglas de la
  memoria para reflejar el alcance real.
- Corregir la presentacion ambigua de dispersion estadistica.
- Eliminar texto plantilla o referencias claramente obsoletas detectadas.

### 4.2 Condicionado al inventario

- Generar evidencia de `neural_position`.
- Incorporar el oraculo a la tabla final.
- Regenerar artefactos existentes.

Estas tareas solo se ejecutaran si el inventario demuestra que son necesarias
para el alcance final acordado o que falta muy poco para completarlas.

### 4.3 Fuera de alcance

- Cambiar el modelo fisico sin un fallo reproducible.
- Ampliar el TFG a un gemelo digital o producto industrial.
- Introducir nuevas arquitecturas neuronales.
- Rehacer resultados correctos por motivos meramente administrativos.
- Versionar telemetrias masivas o checkpoints en Git por defecto.
- Reescribir de forma extensa la memoria antes de cerrar la evidencia.

## 5. Requisitos funcionales

### RF-01. Generacion `outer_force` estricta

`tools/generate_outer_force_dataset.py` debe rechazar entradas incompletas en
el camino normal.

Debe fallar con un mensaje accionable cuando:

- no exista el manifiesto del dataset fuente;
- no exista el manifiesto del banco PID;
- falte el escenario fuente;
- el candidato elegido no tenga un `pid_path` valido;
- no puedan obtenerse `Kp_pos` y `Kd_pos` validos;
- falte la telemetria de la ejecucion experta elegida;
- no exista candidato seguro para un escenario;
- una fila fuente no tenga los campos obligatorios.

No debe:

- crear manifiestos fuente sinteticos;
- crear escenarios stub;
- crear telemetria stub;
- sustituir telemetria experta por telemetria clasica;
- usar ganancias PID predeterminadas silenciosamente;
- ignorar escenarios sin candidato;
- sustituir un candidato ausente por otro candidato de la misma familia;
- capturar excepciones de lectura y continuar sin informar.

Si se desea conservar un modo sintetico para tests o demostraciones, debe ser
una opcion explicita como `--allow-synthetic-placeholder`, quedar marcada en
el manifest y README resultantes, y no poder confundirse con evidencia real.
La opcion preferida es eliminar ese modo si ningun consumidor real lo necesita.

### RF-02. Escritura atomica y `--overwrite` fiable

Los generadores que producen datasets o bancos deben escribir primero en un
directorio temporal hermano, validar el resultado y sustituir el destino solo
tras completar correctamente.

Aplicar como minimo a:

- `tools/generate_outer_force_pid_bank.py`;
- `tools/generate_outer_force_dataset.py`;
- `tools/generate_ood_battery.py`;
- `src/simulador_quad/datasets/classic.py::write_dataset_files`.

Requisitos:

- una ejecucion fallida no puede alterar un destino valido previo;
- los informes de fallo tampoco pueden escribirse dentro del destino valido
  previo antes del reemplazo;
- `--overwrite` debe eliminar residuos que no pertenezcan a la nueva salida;
- nunca puede sobrevivir un manifest antiguo junto a resultados parciales
  nuevos;
- el directorio temporal debe limpiarse tras exito o fallo;
- sin `--overwrite`, un destino existente debe seguir rechazandose;
- los manifests y YAML generados deben conservar rutas relativas canonicas
  como `results/<...>` y no rutas relativas al directorio temporal ni rutas
  absolutas dependientes de la maquina;
- en Windows, la sustitucion debe usar operaciones de `pathlib`/`shutil`
  controladas y rutas resueltas dentro del destino esperado.

Puede crearse un helper compartido pequeno si reduce duplicacion real. No
introducir una abstraccion compleja.

### RF-03. Inventario de evidencia manual

Antes de ejecutar fases o campanas, crear un inventario ligero y versionable
que describa la evidencia existente.

El inventario debe incluir, como minimo:

- artefacto o conjunto de artefactos;
- controlador y arquitectura;
- dataset y split;
- cantidad de escenarios o corridas;
- ruta local relativa;
- estado: `complete`, `partial`, `missing` o `not_in_scope`;
- comando manual conocido, si puede reconstruirse;
- observaciones y limitaciones;
- decision sobre su uso en la memoria.

Los conteos deben calcularse desde los manifests y reportes reales, no
escribirse por estimacion. Debe distinguirse entre numero de episodios del
dataset, numero de corridas cerradas y numero de modelos.

No debe copiar telemetrias ni checkpoints. Debe apuntar a ellos mediante rutas
relativas y resumirlos.

Ubicacion recomendada:

```text
results/evidence_manifest.csv
```

Si `results/` continua ignorado completamente, versionar una copia pequena bajo
`docs/reviews/` o ajustar `.gitignore` para permitir exclusivamente el
manifiesto y las tablas finales citables.

### RF-04. Cierre de la comparacion principal

La comparacion final minima debe incluir:

- los cuatro PID expertos familiares congelados: `hold`, `circle`,
  `lissajous` y `waypoint`;
- `neural_outer_force_mlp`;
- `neural_outer_force_gru`;
- `neural_outer_force_lstm`;
- evaluacion in-distribution disponible;
- evaluacion OOD disponible;
- metricas comunes y causas de fallo.

El inventario debe decidir para cada uno de estos elementos si esta completo.
Solo deben ejecutarse los scripts necesarios para rellenar huecos concretos.

Debe existir un artefacto comparativo canonico claramente documentado. Hay dos
opciones validas:

1. generar `results/comparison_closed_loop_v1.csv`; o
2. declarar `results/comparison_all_runs.csv` (comparable: `test`/`ood`),
   `results/comparison_all_runs_full.csv` (todos los splits) y
   `results/comparison_summary.csv` como evidencia canonica.

Elegir una sola opcion y actualizar todas las referencias documentales. No
mantener rutas prometidas que no se generan.

La transferencia cruzada de PID no es una extension opcional. Debe formar
parte de la comparacion final conforme a RF-04A y RF-04B.

`neural_position` y oraculo outer-force por escenario:

- si se incluyen, deben tener filas y evidencia real;
- si no se incluyen, deben marcarse como fuera del alcance experimental final;
- no deben aparecer como comparaciones completadas solo porque exista tooling.

### RF-04A. Matriz cruzada de PID familiares sobre `test`

Los cuatro PID congelados almacenados en `data/classic_dataset/v1/pids/` deben
evaluarse sobre todos los escenarios del split `test` del dataset clasico.

La matriz obligatoria es:

```text
23 escenarios test x 4 PID familiares = 92 corridas
```

Debe incluir tambien la diagonal, es decir, el PID representativo de la propia
familia. No omitirla por considerarla baseline ya ejecutado: la tabla cruzada
debe poder analizarse como una matriz completa y autocontenida.

Cada corrida debe registrar:

- `scenario_id`;
- familia de la trayectoria;
- `pid_family`;
- identificador y ruta del PID congelado;
- split;
- estado;
- ruta de resultados;
- metricas y causa de terminacion.

Las etiquetas de controlador deben ser inequívocas:

```text
classic_pid_hold
classic_pid_circle
classic_pid_lissajous
classic_pid_waypoint
```

No usar `classic_family_pid` para filas donde no quede identificado que PID
concreto se ejecuto.

El tooling existente `tools/run_classic_transfer_dataset.py` debe reutilizarse
o generalizarse. Debe permitir:

- ejecutar todos los PID o uno concreto;
- filtrar por split, familia y escenario;
- incluir la diagonal;
- usar paralelizacion CPU;
- reanudar y reejecutar;
- generar un reporte deduplicado por `scenario_id + pid_family`.

CLI minima esperada:

```powershell
uv run python tools/run_classic_transfer_dataset.py `
  --dataset data/classic_dataset/v1 `
  --split test `
  --pid-family all `
  --include-native `
  --workers 8 `
  --no-visualization
```

Se permite diseñar flags equivalentes si quedan claramente documentados y
testeados.

### RF-04B. PID familiares sobre bateria OOD

La bateria OOD debe poder ejecutarse con cualquiera de los cuatro PID expertos
familiares congelados. Los PID deben proceder del dataset clasico congelado;
no deben recrearse mediante ganancias genericas ni ajustarse usando resultados
OOD.

Debe existir una asignacion representativa por defecto para ejecutar una
baseline OOD sencilla:

```text
familia OOD lemniscate -> PID lissajous
familia OOD lissajous  -> PID lissajous
familia OOD waypoint   -> PID waypoint
familia OOD composite  -> PID lissajous
```

Esta asignacion es una politica previa y fija, no una seleccion retrospectiva
segun resultados. Debe quedar registrada en el manifest o reporte.

Ademas, debe poder ejecutarse la matriz OOD completa:

```text
10 escenarios OOD x 4 PID familiares = 40 corridas
```

La bateria OOD debe permanecer conceptualmente independiente del controlador:
los escenarios describen trayectoria, vehiculo y perturbaciones. El runner de
PID cruzado debe inyectar el PID congelado seleccionado antes de ejecutar.
Si por compatibilidad el YAML necesita un controlador por defecto, este debe
usar la asignacion representativa y registrar `pid_family`; nunca debe usar
ganancias genericas sin identificar.

CLI minima esperada:

```powershell
# Baseline representativa por defecto
uv run python tools/run_classic_transfer_dataset.py `
  --dataset data/neural_ood/battery_v1 `
  --pid-source-dataset data/classic_dataset/v1 `
  --representative-only `
  --workers 8 `
  --no-visualization

# Matriz completa de los cuatro expertos sobre OOD
uv run python tools/run_classic_transfer_dataset.py `
  --dataset data/neural_ood/battery_v1 `
  --pid-source-dataset data/classic_dataset/v1 `
  --pid-family all `
  --workers 8 `
  --no-visualization
```

El runner debe permitir tambien seleccionar un PID concreto, por ejemplo:

```powershell
uv run python tools/run_classic_transfer_dataset.py `
  --dataset data/neural_ood/battery_v1 `
  --pid-source-dataset data/classic_dataset/v1 `
  --pid-family circle `
  --workers 8 `
  --no-visualization
```

Los resultados OOD deben etiquetarse como `classic_pid_<familia_pid>`. El
resumen no debe etiquetar una ejecucion con PID generico o desconocido como
`classic_family_pid`.

### RF-04C. Resumen de transferencia y comparacion neural

`tools/summarize_comparison.py` debe incorporar:

- la matriz cruzada PID sobre `test`;
- la matriz completa PID sobre OOD;
- la baseline representativa OOD como vista o subconjunto identificable;
- las tres arquitecturas `neural_outer_force`.

Las tablas deben permitir responder, como minimo:

1. Como rinde cada PID en su familia representativa.
2. Como se degrada cada PID al transferirse a otras familias.
3. Que PID generaliza mejor globalmente.
4. Como se compara cada red contra cada PID congelado.
5. Como se compara la red contra la asignacion PID representativa por defecto.

No mezclar estas filas con el oraculo outer-force por escenario. El oraculo es
una cota superior diferente y debe llevar una etiqueta separada si se incluye.

### RF-05. Presentacion estadistica honesta

`tools/summarize_comparison.py` debe dejar claro que `rmse_std` es dispersion
entre escenarios del grupo, no intervalo de confianza ni incertidumbre de una
misma condicion repetida.

La salida LaTeX y cualquier documentacion asociada deben:

- usar una cabecera explicita como `media (desv. entre escenarios)`; o
- separar media y desviacion en columnas distintas.

No usar `media ± desviacion` sin explicar la poblacion agregada.

### RF-06. Reproducibilidad del entrenamiento

Mejorar la reproducibilidad de:

- `tools/train_neural_controller.py`;
- `tools/train_neural_position_controller.py`.

Como minimo:

- registrar la semilla efectiva;
- inicializar de forma coherente Python, NumPy y PyTorch;
- usar un generador sembrado para el `DataLoader` con `shuffle=True`;
- documentar que el determinismo completo puede depender del dispositivo y de
  operaciones CUDA.

No activar algoritmos deterministas globales si degradan o rompen el
entrenamiento sin medir antes el impacto.

### RF-07. Limpieza y alineacion documental

Actualizar:

- `docs/reviews/README.md` para senalar la auditoria mas reciente y marcar las
  antiguas como historicas;
- `.agents/skills/redactar-latex-academico/` para mantener criterios de
  redaccion academica y LaTeX reutilizables;
- `README.md` y `docs/simulador/` para reflejar el artefacto comparativo
  canonico y el alcance final;
- `docs/simulador/trazabilidad.md` para distinguir `tooling implementado` de
  `evidencia experimental disponible`;
- `pyproject.toml` para sustituir la descripcion plantilla.

No editar `docs/preliminary/`: ya ha sido eliminado.

No afirmar que los resultados existentes son invalidos por su metadata de Git.
Cuando sea relevante, describirlos como resultados de la campana manual del
10 de junio de 2026.

## 6. Requisitos de calidad

### RQ-01. Integridad de artefactos

Un manifest publicado debe describir exclusivamente archivos presentes y
validados en la misma generacion.

### RQ-02. Errores accionables

Los fallos de entrada deben identificar:

- escenario o fila afectada;
- archivo o campo ausente;
- accion necesaria para corregirlo.

### RQ-03. Compatibilidad

Mantener las interfaces CLI actuales salvo cuando una opcion permita
comportamiento inseguro. Cualquier cambio incompatible debe documentarse.

### RQ-04. Simplicidad

Preferir helpers pequenos, `pathlib`, validacion explicita y pocas
abstracciones. No crear un framework generico de pipelines.

### RQ-05. Trazabilidad

Los cambios de comportamiento deben propagarse a `README.md` y
`docs/simulador/`. Los cambios de narrativa o evidencia final deben propagarse
a `TFG_Memoria/` solo cuando exista evidencia cerrada.

## 7. Estrategia de pruebas

### 7.1 Tests obligatorios para generadores

Anadir tests que verifiquen:

- rechazo de manifiesto fuente ausente;
- rechazo de escenario ausente;
- rechazo de PID o ganancias ausentes;
- rechazo de telemetria experta ausente;
- ausencia de stubs o defaults silenciosos;
- conservacion intacta del destino previo tras un fallo;
- eliminacion de residuos antiguos tras `--overwrite`;
- ausencia de manifest viejo tras fallo;
- exito del camino real existente.

Ubicaciones preferidas:

- `tests/test_outer_force_generation_integration.py`;
- `tests/test_generate_ood_battery.py`;
- `tests/test_classic_dataset_generation.py`;
- un nuevo fichero pequeno para el helper atomico, si se crea.

### 7.2 Tests obligatorios para comparacion y entrenamiento

- comprobar que la transferencia `test` incluye las cuatro familias PID y la
  diagonal;
- comprobar que `--pid-family circle` ejecuta exclusivamente el PID circle;
- comprobar que la matriz OOD completa genera 40 combinaciones unicas;
- comprobar que la baseline representativa OOD usa la politica declarada;
- comprobar que los PID se cargan desde el dataset clasico congelado;
- comprobar que ninguna fila OOD con PID conocido se etiqueta ambiguamente
  como `classic_family_pid`;
- comprobar que los reportes se deduplican por `scenario_id + pid_family`;
- comprobar el etiquetado estadistico generado;
- comprobar que semillas y configuracion quedan registradas;
- comprobar que dos `DataLoader` inicializados con la misma semilla producen
  el mismo orden en CPU.

### 7.3 Verificacion general

```powershell
uv run pytest -q
uv run python tools/run_experimental_campaign.py --dry-run
git status --short
```

La suite completa debe seguir pasando. Los comandos pesados de generacion o
entrenamiento deben ejecutarse solo tras el inventario y con alcance concreto.

## 8. Plan de implementacion

### Fase 0. Congelar decisiones e inventariar

1. Inspeccionar `data/`, `results/` y comandos documentados.
2. Crear el manifiesto de evidencia manual.
3. Clasificar cada bloque como completo, parcial, ausente o fuera de alcance.
4. Decidir el artefacto comparativo canonico.
5. Confirmar la inclusion obligatoria de transferencia PID y decidir
   explicitamente si `neural_position` y oraculo entran en la evidencia final.

**Checkpoint:** no ejecutar campanas pesadas hasta que el inventario permita
enumerar exactamente los huecos.

### Fase 1. Endurecer generadores

1. Eliminar fallbacks silenciosos de `generate_outer_force_dataset.py`.
2. Introducir escritura temporal y sustitucion segura.
3. Aplicar el patron a los cuatro generadores obligatorios.
4. Anadir tests de fallo y overwrite.
5. Actualizar documentacion de CLI y mantenimiento.

**Checkpoint:** una entrada incompleta falla sin alterar destinos existentes y
la suite focal pasa.

### Fase 2. Cerrar evidencia minima

1. Comparar el inventario con la matriz minima de `classic` y
   `neural_outer_force`.
2. Corregir y generalizar el runner de transferencia PID.
3. Ejecutar la matriz de 92 corridas PID sobre `test`.
4. Ejecutar la baseline representativa y la matriz de 40 corridas PID sobre
   OOD.
5. Ejecutar solo las demas corridas o resumenes ausentes.
6. Generar o designar el artefacto comparativo canonico.
7. Verificar filas, splits, escenarios, PID concretos y ausencia de rutas
   rotas.
8. Actualizar el manifiesto de evidencia con conteos reales.

**Checkpoint:** la comparacion principal es completa y puede reconstruirse
desde comandos documentados.

### Fase 3. Resolver ramas secundarias

Para cada rama `neural_position` y oraculo:

1. medir lo que falta;
2. incluirla si ya esta completa o su cierre es razonable;
3. en caso contrario, declararla extension fuera de la evidencia final;
4. eliminar promesas documentales incompatibles con esa decision.

**Checkpoint:** no existe ninguna rama descrita simultaneamente como
implementada, evaluada y carente de resultados.

### Fase 4. Estadistica, reproducibilidad y documentacion

1. Corregir la presentacion de `rmse_std`.
2. Mejorar y documentar semillas de entrenamiento.
3. Actualizar README, documentacion viva, trazabilidad e indice de reviews.
4. Alinear la skill de redaccion academica y `pyproject.toml`.
5. Actualizar la memoria solo con conclusiones respaldadas por la evidencia
   final.

**Checkpoint:** documentacion y memoria apuntan exclusivamente a comandos,
artefactos y alcance reales.

### Fase 5. Verificacion final

1. Ejecutar la suite completa.
2. Ejecutar validadores y dry-run de campana.
3. Revisar rutas del manifiesto de evidencia.
4. Verificar que no existen stubs ni residuos antiguos en artefactos citables.
5. Revisar el diff para evitar cambios ajenos.

## 9. Tareas implementables

- [ ] T01. Inventariar la campana manual existente.
  - Aceptacion: existe un manifiesto pequeno con estado y decision de uso de
    cada bloque de evidencia.
  - Verificacion: todas las rutas declaradas como `complete` existen.
  - Archivos: manifiesto nuevo y, si procede, ajuste minimo de `.gitignore`.

- [ ] T02. Fijar el alcance comparativo final.
  - Aceptacion: queda documentado que ramas se incluyen y cuales son
    extensiones.
  - Verificacion: README, validacion y trazabilidad no se contradicen.
  - Archivos: `README.md`, `docs/simulador/validacion.md`,
    `docs/simulador/trazabilidad.md`.

- [ ] T03. Eliminar fallbacks inseguros del dataset `outer_force`.
  - Aceptacion: entradas incompletas producen errores accionables y nunca
    generan stubs.
  - Verificacion:
    `uv run pytest tests/test_outer_force_generation_integration.py -q`.
  - Archivos: `tools/generate_outer_force_dataset.py` y tests.

- [ ] T04. Implementar escritura atomica reutilizable.
  - Aceptacion: un fallo conserva intacto el destino anterior.
  - Verificacion: tests unitarios de exito, fallo y cleanup.
  - Archivos: helper pequeno bajo `src/simulador_quad/` o `tools/`, y tests.

- [ ] T05. Aplicar escritura atomica al banco `outer_force`.
  - Aceptacion: nunca queda un manifest viejo junto a resultados parciales.
  - Verificacion:
    `uv run pytest tests/test_outer_force_generation_integration.py -q`.
  - Archivos: `tools/generate_outer_force_pid_bank.py` y tests.

- [ ] T06. Aplicar overwrite limpio al dataset clasico y bateria OOD.
  - Aceptacion: no sobreviven residuos de ejecuciones anteriores.
  - Verificacion:
    `uv run pytest tests/test_classic_dataset_generation.py tests/test_generate_ood_battery.py -q`.
  - Archivos: generadores afectados y tests.

- [ ] T07. Completar exclusivamente los huecos experimentales principales.
  - Aceptacion: las tres arquitecturas `outer_force`, la matriz PID `test` de
    92 corridas y la matriz PID OOD de 40 corridas tienen evidencia conforme
    al alcance decidido.
  - Verificacion: manifiesto de evidencia y conteos de la tabla comparativa.
  - Archivos: artefactos locales y manifiesto; no modificar codigo salvo fallo
    demostrado.

- [ ] T08. Generalizar la ejecucion cruzada de PID.
  - Aceptacion: el runner permite dataset objetivo separado del dataset fuente
    de PID, PID concreto, todos los PID, baseline representativa, filtros,
    diagonal, reanudacion y paralelizacion.
  - Verificacion: tests de matriz `test`, OOD, seleccion individual y
    deduplicacion.
  - Archivos: `tools/run_classic_transfer_dataset.py`, tests y documentacion.

- [ ] T09. Generar o designar la comparacion canonica.
  - Aceptacion: existe una unica referencia documental para la comparacion
    final y contiene las redes y cada PID familiar identificado.
  - Verificacion: script de resumen y comprobacion de valores/controladores.
  - Archivos: `results/`, README y documentacion de validacion.

- [ ] T10. Corregir la presentacion de dispersion.
  - Aceptacion: ninguna tabla presenta `rmse_std` ambiguamente como
    incertidumbre.
  - Verificacion: tests de salida y revision del LaTeX generado.
  - Archivos: `tools/summarize_comparison.py` y tests.

- [ ] T11. Mejorar reproducibilidad del entrenamiento.
  - Aceptacion: Python, NumPy, PyTorch y shuffle quedan sembrados y registrados.
  - Verificacion: tests de orden reproducible en CPU.
  - Archivos: ambos trainers y tests.

- [ ] T12. Alinear documentacion y gobernanza.
  - Aceptacion: reviews, reglas de memoria, trazabilidad y descripcion del
    proyecto reflejan el estado actual.
  - Verificacion: busqueda de referencias rotas y contradicciones conocidas.
  - Archivos: `docs/reviews/README.md`,
    `.agents/skills/redactar-latex-academico/`,
    `pyproject.toml` y documentos vivos afectados.

- [ ] T13. Verificacion integral.
  - Aceptacion: suite completa aprobada, rutas del inventario validas y diff
    limitado al alcance.
  - Verificacion:
    `uv run pytest -q`,
    `uv run python tools/run_experimental_campaign.py --dry-run`,
    `git status --short`.

## 10. Orden, paralelizacion y commits

Orden obligatorio:

```text
T01 -> T02 -> T08 -> T07 -> T09
T03 -> T04 -> T05 -> T06
T09 -> T10 -> T12
T11 puede ejecutarse tras T02
T13 cierra todo
```

Trabajo paralelizable:

- endurecimiento de generadores y elaboracion del inventario;
- reproducibilidad de entrenamiento y correcciones documentales no
  dependientes de resultados;
- tests focales de generadores distintos, si no comparten helper en edicion.

Commits recomendados, solo si el usuario los solicita:

1. `fix: reject incomplete outer-force datasets`
2. `fix: make dataset generation atomic`
3. `docs: define final experimental evidence scope`
4. `feat: run frozen pid transfer matrices`
5. `results: consolidate final controller comparison`
6. `fix: clarify comparison statistics`
7. `fix: seed neural training reproducibly`
8. `docs: align repository governance with current state`

Cada commit debe contener una unica unidad funcional y sus pruebas.

## 11. Limites para el agente implementador

### Siempre

- Trabajar con los cambios existentes del usuario.
- Inspeccionar antes de regenerar.
- Usar `uv` para Python.
- Anadir pruebas para cambios de comportamiento.
- Actualizar documentacion afectada.
- Mantener rutas relativas en manifests versionables.

### Consultar antes

- Excluir `neural_position` u oraculo si la documentacion normativa sigue
  exigiendolos y la correccion implicaria cambiar el alcance.
- Ejecutar entrenamientos o campanas que requieran varias horas.
- Anadir dependencias.
- Versionar checkpoints, telemetrias masivas o datasets.
- Modificar conclusiones sustantivas de la memoria.

### Nunca

- Invalidar o borrar los resultados manuales correctos por su metadata Git.
- Regenerar toda la campana sin inventario previo.
- Crear telemetria, escenarios, ganancias o metricas sinteticas en un dataset
  presentado como real.
- Ocultar entradas incompletas mediante defaults.
- Mezclar `neural`, `neural_position` y checkpoints legacy.
- Reintroducir `docs/preliminary/`.
- Hacer commits sin solicitud explicita.

## 12. Criterios de cierre

La subsanacion estara completa cuando:

1. Los generadores obligatorios fallen ante entradas incompletas y escriban de
   forma segura.
2. Ningun `--overwrite` probado deje residuos o manifests obsoletos.
3. Exista un inventario versionable de la campana manual.
4. Este documentado que evidencia se usa y que ramas quedan fuera.
5. La comparacion principal clasico frente a `neural_outer_force` tenga un
   artefacto canonico completo.
6. Existan 92 corridas cruzadas PID sobre `test` y 40 sobre OOD, con cada PID
   familiar identificado.
7. La bateria OOD pueda ejecutarse con un PID concreto, los cuatro PID o la
   asignacion representativa por defecto.
8. Las tablas distingan claramente media y dispersion entre escenarios.
9. La documentacion viva, trazabilidad, reviews y memoria no prometan
   artefactos ausentes.
10. La suite completa pase.
11. No se hayan regenerado innecesariamente resultados que el usuario ya
   considera correctos.
