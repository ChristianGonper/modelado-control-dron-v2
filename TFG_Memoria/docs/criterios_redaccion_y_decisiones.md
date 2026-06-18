# Criterios de redacción y decisiones pendientes de desarrollar

## Procedimiento de redacción

La memoria debe construirse a partir de las ideas, decisiones y opiniones que el
usuario verbalice, la evidencia del repositorio, las fuentes académicas y las
propuestas razonadas de la IA. El agente transformará esas aportaciones en
redacción académica, podrá proponer argumentos o alternativas y avisará al
usuario de cualquier ampliación relevante o justificación que siga faltando.

Cuando sea necesario explicar una implementación concreta, se formularán
preguntas dirigidas a la CLI `grok` para localizar y entender el código
pertinente. Después se verificarán únicamente los archivos necesarios antes de
incorporar la explicación a la memoria.

Para afirmaciones procedentes de literatura se usarán fuentes originales
verificadas. NotebookLM podrá procesar varios artículos, responder cuestiones
concretas y preparar informes con propuestas de citas IEEE, pero las citas y
afirmaciones deberán comprobarse antes de incorporarlas.

## Criterio narrativo

El trabajo debe contar una historia cohesionada que comience dejando claro qué
se pretende hacer, por qué resulta relevante y cómo se va a comprobar. Cada
capítulo debe preparar el siguiente y toda decisión importante debe relacionarse
con los objetivos, la implementación o la metodología experimental.

El título del segundo capítulo será **Estado del arte**, conforme a la
denominación habitual observada en otros trabajos. Los fundamentos procedentes
de la literatura se presentarán allí; las decisiones adoptadas y su aplicación
concreta se desarrollarán en los capítulos técnicos y metodológicos.

## Decisiones que deben justificarse

Durante la redacción no deben quedar al azar, entre otras, las siguientes
decisiones:

- las ecuaciones dinámicas empleadas y las simplificaciones físicas adoptadas;
- las convenciones ENU/FRD, límites físicos y límite de vuelco;
- el diseño y la sintonización de los controladores PD, junto con los métodos
  clásicos alternativos y la razón para no emplearlos;
- las trayectorias, perturbaciones, escenarios, splits y mecanismos de
  comparación escogidos;
- las políticas de penalización, filtros de seguridad y criterios de éxito;
- la frontera híbrida de predicción de fuerza deseada y las variables de entrada
  seleccionadas;
- el tamaño, parámetros y entrenamiento de MLP, GRU y LSTM;
- los hiperparámetros probados y el criterio usado para seleccionar modelos;
- las métricas elegidas y la relación entre resultados, objetivos y
  conclusiones.

Las explicaciones deben cubrir, según corresponda, motivación, alternativas,
implementación, evidencia y limitaciones.

## Alcance neuronal acordado

La comparación principal incluye MLP, GRU y LSTM que sustituyen el lazo externo
y predicen la fuerza deseada en el sistema ENU. Las tres arquitecturas forman
parte del trabajo.

Por ahora quedan fuera del alcance experimental principal:

- `neural_position`, que predice log-multiplicadores de las ganancias;
- el entrenamiento con `outer_force_full_v1`, que utiliza 31 variables.

Estas rutas pueden mencionarse brevemente como alternativas implementadas o
trabajo futuro, pero no deben confundirse con la comparación principal.

## Decisiones de formato y terminología

- Se mantendrá la clase LaTeX actual mientras el resultado visual cumpla el
  reglamento; no es necesario migrar a comandos `\chapter`.
- El controlador clásico se describirá técnicamente como **PD en cascada**.
  Las denominaciones PID se conservarán únicamente cuando sea necesario
  identificar artefactos, scripts o nombres heredados.
- Se permiten snippets breves cuando ayuden a explicar una decisión; para el
  resto del código se enlazará el repositorio mediante una nota al pie.
- En la memoria se utilizará «predicción de fuerza deseada» en lugar de
  `outer-force`. No se usará «predicción de empuje» porque la red no produce
  directamente el empuje colectivo ni los comandos de rotor.
- Los términos se introducirán primero en español. Los acrónimos ingleses
  aceptados, como OOD, se definirán junto al término y se añadirán de inmediato
  a la lista de abreviaturas.
- La declaración de uso de IA no se actualizará durante la redacción ordinaria.
  El usuario proporcionará al final el relato completo de herramientas y usos.
