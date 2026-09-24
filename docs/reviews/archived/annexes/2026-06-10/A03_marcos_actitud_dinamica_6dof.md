# Anexo A03 — Marcos, actitud y dinámica 6DOF

**Fecha:** 2026-06-10 | **Owner:** A03

## Superficie revisada

`src/simulador_quad/core/frames.py`, `attitude.py`, `contracts.py`, `dynamics/rigid_body.py`, `dynamics/perturbations.py`, `tests/test_attitude.py`, `tests/test_dynamics.py`, `tests/test_perturbations.py`.

## Invariantes y contratos comprobados

- Empuje `-Z_B` verificado (`test_attitude.py`, `test_hover_level_frd_thrust_sign`).
- Drag lineal centralizado en `perturbations.compute_linear_drag`; usado desde `rigid_body.py:29`.
- RK4 preserva norma cuaternión (`test_dynamics.py`).

## Hallazgos del dominio

| ID | Sev. |
|----|------|
| F-006 | P2 |
| F-007 | P2 |

## Históricos revalidados

- Drag duplicado rigid_body/perturbations (mayo 2026): **refutado** — import único en rigid_body.
- Import perturbations no usado en runner (mayo): **refutado** — runner usa WindModel/ObservationNoise.

## No verificable

- Estudio sensibilidad `physics_dt_s` sin ejecutar campaña numérica extendida.

## Zonas sin problemas

- Caída libre ENU signo Z (`test_free_fall`).
- Conservación orientación sin torque.
- Drag disipativo con orientación no trivial (`test_perturbations.py`).

## Comandos

`uv run pytest tests/test_attitude.py tests/test_dynamics.py tests/test_perturbations.py -q` → **24 passed**.

## R2 — Contraste cruzado

| Revisor | Pregunta | Veredicto |
|---------|----------|-----------|
| A04 | ¿Fuerzas cuerpo coherentes con actuadores? | Sí |
| A05 | ¿Composite afecta dinámica estado? | F-021 limitación transición |
| A11 | ¿Cobertura hover FRD suficiente? | Parcial F-006 |