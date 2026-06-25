# Revisiones y auditorias

Esta carpeta contiene revisiones tecnicas del simulador y auditorias de estado.

## Diagnostico vigente (junio 2026)

- **`auditoria_integral_tfg_2026-06-10.md`**: auditoria integral READ-ONLY (cientifico, simulador, neuronal, documentacion), dictamen para memoria, hallazgos P0–P2, mapa de regeneracion de evidencias y delta vs mayo 2026. **Consultar primero** para el estado actual del TFG.
- **`estudio_sensibilidad_neuronal_outer_force_2026-06-25.md`**:
  evidencia reproducible de sensibilidad de `outer_force_min_v1` frente a
  `hidden_dim=128`, ventanas recurrentes `L=10/40` y semillas adicionales. No
  cambia la configuracion principal, pero justifica documentar que fue
  contrastada.

## Auditoria multivista (mayo 2026 — referencia historica)

Fecha 2026-05-04. Util para el contexto del saneamiento clasico, pero **puede contradecir** el estado de junio 2026 (README, trazabilidad, control neuronal, suite de tests). Contrastar siempre con `docs/simulador/` y `auditoria_integral_tfg_2026-06-10.md`.

- `auditoria_sintesis_multivista.md`: sintesis principal y orden recomendado de saneamiento (mayo 2026).
- `auditoria_fisica_modelado_6dof.md`: revision de fisica, marcos, unidades, RK4, drag y supuestos.
- `auditoria_control_ingenieria.md`: revision de control clasico, mixer, actuadores, trayectorias.
- `auditoria_software_cientifico.md`: revision de mantenibilidad, reproducibilidad, contratos y dependencias.
- `auditoria_pruebas_validacion.md`: revision de pruebas, escenarios, metricas y evidencias.
- `auditoria_documentacion_trazabilidad_tfg.md`: revision de documentacion, README, planes y trazabilidad.

**Errata mayo → junio (resumen):** README raiz completo; existe `docs/simulador/trazabilidad.md` y `validacion.md`; control `neural` y `neural_position` documentados e implementados; `docs/preliminar/` retirado; suite de tests ampliada. Persisten lagunas de **evidencia experimental regenerada** (outer-force, OOD cerrado, tabla comparativa de controladores).

## Revisiones historicas

- `04_revision_fisica_simulador.md`: revision fisica anterior; conservar como historica.
- `05_revision_subsanacion_findings_simulador.md`: revision de subsanacion anterior; varios hallazgos ya no aplican (waypoints, loader); conservar como historica.

## Uso recomendado

1. Consultar primero `auditoria_integral_tfg_2026-06-10.md`.
2. Usar las auditorias multivista de mayo solo con contraste explicito al estado actual.
3. Usar `docs/simulador/` como documentacion viva del codigo implementado.
4. Si se corrige un hallazgo, actualizar la documentacion viva afectada y, si procede, anotar el cambio en una nueva revision o errata aqui.
