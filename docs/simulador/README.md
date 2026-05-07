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
- Mezclador de cuadricoptero con empuje colectivo y momentos de cuerpo.
- Actuadores con saturacion, retardo puro opcional y lag de primer orden sobre `omega`.
- Drag lineal simplificado, viento constante y ruido gaussiano de observacion en posicion/velocidad.
- Escenarios YAML, telemetria JSON, metricas JSON con unidades fisicas explicitas y figuras PNG reproducibles.

No implementado todavia:

- Controlador neuronal real por imitacion.
- Entrenamiento, dataset y evaluacion neuronal en bucle cerrado.
- Aerodinamica formal mas alla del drag lineal.
- Modelo de bateria, sensores realistas, estimador onboard, contacto con suelo o datos experimentales.

## Documentos

- [Guia de uso](guia_uso.md): instalacion con `uv`, ejecucion de escenarios, resultados y visualizacion.
- [Referencia de escenarios YAML](escenarios_yaml.md): campos admitidos, unidades, marcos de referencia y ejemplos de trayectorias.
- [Arquitectura actual](arquitectura.md): flujo de simulacion, modulos, contratos, telemetria y metricas.
- [Trazabilidad](trazabilidad.md): matriz requisito-modelo-codigo-prueba-escenario-metrica del simulador clasico.
- [Validacion](validacion.md): clasificacion de escenarios, criterios de aceptacion y evidencias para la memoria.
- [Mantenimiento documental](mantenimiento.md): checklist para actualizar esta documentacion despues de cambios agresivos.

## Comandos minimos

```powershell
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml
uv run simulador-quad run scenarios\circle_drag.yaml
uv run simulador-quad plot results\hover_clean\telemetry.json --metrics results\hover_clean\metrics.json --out results\hover_clean\figures
```

Las figuras generadas tienen nombres estables:

- `trajectory_xy.png`
- `position_time.png`
- `tracking_error.png`
- `rotor_speeds.png`
- `control_effort.png`
