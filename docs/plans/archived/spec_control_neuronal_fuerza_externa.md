# Spec: Control neuronal de fuerza externa con lazo interno clasico

## Estado de la especificacion

Documento activo e implementado. Define el contrato del controlador
`neural` outer-force, su dataset experto y sus criterios de validacion. El
codigo y las pruebas automatizadas cubren el contrato funcional; los
resultados experimentales finales deben regenerarse antes de usarlos en la
memoria.

Decisiones confirmadas:

- Se conserva `controller.type: "neural_position"` como programador neuronal
  de multiplicadores de ganancias.
- Se elimina el significado vigente de `controller.type: "neural"` como red
  que predice empuje colectivo y momentos finales.
- `controller.type: "neural"` pasa a designar una red que predice la fuerza
  deseada del lazo externo en mundo ENU.
- El lazo interno de actitud continua siendo clasico.
- La primera comparacion incluira `MLP`, `GRU` y `LSTM`; `MLP` sera la
  arquitectura prioritaria para una futura linea LiteWing.
- El aprendizaje permanece dentro del alcance de imitacion supervisada:
  la red imita un oraculo de PIDs seleccionados, no optimiza directamente el
  error de trayectoria mediante entrenamiento en bucle cerrado.

## Objective

Implementar un controlador neuronal hibrido que sustituya solo el lazo
externo de posicion del controlador clasico:

```text
observacion + referencia
        |
        v
red neuronal -> desired_force_W_N[3]
        |
        v
conversion clasica fuerza-actitud + PID clasico de actitud
        |
        v
collective_thrust_N + body_moments_Nm[3]
        |
        v
mixer y actuadores existentes
```

La red debe aprender por imitacion las fuerzas externas solicitadas por
expertos PID seleccionados mediante un banco reproducible. Esta formulacion
mantiene una division defendible:

- el lazo neuronal decide la fuerza necesaria para seguir la trayectoria;
- el lazo interno clasico estabiliza la actitud requerida;
- el mixer y los actuadores conservan el contrato fisico vigente.

El objetivo experimental es comparar, en bucle cerrado, cuatro referencias:

1. PID clasico baseline congelado.
2. Oraculo PID seleccionado por escenario.
3. `neural_position` vigente, que predice multiplicadores.
4. Nuevo `neural`, que predice fuerza externa.

No se presupone que la red supere al baseline; esa conclusion solo sera valida
si se obtiene con metricas de ejecucion cerrada.

## Scope

### Included

- Nuevo contrato de salida neuronal `desired_force_W_N[3]` en ENU y N.
- Conservacion del PID interno clasico para actitud y momentos.
- Reutilizacion del nombre YAML `type: "neural"` para el nuevo contrato.
- Conservacion independiente de `type: "neural_position"`.
- Dataset nuevo generado desde un banco de PIDs de lazo externo.
- Seleccion de un experto PID seguro por escenario.
- Dos versiones de features para comparar entrada minima frente a entrada
  observable completa.
- Entrenamiento y evaluacion de `MLP`, `GRU` y `LSTM`.
- Clipping de fuerza por empuje maximo y angulo de inclinacion solicitado.
- Actualizacion de pruebas, scripts y documentacion viva cuando se implemente.

### Excluded

- Control neuronal directo de momentos finales o velocidades de rotor.
- Port a LiteWing, comunicacion offboard o sensorizacion real.
- Reinforcement learning, differentiable simulation u optimizacion directa
  de `position_rmse_m` durante entrenamiento.
- Alterar la dinamica, el mixer o los actuadores para mejorar artificialmente
  un controlador neuronal.
- Migrar checkpoints legacy del antiguo `type: "neural"`.

## Control Architecture

### Contrato clasico que se reutiliza

El controlador clasico vigente ya contiene la descomposicion adecuada:

```python
desired_force_W = controller.compute_desired_force_W(obs_state, reference)
thrust_N, q_des = controller.desired_force_to_attitude(
    desired_force_W, reference.yaw_rad
)
tau_B = controller.compute_attitude_moments(obs_state, q_des)
command = ControlCommand(thrust_N, tau_B)
```

La implementacion debera extraer o exponer una ruta reutilizable para ejecutar
solo las tres ultimas operaciones desde una fuerza externa recibida. No se
duplicaran las ecuaciones de conversion de actitud ni el PID interno en la
clase neuronal.

### Nuevo controlador `neural`

El controlador implementado mantiene el contrato existente:

```python
compute_control(
    time_s: float,
    obs_state: VehicleState,
    reference: TrajectoryReference,
) -> ControlCommand
```

En cada llamada:

1. Construye features usando `obs_state` y `reference`.
2. Normaliza la entrada con estadisticos del entrenamiento.
3. Evalua la arquitectura seleccionada.
4. Desnormaliza una salida de dimension `3`:
   `desired_force_W_N = [F_x, F_y, F_z]`.
5. Aplica limites de seguridad sobre la fuerza predicha.
6. Convierte la fuerza limitada en empuje colectivo y orientacion deseada
   usando el codigo clasico.
7. Calcula momentos con el PID interno clasico.
8. Devuelve el `ControlCommand` convencional al mixer.

### Controlador `neural_position` conservado

El modo actual se mantendra como alternativa experimental:

```text
red -> log multiplicadores de Kp_pos/Kd_pos
    -> compute_desired_force_W con ganancias programadas
    -> conversion clasica fuerza-actitud
    -> PID interno clasico
```

Sus checkpoints, normalizadores, scripts y metricas no son intercambiables con
los del nuevo controlador de fuerza.

### Limites de fuerza externa

El nuevo `neural` debe limitar su salida antes de calcular la actitud deseada:

- `max_thrust_N = mass_kg * gravity_m_s2 * 2.5`, salvo ampliacion futura
  explicitamente configurada y documentada.
- `max_desired_tilt_rad` obligatorio en el bloque YAML neuronal.
- Si la norma de fuerza supera `max_thrust_N`, se escala el vector manteniendo
  su direccion.
- Si la direccion de fuerza requiere una inclinacion superior a
  `max_desired_tilt_rad`, se limita su componente horizontal preservando una
  componente vertical fisicamente consistente.
- El PID interno mantiene `max_body_moments_Nm` como proteccion adicional.

Valor recomendado para comenzar validacion orientada a transferencia:

```yaml
max_desired_tilt_rad: 0.52  # 30 deg
```

El clipping se registra para distinguir control estable de control mantenido
por una limitacion activa frecuente.

## YAML Interface

### Nuevo `type: neural`

```yaml
controller:
  type: "neural"
  architecture: "mlp"
  checkpoint_path: "data/neural_control/outer_force_mlp_v1/checkpoints/mlp_best.pt"
  normalization_path: "data/neural_control/outer_force_mlp_v1/normalization.json"
  feature_version: "outer_force_min_v1"
  clip_to_classic_limits: true
  max_desired_tilt_rad: 0.52
  Kp_att: [4.0, 4.0, 1.0]
  Kd_att: [1.5, 1.5, 0.5]
  max_body_moments_Nm: [10.0, 10.0, 2.0]
```

Campos:

| Campo | Requisito |
| --- | --- |
| `architecture` | Uno de `mlp`, `gru`, `lstm`. |
| `checkpoint_path` | Checkpoint con `controller_mode: neural_outer_force`. |
| `normalization_path` | Estadisticos compatibles con target de fuerza. |
| `feature_version` | Uno de `outer_force_min_v1`, `outer_force_full_v1`. |
| `max_desired_tilt_rad` | Positivo y menor que `pi/2`; obligatorio. |
| `clip_to_classic_limits` | `true` por defecto; no desactivarlo en resultados principales. |
| `Kp_att`, `Kd_att` | PID interno, opcional si se aceptan defaults clasicos. |
| `max_body_moments_Nm` | Limites FRD del PID interno. |

### Compatibilidad y fallo temprano

- Un checkpoint legacy que produzca cuatro salidas
  `[thrust, moment_x, moment_y, moment_z]` debe rechazarse.
- Un checkpoint de `neural_position` con seis salidas debe rechazarse al
  cargarlo como `neural`.
- Un normalizador con nombres de targets o version incompatible debe
  rechazarse.
- Los resultados historicos y checkpoints existentes se conservan como
  artefactos de la fase anterior, sin migracion silenciosa.

## Dataset Specification

### Por que el dataset vigente no vale directamente

`data/position_gain_dataset/` fue disenado para que cada muestra tenga como
target seis multiplicadores constantes por episodio:

```text
log(Kp_pos / base_Kp_pos), log(Kd_pos / base_Kd_pos)
```

El nuevo controlador necesita un target distinto para cada instante:

```text
desired_force_W_N[3]
```

Ademas, el banco vigente genera variantes que cambian ganancias externas e
internas. En el nuevo experimento el PID interno debe permanecer fijo, ya que
tambien sera el lazo utilizado por la red. Por tanto:

- se puede reutilizar la idea, escenarios base y scoring del banco;
- no se reutilizan directamente sus etiquetas ni su conjunto de episodios
  como dataset final;
- se genera un dataset versionado nuevo de fuerza externa.

### Oraculo PID por escenario

El dataset de fuerza se genera a partir de demostraciones seleccionadas:

1. Partir de cada escenario y split del dataset clasico.
2. Construir variantes de PID modificando exclusivamente `Kp_pos` y
   `Kd_pos`.
3. Mantener `Kp_att`, `Kd_att` y limites internos fijados para la familia o
   escenario.
4. Ejecutar cada variante con las mismas condiciones iniciales, semilla,
   perturbaciones y trayectoria.
5. Excluir variantes que fallen filtros de seguridad.
6. Seleccionar un unico experto seguro por escenario.
7. Conservar telemetria, PID seleccionado, metricas de candidatos y criterio
   de seleccion.

Criterio de seleccion del experto:

1. Menor `position_rmse_m`.
2. Si varias variantes estan dentro del `5%` del mejor RMSE, menor esfuerzo
   de control entre ellas.
3. Si persiste empate, elegir la variante mas conservadora.

El oraculo no convierte el aprendizaje en optimizacion directa: el modelo
continua entrenandose mediante supervision sobre acciones de un experto.

### Splits y ausencia de leakage

- Los escenarios conservan el split asignado por el dataset fuente.
- `train`: ajuste de pesos y normalizacion.
- `val`: early stopping y seleccion de checkpoint.
- `test`: evaluacion in-distribution, no entrenamiento.
- OOD: dataset independiente de trayectorias o perturbaciones no usadas para
  ajuste.
- El oraculo puede calcularse en `test` y OOD para establecer referencia de
  comparacion, pero sus muestras no entran en entrenamiento ni normalizacion.

### Fuente de observacion

La nueva rama debe construir entradas y targets desde la observacion vista por
el experto, no desde el estado verdadero del simulador:

```python
observation = telemetry_entry["observation"]
reference = telemetry_entry["reference"]
```

Esto corrige una brecha vigente: el loader neuronal existente extrae features
de `state`, aunque el runner exporta tambien `observation`. Cuando hay ruido,
entrenar con `state` proporciona a la red informacion que no tendria durante
inferencia.

### Target de fuerza

Para cada muestra del experto seleccionado:

```python
pos_error_W_m = reference.position_W_m - observation.position_W_m
vel_error_W_m_s = reference.velocity_W_m_s - observation.velocity_W_m_s

desired_acceleration_W_m_s2 = (
    Kp_pos * pos_error_W_m
    + Kd_pos * vel_error_W_m_s
    + reference.acceleration_W_m_s2
)

desired_force_W_N = mass_kg * (
    desired_acceleration_W_m_s2
    - np.array([0.0, 0.0, -gravity_m_s2])
)
```

La implementacion debe verificar este target contra
`ClassicCascadeController.compute_desired_force_W(...)`, evitando mantener
dos definiciones independientes de la misma ecuacion.

## Feature Versions

Se implementaran dos versiones comparables de entrada. Ambas usan
`observation`, no `state`.

### `outer_force_min_v1`

Entrada minima asociada estrictamente al lazo externo PID:

| Feature | Dimension |
| --- | ---: |
| `error_pos_W_m` | 3 |
| `error_vel_W_m_s` | 3 |
| `reference.acceleration_W_m_s2` | 3 |
| Total | 9 |

Esta variante es la referencia conceptual principal: contiene las variables
necesarias para imitar la ley de fuerza externa del PID.

### `outer_force_full_v1`

Entrada completa observable equivalente al vector neuronal actual, pero
construida desde `observation`:

| Feature group | Dimension |
| --- | ---: |
| Posicion, velocidad, orientacion y velocidad angular observadas | 13 |
| Posicion, velocidad, aceleracion y yaw de referencia | 10 |
| Error de posicion y velocidad | 6 |
| `sin(yaw)`, `cos(yaw)` | 2 |
| Total | 31 |

Esta variante evaluara si la informacion de actitud/dinamica ayuda en
perturbaciones y transitorios, aun cuando el experto nominal dependa
principalmente del error traslacional.

### Target version

Ambas variantes utilizan:

```text
target_version: desired_force_W_v1
target_names: [force_x_W_N, force_y_W_N, force_z_W_N]
```

## Training Specification

### Arquitecturas

| Arquitectura | Entrada | Salida | Secuencia |
| --- | --- | --- | --- |
| `MLP` | muestra actual | `[batch, 3]` | No |
| `GRU` | ventana de muestras | `[batch, 3]` | `sequence_length=20` default |
| `LSTM` | ventana de muestras | `[batch, 3]` | `sequence_length=20` default |

La MLP sera el modelo recomendado para la futura linea real; GRU y LSTM se
mantienen para comparacion dentro del simulador.

### Normalizacion

- Ajustar estadisticos exclusivamente sobre muestras `train`.
- Guardar normalizacion de entradas y de fuerza objetivo.
- Mantener normalizadores distintos por `feature_version`.
- Aplicar el normalizador congelado a `val`, `test`, OOD e inferencia.
- Registrar nombres de features, targets y versiones en
  `normalization.json`.

### Artefactos

Cada entrenamiento debe escribir:

```text
data/neural_control/<run_id>/
  config.yaml
  normalization.json
  checkpoints/
    <architecture>_best.pt
  metrics/
    train_force_metrics.json
    val_force_metrics.json
    test_force_metrics.json
    ood_force_metrics.json       # solo cuando se proporcione OOD
```

Contenido minimo de `config.yaml`:

```yaml
controller_mode: "neural_outer_force"
architecture: "mlp"
input_dim: 9
output_dim: 3
feature_version: "outer_force_min_v1"
target_version: "desired_force_W_v1"
hidden_dim: 64
sequence_length: null
seed: 42
max_desired_tilt_rad: 0.52
clip_to_classic_limits: true
```

## Evaluation Specification

### Evaluacion supervisada

La evaluacion supervisada mide fidelidad de imitacion al oraculo:

- `mse_normalized`;
- `mae_force_W_N[3]`;
- `rmse_force_W_N[3]`;
- `mae_force_norm_N`;
- `rmse_force_norm_N`;
- porcentaje de muestras cuya prediccion excede `max_thrust_N` antes de
  clipping;
- porcentaje de muestras cuya prediccion excede
  `max_desired_tilt_rad` antes de clipping.

Estas metricas no bastan para afirmar calidad de control.

### Evaluacion en bucle cerrado

La comparacion principal se realizara ejecutando escenarios con:

| Controlador | Funcion |
| --- | --- |
| PID baseline | Referencia clasica congelada por familia. |
| PID oraculo | Mejor candidato seguro seleccionado por escenario. |
| `neural_position` | Red vigente de multiplicadores. |
| `neural` outer-force | Nueva red de fuerza con PID interno. |

Metricas:

- `position_rmse_m`, principal;
- `position_mae_m`;
- `position_max_err_m`;
- `termination_reason`;
- `saturation_percentage`;
- `degradation_percentage`;
- `force_norm_clip_percentage`;
- `force_tilt_clip_percentage`.

Se reportaran resultados por arquitectura y por `feature_version`. La
conclusion debera separar:

- fidelidad al oraculo;
- control in-distribution en bucle cerrado;
- control OOD en bucle cerrado;
- relevancia practica de la MLP para trabajo futuro LiteWing.

## Commands

Los nombres corresponden a la interfaz implementada:

```powershell
# Suite de regresion
uv run pytest

# Banco de PIDs exclusivamente externos
uv run python tools\generate_outer_force_pid_bank.py --dataset data\classic_dataset\v1 --out data\outer_force_pid_bank\v1

# Dataset con experto seleccionado y targets de fuerza
uv run python tools\generate_outer_force_dataset.py --source-dataset data\classic_dataset\v1 --pid-bank data\outer_force_pid_bank\v1 --out data\outer_force_dataset\v1

# Entrenamiento MLP, features minimas
uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 --architecture mlp --feature-version outer_force_min_v1 --out data\neural_control\outer_force_mlp_min_v1 --device auto

# Entrenamiento MLP, features completas
uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 --architecture mlp --feature-version outer_force_full_v1 --out data\neural_control\outer_force_mlp_full_v1 --device auto

# Evaluacion supervisada
uv run python tools\evaluate_neural_controller.py --dataset data\outer_force_dataset\v1 --run data\neural_control\outer_force_mlp_min_v1 --device auto

# Ejecucion cerrada OOD
uv run python tools\run_neural_scenario.py --scenario scenarios\neural_ood_lemniscate.yaml --checkpoint data\neural_control\outer_force_mlp_min_v1\checkpoints\mlp_best.pt --normalization data\neural_control\outer_force_mlp_min_v1\normalization.json --device auto --no-visualization
```

Los comandos generan artefactos locales; no implican que existan ya
checkpoints entrenados o resultados finales versionados.

## Project Structure

La implementacion usa las responsabilidades existentes:

```text
src/simulador_quad/control/
  classic.py                    -> reutilizacion lazo interno desde fuerza ENU
  neural.py                     -> nuevo neural outer-force y neural_position conservado

src/simulador_quad/ml/
  dataset.py                    -> features/versiones y targets desired_force_W

tools/
  generate_outer_force_pid_bank.py
  generate_outer_force_dataset.py
  train_neural_controller.py
  evaluate_neural_controller.py
  run_neural_scenario.py

tests/
  test_neural_outer_force.py
  test_neural_position_control.py
  test_neural_dataset.py

docs/simulador/
  control_neuronal.md
  arquitectura.md
  escenarios_yaml.md
  validacion.md
  trazabilidad.md
```

La documentacion viva de `docs/simulador/` se actualiza una vez verificado el
comportamiento implementado.

## Code Style

La implementacion debera mantener unidades y marco en nombres, y delegar en el
controlador clasico la matematica compartida:

```python
desired_force_W_N = self._predict_desired_force_W_N(obs_state, reference)
desired_force_W_N = self._limit_desired_force_W_N(desired_force_W_N)
return self.classic_inner.compute_control_from_desired_force_W(
    obs_state,
    reference.yaw_rad,
    desired_force_W_N,
)
```

Reglas:

- Usar `*_W_*` para vectores expresados en mundo ENU.
- Usar `*_B_*` para magnitudes expresadas en cuerpo FRD.
- Incluir unidades en nombres de outputs, targets y metricas.
- No duplicar la ecuacion del experto entre controlador y dataset sin una
  prueba de equivalencia.
- Mantener nuevas abstracciones pequenas y ligadas a contratos fisicos
  concretos.

## Testing Strategy

### Unit tests

- `compute_control_from_desired_force_W(...)` conserva el resultado del PID
  clasico cuando recibe la fuerza producida por su propio lazo externo.
- Target de dataset coincide con `compute_desired_force_W(...)` para el PID
  experto y la misma `observation`.
- `outer_force_min_v1` devuelve dimension `9`.
- `outer_force_full_v1` devuelve dimension `31`.
- Los features cambian si cambia `observation` aunque `state` permanezca fijo.
- El clipping por norma limita fuerza maxima sin producir no finitos.
- El clipping por inclinacion impide solicitar mas de
  `max_desired_tilt_rad`.
- Checkpoint de salida `4` legacy y checkpoint de salida `6`
  `neural_position` fallan al cargarse como outer-force.
- `NeuralPositionController` conserva targets, clipping y carga de
  checkpoint actuales.

### Dataset and selection tests

- El banco outer-force varia `Kp_pos` y `Kd_pos` pero mantiene constantes
  `Kp_att` y `Kd_att`.
- Candidatos inseguros no pueden seleccionarse como experto.
- Se selecciona un unico PID por escenario con la regla RMSE, `5%` y
  conservadurismo.
- `manifest.csv` conserva split y trazabilidad hacia escenario fuente,
  candidato elegido y resultados comparados.
- Normalizacion se calcula solo con `train`.

### Integration tests

- Loader/schema aceptan el nuevo contrato `controller.type: neural`.
- MLP, GRU y LSTM ejecutan un escenario corto outer-force.
- `neural_position` sigue ejecutando un escenario corto sin cambio de
  comportamiento.
- Evaluacion supervisada escribe metricas de fuerza por split.
- Evaluacion cerrada escribe metricas fisicas y porcentajes de clipping.
- Los escenarios historicos clasicos siguen pasando sus regresiones.

### Experimental validation

- Ejecutar escenarios nominales de las familias existentes.
- Ejecutar al menos una trayectoria OOD ya disponible.
- Comparar baseline, oraculo, `neural_position` y outer-force en las mismas
  condiciones y seeds.
- No aceptar como resultado principal un modelo que termine por crash,
  inclinacion excesiva o saturacion persistente en escenarios nominales.

## Documentation

Documentos actualizados tras la implementacion:

- `README.md`: nuevo significado de `neural`, modos disponibles y comandos.
- `docs/simulador/control_neuronal.md`: targets de fuerza, features y
  comparacion con multiplicadores.
- `docs/simulador/arquitectura.md`: separacion de lazo externo neuronal y PID
  interno.
- `docs/simulador/escenarios_yaml.md`: contrato nuevo y limite de inclinacion.
- `docs/simulador/validacion.md`: metricas y escenarios de comparacion.
- `docs/simulador/trazabilidad.md`: dataset outer-force y evidencias.

El documento LiteWing activo podra referenciar este controlador como candidato
de futuro despliegue, pero su implementacion real queda en una fase separada.

## Boundaries

- Always: mantener mundo ENU y cuerpo FRD con unidades explicitas.
- Always: conservar `neural_position` funcional y separado de outer-force.
- Always: usar `observation` para features y targets neuronales nuevos.
- Always: mantener el PID interno constante al construir el oraculo.
- Always: calcular normalizacion exclusivamente con `train`.
- Always: evaluar calidad final en bucle cerrado, no solo con loss
  supervisada.
- Ask first: introducir optimizacion directa de trayectoria o aprendizaje por
  refuerzo.
- Ask first: cambiar la interfaz de salida a setpoints especificos LiteWing,
  PWM o velocidades de rotor.
- Ask first: cambiar parametros fisicos, escenarios base o criterios
  normativos del TFG.
- Never: mezclar checkpoints legacy con el nuevo contrato sin fallo explicito.
- Never: seleccionar expertos usando muestras de `test` u OOD para entrenar.
- Never: presentar clipping frecuente como evidencia de un controlador
  correctamente aprendido.
- Never: modificar dinamica, mixer o actuadores para ocultar fallos del modelo.

## Success Criteria

El contrato software se considera implementado cuando:

1. `type: neural` produzca fuerza externa ENU y use el PID interno clasico.
2. `type: neural_position` siga funcionando como programador de ganancias.
3. El dataset outer-force seleccione un experto seguro por escenario con PID
   interno fijo y targets de fuerza trazables.
4. Puedan generarse y evaluarse artefactos para `outer_force_min_v1` y
   `outer_force_full_v1`; los resultados finales se obtienen en la fase
   experimental.
5. MLP, GRU y LSTM puedan entrenarse, evaluarse y ejecutarse en bucle
   cerrado bajo el nuevo contrato.
6. Los artefactos incompatibles fallen de forma explicita.
7. La suite `uv run pytest` pase.
8. La documentacion viva describa solo el comportamiento realmente
   implementado y sus limitaciones.

## Assumptions

- PyTorch continua siendo el stack de entrenamiento.
- Los escenarios y splits existentes son la base inicial para construir el
  nuevo dataset; los targets se regeneran.
- `max_desired_tilt_rad=0.52` es el valor inicial recomendado, no un limite
  validado para hardware real.
- La comparacion frente al oraculo sirve como referencia experimental, no como
  afirmacion de optimalidad.
- La transferencia a LiteWing se abordara despues, preferentemente empezando
  por la MLP y conservando control interno clasico.

## Open Questions

No quedan decisiones bloqueantes para implementar esta especificacion. La
seleccion futura de una interfaz de hardware LiteWing, posicion externa o
ejecucion offboard pertenece a la spec sim-to-real separada.
