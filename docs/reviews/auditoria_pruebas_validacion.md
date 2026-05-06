# Auditoria de pruebas, validacion, escenarios y metricas

Fecha de auditoria: 2026-05-04  
Alcance: repositorio `modelado-control-dron`, con foco en pruebas, validacion fisica, escenarios YAML, metricas, artefactos en `results/` y evidencias necesarias para una memoria de TFG.  
Restriccion aplicada: no se ha modificado codigo fuente ni tests. No se han regenerado resultados para evitar efectos colaterales sobre `results/`.

## Referencias normativas usadas

- `AGENTS.md`: el trabajo debe mantener el enfoque de simulador 6DOF para comparar control clasico y control neuronal por imitacion, con trazabilidad, reproducibilidad y claridad.
- `docs/01_principios_tfg.md`: exige trazabilidad desde objetivo, requisito, modelo, software, escenario y metrica, ademas de reproducibilidad experimental.
- `docs/02_requisitos_ingenieria_simulador.md`: exige pruebas o escenarios para cuaterniones, ENU/FRD, RK4, actuadores, perturbaciones, condiciones de fin y metricas obligatorias.
- `docs/03_criterios_ingenieria_software.md`: exige pruebas para invariantes fisicas, telemetria, metricas, escenarios minimos con control clasico y neuronal cargado o simulado.

## Resumen ejecutivo

El repositorio tiene una base de pruebas razonable para componentes fisicos aislados: actitud, RK4 en casos simples, actuadores, mezclador, perturbaciones, trayectorias, runner, metricas y visualizacion. Tambien existen escenarios YAML ejecutables para `hover`, `circle`, `lissajous` y `waypoint`, y artefactos de salida en `results/` con `telemetry.json`, `metrics.json`, figuras y visor HTML.

La principal debilidad para un TFG no es la ausencia total de tests, sino la falta de una capa explicita de validacion experimental y de criterios de aceptacion numericos. Los tests actuales verifican funciones, pero no fijan una matriz de validacion con tolerancias fisicas, regresiones numericas de escenarios, comparacion clasico-neuronal, ni evidencias resumidas listas para defender resultados en memoria academica.

## Hallazgos priorizados

### P0 - No hay cobertura de controlador neuronal ni comparacion cerrada clasico vs neuronal

**Evidencia.** La documentacion viva declara que todavia no existe controlador neuronal real, entrenamiento, dataset ni evaluacion neuronal en bucle cerrado (`docs/simulador/README.md:23-26`). El cargador de escenarios solo acepta `controller.type == "classic"` y rechaza cualquier otro tipo (`src/simulador_quad/scenarios/loader.py:81-90`). La referencia YAML tambien indica que actualmente solo se acepta `"classic"` (`docs/simulador/escenarios_yaml.md:172-181`). Los tests de control cubren solo `ClassicCascadeController` (`tests/test_control.py:6-71`).

**Riesgo.** El objetivo normativo del TFG es comparar control clasico frente a control neuronal por imitacion. Sin al menos un controlador neuronal cargable o simulado en tests y escenarios, la validacion no cubre el eje central del trabajo. Las metricas actuales pueden evaluar el simulador clasico, pero no sostienen una comparacion academica entre estrategias.

**Recomendacion.** Definir una fase minima de validacion neuronal:

- test de carga/inferencia de un controlador neuronal ficticio o congelado con interfaz `observacion + referencia -> comando`;
- escenario YAML equivalente para clasico y neuronal con misma semilla y condiciones;
- metrica comparativa tabulada por escenario: RMSE, MAE, error maximo, esfuerzo, saturacion, terminacion;
- evidencia en `results/` separada por controlador, por ejemplo `results/hover_clean/classic/` y `results/hover_clean/neural_stub/`.

### P1 - Falta una matriz explicita de validacion con criterios de aceptacion numericos

**Evidencia.** Hay pruebas unitarias de casos conocidos: caida libre y hover (`tests/test_dynamics.py:4-46`), rotacion simple (`tests/test_dynamics.py:68-90`), signo de empuje ENU/FRD (`tests/test_attitude.py:29-42`), drag disipativo (`tests/test_perturbations.py:4-22`) y multi-rate (`tests/test_runner.py:47-79`). Sin embargo, no existe un documento o fixture que vincule cada requisito normativo con un test, escenario, tolerancia y resultado esperado. Las metricas se calculan sin umbrales de aceptacion (`src/simulador_quad/metrics/report.py:43-59`).

**Riesgo.** Para memoria academica, "el test pasa" no equivale a "el modelo queda validado". Sin tolerancias y criterios por escenario, no se puede defender si un RMSE de 0.31 m en hover, 0.50 m en Lissajous o 0.27 m con viento son buenos, malos o simplemente observados.

**Recomendacion.** Crear una matriz de validacion, idealmente en `docs/simulador/validacion.md`, con columnas:

- requisito;
- modulo/software;
- test unitario;
- escenario YAML;
- metrica;
- criterio de aceptacion;
- artefacto de evidencia en `results/`;
- estado: cubierto, parcial, pendiente.

Ejemplo: "Hover sin perturbaciones: `termination_reason == Time limit reached`, `saturation_percentage == 0`, `position_rmse_m < X`, `max_rotor_speed_rad_s < omega_max`".

### P1 - No hay regresiones numericas de escenarios completos

**Evidencia.** `tests/test_runner.py` valida un runner sintetico corto y condiciones de terminacion (`tests/test_runner.py:47-138`), pero no ejecuta los YAML reales de `scenarios/`. Los escenarios reales declaran salidas en `results/` (`scenarios/hover_clean.yaml:44-47`, `scenarios/circle_noisy_wind.yaml:48-51`), y existen resultados historicos, pero no hay test que compare metricas esperadas por escenario contra bandas estables.

**Riesgo.** Cambios en controlador, integrador, mezclador o parametros pueden degradar los resultados sin romper tests unitarios. Esto es especialmente critico porque el TFG depende de conclusiones cuantitativas.

**Recomendacion.** Anadir en una fase futura tests de regresion de escenarios completos, sin usar los `results/` versionados como oraculo unico. Propuesta:

- ejecutar escenarios cortos o perfiles `*_regression.yaml` en directorio temporal;
- fijar tolerancias por metrica, no igualdad exacta;
- verificar `termination_reason`, duracion aproximada, RMSE maximo, saturacion maxima y ausencia de no finitos;
- mantener una tabla de baseline con fecha, commit y entorno.

### P1 - La telemetria cubre muchos campos, pero no registra todo lo necesario para auditar fallos y estabilidad

**Evidencia.** `TelemetrySample` contiene estado, observacion, referencia, comando, rotor objetivo/aplicado y causa de terminacion (`src/simulador_quad/core/contracts.py:57-66`). La exportacion JSON incluye esos campos (`src/simulador_quad/telemetry/export.py:16-57`). La causa de terminacion se escribe solo en la ultima muestra existente cuando se detecta el fin (`src/simulador_quad/runner.py:141-146`).

**Riesgo.** Para auditar estabilidad y terminaciones, falta informacion agregada o directa como:

- instante exacto de terminacion en `metrics.json`;
- estado final asociado a terminacion;
- contador consecutivo de saturacion o degradacion;
- margen respecto a limites de actitud, posicion y velocidad;
- flags de no finitos en comandos y metricas, no solo en estado.

**Recomendacion.** Extender metricas y telemetria en fases posteriores para incluir `termination_time_s`, `final_state`, `max_tilt_angle_rad`, maximos de posicion/velocidad, duracion consecutiva maxima de saturacion y validacion de no finitos en comandos/rotors/metricas.

### P1 - Las metricas obligatorias estan parcialmente cubiertas, pero son insuficientes para comparacion experimental robusta

**Evidencia.** `compute_metrics` calcula RMSE, MAE, maximo, desviacion de error, esfuerzo agregado, velocidades maximas, saturacion, degradacion, causa y duracion (`src/simulador_quad/metrics/report.py:43-59`). La documentacion describe esos campos (`docs/simulador/arquitectura.md:66-78`, `docs/simulador/guia_uso.md:79-89`). El test de metricas solo usa dos muestras sinteticas y comprueba un subconjunto (`tests/test_metrics.py:33-49`).

**Riesgo.** El esfuerzo de control se reduce a `abs(T) + ||tau||` (`src/simulador_quad/metrics/report.py:25-27`), mezclando magnitudes con unidades distintas. Esto puede valer como indicador interno, pero no basta para defender esfuerzo de control en un TFG. Tampoco hay metricas por eje, energia aproximada, integral de empuje, RMS de momentos, error estacionario, overshoot, tiempo de establecimiento o tracking por tramo.

**Recomendacion.** Separar metricas fisicas:

- seguimiento: RMSE/MAE/maximo por eje y norma, error final, error estacionario;
- esfuerzo: media/max/RMS de empuje colectivo, momentos por eje, omega por rotor, integral de `sum(omega_i^2)` o `sum(T_i)`;
- estabilidad: max roll/pitch, max velocidad, max altura/min altura, no finitos;
- actuadores: porcentaje de saturacion por rotor, degradacion colectiva, margen a `omega_max`;
- comparacion: tabla por escenario y controlador con deltas relativos.

### P2 - Los escenarios YAML son legibles y trazables, pero no declaran criterios esperados

**Evidencia.** Los escenarios declaran vehiculo, estado inicial, trayectoria, controlador, perturbaciones, tiempos, terminacion y salida, por ejemplo `hover_clean.yaml` (`scenarios/hover_clean.yaml:4-47`) y `circle_noisy_wind.yaml` (`scenarios/circle_noisy_wind.yaml:4-51`). La documentacion explica estructura y convenciones (`docs/simulador/escenarios_yaml.md:1-40`, `docs/simulador/escenarios_yaml.md:245-253`).

**Riesgo.** Un escenario reproducible no es necesariamente un escenario validado. Falta declarar si el escenario es de validacion nominal, robustez, estres o fallo esperado, y que resultados son aceptables.

**Recomendacion.** Anadir metadatos no invasivos en una futura revision de escenarios:

```yaml
validation:
  category: nominal | robustness | stress | expected_failure
  expected_termination: "Time limit reached"
  acceptance:
    max_position_rmse_m: 0.5
    max_saturation_percentage: 1.0
```

Si se prefiere no cambiar YAML, mantener estos criterios en una tabla documental versionada.

### P2 - Hay resultados historicos utiles, pero su trazabilidad es incompleta como evidencia final

**Evidencia.** Existen artefactos en `results/` para `hover_clean`, `circle_drag`, `circle_noisy_wind`, `lissajous_clean`, `waypoint_clean` y escenarios de estres. `metrics.json` incluye `metadata.config`, nombre de escenario y semilla. La guia afirma que esto mantiene trazabilidad (`docs/simulador/guia_uso.md:91-101`). La inspeccion de metricas existentes muestra terminaciones por limite de tiempo para los escenarios principales y un fallo de actitud en `results/test_line`.

**Riesgo.** Los resultados no registran commit, version de paquete, comando ejecutado, fecha de ejecucion, version de Python/uv ni si el arbol estaba limpio. Ademas, hay resultados de escenarios de estres (`stress_delay_instability`, `stress_wind_heavy`) sin YAML correspondiente visible en `scenarios/`, lo que dificulta reproducirlos desde el repositorio actual.

**Recomendacion.** Para resultados usados en memoria, guardar un manifiesto por ejecucion:

- commit Git;
- estado limpio/sucio;
- comando;
- fecha/hora;
- version Python y dependencias principales;
- ruta exacta del YAML o copia del YAML completo;
- hash del fichero de escenario;
- identificador de controlador y artefacto neuronal, cuando exista.

### P2 - Invariantes fisicas principales cubiertas, pero faltan tests de propiedades y casos limite

**Evidencia.** Hay tests para normalizacion de cuaterniones (`tests/test_attitude.py:9-17`), signo de empuje (`tests/test_attitude.py:29-42`), hover ideal (`tests/test_dynamics.py:26-46`), drag disipativo (`tests/test_perturbations.py:4-22`), saturacion de actuadores (`tests/test_actuators.py:75-92`) y mezclador con saturacion (`tests/test_mixer.py:49-72`).

**Riesgo.** Estos tests son buenos como "smoke tests fisicos", pero no exploran:

- orientaciones no triviales para drag y empuje;
- matrices de inercia no diagonales;
- conservacion de norma tras simulaciones largas;
- energia o monotonia en drag lineal;
- limites invalidos en parametros fisicos;
- comandos negativos o extremos en mezclador;
- retardo no entero respecto a `dt`;
- no finitos en comandos, rotor commands o metricas.

**Recomendacion.** Ampliar pruebas con parametrizacion pytest y casos de propiedad simples: drag siempre disipativo respecto a velocidad relativa, `||q||` permanece cerca de 1 tras N pasos, fuerzas de hover compensan gravedad en actitud nivelada, saturacion nunca supera `omega_max`, y no finitos detienen episodio con causa clara.

### P2 - La validacion de multi-rate y ZOH existe, pero no comprueba dinamica aplicada entre ciclos

**Evidencia.** `test_runner_multi_rate` comprueba numero de llamadas de control y muestras de telemetria (`tests/test_runner.py:47-79`). En el runner el comando se actualiza solo cada `control_dt_s` y se reutiliza entre pasos de fisica (`src/simulador_quad/runner.py:151-176`).

**Riesgo.** El test confirma conteo temporal, pero no prueba que el comando retenido por ZOH sea exactamente el aplicado durante los subpasos, ni que actuadores y telemetria queden alineados temporalmente. Un desfase en retardo/lag podria pasar desapercibido.

**Recomendacion.** Anadir un test con controlador que cambia escalonadamente el comando y verificar en telemetria y estado aplicado que:

- el comando se mantiene constante entre actualizaciones;
- el actuador evoluciona en cada `physics_dt_s`;
- el retardo puro corresponde al numero de pasos esperado;
- la muestra de telemetria documenta si el estado es antes o despues del paso fisico.

### P3 - Las pruebas de exportacion y visualizacion validan existencia, no contenido cientifico

**Evidencia.** `test_exports` comprueba que se crean ficheros (`tests/test_metrics.py:51-60`). `test_visualization.py` valida generacion de figuras/HTML y contenido basico, no exactitud visual ni coherencia de ejes. La exportacion incluye campos necesarios (`src/simulador_quad/telemetry/export.py:19-53`).

**Riesgo.** Las figuras pueden existir pero representar mal ejes, unidades, leyendas o datos. Para memoria, los graficos deben ser auditables.

**Recomendacion.** Anadir checks ligeros de contenido:

- `telemetry.json` con esquema minimo y arrays de longitud 3/4;
- `metrics.json` con campos obligatorios y tipos numericos finitos;
- figuras generadas desde telemetria conocida con nombres y series esperadas;
- convencion ENU visible en documentacion de graficos.

## Cobertura conceptual frente a requisitos normativos

| Area | Estado actual | Evidencia | Brecha principal |
| --- | --- | --- | --- |
| Cuaterniones | Parcialmente cubierto | `tests/test_attitude.py:9-17`, `tests/test_dynamics.py:48-66` | Falta simulacion larga y orientaciones variadas. |
| Signo ENU/FRD | Cubierto a nivel basico | `tests/test_attitude.py:29-42`, `tests/test_actuators.py:67-73` | Falta empuje con actitud no nivelada. |
| RK4 | Parcialmente cubierto | `tests/test_dynamics.py:4-90` | Falta regresion contra soluciones analiticas adicionales y tolerancias por dt. |
| Actuadores | Parcialmente cubierto | `tests/test_actuators.py:5-92` | Falta retardo no entero, lag+saturacion combinados y margenes por rotor. |
| Mezclador | Parcialmente cubierto | `tests/test_mixer.py:21-72` | Falta verificar recuperacion de momentos reales tras saturacion. |
| Perturbaciones | Parcialmente cubierto | `tests/test_perturbations.py:4-38` | Falta viento/drag con actitud no identidad y estadistica de ruido. |
| Multi-rate/ZOH | Parcialmente cubierto | `tests/test_runner.py:47-79` | Falta comprobar comando aplicado en subpasos. |
| Terminacion | Parcialmente cubierta | `tests/test_runner.py:81-138` | Falta actitud, posicion/velocidad, comandos no finitos y estado final en metricas. |
| YAML | Parcialmente cubierto | `scenarios/*.yaml`, `docs/simulador/escenarios_yaml.md` | Falta validacion automatica de schema y criterios esperados. |
| Metricas | Parcialmente cubierto | `src/simulador_quad/metrics/report.py:43-59`, `tests/test_metrics.py:33-49` | Falta desagregacion fisica y criterios de aceptacion. |
| `results/` | Parcialmente cubierto | `results/*/metrics.json`, `docs/simulador/guia_uso.md:30-35` | Falta manifiesto de reproducibilidad y vinculo a commit. |
| Control neuronal | No cubierto | `docs/simulador/README.md:23-26`, `src/simulador_quad/scenarios/loader.py:81-90` | Bloquea comparacion central del TFG. |

## Observaciones sobre resultados existentes

Se inspeccionaron los `metrics.json` presentes sin regenerar resultados. Resumen conceptual:

- Escenarios principales como `hover_clean`, `circle_drag`, `circle_noisy_wind`, `lissajous_clean` y `waypoint_clean` terminan por `Time limit reached`.
- `circle_noisy_wind` registra degradacion colectiva aproximada del 1.98 %, aunque saturacion 0 %. Esto conviene explicarlo en memoria como degradacion de mezclador, no como saturacion de rotor.
- `test_line` termina por `Attitude angle exceeded limit`, con degradacion alta. Si se usa como evidencia, debe clasificarse como fallo esperado o excluirse de comparaciones nominales.
- Existen resultados de estres sin escenario YAML versionado visible. No deberian usarse como evidencia academica final salvo que se anada el escenario reproducible o se documente el YAML en `metadata.config` con manifiesto.

## Recomendaciones concretas por fase

### Fase inmediata: documentacion de validacion

1. Crear matriz de trazabilidad requisito-test-escenario-metrica.
2. Clasificar escenarios existentes como nominal, robustez, estres o fallo esperado.
3. Definir tolerancias numericas iniciales para resultados ya existentes.
4. Declarar que las metricas actuales son indicadores de simulacion clasica, no comparacion final clasico-neuronal.

### Fase de pruebas

1. Anadir tests de regresion de escenarios completos en directorios temporales.
2. Parametrizar invariantes fisicas: norma de cuaternion, drag disipativo, saturacion, empuje ENU/FRD.
3. Verificar schema minimo de YAML y JSON exportados.
4. Cubrir terminacion por actitud, posicion/velocidad, no finitos en comandos y saturacion persistente con estado final.

### Fase experimental para memoria

1. Generar una tabla oficial de escenarios y criterios de aceptacion.
2. Ejecutar todos los escenarios oficiales con manifiesto de reproducibilidad.
3. Separar resultados por controlador.
4. Exportar una tabla comparativa final con metricas comunes y condiciones experimentales.
5. Conservar figuras y telemetria como evidencia secundaria, no como unica fuente de conclusiones.

## Evidencias minimas recomendadas para la memoria academica

- Tabla de requisitos de validacion con referencia a test, escenario y metrica.
- Tabla de escenarios: tipo, perturbaciones, duracion, semilla, controlador, objetivo experimental.
- Tabla de metricas por escenario y controlador.
- Graficas de seguimiento por escenario representativo: posicion vs referencia, error temporal, velocidades de rotor y esfuerzo.
- Discusion de fallos: terminaciones anticipadas, saturacion, degradacion colectiva y limites de validez.
- Manifesto reproducible por lote de resultados: commit, comando, entorno, fecha, YAML y artefactos generados.

## Conclusion

El repositorio esta en buen punto para validar componentes del simulador clasico, pero todavia no tiene una estructura de validacion suficiente para cerrar el TFG. El siguiente salto de calidad debe ser convertir pruebas y resultados en evidencia trazable: criterios de aceptacion, regresiones de escenarios, manifiestos reproducibles y comparacion cerrada entre controlador clasico y neuronal. Sin esa capa, las metricas actuales son utiles para desarrollo, pero insuficientes como base completa de conclusiones academicas.
