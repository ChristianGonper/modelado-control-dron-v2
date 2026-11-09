# Documentación del simulador

El simulador `simulador-quad` reproduce la dinámica de un cuadricóptero y permite estudiar cómo sigue una trayectoria con distintos controladores. La documentación de esta carpeta explica cómo utilizar el código y cómo se organizan sus experimentos. Para el protocolo y los resultados académicos, la referencia es la [memoria del TFG](../../site/assets/reports/TFG_Memoria_es.pdf).

## ¿Por dónde empezar?

- **Quiero ejecutar una simulación:** sigue la [guía de uso](guia_uso.md), desde la preparación del entorno hasta la interpretación de los archivos de salida.
- **Quiero modificar una trayectoria o un escenario:** consulta la [referencia de escenarios YAML](escenarios_yaml.md), con campos, unidades y ejemplos.
- **Quiero probar la aplicación interactiva:** la [guía de NeuroFlight](../neuroflight.md) explica sus modelos, instalación y uso local.

## Para profundizar

- [Arquitectura](arquitectura.md): módulos, flujo de simulación, controladores y datos de salida.
- [Datos clásicos](dataset_clasico.md): escenarios reproducibles, controladores PD y preparación de los datos de expertos.
- [Control neuronal](control_neuronal.md): aprendizaje de la fuerza exterior, entrenamiento y evaluación.
- [Validación](validacion.md): escenarios, métricas y alcance de la evidencia.
- [Evaluación experimental](evaluacion-experimental.md): ejecución de comparaciones y generación de figuras.
- [Trazabilidad](trazabilidad.md): relación entre requisitos, código, pruebas y resultados.
- [Mantenimiento](mantenimiento.md): qué documentación y pruebas revisar al cambiar el simulador.

El modelo utiliza seis grados de libertad y representa actuadores, viento, ruido y un control en cascada. Las redes neuronales del TFG aprenden a calcular la fuerza del control de posición; la estabilización de actitud sigue siendo clásica.
