# Guía de uso del simulador

Esta guía te acompaña en una primera simulación desde la terminal: prepara el entorno, ejecuta un escenario y examina sus resultados. Si prefieres configurar y comparar misiones en una interfaz gráfica, consulta la [guía de NeuroFlight](../neuroflight.md).

## Preparar el entorno

Necesitas Python 3.13 o posterior y [uv](https://docs.astral.sh/uv/). Abre una terminal PowerShell en la raíz del repositorio y ejecuta:

```powershell
uv sync
```

Esto instala las dependencias del proyecto. Las pruebas automáticas están destinadas al desarrollo y se ejecutan con `uv run pytest`; no es necesario ejecutarlas para probar un escenario.

## Ejecutar una primera simulación

El siguiente escenario simula un cuadricóptero que intenta mantener una posición:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml
```

Al finalizar, consulta la carpeta `results/hover_clean/`, indicada por `output.dir` en el propio escenario. Las ejecuciones nuevas pueden sobrescribir resultados de la misma ruta: cambia `output.dir` si quieres conservar varias por separado.

En la carpeta encontrarás, entre otros archivos:

- `telemetry.json`: evolución temporal de los estados, las referencias y las señales de control.
- `metrics.json`: resumen numérico de la ejecución y motivo de terminación.
- `visualization_3d.html`: visor interactivo de la trayectoria.
- `figures/`: figuras de diagnóstico generadas para la ejecución.

Para ejecutar el escenario sin generar la visualización y las figuras, añade `--no-visualization`:

```powershell
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
```

Esta opción resulta útil para ejecuciones por lotes. El visor y las figuras no se producirán en esa ejecución; la telemetría y las métricas sí permiten analizarla después.

## Leer el resultado

Abre `metrics.json` y comprueba primero `termination_reason`. Una simulación puede terminar por una condición física o de seguridad sin que eso signifique que el programa haya fallado: el motivo forma parte del resultado. En el escenario inicial `hold`, `Time limit reached` es la terminación esperada. Para una trayectoria finita `line` o `waypoint`, la misión se completa con `Trajectory completed`; en `composite`, con `Composite trajectory completed`. Un límite de tiempo no equivale a completar esas trayectorias finitas. La [validación](validacion.md) explica los criterios de éxito y sus límites.

Las figuras permiten observar cómo cambian la posición, el error, la actitud y las señales de control durante el episodio. El visor HTML ofrece una vista espacial; puedes rotar, desplazar y acercar la cámara. Compara los controladores solo sobre intervalos y condiciones equivalentes, especialmente si uno se detuvo antes.

## Regenerar figuras

Con la telemetría y las métricas de una ejecución puedes generar de nuevo las figuras. Por ejemplo:

```powershell
uv run simulador-quad plot results\hover_clean\telemetry.json `
  --metrics results\hover_clean\metrics.json `
  --out results\hover_clean\figures_report --profile report --formats png pdf
```

`--metrics` es opcional. El perfil `report` prepara figuras para documentos y `--formats` selecciona los formatos; sin estas opciones se usa el perfil de diagnóstico. El PDF se obtiene con `plot`, no es una opción del comando `run`.

## Probar otro escenario

Los ejemplos de `scenarios/` incluyen un círculo (`circle_drag.yaml`) y un caso con ruido y viento (`circle_noisy_wind.yaml`). Puedes copiarlos y cambiar una condición cada vez para entender su efecto. Cada YAML define, entre otros datos, la trayectoria, el controlador y las perturbaciones. La [referencia de escenarios](escenarios_yaml.md) describe los campos, unidades y valores admitidos.

Para profundizar, la [arquitectura](arquitectura.md) explica el flujo del simulador; [datos clásicos](dataset_clasico.md) y [control neuronal](control_neuronal.md) describen la preparación experimental. La [evaluación experimental](evaluacion-experimental.md) reúne los pasos para comparar controladores en los conjuntos de prueba. Para entrenar los modelos de la aplicación, sigue la [guía de NeuroFlight](../neuroflight.md).
