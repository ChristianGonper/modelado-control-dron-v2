# Simulador 6DOF de cuadricóptero

[Español](README.md) | [English](README.en.md)

Simulador reproducible de dinámica 6DOF para estudiar el seguimiento de trayectorias de un cuadricóptero y comparar control clásico PID con control neuronal entrenado por imitación. El proyecto reúne el modelo físico, los controladores, los escenarios, las campañas experimentales y las herramientas de análisis en un único paquete de Python.

## Características

- Dinámica de cuerpo rígido 6DOF con mundo ENU, cuerpo FRD y actitud mediante cuaterniones.
- Integración RK4 con frecuencias independientes de física, control y telemetría.
- Mixer de cuadricóptero y actuadores con saturación, retardo puro opcional y dinámica de primer orden.
- Perturbaciones configurables: drag lineal, viento constante y ruido de observación.
- Control PID clásico en cascada para posición y actitud.
- Control neuronal híbrido: una red predice la fuerza deseada del lazo externo y el controlador clásico mantiene la estabilización de actitud.
- Modelos MLP, GRU y LSTM implementados con PyTorch.
- Trayectorias `hold`, `circle`, `lissajous`, `lemniscate`, `waypoint` y `composite`.
- Escenarios YAML, telemetría y métricas JSON, figuras estáticas y visualización 3D interactiva.
- Herramientas reproducibles para generar datasets, ajustar controladores, entrenar redes y ejecutar campañas comparativas.

## Requisitos

- Python 3.13 o posterior.
- [`uv`](https://docs.astral.sh/uv/) para gestionar el entorno y las dependencias.
- Una GPU compatible con CUDA es opcional; las simulaciones y el entrenamiento también pueden ejecutarse en CPU.

## Inicio rápido

Clona el repositorio e instala el entorno:

```powershell
git clone https://github.com/ChristianGonper/modelado-control-dron-v2.git
cd modelado-control-dron-v2
uv sync
```

Ejecuta las pruebas y una simulación de ejemplo:

```powershell
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
```

Genera las figuras del episodio:

```powershell
uv run simulador-quad plot results\hover_clean\telemetry.json `
  --metrics results\hover_clean\metrics.json `
  --out results\hover_clean\figures
```

## Controladores

### PID clásico

El controlador clásico utiliza una arquitectura en cascada. El lazo externo convierte el error de posición en una fuerza deseada en el marco mundo; el lazo interno transforma esa referencia en actitud, empuje y velocidades de rotor. Las ganancias, límites y condiciones experimentales se definen en los escenarios YAML.

### Control neuronal por imitación

El controlador `neural` conserva el lazo interno clásico y sustituye el lazo externo por una red que predice `desired_force_W_N[3]`. El aprendizaje supervisado utiliza demostraciones generadas por expertos PID seleccionados automáticamente. Esta separación permite comparar seguimiento, robustez y seguridad sin delegar la estabilización completa del vehículo a la red.

El flujo mínimo de entrenamiento es:

```powershell
uv run python tools\generate_outer_force_pid_bank.py `
  --dataset data\classic_dataset\v1 `
  --out data\outer_force_pid_bank\v1 `
  --workers 8

uv run python tools\generate_outer_force_dataset.py `
  --source-dataset data\classic_dataset\v1 `
  --pid-bank data\outer_force_pid_bank\v1 `
  --out data\outer_force_dataset\v1

uv run python tools\train_neural_controller.py `
  --dataset data\outer_force_dataset\v1 `
  --architecture mlp `
  --feature-version outer_force_min_v1 `
  --out data\neural_control\outer_force_mlp_min_v1 `
  --device auto
```

También existe el modo experimental `neural_position`, en el que la red programa multiplicadores de ganancias del controlador de posición.

## Escenarios y resultados

Los escenarios reproducibles se encuentran en [`scenarios/`](scenarios/). Cada archivo configura la trayectoria, el controlador, la dinámica de actuadores, las perturbaciones y los límites de seguridad.

Una ejecución puede producir:

- `telemetry.json`: evolución temporal del estado, referencias y señales de control.
- `metrics.json`: métricas físicas y criterios de terminación.
- Figuras PNG, SVG o PDF con perfiles de diagnóstico o informe.
- Un visor HTML 3D interactivo.

Para ejecutar la campaña experimental completa:

```powershell
uv run python tools\run_experimental_campaign.py --dry-run
uv run python tools\run_experimental_campaign.py --rerun --workers 8 --device cuda
```

El modo `--dry-run` permite inspeccionar las fases y comandos antes de iniciar una campaña costosa.

## Estructura del proyecto

```text
src/simulador_quad/  Modelo físico, controladores, simulación y CLI
scenarios/           Escenarios YAML reproducibles
tests/               Pruebas unitarias y de integración
tools/               Datasets, ajuste, entrenamiento y campañas
docs/simulador/      Documentación técnica del software
data/                Datasets y modelos generados localmente
results/             Telemetría, métricas y figuras generadas
```

`data/` y la mayor parte de las salidas de ejecución se generan localmente y no forman parte del código fuente.

## Validación

La batería de pruebas cubre el modelo físico, las convenciones de marcos, los controladores, la configuración, las métricas y los principales flujos de ejecución:

```powershell
uv run pytest
```

La comparación experimental distingue entre completar una misión (`mission_success`) y terminar sin fallo físico (`safety_success`). Alcanzar el límite temporal en una trayectoria finita no se considera una misión completada.

## Contacto

Christian González Pérez

- Universidad: [cgonzp08@estudiantes.unileon.es](mailto:cgonzp08@estudiantes.unileon.es)
- Personal: [christian.gonzalez.perez@proton.me](mailto:christian.gonzalez.perez@proton.me)
