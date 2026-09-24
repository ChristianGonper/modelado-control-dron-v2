# Sintesis de auditoria multivista del repositorio

Fecha: 2026-05-04

Alcance: sintesis de las auditorias generadas desde cinco perspectivas: fisica/modelado 6DOF, control e ingenieria aeroespacial, software cientifico simple, pruebas/validacion y documentacion/trazabilidad TFG. No se ha modificado codigo fuente ni tests.

## Reportes generados

- `docs/reviews/auditoria_fisica_modelado_6dof.md`
- `docs/reviews/auditoria_control_ingenieria.md`
- `docs/reviews/auditoria_software_cientifico.md`
- `docs/reviews/auditoria_pruebas_validacion.md`
- `docs/reviews/auditoria_documentacion_trazabilidad_tfg.md`

## Dictamen global

El repositorio esta en buen estado como base de simulador 6DOF clasico para un TFG: tiene paquete Python organizado, convenciones ENU/FRD visibles, dinamica Newton-Euler, cuaterniones, RK4, actuadores con lag/retardo/saturacion, mixer, escenarios YAML, telemetria, metricas, visualizacion y tests unitarios de componentes criticos.

La prioridad no deberia ser aumentar fidelidad aerodinamica ni introducir mas arquitectura. El salto de calidad necesario es academico y experimental: cerrar la trazabilidad requisito-modelo-codigo-prueba-escenario-metrica, limpiar documentacion obsoleta, validar entradas fisicas, definir criterios de aceptacion por escenario y preparar de forma reproducible la futura comparacion clasico-neuronal.

## Verificacion observada

La verificacion comun ejecutada durante la auditoria fue:

```powershell
uv run pytest
```

Resultado observado por la auditoria principal y varios subagentes: 29 tests pasan.

Algunos subagentes ejecutaron escenarios principales (`hover_clean`, `circle_drag`, `circle_noisy_wind`) y observaron terminacion por `Time limit reached`. El estado Git final solo muestra nuevos reportes en `docs/reviews/`.

## Puntos de vista elegidos

### 1. Fisica y modelado 6DOF

Objetivo: comprobar si el modelo implementado es fisicamente defendible dentro del alcance limitado del TFG.

Foco: ENU/FRD, empuje en `-Z_B`, gravedad, drag lineal, viento, Newton-Euler, RK4, cuaterniones, actuadores y supuestos de validez.

Conclusiones principales:

- La base fisica es razonable para v1.
- Hay riesgo de contradiccion entre documentacion preliminar y codigo real.
- Faltan validaciones fisicas de parametros de escenario.
- Conviene reforzar tests con actitud nivelada real ENU/FRD y fuerza de empuje en cuerpo.

### 2. Control e ingenieria aeroespacial

Objetivo: revisar si el simulador sirve como banco de comparacion entre controlador clasico y futura imitacion neuronal.

Foco: controlador en cascada, ganancias, mixer, actuadores, trayectorias, metricas, escenarios comunes y contrato de control.

Conclusiones principales:

- El controlador clasico es interpretable y util como baseline.
- Sus ganancias no son plenamente trazables desde YAML ni metadata.
- La comparativa neuronal aun no es ejecutable.
- Las metricas de esfuerzo mezclan unidades y deben separarse antes de usarse como argumento fuerte.

### 3. Software cientifico simple

Objetivo: evaluar mantenibilidad, claridad y reproducibilidad sin sobredisenar.

Foco: estructura de paquete, dataclasses, CLI, pyproject/uv, dependencias, validacion de entradas, errores, docstrings y metadata.

Conclusiones principales:

- La estructura modular es clara y apropiada para codigo cientifico.
- Faltan contratos ejecutables: dimensiones, finitud, signos y rangos fisicos.
- `README.md` raiz esta vacio y `pyproject.toml` conserva descripcion generica.
- La reproducibilidad debe registrar version de codigo, entorno, comando y hash/configuracion efectiva.

### 4. Pruebas, validacion, escenarios y metricas

Objetivo: comprobar si los tests y resultados son evidencia suficiente para una memoria academica.

Foco: cobertura conceptual, regresiones numericas, invariantes fisicas, escenarios YAML, outputs `results/`, metricas y criterios de aceptacion.

Conclusiones principales:

- La suite cubre bien bloques aislados.
- Falta matriz de validacion con tolerancias numericas.
- No hay regresiones de escenarios completos contra bandas aceptables.
- No hay cobertura de controlador neuronal ni comparacion cerrada.

### 5. Documentacion, trazabilidad y adecuacion TFG

Objetivo: revisar si la documentacion permite defender el trabajo ante tribunal.

Foco: docs normativos, README, docs/simulador, docs/preliminar, docs/plans, docs/reviews, coherencia de alcance y separacion v1/futuro.

Conclusiones principales:

- Los documentos normativos son solidos.
- `docs/simulador/` esta bastante alineado con el codigo actual.
- `docs/preliminar/` contiene contenido obsoleto o aspiracional presentado como implementado.
- Falta una matriz unica de trazabilidad y un indice de estado de revisiones/planes.

## Hallazgos transversales prioritarios

### P0 - La documentacion preliminar puede sobrerreclamar alcance

Nota del usuario: ya está quitada la carpeta e ignorada.

Varios documentos preliminares mencionan viento Ornstein-Uhlenbeck, drag cuadratico, perdida inducida, MLP/GRU/LSTM, dataset neuronal y CLI antiguo. El codigo actual implementa v1 clasica con viento constante/simple, drag lineal y controlador clasico.

Accion recomendada: marcar `docs/preliminar/*` como historico/no normativo o reescribirlo antes de usarlo en la memoria.

### P0 - Falta trazabilidad requisito-codigo-prueba-escenario-metrica

La trazabilidad esta dispersa: docs normativos, arquitectura, guia, tests y escenarios. No hay una tabla unica auditable.

Accion recomendada: crear `docs/simulador/trazabilidad.md` con requisito, justificacion, codigo, prueba, escenario, metrica, criterio de aceptacion y estado.

### P1 - La comparacion clasico-neuronal aun no existe

El objetivo final del TFG incluye imitacion neuronal, pero el cargador solo acepta `classic` y no hay dataset, entrenamiento, normalizacion, checkpoint ni evaluacion cerrada neuronal.

Accion recomendada: antes de implementar la red, congelar el contrato experimental: observacion, referencia, accion objetivo, normalizacion, escenarios train/val/test, semillas y evaluacion cerrada.

### P1 - Escenarios y contratos aceptan parametros fisicos sin validacion suficiente

Las dataclasses y el loader aceptan arrays y valores crudos. Esto puede permitir masas negativas, inercias invalidas, cuaterniones no normalizados, drag negativo o rotores mal definidos.

Accion recomendada: anadir validacion simple y explicita, sin crear una arquitectura pesada.

### P1 - Falta reproducibilidad fuerte de resultados

Las metricas guardan escenario, semilla y config, pero no commit, dirty flag, version Python, plataforma, comando, version del paquete ni hash de `uv.lock`.

Accion recomendada: ampliar `metrics.metadata` con informacion de entorno y codigo.

### P1 - Las metricas de esfuerzo necesitan unidades claras

El esfuerzo agregado actual suma newtons y newton-metro. Puede servir como proxy interno, pero no como metrica fisica principal.

Accion recomendada: separar empuje, momentos, velocidades de rotor, saturacion, degradacion y, si se quiere un indice compuesto, normalizarlo y declararlo como heuristico.

### P2 - Tests buenos pero insuficientes como validacion de TFG

Los tests unitarios pasan, pero faltan regresiones de escenarios completos, criterios numericos de aceptacion y pruebas de propiedades fisicas con orientaciones no triviales.

Accion recomendada: crear escenarios cortos de regresion y una matriz de validacion con tolerancias.

### P2 - README y metadatos del paquete no sirven aun como puerta de entrada

El README raiz esta vacio y `pyproject.toml` mantiene `description = "Add your description here"`.

Accion recomendada: completar README con objetivo, estado, alcance, comandos `uv`, mapa documental y advertencia de control neuronal pendiente.

## Orden de trabajo recomendado

1. Limpiar capa documental: README raiz, estado de preliminares, indice de revisiones y separacion clara entre v1 clasica y fase neuronal futura.
2. Crear matriz de trazabilidad y validacion.
3. Anadir validacion de escenarios y parametros fisicos.
4. Mejorar metadata reproducible de resultados.
5. Separar metricas de esfuerzo por unidades fisicas.
6. Reforzar tests de convenciones ENU/FRD, drag, saturacion, ZOH y escenarios completos.
7. Congelar contrato de imitacion neuronal antes de implementar entrenamiento.
8. Implementar y validar controlador neuronal solo despues de estabilizar baseline, escenarios y metricas.

## Criterio de cierre sugerido para la fase actual

Antes de usar resultados de la v1 clasica en la memoria, el repositorio deberia permitir:

```powershell
uv sync
uv run pytest
uv run simulador-quad run scenarios\hover_clean.yaml --no-visualization
```

y producir metricas con suficiente informacion para reconstruir:

- codigo usado;
- entorno;
- escenario y parametros efectivos;
- semilla;
- controlador y ganancias;
- causa de terminacion;
- metricas fisicas separadas;
- artefactos de telemetria y figuras.

## Conclusion

La base tecnica del simulador es defendible para una primera version clasica. La mayor deuda no es de complejidad tecnica, sino de rigor academico: evitar sobrerreclamos, cerrar trazabilidad, validar entradas y convertir tests/resultados en evidencia experimental. Ese trabajo debe hacerse antes de tratar la comparacion neuronal como resultado final del TFG.
