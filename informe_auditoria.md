# Informe de Auditoría Técnica: Simulador 6DOF de Cuadricóptero (TFG)

## Resumen Ejecutivo
El repositorio presenta una base sólida para un simulador 6DOF clásico orientado a un TFG. Implementa de forma coherente la dinámica de cuerpo rígido con cuaterniones e integración RK4, y proporciona un controlador clásico estructurado. La arquitectura respeta los principios de simplicidad del software científico, las pruebas unitarias pasan en su totalidad y se han establecido buenas prácticas para la exportación de métricas y la reproducibilidad.
La deuda principal no es de complejidad técnica ni errores físicos graves en la implementación, sino de rigor académico: la documentación preliminar contiene afirmaciones de alcance sobre una capa de control neuronal y aerodinámica avanzada que no existen en el código, falta validación robusta para evitar entradas físicamente inviables, y la trazabilidad experimental necesita consolidación para que los resultados puedan usarse formalmente en la memoria del TFG.

## Hallazgos Priorizados

### P0: Sobrerreclamo de alcance en documentación preliminar
*   **Evidencia:** `docs/preliminar/*` (histórico citado en auditorías previas), `README.md` (falta completar).
*   **Explicación técnica:** Varios documentos históricos asumen un modelo neuronal, aerodinámica compleja y viento avanzado que no se reflejan en el código actual (que tiene drag lineal, viento constante y control clásico).
*   **Impacto en el TFG:** Riesgo severo. Si el tribunal lee documentos preliminares como vigentes, evaluará el TFG sobre expectativas no implementadas.
*   **Recomendación:** Eliminar, mover a `archived/` o marcar explícitamente `docs/preliminar/` como documentación histórica. Asegurar que el `README.md` y `docs/01_principios_tfg.md` reflejen de forma unívoca el estado actual (Fase 1: Clásica).

### P0: Falta matriz centralizada de trazabilidad
*   **Evidencia:** Auditoría multivista (`docs/reviews/auditoria_documentacion_trazabilidad_tfg.md`).
*   **Explicación técnica:** La relación entre los requisitos, la implementación matemática, los tests, y los escenarios está dispersa.
*   **Impacto en el TFG:** Dificulta la defensa del simulador frente a preguntas sobre cobertura de requisitos y validez del modelo.
*   **Recomendación:** Consolidar y completar el archivo `docs/simulador/trazabilidad.md` vinculando requisitos explícitos con funciones clave y escenarios de validación.

### P1: Falta de validación física robusta de parámetros (Escenarios)
*   **Evidencia:** `src/simulador_quad/scenarios/schema.py`, `docs/reviews/auditoria_control_ingenieria.md`.
*   **Explicación técnica:** Aunque `schema.py` hace comprobaciones básicas, podría no estar bloqueando estados físicamente inconsistentes (ej. ganancias negativas, drag inválido, etc.) a nivel del controlador o de configuraciones no contempladas.
*   **Impacto en el TFG:** Afecta la reproducibilidad y confiabilidad. Simulaciones con configuraciones malformadas podrían correr sin error y generar datos no físicos, invalidando las comparativas posteriores.
*   **Recomendación:** Expandir `validate_scenario_config` en `schema.py` para validar rangos físicos estrictos de todos los parámetros (ej., propiedades de los rotores, validación de inercia y límites de empuje).

### P1: La comparativa clásico-neuronal es un contrato abierto
*   **Evidencia:** `docs/simulador/README.md`, `src/simulador_quad/scenarios/loader.py` (solo carga control clásico).
*   **Explicación técnica:** El TFG pretende comparar el control clásico con el neuronal, pero los contratos experimentales (dataset, métricas específicas, semillas de validación) no están congelados para la fase neuronal.
*   **Impacto en el TFG:** Cuando se añada el control neuronal, será difícil garantizar igualdad de condiciones sin un marco comparativo predefinido, lo que pone en riesgo el rigor académico.
*   **Recomendación:** Documentar en un archivo dedicado (`docs/simulador/comparativa_experimental.md`) el "contrato" de entradas y salidas para la futura red neuronal antes de escribir código nuevo.

### P1: Métricas de esfuerzo carecen de separación rigurosa de unidades
*   **Evidencia:** `src/simulador_quad/metrics/report.py` (línea 49 `control_effort_heuristic_mean`).
*   **Explicación técnica:** Se suma empuje (N) con momentos (Nm) para calcular un esfuerzo de control heurístico. Esto carece de sentido físico.
*   **Impacto en el TFG:** Usar esta métrica agregada para demostrar eficiencia energética en el TFG no resistirá una revisión técnica del tribunal.
*   **Recomendación:** Eliminar o marcar claramente `control_effort_heuristic_*` como "diagnóstico sin rigor dimensional" y usar únicamente las métricas desagregadas (empuje en N, momentos en Nm) para el análisis.

### P2: Tests funcionales limitados
*   **Evidencia:** Carpeta `tests/` pasa, pero según auditorías faltan escenarios de regresión completos.
*   **Explicación técnica:** Las pruebas unitarias cubren bloques asilados (actitud, integrador) y comprueban invariantes. No se están ejecutando validaciones automáticas con bandas de tolerancia numérica para episodios completos bajo condiciones límite.
*   **Impacto en el TFG:** Modificaciones futuras (ej. al añadir la red neuronal) pueden introducir cambios sutiles en la dinámica que las pruebas actuales no capturarán.
*   **Recomendación:** Implementar tests de integración/regresión que simulen escenarios oficiales completos y validen que el RMSE y otras métricas caen dentro de un umbral aceptable conocido.

### P3: Claridad en docstrings y comentarios residuales
*   **Evidencia:** `src/simulador_quad/control/classic.py` (líneas 47-57 con comentarios tipo "Wait...").
*   **Explicación técnica:** Existen comentarios en el código que demuestran dudas pasadas sobre los ejes y rotaciones durante la implementación.
*   **Impacto en el TFG:** Puede dar una impresión de falta de dominio del sistema de referencia por parte del autor.
*   **Recomendación:** Sustituir los comentarios dudosos por docstrings asertivos explicando la decisión de diseño tomada para las transformaciones ENU/FRD.

## Lo que está bien cubierto
*   **Física Básica:** Implementación coherente de convenciones ENU/FRD, uso de cuaterniones para evitar singularidades, Newton-Euler e integración robusta vía RK4.
*   **Pipeline Experimental:** Buena implementación del bucle `multi-rate` (`physics_dt`, `control_dt`, `telemetry_dt`), mezcla y saturación de actuadores, y sistema declarativo YAML muy alineado con la reproducibilidad científica.
*   **Código Científico:** Estructura modular, trazabilidad del código base (tipos, convenciones de unidades explícitas en las variables), que garantiza una fácil lectura.
*   **Herramientas Auxiliares:** Gestión sólida de telemetría y metadatos de entorno/git garantizando la reproducibilidad (implementado en `app.py` y `report.py`).

## Riesgos Residuales
*   Asegurar que los datos generados por el controlador clásico en la versión actual sean suficientes y ricos en perturbaciones para entrenar de forma eficiente la capa neuronal por imitación en el futuro.
*   Riesgo de que un error en la configuración manual de las ganancias PID dentro del código (hardcodeado en `ClassicCascadeController`) no se refleje correctamente si se decide sobreescribirlo vía YAML en el futuro.

## Siguiente Orden Recomendado de Trabajo
1.  **Limpieza Documental:** Modificar el `README.md`, marcar los documentos preliminares obsoletos y completar el sistema de trazabilidad.
2.  **Limpieza de Código:** Remover los comentarios dubitativos y sustituir la métrica "heurística" de control por las métricas físicas desagregadas en `report.py`.
3.  **Validaciones Físicas:** Expandir `schema.py` para asegurar que todo escenario procesado es físicamente válido e implementar tests de integración por tolerancias.
4.  **Congelar Base Clásica:** Considerar la base actual consolidada y congelada una vez los puntos anteriores sean resueltos, preparando el terreno para la evaluación neuronal.
