# Especificacion: manual HTML didactico del simulador

## Estado

Especificacion validada para implementacion.

## 1. Objetivo

Crear un sitio HTML estatico multipagina que ayude al propio alumno a
comprender, recorrer y explicar su TFG sobre el simulador 6DOF de
cuadricoptero, el control clasico y el control neuronal por imitacion.

El sitio sera un recurso didactico intermedio entre la documentacion viva y la
memoria academica. Debe explicar el funcionamiento fisico, de control y
experimental del trabajo sin limitarse a convertir Markdown existente a HTML.

El manual debe:

- priorizar ingenieria aeroespacial, modelado, control y redes neuronales;
- mostrar como se conectan conceptos, codigo, escenarios, datasets y
  resultados;
- permitir que el alumno identifique el flujo completo de su trabajo;
- explicar el uso de archivos y herramientas sin convertir el manual en una
  guia extensa de ingenieria de software;
- utilizar HTML rico, SVG, tablas, diagramas y snippets cuando mejoren la
  comprension;
- funcionar localmente abriendo `docs/html/index.html`, sin servidor ni
  dependencias web externas.

## 2. Decisiones cerradas

Estas decisiones no deben reabrirse durante la implementacion:

1. El resultado sera un sitio estatico multipagina bajo `docs/html/`.
2. El HTML es un anadido y no sustituye a los documentos Markdown.
3. El HTML solo se actualizara cuando el usuario lo solicite expresamente.
4. No se integrara contenido procedente de:
   - `docs/simulador/trazabilidad.md`;
   - `docs/simulador/mantenimiento.md`.
5. El sitio se orienta al propio alumno. Debe facilitar que comprenda y pueda
   explicar su trabajo; no incluira ejercicios ni evaluaciones formales.
6. Se usaran snippets de codigo cortos, selectivos y anotados. No se explicara
   exhaustivamente la implementacion interna ni el tooling.
7. Se incorporara evidencia experimental actual para ensenar a interpretar
   resultados. Toda evidencia se marcara como instantanea fechada.
8. La interactividad sera ligera y sin dependencias:
   - navegacion;
   - pestanas;
   - acordeones;
   - resaltado o copia de snippets mediante JavaScript local pequeno.
9. No se usaran frameworks frontend, gestores de paquetes JavaScript, CDN ni
   librerias remotas.
10. La huella Git y las fuentes integradas quedaran registradas para poder
    comparar una futura actualizacion con la instantanea original.
11. No se modificara la narrativa ni el contenido de `TFG_Memoria/` como parte
    de esta tarea.
12. No se generaran resultados experimentales nuevos. El manual consumira
    exclusivamente evidencia ya disponible y versionable.

## 3. Publico y criterio editorial

El lector principal es el alumno autor del TFG, con formacion de ingenieria
aeroespacial y conocimientos basicos de programacion y redes neuronales.

Cada tema tecnico debe responder, cuando aplique, a estas preguntas:

1. Que concepto representa.
2. Por que es necesario en este simulador.
3. Que unidades, signos y marcos de referencia utiliza.
4. Como se conecta con el resto del flujo.
5. Donde aparece en escenarios, codigo, telemetria o resultados.
6. Que simplificaciones y limites tiene.
7. Como se puede explicar posteriormente en la memoria o defensa.

La explicacion conceptual debe preceder al snippet o comando. El codigo actua
como evidencia y puente hacia la implementacion, no como organizador principal
de la narrativa.

## 4. Fuentes de contenido

### 4.1 Fuentes principales

Usar como fuentes de verdad, por este orden:

1. `docs/01_principios_tfg.md`.
2. `docs/02_requisitos_ingenieria_simulador.md`.
3. Documentos permitidos de `docs/simulador/`.
4. Codigo, escenarios y pruebas actuales.
5. `README.md`.
6. `results/comparison_summary.csv`,
   `results/comparison_all_runs.csv` y `results/evidence_manifest.csv`.
7. `TFG_Memoria/` como apoyo para conectar el manual con la futura narrativa
   academica, sin copiar extensamente ni modificarla.

Documentos permitidos de `docs/simulador/`:

- `README.md`;
- `arquitectura.md`;
- `control_neuronal.md`;
- `dataset_clasico.md`;
- `escenarios_yaml.md`;
- `guia_uso.md`;
- `validacion.md`.

### 4.2 Fuentes excluidas

No leer ni integrar como fuente de contenido del manual:

- `docs/simulador/trazabilidad.md`;
- `docs/simulador/mantenimiento.md`.

La exclusion debe quedar registrada en el manifiesto de instantanea.

Las auditorias, planes historicos y anexos de revision no deben utilizarse
como narrativa del manual. Solo pueden consultarse para resolver una
contradiccion tecnica concreta y nunca deben listarse como fuentes integradas.

### 4.3 Politica de evidencia

Los valores experimentales mostrados deben derivarse de los CSV canonicos
versionados en `results/`. No se copiaran manualmente valores desde la memoria
ni se inventaran resultados ausentes.

Cada tabla o visualizacion de resultados debe indicar:

- archivo fuente;
- fecha o huella de la instantanea;
- poblacion agregada;
- significado de la metrica;
- limitacion relevante de interpretacion.

La desviacion entre escenarios no se presentara como incertidumbre
estadistica ni intervalo de confianza.

## 5. Arquitectura del sitio

Crear esta estructura base:

```text
docs/html/
  index.html
  01_modelo_6dof.html
  02_control_clasico.html
  03_escenarios_simulacion.html
  04_dataset_experto.html
  05_control_neuronal.html
  06_validacion_resultados.html
  07_guia_operativa.html
  assets/
    styles.css
    site.js
    diagrams/
  snapshot.json
  README.md
```

No crear un sistema de plantillas, generador estatico ni pipeline automatico
salvo que durante la implementacion se demuestre imprescindible para evitar
errores repetitivos. La primera version debe mantenerse como HTML, CSS, JS y
SVG simples y revisables.

Los nombres pueden ajustarse ligeramente por claridad, pero debe conservarse
la separacion tematica y una portada unica.

## 6. Contenido obligatorio

### 6.1 Portada y mapa del trabajo

La portada debe:

- explicar objetivo, alcance y limites del TFG;
- mostrar una ruta recomendada de lectura;
- incluir un mapa visual del flujo completo:

```text
escenario -> referencia y observacion -> controlador -> mixer y actuadores
-> dinamica 6DOF -> telemetria y metricas -> dataset -> entrenamiento
-> evaluacion cerrada -> comparacion
```

- distinguir ingenieria aeroespacial, aprendizaje neuronal y soporte
  operativo;
- enlazar cada bloque con su capitulo;
- mostrar discretamente commit, fecha y estado Git de la instantanea;
- explicar que el HTML no sustituye al Markdown y se actualiza solo a peticion
  del usuario;
- enlazar a `snapshot.json`.

### 6.2 Modelo fisico 6DOF

Explicar:

- mundo ENU y cuerpo FRD;
- convenciones de ejes, signos, actitud y empuje;
- estado fisico del vehiculo;
- cuaterniones y transformacion cuerpo-mundo;
- dinamica translacional y rotacional;
- fuerzas, momentos y gravedad;
- drag lineal, viento y simplificaciones;
- integracion RK4 y normalizacion del cuaternion;
- limites de validez del modelo.

Incluir:

- SVG de marcos ENU/FRD;
- SVG de fuerzas y momentos del cuadricoptero;
- tabla de variables, marco y unidades;
- ecuaciones legibles;
- snippets anotados y breves conectados con
  `src/simulador_quad/dynamics/rigid_body.py` y los helpers de actitud.

### 6.3 Actuadores, mixer y control clasico

Explicar:

- relacion entre empuje colectivo, momentos y rotores;
- mixer y geometria de actuacion;
- saturacion, retardo y lag;
- estructura en cascada;
- lazo externo de posicion;
- fuerza deseada expresada en mundo ENU;
- conversion fuerza-yaw a actitud deseada;
- lazo interno de actitud y momentos FRD;
- por que el controlador clasico tambien forma parte del controlador neuronal
  hibrido.

Incluir:

- diagrama de bloques del control clasico;
- flujo visual desde errores de posicion hasta rotores;
- tabla de entradas, salidas, unidades y marcos;
- snippets selectivos de `control/classic.py`, mixer y actuadores.

### 6.4 Escenarios y flujo de simulacion

Explicar:

- componentes de un escenario YAML;
- vehiculo, estado inicial, trayectoria, controlador, perturbaciones, timing,
  terminacion y salida;
- trayectorias `hold`, `circle`, `lissajous`, `waypoint` y `composite`;
- diferencia entre trayectorias temporales y state-aware;
- pasos separados de fisica, control y telemetria;
- flujo de una ejecucion y artefactos resultantes;
- diferencia entre estado verdadero, observacion y referencia.

Incluir:

- un YAML minimo anotado;
- un diagrama temporal multi-rate;
- una tabla de artefactos generados;
- comandos esenciales de ejecucion con `uv`.

### 6.5 Dataset clasico y experto outer-force

Explicar:

- finalidad del dataset clasico;
- familias, perfiles, perturbaciones y splits;
- PID congelados por familia;
- diferencia entre escenario, episodio, corrida, telemetria, dataset y
  evidencia;
- construccion del banco de candidatos outer-force;
- filtros de seguridad y seleccion del experto por escenario;
- generacion de targets `desired_force_W_N`;
- separacion entre `train`, `val`, `test` y OOD;
- por que la normalizacion se ajusta solo con `train`.

Incluir:

- diagrama del pipeline de dataset experto;
- tablas de familias y artefactos;
- snippets o comandos anotados solo donde ayuden a comprender el flujo.

### 6.6 Control neuronal por imitacion

Explicar:

- motivacion de aprender el lazo externo de fuerza;
- contrato `outer_force`: observacion y referencia a
  `desired_force_W_N[3]`;
- features minimas y completas;
- targets y normalizacion;
- diferencias conceptuales entre MLP, GRU y LSTM;
- entrenamiento supervisado por imitacion;
- inferencia hibrida con limites de norma, inclinacion y componente vertical;
- conservacion del PID clasico de actitud;
- diferencia entre error supervisado de fuerza y desempeno en bucle cerrado;
- compatibilidad y rechazo de checkpoints legacy;
- `neural_position` solo como extension/tooling fuera de la comparacion
  principal.

Incluir:

- diagrama de entrenamiento;
- diagrama de inferencia cerrada;
- tabla de entradas, salidas y protecciones;
- snippets anotados del contrato outer-force y clipping, sin recorrer toda la
  clase.

### 6.7 Validacion y resultados

Explicar:

- criterios de validez y terminacion;
- diferencia entre exito de mision, seguridad y exito de control;
- RMSE, error maximo, saturacion, degradacion y clipping;
- diferencia entre evaluacion supervisada y cerrada;
- comparacion `test` frente a OOD;
- transferencia cruzada de PID;
- como leer una tabla y una figura comparativa;
- limites para extraer conclusiones.

Incluir evidencia actual procedente de los CSV canonicos:

- tablas resumidas de controladores y familias;
- visualizacion de transferencia PID;
- comparacion clasico frente a MLP, GRU y LSTM;
- notas explicitas sobre cantidad de corridas y dispersion entre escenarios.

No ocultar fallos ni seleccionar solo resultados favorables.

### 6.8 Guia operativa y mapa de archivos

Explicar de forma breve:

- como preparar el entorno con `uv`;
- como ejecutar un escenario;
- como generar y leer artefactos;
- como recorrer el pipeline clasico y neuronal;
- como localizar los archivos importantes por concepto;
- que herramientas existen y para que se usan.

No explicar internals de herramientas o arquitectura SWE salvo cuando sean
criticos para comprender fisica, control, reproducibilidad o validez
experimental.

Incluir:

- comandos esenciales reproducibles;
- mapa conceptual de directorios y archivos;
- glosario de abreviaturas, senales, unidades y artefactos.

## 7. Lenguaje visual y componentes

El sitio debe usar una identidad comun y sobria, adecuada para documentacion
tecnica academica.

Componentes obligatorios:

- navegacion lateral comun en escritorio;
- navegacion compacta en pantallas estrechas;
- indice local por pagina;
- breadcrumbs o indicador de capitulo;
- tablas adaptables;
- bloques de ecuaciones;
- snippets con ruta de origen y anotacion;
- SVG propios;
- enlaces entre conceptos relacionados;
- callouts con estas categorias:
  - `Concepto fisico`;
  - `Decision de diseno`;
  - `Limitacion`;
  - `Conexion con la memoria`;
  - `Como reproducirlo`.

Los diagramas SVG deben:

- ser legibles sin color;
- mantener ENU/FRD y unidades correctas;
- utilizar texto seleccionable cuando sea razonable;
- incluir `title` o descripcion accesible;
- evitar decoracion sin contenido tecnico.

No usar imagenes generadas por IA para diagramas tecnicos. Preferir SVG
editables y deterministas.

## 8. Contrato de instantanea documental

Crear `docs/html/snapshot.json` con, como minimo:

```json
{
  "schema_version": 1,
  "created_at": "ISO-8601",
  "git_commit": "hash completo",
  "git_dirty": false,
  "integrated_sources": [
    {
      "path": "docs/...",
      "sha256": "..."
    }
  ],
  "excluded_sources": [
    "docs/simulador/trazabilidad.md",
    "docs/simulador/mantenimiento.md"
  ],
  "candidate_documents_at_creation": [
    "docs/..."
  ],
  "evidence_sources": [
    {
      "path": "results/...",
      "sha256": "..."
    }
  ]
}
```

Requisitos:

- `git_commit` debe corresponder al `HEAD` usado para crear el manual;
- `git_dirty` debe reflejar el estado real en el momento de capturar la
  instantanea;
- los hashes deben calcularse sobre bytes de archivo con SHA-256;
- `integrated_sources` solo incluye documentos realmente utilizados;
- `candidate_documents_at_creation` permite detectar documentos nuevos en una
  futura actualizacion;
- las fuentes excluidas deben permanecer explicitamente registradas;
- el sitio debe seguir funcionando aunque `snapshot.json` se abra sin
  JavaScript.

Crear tambien `docs/html/README.md` con:

- finalidad del sitio;
- como abrirlo;
- politica de instantanea manual;
- como comparar fuentes en una futura actualizacion;
- prohibicion de asumir que el HTML esta sincronizado con Markdown.

Anadir una nota breve en `AGENTS.md`, dentro de las fuentes de verdad o reglas
documentales:

> `docs/html/` es una instantanea didactica adicional identificada por su
> huella Git. No sustituye al Markdown y solo se actualiza cuando el usuario lo
> solicita.

El HTML no debe incorporarse como fuente de verdad normativa.

## 9. Accesibilidad y portabilidad

Requisitos minimos:

- funcionar desde `file://` abriendo `docs/html/index.html`;
- no realizar peticiones de red;
- HTML semantico con jerarquia correcta de encabezados;
- navegacion utilizable mediante teclado;
- foco visible;
- contraste suficiente;
- texto alternativo o descripcion para diagramas;
- tablas con encabezados;
- diseno legible en escritorio y movil;
- contenido esencial accesible sin JavaScript;
- respetar `prefers-reduced-motion`;
- no depender solo del color para transmitir significado.

## 10. Limites

### Siempre

- Mantener mundo ENU, cuerpo FRD, signos y unidades correctos.
- Verificar conceptos contra fuentes de verdad actuales.
- Usar `uv` para cualquier comando Python auxiliar.
- Mantener HTML, CSS, JS y SVG simples y locales.
- Identificar claramente la instantanea y sus fuentes.
- Tratar los resultados como evidencia fechada y limitada.
- Actualizar `AGENTS.md` con la politica breve del HTML.

### Consultar antes

- Anadir una dependencia nueva.
- Introducir un generador estatico o pipeline automatico.
- Modificar documentos Markdown fuente para adaptarlos al HTML.
- Cambiar narrativa o resultados de `TFG_Memoria/`.
- Generar o ejecutar nueva evidencia experimental.

### Nunca

- Sustituir, borrar o degradar la documentacion Markdown.
- Presentar el HTML como fuente normativa o automaticamente sincronizada.
- Integrar contenido de `trazabilidad.md` o `mantenimiento.md`.
- Usar CDN, recursos remotos o frameworks frontend.
- Inventar ecuaciones, unidades, resultados o conclusiones.
- Ahondar en SWE o tooling sin impacto directo en comprension, uso,
  reproducibilidad o validez.
- Ocultar resultados fallidos o presentar dispersion entre escenarios como
  incertidumbre estadistica.

## 11. Estrategia de implementacion

### Fase 1. Inventario y esqueleto

1. Capturar commit y estado Git inicial.
2. Inventariar fuentes permitidas, excluidas y evidencia disponible.
3. Crear estructura, estilos comunes y navegacion multipagina.
4. Crear `snapshot.json` y `docs/html/README.md`.
5. Anadir la nota breve a `AGENTS.md`.

**Checkpoint:** la portada y todas las paginas vacias enlazan correctamente y
el sitio funciona desde `file://`.

### Fase 2. Fundamentos aeroespaciales y control

1. Redactar portada, modelo 6DOF y control clasico.
2. Crear SVG de marcos, fuerzas, mixer y control en cascada.
3. Integrar tablas de variables, unidades y marcos.
4. Anadir snippets selectivos verificados contra codigo.

**Checkpoint:** un lector puede explicar el estado, las ecuaciones, ENU/FRD y
el flujo de control hasta rotores.

### Fase 3. Simulacion, datasets y red neuronal

1. Redactar escenarios y flujo multi-rate.
2. Redactar dataset clasico y seleccion del experto.
3. Redactar entrenamiento e inferencia outer-force.
4. Crear diagramas de dataset, entrenamiento e inferencia cerrada.

**Checkpoint:** el lector puede seguir el flujo desde un YAML hasta un
checkpoint y su ejecucion cerrada.

### Fase 4. Validacion, evidencia y uso

1. Redactar validacion y guia operativa.
2. Construir tablas y visualizaciones desde CSV canonicos.
3. Identificar todas las cifras con fuente y huella de instantanea.
4. Completar mapa de archivos y glosario.

**Checkpoint:** el lector puede interpretar resultados, distinguir tipos de
evaluacion y reproducir los comandos esenciales.

### Fase 5. Verificacion integral

1. Verificar enlaces internos, rutas y ausencia de recursos remotos.
2. Validar semantica HTML y accesibilidad basica.
3. Abrir todas las paginas desde `file://`.
4. Revisar visualmente escritorio y movil.
5. Comprobar hashes y contenido de `snapshot.json`.
6. Confirmar que no se integro contenido excluido.
7. Revisar ecuaciones, unidades, marcos y resultados contra sus fuentes.

## 12. Tareas implementables

- [ ] T01. Crear inventario y contrato de instantanea.
  - Aceptacion: `snapshot.json` contiene commit, estado Git, hashes, fuentes
    integradas, candidatas, excluidas y evidencia.
  - Verificacion: recalcular hashes y comparar.
  - Archivos: `docs/html/snapshot.json`, `docs/html/README.md`, `AGENTS.md`.

- [ ] T02. Crear sistema visual y navegacion comun.
  - Aceptacion: todas las paginas comparten navegacion, estilos, indice local
    y comportamiento adaptable sin dependencias externas.
  - Verificacion: abrir cada pagina directamente desde disco.
  - Archivos: HTML base, `assets/styles.css`, `assets/site.js`.

- [ ] T03. Redactar portada y mapa completo del trabajo.
  - Aceptacion: el flujo conceptual completo y la politica de instantanea son
    visibles desde `index.html`.
  - Verificacion: todos los bloques enlazan a su capitulo.

- [ ] T04. Redactar modelo 6DOF y crear diagramas fisicos.
  - Aceptacion: estado, marcos, fuerzas, momentos, ecuaciones, RK4 y limites
    quedan explicados con unidades y snippets verificados.
  - Verificacion: revision cruzada con requisitos y codigo.

- [ ] T05. Redactar mixer, actuadores y control clasico.
  - Aceptacion: queda explicado el flujo desde errores de posicion hasta
    comandos de rotor y la estructura en cascada.
  - Verificacion: revision cruzada con `control/classic.py`, mixer y
    actuadores.

- [ ] T06. Redactar escenarios y flujo de simulacion.
  - Aceptacion: el lector puede interpretar un YAML, el flujo multi-rate y los
    artefactos resultantes.
  - Verificacion: ejecutar o contrastar los comandos documentados.

- [ ] T07. Redactar dataset clasico y seleccion del experto.
  - Aceptacion: quedan diferenciados escenarios, episodios, splits, bancos,
    expertos, targets y evidencia.
  - Verificacion: revision contra manifests y documentacion viva permitida.

- [ ] T08. Redactar control neuronal outer-force.
  - Aceptacion: quedan explicados features, targets, modelos, entrenamiento,
    clipping, inferencia hibrida y evaluacion cerrada.
  - Verificacion: revision contra codigo y configuraciones actuales.

- [ ] T09. Redactar validacion e integrar resultados actuales.
  - Aceptacion: las tablas y visualizaciones proceden de CSV canonicos,
    incluyen fallos y declaran poblacion, fuente y limitaciones.
  - Verificacion: recalcular una muestra de valores desde los CSV.

- [ ] T10. Redactar guia operativa, mapa de archivos y glosario.
  - Aceptacion: el lector puede localizar conceptos y ejecutar los flujos
    esenciales sin una explicacion extensa de SWE.
  - Verificacion: comprobar rutas y comandos.

- [ ] T11. Verificar sitio completo.
  - Aceptacion: enlaces, accesibilidad basica, responsive, `file://`,
    instantanea y exactitud tecnica quedan revisados.
  - Verificacion: inspeccion visual con navegador y comprobaciones
    automatizadas ligeras.

## 13. Verificacion prevista

La implementacion puede anadir scripts de comprobacion pequenos bajo
`tools/` o tests bajo `tests/` solo si aportan validacion reproducible y no
introducen dependencias.

Comprobaciones minimas:

```powershell
# Confirmar que no hay URLs remotas en el sitio
rg -n 'https?://|//cdn' docs/html

# Confirmar exclusiones
rg -n 'trazabilidad\.md|mantenimiento\.md' docs/html

# Revisar estado final
git status --short
```

La segunda busqueda solo puede encontrar las exclusiones declaradas en
`snapshot.json` o `docs/html/README.md`; no debe encontrar contenido integrado
ni enlaces de lectura hacia esos documentos.

Usar el navegador local para verificar:

- portada;
- navegacion entre todos los capitulos;
- vista movil;
- pestanas y acordeones;
- funcionamiento sin JavaScript para el contenido esencial;
- legibilidad de SVG y tablas.

## 14. Criterios de cierre

La tarea estara completa cuando:

1. Existe un sitio multipagina funcional desde `docs/html/index.html`.
2. El manual permite seguir el flujo completo del TFG desde el modelo fisico
   hasta la comparacion experimental.
3. La narrativa prioriza ingenieria aeroespacial, control e imitacion
   neuronal.
4. El uso de SWE y tooling queda limitado a comprension y operacion.
5. Los SVG, tablas, ecuaciones y snippets aportan informacion tecnica
   correcta.
6. La evidencia actual esta integrada, fechada y correctamente limitada.
7. El HTML no contiene recursos externos ni requiere servidor.
8. `snapshot.json` permite identificar commit, fuentes cambiadas y documentos
   nuevos en una futura actualizacion.
9. `trazabilidad.md` y `mantenimiento.md` permanecen excluidos.
10. `AGENTS.md` registra que el HTML es una instantanea adicional actualizada
    solo bajo peticion.
11. El sitio supera la revision visual, de enlaces, accesibilidad basica y
    exactitud tecnica.
12. No se ha modificado la memoria ni se ha generado evidencia experimental
    nueva.

