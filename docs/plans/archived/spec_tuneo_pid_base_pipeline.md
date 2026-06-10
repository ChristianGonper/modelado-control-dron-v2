# Especificacion: tuneo reproducible de PID base e integracion en campaña

## Objetivo

Definir un flujo reproducible para obtener un unico PID clasico base por familia
antes de generar datasets, entrenar redes o ejecutar comparaciones.

El PID base debe reducir errores respecto a los valores iniciales sin convertirse
en un oraculo ajustado por escenario o perturbacion. Una vez seleccionado, queda
congelado para todos los escenarios de la familia.

El flujo tambien debe asegurar que el dataset `neural_position` varia y etiqueta
exclusivamente ganancias externas `Kp_pos` y `Kd_pos`. Las ganancias internas
`Kp_att` y `Kd_att` deben permanecer iguales al PID base congelado.

## Criterios cientificos

- Existe un unico PID base por familia: `hold`, `circle`, `lissajous` y
  `waypoint`.
- El PID base no se reajusta por geometria, perturbacion, split, semilla ni
  escenario.
- El tuneo no usa episodios `test` ni escenarios OOD.
- La seleccion usa simulaciones cerradas, filtros duros y metricas fisicas.
- Los valores iniciales, candidatos, resultados y PID elegido quedan trazados.
- Si el PID inicial cumple los criterios, se conserva y no se ejecuta el tuneo.

## Flujo propuesto

### 1. Generacion del dataset clasico inicial

Generar escenarios y PIDs iniciales deterministas. Los PIDs iniciales tienen
`source: default_initial` y no se consideran tuneados.

### 2. Ronda inicial de diagnostico

Evaluar cada PID inicial sobre un conjunto fijo de diagnostico por familia:

- Solo escenarios del split `train`.
- Una geometria representativa lenta y una exigente.
- Perfiles `P0_nominal`, `P2_wind_east` y `P5_combined`.
- Semillas fijadas en el manifiesto.

Una familia requiere tuneo si ocurre cualquiera de estas condiciones:

- Algun escenario no pasa `passes_hard_filters`.
- El RMSE medio supera el umbral de su familia.

Umbrales agregados por defecto:

| Familia | RMSE medio maximo |
|---|---:|
| `hold` | 0.25 m |
| `circle` | 0.35 m |
| `lissajous` | 0.45 m |
| `waypoint` | 0.40 m |

Estos umbrales son la primera configuracion oficial del pipeline. Deben poder
modificarse de forma explicita mediante argumentos o configuracion de campaña,
quedando registrados en los artefactos de diagnostico y tuneo. Cambiarlos
produce una condicion experimental distinta que debe documentarse.

### 3. Tuneo progresivo

El tuneo modifica `Kp_pos`, `Kd_pos`, `Kp_att` y `Kd_att` del PID base de la
familia. Usa el mismo conjunto de diagnostico que la ronda inicial.

La busqueda debe ser determinista y mas eficiente que una rejilla cartesiana
`3^4`:

1. Incluir siempre el PID inicial como candidato.
2. Ejecutar una primera ronda de candidatos obtenidos mediante muestreo
   log-uniforme estratificado de multiplicadores.
3. Conservar los mejores candidatos que pasan filtros duros.
4. Refinar localmente alrededor de esos candidatos con perturbaciones menores.
5. Seleccionar por score agregado medio.
6. Entre candidatos dentro del 5% del mejor score, elegir el de menor esfuerzo
   de control y, despues, el de menor desviacion respecto al PID inicial.

Valores aceptados:

- Primera ronda: 32 candidatos por familia.
- Refinamiento: 16 candidatos por familia.
- Rango inicial de multiplicadores: `[0.5, 2.0]`.
- Semilla del buscador: `1042`.

Una familia se retunea si falla cualquier escenario del conjunto de
diagnostico, aunque su RMSE medio permanezca por debajo del umbral agregado.

### 4. Congelacion y regeneracion

Guardar el PID seleccionado en:

```text
data/classic_dataset/v1/pids/pid_<family>_v1.yaml
```

El YAML debe contener:

- `source: tuned_progressive_search` o `source: default_initial_accepted`.
- Configuracion de busqueda.
- Conjunto de diagnostico.
- Metricas del PID inicial y seleccionado.
- Motivo por el que se ejecuto o se omitio el tuneo.

Despues de congelar los PIDs, regenerar los escenarios clasicos para que todos
usen las ganancias seleccionadas y ejecutar el dataset clasico completo.

### 5. Bancos neuronales

#### Outer-force

Construir variantes por escenario modificando exclusivamente `Kp_pos` y
`Kd_pos`, manteniendo fijo el PID interno. El banco debe cubrir variantes con
mayor amortiguacion derivativa que las actuales.

#### Neural-position

Construir variantes por familia modificando exclusivamente `Kp_pos` y
`Kd_pos`. No modificar `Kp_att`, `Kd_att` ni limites internos, porque la red
solo predice ganancias externas.

## Integracion en la campaña

La campaña desde un repositorio sin resultados debe ejecutar:

1. Pruebas de sanidad.
2. Generacion inicial del dataset clasico.
3. Diagnostico y tuneo condicional de PID base por familia.
4. Regeneracion y ejecucion completa del dataset clasico con PIDs congelados.
5. Generacion de bancos y datasets neuronales.
6. Entrenamiento de seis modelos.
7. Evaluacion supervisada, cerrada ID y OOD.
8. Transferencia clasica y consolidacion.

La campaña debe abortar si falta cualquier manifiesto o artefacto requerido por
una fase seleccionada.

## Comandos previstos

```powershell
# Diagnosticar y tunear solo las familias que lo necesiten
uv run python tools\tune_classic_pid.py --dataset data\classic_dataset\v1 --out data\classic_dataset\v1\pids

# Forzar tuneo de todas las familias
uv run python tools\tune_classic_pid.py --dataset data\classic_dataset\v1 --out data\classic_dataset\v1\pids --force

# Ejecutar la campaña completa desde cero
uv run python tools\run_experimental_campaign.py --rerun
```

## Estructura prevista

- `tools/tune_classic_pid.py`: diagnostico, busqueda progresiva y escritura de
  PIDs congelados.
- `tools/run_experimental_campaign.py`: integracion del tuneo y validacion de
  prerequisitos.
- `tools/generate_pid_bank.py`: variantes externas para `neural_position`.
- `tools/generate_outer_force_pid_bank.py`: variantes externas por escenario.
- `tests/`: pruebas unitarias y de integracion del criterio de tuneo.
- `README.md` y `docs/simulador/guia_uso.md`: flujo reproducible desde cero.

## Estrategia de pruebas

- Probar que un PID inicial aceptable no se retunea.
- Probar que un PID que supera umbrales activa el tuneo.
- Probar reproducibilidad con la misma semilla.
- Probar que el PID seleccionado pasa filtros duros en todo el diagnostico.
- Probar que los bancos neuronales no modifican `Kp_att` ni `Kd_att`.
- Probar que la campaña aborta antes de entrenar si falta un manifiesto.
- Ejecutar la suite completa con `uv run pytest -q`.

## Limites

### Siempre

- Mantener mundo ENU y cuerpo FRD.
- Mantener un unico PID base congelado por familia.
- Registrar criterios, semillas y resultados de tuneo.
- Mantener `test` y OOD fuera del tuneo.

### Requiere decision explicita

- Cambiar filtros duros o umbrales agregados.
- Permitir PIDs distintos por escenario o perturbacion.
- Añadir nuevas dependencias de optimizacion.

### Nunca

- Elegir PIDs usando resultados de `test` u OOD.
- Relajar filtros para hacer pasar un candidato.
- Modificar ganancias internas en datasets cuya red solo predice ganancias
  externas.

## Criterios de aceptacion

- Un repositorio sin resultados puede ejecutar la campaña completa siguiendo un
  unico flujo documentado.
- Cada PID base queda identificado como inicial aceptado o tuneado.
- El tuneo es reproducible y usa menos evaluaciones que una rejilla densa
  equivalente.
- Los dos escenarios outer-force actualmente bloqueantes obtienen al menos un
  candidato seguro sin relajar filtros.
- `neural_position` conserva las ganancias internas del PID base.

## Decisiones confirmadas

1. Los umbrales RMSE agregados definidos son los valores por defecto iniciales
   y pueden modificarse explicitamente.
2. El presupuesto por familia es de 32 candidatos iniciales mas 16 candidatos
   de refinamiento.
3. Una familia se retunea si falla cualquier escenario del conjunto de
   diagnostico.
