# Auditoria de fisica y modelado 6DOF del simulador

Fecha: 2026-05-04

Alcance: auditoria del repositorio desde la perspectiva de fisica, modelado 6DOF y validez para un TFG de simulador de cuadricoptero. Se han leido `AGENTS.md`, `docs/01_principios_tfg.md`, `docs/02_requisitos_ingenieria_simulador.md` y `docs/03_criterios_ingenieria_software.md`. No se ha modificado codigo fuente ni tests.

## Verificacion ejecutada

```powershell
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml
uv run simulador-quad run scenarios\circle_drag.yaml
uv run simulador-quad run scenarios\circle_noisy_wind.yaml
```

Resultado observado:

- `uv run pytest`: 29 tests pasan.
- `hover_clean`: termina por `Time limit reached`, RMSE posicion aproximado `0.3120 m`.
- `circle_drag`: termina por `Time limit reached`, RMSE posicion aproximado `0.3232 m`.
- `circle_noisy_wind`: termina por `Time limit reached`, RMSE posicion aproximado `0.4141 m`.

La suite esta verde y los escenarios principales ejecutan hasta limite temporal, pero esto no cierra por si solo la validez fisica: hay puntos de trazabilidad, documentacion y validacion fisica que deben corregirse antes de usar los resultados como base fuerte de memoria.

## Resumen tecnico

La implementacion actual contiene una base fisica razonable para la primera version del TFG:

- Estado 6DOF con posicion y velocidad en mundo, cuaternion `q_WB` y velocidad angular en cuerpo (`src/simulador_quad/core/contracts.py:5-11`).
- Convencion ENU/FRD documentada en el codigo de actitud nivelada (`src/simulador_quad/core/frames.py:3-19`).
- Empuje de rotores aplicado como fuerza `[0, 0, -T_i]` en cuerpo FRD (`src/simulador_quad/dynamics/actuators.py:74-80`).
- Dinamica translacional con gravedad `[0, 0, -mg]` y drag lineal relativo al viento (`src/simulador_quad/dynamics/rigid_body.py:31-38`).
- Dinamica rotacional de Newton-Euler con termino giroscopico `omega x I omega` (`src/simulador_quad/dynamics/rigid_body.py:44-48`).
- Integrador RK4 con normalizacion final del cuaternion (`src/simulador_quad/dynamics/rigid_body.py:69-108`).
- Actuadores con retardo puro discretizado, lag de primer orden sobre `omega`, saturacion y ley cuadratica `T_i = k_f omega_i^2` (`src/simulador_quad/dynamics/actuators.py:5-27`, `src/simulador_quad/dynamics/actuators.py:58-87`).
- Orquestacion multi-rate con control por `control_dt_s`, fisica por `physics_dt_s` y telemetria por `telemetry_dt_s` (`src/simulador_quad/runner.py:151-209`).

El mayor riesgo no es que el simulador este "mal" en bloque, sino que algunas partes importantes no estan suficientemente blindadas contra errores de convencion y que parte de la documentacion preliminar describe modelos distintos a los realmente implementados.

## Hallazgos priorizados

### P1 - La documentacion preliminar contradice el alcance fisico real y puede invalidar la trazabilidad de la memoria

Referencias:

- `docs/preliminar/fisica_y_matematicas.md:17` menciona perdida inducida.
- `docs/preliminar/fisica_y_matematicas.md:58-69` documenta viento Ornstein-Uhlenbeck, drag cuadratico e induced hover loss.
- `docs/preliminar/fisica_y_matematicas.md:45-50` documenta una matriz de mezclador con signos `[1, y_i, -x_i, ...]` y minimos cuadrados.
- `docs/preliminar/informe_fisica_simulador.tex:48` afirma perturbaciones con viento Ornstein-Uhlenbeck e inducido.
- `docs/preliminar/informe_fisica_simulador.tex:181-203` vuelve a describir drag parabolico, perdida inducida y viento OU.
- El codigo actual implementa viento constante (`src/simulador_quad/dynamics/perturbations.py:23-29`), drag lineal (`src/simulador_quad/dynamics/rigid_body.py:31-34`) y mezclador 4x4 por inversa con signos `tau_x=-yT`, `tau_y=xT` (`src/simulador_quad/dynamics/mixer.py:16-35`).

Riesgo para el TFG:

La memoria podria defender ecuaciones que no corresponden al software usado para generar resultados. Esto rompe la cadena exigida por los documentos normativos: requisito -> modelo matematico -> implementacion -> escenario -> metrica.

Recomendacion:

Antes de congelar resultados, unificar la documentacion tecnica con la implementacion real de v1:

- Declarar explicitamente que el modelo de v1 usa drag lineal en cuerpo respecto a velocidad relativa al viento, no drag cuadratico.
- Sustituir las secciones de viento OU e induced hover loss por "fuera de alcance / trabajo futuro", salvo que se implementen despues con pruebas y escenarios.
- Documentar la matriz real del mezclador con la misma convencion del codigo: `sum(T_i)`, `tau_x=sum(-y_i T_i)`, `tau_y=sum(x_i T_i)`, `tau_z=sum(s_i k_m/k_f T_i)`.

### P1 - Las pruebas de dinamica validan casos con cuaternion identidad que no representan la actitud nivelada ENU/FRD del simulador

Referencias:

- `tests/test_dynamics.py:12-18` usa `q0=[1,0,0,0]` y pasa una fuerza llamada `force_W`.
- `tests/test_dynamics.py:34-41` verifica hover con `q0=[1,0,0,0]` y `force_W=[0,0,mg]`.
- La funcion auditada recibe `force_B_N`, no fuerza mundo (`src/simulador_quad/dynamics/rigid_body.py:13`, `src/simulador_quad/dynamics/rigid_body.py:61`), y la rota con `body_to_world` (`src/simulador_quad/dynamics/rigid_body.py:25-27`).
- La actitud nivelada ENU/FRD real se obtiene con `get_level_quaternion`, donde `Z_B` apunta a `-Z_W` (`src/simulador_quad/core/frames.py:16-29`).
- Existe una prueba especifica del signo del empuje ENU/FRD (`tests/test_attitude.py:29-42`), pero no se replica en `rk4_step`.

Riesgo para el TFG:

El integrador puede pasar tests aunque alguien introduzca una regresion en la convencion cuerpo-mundo de la fuerza, porque parte de los tests ejercitan una orientacion cuerpo=mundo no fisica para el cuadricoptero ENU/FRD. Esto es especialmente peligroso en un TFG donde el signo del empuje y los marcos de referencia son criterios centrales.

Recomendacion:

Sin cambiar ahora tests por restriccion de esta auditoria, dejar como accion correctiva:

- Cambiar o ampliar `test_ideal_hover` para usar `q_level=get_level_quaternion(0)` y `force_B_N=[0,0,-mg]`.
- Renombrar variables de tests de `force_W` a `force_B` cuando llamen a `rk4_step`.
- Añadir un caso inclinado conocido: fuerza `[0,0,-T]` en cuerpo, `q_WB` no trivial, y verificacion de la componente mundo esperada.

### P1 - Falta validacion fisica de parametros criticos de escenario

Referencias:

- Las dataclasses aceptan arrays y escalares sin `__post_init__` ni validaciones (`src/simulador_quad/core/contracts.py:5-66`).
- El loader convierte directamente masa, inercia, drag y rotores desde YAML (`src/simulador_quad/scenarios/loader.py:21-40`).
- Si `orientation_WB` viene del YAML, se usa sin normalizar ni verificar norma (`src/simulador_quad/scenarios/loader.py:47-57`).
- El esquema de escenario es declarativo, pero no valida dimensiones, positividad, simetria de inercia ni semidefinicion positiva (`src/simulador_quad/scenarios/schema.py:6-17`).

Riesgo para el TFG:

Un escenario con masa negativa, matriz de inercia singular/no simetrica, drag negativo, `k_f<=0`, `omega_max<=0`, `turning_direction` distinto de +/-1 o cuaternion no unitario puede producir resultados numericos sin que el simulador avise. Esto compromete reproducibilidad y puede contaminar comparaciones entre control clasico y neuronal.

Recomendacion:

Definir una validacion minima de escenario antes de ejecutar:

- `mass_kg > 0`, `gravity_m_s2 > 0`.
- `inertia_B_kg_m2` 3x3, simetrica y definida positiva.
- `linear_drag_coefficient >= 0` y dimension 3 o escalar documentado.
- `k_f > 0`, `k_m >= 0`, `omega_max_rad_s > 0`, `time_constant_s >= 0`, `delay_s >= 0`.
- `turning_direction in {-1, 1}`.
- `orientation_WB` finito y normalizado, o normalizar registrando la accion.
- `physics_dt_s`, `control_dt_s`, `telemetry_dt_s > 0` y relaciones multi-rate documentadas.

### P2 - Hay dos implementaciones del drag lineal con riesgo de divergencia

Referencias:

- `compute_linear_drag` implementa el drag en `src/simulador_quad/dynamics/perturbations.py:5-21`.
- `compute_state_derivative` reimplementa el mismo calculo dentro de la dinamica (`src/simulador_quad/dynamics/rigid_body.py:29-34`).
- `runner.py` importa `compute_linear_drag`, pero no lo usa (`src/simulador_quad/runner.py:8`).

Riesgo para el TFG:

La ecuacion auditada y la ecuacion usada por el integrador pueden separarse con el tiempo. En un modelo fisico, esa duplicacion es un riesgo de trazabilidad: una prueba podria validar `compute_linear_drag` mientras la simulacion usa otra formula.

Recomendacion:

Hacer que el integrador use una unica funcion de drag o eliminar la funcion no usada. Si se mantiene el drag dentro de `rigid_body.py` por dependencia de RK4, la funcion documentada y testeada debe ser esa misma ruta.

### P2 - La estrategia de saturacion del mezclador es prometedora, pero requiere documentacion matematica y casos limite mas claros

Referencias:

- La matriz se construye explicitamente en `src/simulador_quad/dynamics/mixer.py:16-35`.
- La estrategia intenta priorizar momentos frente a empuje desplazando el colectivo (`src/simulador_quad/dynamics/mixer.py:48-72`).
- Los tests cubren hover, pitch y saturacion (`tests/test_mixer.py:21-72`).

Riesgo para el TFG:

La idea coincide con el requisito normativo, pero la formulacion de `delta_min/delta_max` y el caso no factible (`T_target_thrust=(T_min+T_max)/2`) no estan justificados en documento fisico. Para una memoria, no basta con que el algoritmo pase tests: debe poder explicarse por que conserva autoridad de actitud y que se sacrifica cuando no hay solucion factible.

Recomendacion:

Documentar la asignacion como problema de factibilidad:

```text
T_req = T_collective_part + T_moment_part + delta * 1
T_min <= T_req <= T_max
```

Explicar el papel de `delta`, cuando se marca `degraded_collective_thrust`, y anadir escenarios de prueba con roll, pitch, yaw combinados, empuje bajo, empuje maximo y demanda de yaw no factible.

### P2 - Los limites de actitud de algunos escenarios son demasiado permisivos para funcionar como criterio fisico de aceptacion

Referencias:

- `circle_drag.yaml` fija `max_attitude_angle_rad: 3.14` (`scenarios/circle_drag.yaml:40-44`).
- `circle_noisy_wind.yaml` fija `max_attitude_angle_rad: 3.14` (`scenarios/circle_noisy_wind.yaml:42-46`).
- El runner evalua la inclinacion comparando `Z_B` con la vertical hacia abajo en ENU (`src/simulador_quad/runner.py:75-90`).

Riesgo para el TFG:

Un limite de 3.14 rad equivale practicamente a permitir inversion completa antes de terminar por actitud. Esto puede ser util para depuracion, pero es debil como criterio de seguridad o validez fisica. Si un controlador neuronal se evalua con ese limite, podria sobrevivir episodios con actitudes no aceptables para un cuadricoptero realista de seguimiento.

Recomendacion:

Separar dos tipos de escenarios:

- Escenarios de depuracion con limites amplios, etiquetados como tales.
- Escenarios de evaluacion TFG con limites fisicamente defendibles, por ejemplo roll/pitch maximo entre 45 y 75 grados segun el objetivo de maniobra, y ese valor documentado en el escenario.

### P2 - La telemetria es adecuada, pero faltan algunas magnitudes fisicas utiles para auditar energia, fuerzas y perturbaciones

Referencias:

- La telemetria registra estado, observacion, referencia, comando, rotor objetivo y rotor aplicado (`src/simulador_quad/core/contracts.py:57-66`).
- La exportacion incluye comandos y estados de rotores (`src/simulador_quad/telemetry/export.py`, revisado indirectamente por la salida de metricas).
- `runner.py` calcula viento y fuerzas aplicadas, pero no registra fuerza total en mundo, fuerza de drag ni viento usado en cada muestra (`src/simulador_quad/runner.py:202-209`).

Riesgo para el TFG:

Cuando haya un error de seguimiento o una diferencia entre control clasico y neuronal, sera dificil separar si procede de saturacion, drag, viento, falta de empuje vertical, error de actitud o numerica. Para un TFG, la trazabilidad experimental mejora mucho si las fuerzas y perturbaciones aplicadas pueden inspeccionarse directamente.

Recomendacion:

Anadir en una fase posterior campos opcionales de telemetria fisica:

- `wind_W_m_s`.
- `force_thrust_B_N` y/o `force_thrust_W_N`.
- `force_drag_W_N`.
- `gravity_force_W_N` o al menos `acceleration_W_m_s2` resultante.
- `total_torque_B_Nm`.

### P3 - La dinamica rotacional acepta inercia completa, pero la documentacion y escenarios comunican principalmente inercia diagonal

Referencias:

- El codigo usa `np.linalg.inv(inertia_B_kg_m2)` y admite matriz completa (`src/simulador_quad/dynamics/rigid_body.py:45-48`).
- Los escenarios usan matrices diagonales (`scenarios/hover_clean.yaml:6`, `scenarios/circle_drag.yaml:6`, `scenarios/circle_noisy_wind.yaml:6`).
- Parte de la documentacion preliminar afirma inercia diagonal como si fuese la hipotesis general (`docs/preliminar/fisica_y_matematicas.md:19-24`, `docs/preliminar/informe_fisica_simulador.tex:118-123`).

Riesgo para el TFG:

No es un fallo de implementacion, pero debe quedar claro si v1 asume tensor diagonal o si admite tensor completo. Si se presenta como diagonal, los escenarios y ecuaciones deben declararlo. Si se presenta como tensor general, deben existir validaciones y al menos una prueba con terminos fuera de diagonal.

Recomendacion:

Para v1, declarar "tensor diagonal por escenario base; el codigo permite matriz 3x3, pero la validez se limita a matrices simetricas definidas positivas". Esto evita prometer una generalidad que no se ha validado experimentalmente.

### P3 - El controlador clasico es fisicamente interpretable, pero sus ganancias y supuestos necesitan trazabilidad experimental mas explicita

Referencias:

- Ganancias de posicion y actitud fijadas en codigo (`src/simulador_quad/control/classic.py:12-25`).
- Saturacion de empuje y momentos en codigo (`src/simulador_quad/control/classic.py:20-25`, `src/simulador_quad/control/classic.py:102-105`).
- El loader permite `max_body_moments_Nm` desde YAML (`src/simulador_quad/scenarios/loader.py:81-88`), pero las ganancias principales no estan parametrizadas por escenario.

Riesgo para el TFG:

El controlador clasico sera baseline y generador de datos de imitacion. Si sus ganancias no estan trazadas como parte del escenario o de la configuracion experimental, es mas dificil reproducir exactamente el conjunto de datos y justificar comparaciones.

Recomendacion:

Registrar en metricas o metadata todas las ganancias efectivas (`Kp_pos`, `Kd_pos`, `Kp_att`, `Kd_att`), limites de empuje/momento y version del controlador. No es imprescindible mover todas las ganancias a YAML inmediatamente, pero si deben quedar exportadas.

## Riesgos principales para el TFG

1. Riesgo de trazabilidad: documentos preliminares describen modelos fuera de alcance o no implementados.
2. Riesgo de convencion: algunos tests de dinamica no ejercitan ENU/FRD real, aunque la implementacion principal parece respetar la convencion de empuje.
3. Riesgo de escenarios invalidos: falta validacion fisica de parametros antes de simular.
4. Riesgo de interpretacion experimental: limites de actitud demasiado permisivos y telemetria de fuerzas incompleta pueden ocultar comportamientos fisicamente no aceptables.
5. Riesgo de comparacion neuronal: si el baseline clasico y sus parametros no quedan exportados, los datos de imitacion pierden reproducibilidad.

## Recomendaciones de cierre antes de usar resultados en la memoria

Prioridad alta:

1. Corregir documentacion preliminar para que coincida con el modelo real v1: ENU/FRD, empuje `-Z_B`, RK4, drag lineal, viento constante/simple, sin induced loss ni OU salvo trabajo futuro.
2. Anadir validacion fisica de escenarios y parametros.
3. Reforzar pruebas de dinamica con `get_level_quaternion` y fuerza de empuje en cuerpo `[0,0,-T]`.

Prioridad media:

4. Eliminar la duplicacion del drag o asegurar que la funcion testeada es la usada por RK4.
5. Documentar formalmente la estrategia de saturacion del mezclador y sus casos no factibles.
6. Definir limites de actitud fisicamente defendibles para escenarios de evaluacion, separandolos de escenarios de depuracion.

Prioridad baja:

7. Exportar fuerzas, viento y torque total en telemetria para mejorar diagnosis fisica.
8. Exportar ganancias efectivas del controlador clasico en metricas/metadata.
9. Aclarar si la inercia de v1 es diagonal por hipotesis o tensor 3x3 general validado.

## Conclusion tecnica

El simulador tiene una base 6DOF defendible para un TFG de alcance limitado: usa cuaterniones, ENU/FRD, Newton-Euler, actuadores con omega y RK4 multi-rate. La implementacion principal parece alineada con los requisitos fisicos centrales, y los escenarios principales actualmente ejecutan hasta el limite temporal.

La principal deuda para convertirlo en material academico solido no es aumentar fidelidad aerodinamica, sino cerrar trazabilidad y validacion: que la documentacion no prometa modelos no usados, que los tests ataquen explicitamente las convenciones ENU/FRD, que los escenarios invalidos sean rechazados y que los resultados exporten suficiente contexto fisico para defender la comparacion entre control clasico y control neuronal.
