# NeuroFlight: guía de uso local

NeuroFlight es una aplicación que permite experimentar con el simulador del TFG desde el navegador. Puedes diseñar una trayectoria, compararla con un controlador PD y tres redes neuronales, reproducir los vuelos y examinar métricas y señales. Todo se ejecuta en tu ordenador: no controla un dron real y no entrena redes desde la interfaz.

Esta guía separa tres recorridos: [preparar los modelos](#1-preparar-los-modelos), [instalar y arrancar la aplicación](#2-instalar-y-arrancar-neuroflight) y [explorar una misión](#3-recorrer-una-misión). Al final se describe la [ruta de entrenamiento](#entrenar-desde-cero).

## 1. Preparar los modelos

**Un clon del repositorio no incluye los pesos necesarios para NeuroFlight.** Antes de iniciar una comparación necesitas un paquete completo en `data/neuroflight_bundle/`. Puedes obtenerlo de alguien que ya lo tenga; actualmente no hay una descarga pública configurada. Sin el paquete, la aplicación no puede simular. Si no dispones de él, consulta [entrenar desde cero](#entrenar-desde-cero): esa ruta es técnica y aún no se ha verificado de principio a fin.

El paquete de este equipo contiene cuatro controladores PD y tres redes de fuerza exterior regenerados el 23 de septiembre de 2026; no son los pesos históricos de la memoria. Los datos de entrenamiento proceden de simulaciones y demostraciones de expertos PD, no de vuelos reales. El manifiesto permite verificar la integridad del paquete; los experimentos nuevos no son resultados agregados del TFG. Para conocer el protocolo académico, consulta la [memoria](../site/assets/reports/TFG_Memoria_es.pdf).

Si ya tienes la carpeta `data/regenerated_2026-09-23/`, después de instalar las dependencias puedes crear el paquete con `uv run python tools\package_demo_artifacts.py`. El comando escribe en el destino: conserva antes cualquier paquete que necesites.

## 2. Instalar y arrancar NeuroFlight

Necesitas Git, Python 3.13 o posterior, [uv](https://docs.astral.sh/uv/) y Node.js con npm. La aplicación está en la rama `concurso-prototipos-eiiia-2026`. En PowerShell:

```powershell
git clone --branch concurso-prototipos-eiiia-2026 https://github.com/ChristianGonper/modelado-control-dron-v2.git
cd modelado-control-dron-v2
uv sync
cd frontend
npm ci
npm run build
cd ..
```

Coloca el paquete completo en `data/neuroflight_bundle/` y arranca el servidor desde la raíz del repositorio:

```powershell
uv run neuroflight
```

Abre <http://127.0.0.1:8000>. Mantén la terminal abierta mientras uses la aplicación; para detenerla, pulsa Ctrl+C. Si la interfaz no aparece, comprueba que `frontend/dist/` existe y vuelve a compilarla. Si no puedes simular, revisa <http://127.0.0.1:8000/api/health>: informa si faltan archivos o si sus hashes no coinciden.

## 3. Recorrer una misión

### Diseñar la trayectoria

En **Misión**, selecciona «Mantener pos.» para una primera prueba y revisa la posición y la duración. La vista 3D muestra la trayectoria prevista antes de ejecutar. También puedes elegir un círculo, Lissajous, una ruta por puntos o una lemniscata, ajustar sus parámetros y añadir viento horizontal.

![Configuración de una misión y vista previa de la trayectoria](neuroflight-assets/mision.png)

Para un recorrido más variado, elige **Composición por tramos**. Puedes encadenar entre dos y cuatro segmentos, cambiar su orden y modificar sus parámetros. La vista previa muestra tanto la ruta nominal como las transiciones automáticas. El PD de referencia se selecciona según la longitud nominal dominante.

![Ejemplo de trayectoria compuesta en NeuroFlight](neuroflight-assets/composicion.png)

### Ejecutar y comparar

Pulsa **Ejecutar Misión** y espera a que termine el cálculo. En **Comparación** revisa el estado de cada método antes de interpretar el vuelo: el PD, MLP, GRU y LSTM pueden no completar la misión en las mismas condiciones. Usa los controles del reproductor y selecciona las trayectorias que quieras observar. Una ejecución interrumpida solo aporta información hasta el instante de parada.

### Analizar

En **Análisis** examina los errores de seguimiento, las protecciones y la telemetría disponible. Al comparar cifras, comprueba qué controladores completaron la trayectoria y durante cuánto tiempo se midió cada uno. Una diferencia en una misión concreta no demuestra que una arquitectura sea mejor en general: para eso consulta el conjunto de experimentos de la memoria.

Las ejecuciones nuevas se guardan en `data/neuroflight_runs/`, junto con su configuración y los hashes del paquete. No modifican los resultados históricos del TFG.

## Entrenar desde cero

Esta es una ruta técnica parcial, no una receta validada de extremo a extremo para obtener un paquete listo para la aplicación.

El repositorio incluye herramientas para generar escenarios, ajustar PD, generar demostraciones y entrenar redes. El siguiente comando **solo muestra** las fases y comandos sin ejecutarlos:

```powershell
uv run python tools\run_experimental_campaign.py --phase 2-5 --workers 2 --device cpu --dry-run
```

Para ejecutarlas, retira `--dry-run` solo después de revisar los comandos y las advertencias de escritura. Las fases 2–5 generan el dataset clásico, ajustan los PD y generan datos de fuerza. La fase 7 de la campaña también entrena otra variante y depende de la fase 6; por ello no se presenta aquí como ruta mínima. Los comandos concretos para las tres redes outer-force y su evaluación están en el anejo de comandos de la [memoria PDF](../site/assets/reports/TFG_Memoria_es.pdf) ([fuente](../TFG_Memoria/appendices/a_comandos.tex)). El proceso completo puede consumir mucho tiempo, CPU, almacenamiento y memoria; CUDA es opcional. No se ha medido aquí una duración ni ejecutado el entrenamiento completo. Las fases escriben en `data/` y algunas regeneran archivos: usa un checkout y directorio de datos separados para no sobrescribir trabajo existente.

Para entrenar las tres redes outer-force una vez generados los datos de las fases 2–5, ejecuta para cada arquitectura el comando del anejo, por ejemplo en PowerShell:

```powershell
foreach ($arquitectura in @('mlp', 'gru', 'lstm')) {
  uv run python tools\train_neural_controller.py --dataset data\outer_force_dataset\v1 `
    --architecture $arquitectura --feature-version outer_force_min_v1 `
    --out "data\neural_control\outer_force_${arquitectura}_min_v1" --device auto
}
```

Si la campaña ha producido los cuatro PD en `data/classic_dataset/v1/pids/` y los tres modelos con checkpoint, configuración y normalización en las rutas anteriores, el empaquetador acepta `data/` como raíz. El destino se escribe o sobrescribe: guarda primero cualquier paquete que necesites conservar.

```powershell
uv run python -c "from pathlib import Path; from tools.package_demo_artifacts import package_bundle; package_bundle(Path('data'), Path('data/neuroflight_bundle'))"
```

Se ha comprobado la función de empaquetado con los artefactos regenerados existentes en una carpeta temporal; no se ha comprobado esta cadena completa con modelos recién entrenados. Arranca NeuroFlight y comprueba `/api/health` para verificar los hashes del paquete resultante.

El empaquetador usa por defecto `data/regenerated_2026-09-23/`, mientras que la campaña escribe en `data/classic_dataset/` y `data/neural_control/`. Por tanto, entrenar no instala automáticamente los modelos en NeuroFlight. El comando anterior indica explícitamente esa raíz alternativa al [empaquetador](../tools/package_demo_artifacts.py). Esta ruta no se ha validado de extremo a extremo desde cero; nuevos entrenamientos no garantizan reproducir los pesos ni las cifras históricas.
