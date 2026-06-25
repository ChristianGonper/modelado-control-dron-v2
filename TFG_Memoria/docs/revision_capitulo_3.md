# Revision tecnica del capitulo 3

Este documento recoge decisiones y pendientes editoriales derivados de la
revision de los apartados de modelo fisico, control clasico, control neuronal y
metodologia. No es texto de la memoria.

## Estado del flujo PID y outer-force

Hecho verificado en codigo:

- `tools/tune_classic_pid.py` ajusta el PD clasico por familia sobre casos de
  entrenamiento. Cuando ajusta, escala conjuntamente `Kp_pos`, `Kd_pos`,
  `Kp_att` y `Kd_att`, evalua candidatos en bucle cerrado y escribe
  `pid_<familia>_v1.yaml`.
- `tools/generate_outer_force_pid_bank.py` se ejecuta despues de congelar esos
  PD. Para cada escenario ya generado, toma el controlador del YAML de origen y
  crea cinco variantes locales que modifican solo `Kp_pos` y `Kd_pos`; el lazo
  interno de actitud queda heredado.
- `tools/generate_outer_force_dataset.py` selecciona, por escenario, la variante
  segura con menor RMSE dentro del margen del 5 % y menor esfuerzo. Copia su
  telemetria para construir el dataset de imitacion.

Interpretacion para la memoria:

- No son dos tuneos equivalentes. El primero busca PD completos por familia; el
  segundo genera objetivos de fuerza para imitacion mediante variantes locales
  del lazo externo.
- La palabra "experto externo" debe entenderse como "variante del lazo externo
  seleccionada para ese escenario", no como un nuevo controlador completo de la
  familia.
- Si esta doble seleccion se considera demasiado pesada o conceptualmente
  confusa, una alternativa futura seria entrenar directamente con la fuerza del
  PD congelado por familia y comparar contra el dataset outer-force actual. Eso
  seria un cambio experimental, no una simple correccion de redaccion.

## Estudio neuronal de sensibilidad

El estudio de sensibilidad de ventana, numero de neuronas y semilla se ejecuto
despues de la revision inicial. La evidencia queda documentada en
`../../docs/reviews/estudio_sensibilidad_neuronal_outer_force_2026-06-25.md` y
resumida en `docs/instrucciones_control_neuronal_pendiente.md`.

Decision editorial:

- Mantener `hidden_dim=64`, `sequence_length=20` y semilla 42 como configuracion
  principal comun.
- Documentar en la memoria que se contrasto frente a `hidden_dim=128`, ventanas
  `L=10/40` y semillas adicionales.
- No mezclar esta sensibilidad con las tablas principales salvo que se cree una
  tabla auxiliar de ablation.
- No ampliar por ahora el numero de episodios de entrenamiento.

## Citas

Citas ya reforzadas en esta revision:

- Modelo de cuadricoptero, rotor/mixer y control en cascada:
  `beard2012small`, `mellinger2011minimum`.
- Aprendizaje por imitacion: `ross2011dagger`.
- ReLU, GRU, LSTM y Adam: `nair2010relu`, `cho2014learning`,
  `hochreiter1997lstm`, `kingma2015adam`.

Citas que aun conviene resolver antes de cerrar el capitulo:

- RK4, retencion de orden cero y simulacion multirrate.
- Modelo simplificado de actuador con lag de primer orden y retardo.
- Modelos simplificados de drag, viento constante y ruido gaussiano.
- Criterios de diseno experimental para cobertura, particiones y metricas.
- Criterios de seguridad: limite de actitud, saturacion persistente y umbrales
  de filtros duros.

## Figuras

Las descripciones detalladas deben mantenerse en
`docs/plan_figuras_diagramas.md` y en las fichas `Figuras/diagramas/FIG-xxx.md`.
Este documento solo registra la prioridad editorial detectada durante la
revision del capitulo.

Prioridad alta:

- FIG-002: ejes ENU/FRD y signo del empuje. Evita errores de lectura en todo el
  modelo fisico.
- FIG-004: arquitectura PD en cascada. Sirve de puente directo hacia la red.
- FIG-006: contrato outer-force neuronal. Es clave para explicar que la red
  sustituye solo la fuerza deseada.
- FIG-007: flujo experimental de 11 fases. Debe dejar clara la separacion entre
  tuneo clasico, banco outer-force, entrenamiento, test y OOD.

Prioridad media:

- FIG-005: busqueda progresiva de PD clasico.
- FIG-008: niveles de evaluacion ID, transferencia, composiciones y geometria
  nueva.
- FIG-009/FIG-010: familias de trayectoria y perfiles waypoint.
- FIG-011: orden de rotores y sentidos de giro.

## Correcciones aplicadas durante la revision

- `03_modelo_fisico.tex`: se corrigio `omega_max` de 316 a `500 rad/s`, con
  `T_max = 25 N` por rotor, alineado con escenarios y dataset.
- `05_control_neuronal.tex`: se matizo la seleccion outer-force para no
  confundirla con una segunda busqueda global de PD.
- `06_metodologia.tex`: se restituyo la fase de programacion de ganancias como
  alternativa implementada fuera de la comparacion principal y se explicitaron
  limites en la ecuacion de RMSE/MAE.
