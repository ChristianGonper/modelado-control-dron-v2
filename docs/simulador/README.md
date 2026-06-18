# Documentacion viva del simulador Quad

Esta carpeta documenta el estado actual implementado del simulador `simulador-quad`.
No sustituye a los documentos normativos del TFG ni a los planes historicos: describe como se usa hoy el codigo, que partes estan disponibles y que debe revisarse cuando el simulador cambie.

El publico principal es un alumno o ingeniero aeroespacial que necesita ejecutar escenarios, definir trayectorias, interpretar resultados y explicar el funcionamiento del banco de simulacion.

## Estado actual

Implementado:

- Simulador 6DOF de cuadricoptero como cuerpo rigido.
- Mundo ENU: `X_W` Este, `Y_W` Norte, `Z_W` arriba.
- Cuerpo FRD: `X_B` delante, `Y_B` derecha, `Z_B` abajo.
- Actitud con cuaterniones `orientation_WB` en formato `[w, x, y, z]`.
- Integracion RK4 con pasos separados de fisica, control y telemetria.
- Controlador clasico en cascada.
- Ganancias explicitas opcionales del controlador clasico desde YAML.
- Controlador `neural` por imitacion de fuerza externa ENU, con MLP, GRU y LSTM, y PID clasico en el lazo interno.
- Controlador neuronal `neural_position`, donde la red programa ganancias del lazo externo y el lazo interno clasico estabiliza actitud.
- Pipeline ML con carga de telemetria, normalizacion train-only, entrenamiento supervisado y evaluacion in-distribution/OOD.
- Mezclador de cuadricoptero con empuje colectivo y momentos de cuerpo.
- Actuadores con saturacion, retardo puro opcional y lag de primer orden sobre `omega`.
- Drag lineal simplificado, viento constante y ruido gaussiano de observacion en posicion/velocidad.
- Escenarios YAML, telemetria JSON, metricas JSON con unidades fisicas explicitas y figuras PNG reproducibles.
- Validacion fisica basica de escenarios antes de ejecutar.
- Generacion de dataset clasico versionado con manifiesto CSV, escenarios YAML generados, PID por familia y resultados separados.
- Generacion de dataset `outer_force` mediante banco de PIDs externos, seleccion segura de experto por escenario y targets `desired_force_W_N`.
- Soporte de trayectorias compuestas (`composite`) y transiciones automáticas en línea recta con frenado para validación OOD.

Snapshot verificable del 2026-06-18:

- `215` pruebas pasan con `uv run pytest -q`.
- Las ayudas de `simulador-quad` y de los 21 scripts de `tools/` cargan con `--help`.
- Los CSV versionados en `results/` proceden del commit `fe2e075` del 2026-06-10 y contienen 264 corridas comparables (184 `test`, 80 `ood`). Son un snapshot, no un recuento invariable del codigo.

No implementado todavia:

- Aerodinamica formal mas alla del drag lineal.
- Modelo de bateria, sensores realistas, estimador onboard, contacto con suelo o datos experimentales.

## Documentos

- [Guia de uso](guia_uso.md): instalacion con `uv`, ejecucion de escenarios, resultados y visualizacion.
- [Referencia de escenarios YAML](escenarios_yaml.md): campos admitidos, unidades, marcos de referencia y ejemplos de trayectorias.
- [Arquitectura actual](arquitectura.md): flujo de simulacion, modulos, contratos, telemetria y metricas.
- [Trazabilidad](trazabilidad.md): matriz requisito-modelo-codigo-prueba-escenario-metrica del simulador clasico.
- [Validacion](validacion.md): clasificacion de escenarios, criterios de aceptacion y evidencias para la memoria.
- [Dataset clasico](dataset_clasico.md): fuente reproducible de escenarios y telemetria para construir expertos neuronales.
- [Control neuronal](control_neuronal.md): dataset `outer_force`, entrenamiento, evaluacion supervisada, OOD e inferencia hibrida en bucle cerrado.
- [Mantenimiento documental](mantenimiento.md): checklist para actualizar esta documentacion despues de cambios de contrato.

## Comandos minimos

```powershell
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml
uv run simulador-quad run scenarios\circle_drag.yaml
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
uv run python tools\generate_classic_dataset.py --version v1 --out data\classic_dataset\v1
uv run python tools\run_classic_dataset.py --dataset data\classic_dataset\v1 --no-visualization --workers 4
uv run python tools\generate_outer_force_pid_bank.py --dataset data\classic_dataset\v1 --out data\outer_force_pid_bank\v1 --workers 8
uv run python tools\generate_outer_force_dataset.py --source-dataset data\classic_dataset\v1 --pid-bank data\outer_force_pid_bank\v1 --out data\outer_force_dataset\v1
uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 --architecture mlp --feature-version outer_force_min_v1 --out data\neural_control\outer_force_mlp_min_v1 --device auto
```

Las figuras generadas tienen nombres estables:

- `trajectory_xy.png`
- `trajectory_3d_static.png`
- `position_time.png`
- `attitude_time.png`
- `angular_velocity_time.png`
- `tracking_error.png`
- `rotor_speeds.png`
- `control_effort.png`

Si la telemetria contiene los campos correspondientes, se añaden
`neural_outer_force.png` y `perturbation_response.png`.
