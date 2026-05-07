# Revisiones y auditorias

Esta carpeta contiene revisiones tecnicas del simulador y auditorias de estado. Los documentos mas recientes son el diagnostico vigente para el saneamiento del simulador clasico.

## Diagnostico vigente

- `auditoria_sintesis_multivista.md`: sintesis principal y orden recomendado de saneamiento.
- `auditoria_fisica_modelado_6dof.md`: revision de fisica, marcos, unidades, RK4, drag y supuestos.
- `auditoria_control_ingenieria.md`: revision de control clasico, mixer, actuadores, trayectorias y preparacion futura para imitacion.
- `auditoria_software_cientifico.md`: revision de mantenibilidad, reproducibilidad, contratos y dependencias.
- `auditoria_pruebas_validacion.md`: revision de pruebas, escenarios, metricas y evidencias para memoria.
- `auditoria_documentacion_trazabilidad_tfg.md`: revision de documentacion, README, planes y trazabilidad.

## Revisiones historicas

- `04_revision_fisica_simulador.md`: revision fisica anterior; conservar como historica.
- `05_revision_subsanacion_findings_simulador.md`: revision de subsanacion anterior; conservar como historica.

## Uso recomendado

1. Consultar primero `auditoria_sintesis_multivista.md`.
2. Usar las auditorias por area para justificar specs en `docs/plans/`.
3. No tratar revisiones historicas como estado vigente sin contrastarlas con `docs/simulador/` y las auditorias multivista.
4. Si se corrige un hallazgo, actualizar la documentacion viva afectada y, si procede, anotar el cambio en una nueva revision.
