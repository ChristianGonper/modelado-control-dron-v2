# Spec: Subsanacion de Findings del Simulador

## Supuestos

1. Esta especificacion cubre solo los seis findings detectados en la review de implementacion del simulador.
2. No se amplia el alcance hacia control neuronal, entrenamiento, sensores realistas ni aerodinamica adicional.
3. La fuente normativa sigue siendo:
   - `docs/01_principios_tfg.md`
   - `docs/02_requisitos_ingenieria_simulador.md`
   - `docs/03_criterios_ingenieria_software.md`
   - `docs/plans/plan_implementacion_simulador.md`
4. La convencion fisica que debe prevalecer es mundo ENU, cuerpo FRD, `F_thrust_B = [0, 0, -T]` y `Q_i = s_i k_m omega_i^2`.
5. Los cambios deben mantener el enfoque de codigo cientifico simple, con contratos explicitos y pruebas trazables.

## Objetivo

Subsanar los errores y carencias que impiden considerar lista la primera version del simulador 6DOF de cuadricoptero.

El resultado esperado es una implementacion coherente con ENU/FRD, con telemetria suficiente para trazabilidad experimental, condiciones de fin completas, actuadores discretizados segun los requisitos, controlador clasico con saturaciones documentadas y todas las trayectorias v1 previstas.

## Tech Stack

- Python `>=3.13`.
- NumPy para calculo vectorial.
- SciPy ya existente para conversiones de actitud auxiliares.
- PyYAML para escenarios declarativos.
- pytest para pruebas.
- `uv` como gestor obligatorio de dependencias y ejecucion.

No se deben introducir dependencias nuevas para esta subsanacion salvo aprobacion explicita.

## Commands

Comandos obligatorios de verificacion:

```powershell
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml
uv run simulador-quad run scenarios\circle_drag.yaml
uv run simulador-quad run scenarios\circle_noisy_wind.yaml
```

Comandos auxiliares aceptados:

```powershell
uv run python -m pytest tests\test_mixer.py tests\test_actuators.py
uv run python -m pytest tests\test_runner.py tests\test_metrics.py
```

## Project Structure

Archivos previstos para modificar:

```text
src/simulador_quad/core/contracts.py
  Contratos de telemetria, comandos de rotor, estado aplicado y flags.

src/simulador_quad/dynamics/mixer.py
  Matriz de asignacion, signos ENU/FRD, saturacion y degradacion.

src/simulador_quad/dynamics/actuators.py
  Lag de primer orden, retardo, saturacion, empuje/par aplicado y RPM.

src/simulador_quad/control/classic.py
  Saturacion documentada de momentos.

src/simulador_quad/runner.py
  Observacion registrada, flags de saturacion, terminacion persistente y causa trazable.

src/simulador_quad/telemetry/export.py
  Exportacion JSON completa de telemetria requerida.

src/simulador_quad/metrics/report.py
  Metricas de saturacion, esfuerzo y trazabilidad.

src/simulador_quad/trajectories/analytic.py
src/simulador_quad/scenarios/loader.py
  Trayectoria Line y carga desde YAML.

tests/
  Pruebas unitarias e integracion ajustadas a la convencion final.

scenarios/
  Ajustes de escenarios solo si son necesarios para que sean reproducibles y utiles.
```

## Code Style

Usar nombres fisicos con unidades y marco de referencia cuando aplique. Las funciones importantes deben expresar en docstring las unidades, signos y supuestos.

Ejemplo de estilo esperado:

```python
@dataclass
class RotorTelemetry:
    target_thrust_N: np.ndarray
    omega_cmd_rad_s: np.ndarray
    omega_applied_rad_s: np.ndarray
    rotor_speed_rpm: np.ndarray
    applied_thrust_N: np.ndarray
    applied_reaction_torque_Nm: np.ndarray
    saturation_flags: np.ndarray
    degraded_collective_thrust: bool
```

Reglas concretas:

- Mantener dataclasses como contratos pasivos.
- Evitar abstracciones nuevas si una funcion explicita basta.
- No ocultar signos fisicos en nombres ambiguos.
- No usar constantes globales implicitas para limites de saturacion o terminacion.
- Documentar cualquier simplificacion fisica con comentario o docstring breve.

## Testing Strategy

Las pruebas deben cubrir, como minimo:

- `uv run pytest` debe pasar completo.
- Signos del mixer coherentes con `r x F` y `F_B=[0,0,-T]`.
- Signo de yaw coherente entre mixer y actuadores para `Q_i=s_i k_m omega_i^2`.
- Saturacion del mixer con prioridad de actitud frente a empuje colectivo, incluyendo flags de degradacion.
- Conversiones `omega = sqrt(T/k_f)`, `T=k_f omega^2`, `Q=s k_m omega^2` y RPM.
- Lag con `alpha = 1 - exp(-dt/tau)`.
- Retardo puro de `N` pasos.
- Telemetria que incluya estado verdadero, observacion, referencia, comando solicitado, comando aplicado, empujes, velocidades de rotor en rad/s y RPM, saturacion y causa de terminacion.
- Terminacion por saturacion persistente con causa explicita.
- Control clasico con momentos saturados dentro de limites.
- Trayectoria `Line` con posicion, velocidad y aceleracion finitas y continuidad de posicion/velocidad.
- Ejecucion minima de los tres escenarios YAML.

## Boundaries

Always:

- Usar `uv` para ejecutar pruebas y escenarios.
- Mantener ENU/FRD como convencion unica.
- Actualizar tests cuando se corrija una convencion erronea.
- Registrar en telemetria lo necesario para reproducir y auditar resultados.
- Mantener los cambios acotados a los findings.

Ask first:

- Introducir dependencias nuevas.
- Cambiar el formato general de escenarios YAML.
- Cambiar de forma sustancial las ganancias por defecto del controlador clasico.
- Relajar criterios de terminacion para ocultar inestabilidades.
- Cambiar los documentos normativos principales.

Never:

- Eliminar pruebas fallidas sin sustituirlas por pruebas equivalentes correctas.
- Mezclar entrenamiento neuronal en esta subsanacion.
- Presentar un escenario fallido como valido para comparacion si termina prematuramente por fallo fisico.
- Usar `pip` para gestion de dependencias.
- Corregir signos solo en tests dejando incoherencia fisica en la implementacion.

## Success Criteria

La subsanacion se considera completa cuando se cumplan todos estos criterios:

1. `uv run pytest` pasa sin fallos.
2. Los tests de mixer y actuadores verifican una unica convencion ENU/FRD coherente con los requisitos.
3. El runner registra observacion y telemetria completa en cada muestra exportada.
4. La telemetria JSON incluye, como minimo:
   - tiempo;
   - estado verdadero;
   - observacion usada por el controlador;
   - referencia;
   - comando de control solicitado;
   - empuje objetivo por rotor;
   - `omega_cmd_rad_s`;
   - `omega_applied_rad_s`;
   - `rotor_speed_rpm`;
   - empuje y par aplicado por rotor;
   - flags de saturacion/degradacion;
   - causa de terminacion si aplica.
5. Las metricas incluyen RMSE, MAE, error maximo, esfuerzo de control, velocidad maxima de rotor, porcentaje de tiempo en saturacion, causa y tiempo de terminacion, escenario, controlador, parametros relevantes y semilla.
6. Existe deteccion de saturacion persistente parametrizable desde escenario o configuracion del runner.
7. El lag de actuador usa `alpha = 1 - exp(-dt/tau)`.
8. El controlador clasico limita momentos con saturaciones documentadas y verificadas por tests.
9. La trayectoria `Line` existe, se puede declarar en YAML y devuelve posicion, velocidad, aceleracion y yaw finitos.
10. Los escenarios `hover_clean`, `circle_drag` y `circle_noisy_wind` ejecutan con CLI y generan telemetria/metrica reproducibles. Si `circle_noisy_wind` se mantiene como escenario de fallo, debe declararse como tal; si se pretende escenario de seguimiento, no debe terminar prematuramente.

## Findings Cubiertos

### Finding 1: Convencion de signos inconsistente

Se debe fijar la matriz de asignacion del mixer desde la fisica:

```text
F_i_B = [0, 0, -T_i]
tau_i,B = r_i,B x F_i,B + [0, 0, s_i k_m omega_i^2]
```

Por tanto, para `r_i = [x_i, y_i, 0]`:

```text
tau_x = -y_i T_i
tau_y =  x_i T_i
tau_z =  s_i (k_m / k_f) T_i
```

La implementacion, comentarios y tests deben reflejar esos signos o justificar explicitamente cualquier convencion alternativa aprobada.

### Finding 2: Telemetria insuficiente

Extender contratos y exportacion para registrar el flujo completo:

```text
estado verdadero -> observacion -> referencia -> comando solicitado
-> mixer -> comando objetivo por rotor -> actuadores -> comando aplicado
-> dinamica -> metricas
```

La observacion debe guardarse incluso cuando coincida con el estado verdadero, para mantener un esquema estable.

### Finding 3: Saturacion persistente

El mixer y/o actuadores deben producir flags de saturacion. El runner debe acumular duracion o numero de pasos consecutivos saturados y terminar el episodio con causa explicita cuando supere el umbral configurado.

Ejemplo de causa:

```text
Persistent actuator saturation
```

### Finding 4: Formula de lag

Sustituir la discretizacion actual por:

```text
alpha = 1 - exp(-dt_s / time_constant_s)
omega_applied[k+1] = omega_applied[k] + alpha * (omega_cmd_delayed[k] - omega_applied[k])
```

Si `time_constant_s <= 0`, el estado aplicado debe seguir directamente al comando retrasado.

### Finding 5: Saturacion de momentos del controlador

El controlador clasico debe limitar `body_moments_Nm` por eje. Los limites deben ser configurables o, como minimo, estar documentados como valores por defecto. La saturacion no debe ocultarse: debe poder analizarse en telemetria o metricas.

### Finding 6: Trayectoria Line

Implementar una trayectoria de linea recta suave por velocidad acotada. Debe evitar escalones de posicion como referencia principal.

Contrato minimo:

```text
start_W_m
end_W_m
speed_m_s o duration_s
yaw_rad
```

La posicion debe avanzar de forma continua desde inicio a fin. La velocidad debe ser finita y acotada. La aceleracion puede ser cero en el tramo constante si se documenta la discontinuidad en los extremos, o puede suavizarse si se elige un perfil simple.

## Decisiones Cerradas

1. `Line` usara un perfil smoothstep cubico para que posicion y velocidad sean continuas.
2. Los limites de momento del controlador se declararan en la seccion `controller` del YAML, con defaults conservadores si el escenario no los define.
3. El umbral de saturacion persistente se declarara en segundos en `termination` y se convertira internamente a duracion acumulada o pasos.
4. `circle_noisy_wind` se ajustara como escenario de seguimiento robusto; si se necesita validar fallo por terminacion, se creara otro escenario especifico.

## Open Questions

No quedan preguntas abiertas para pasar a la fase de planificacion.
