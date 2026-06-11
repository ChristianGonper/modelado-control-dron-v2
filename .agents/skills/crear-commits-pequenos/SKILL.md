---
name: crear-commits-pequenos
description: Revisar cambios Git, dividirlos en unidades funcionales pequeñas y crear commits con asuntos expresivos y sencillos, sin prefijos de Conventional Commits. Usar cuando el usuario pida preparar, dividir, organizar, realizar o revisar commits en este repositorio.
---

# Crear commits pequenos

## Regla principal

Crear commits solo cuando el usuario lo solicite explicitamente. Hacer que cada commit represente una unica unidad funcional completa y revisable.

Leer [estilo-commits.md](references/estilo-commits.md) antes de crear los commits.

## Preparar la division

1. Leer las instrucciones `AGENTS.md` aplicables.
2. Inspeccionar `git status`, `git diff`, `git diff --staged` y el historial reciente.
3. Identificar cambios ajenos o no relacionados y dejarlos intactos.
4. Dividir por intencion funcional, no solo por tipo de archivo.
5. Mantener juntos una modificacion y sus pruebas o documentacion necesaria.
6. Separar cambios independientes aunque se hayan realizado al mismo tiempo.
7. No forzar una division que deje el repositorio roto o haga incomprensible un commit.

## Preparar cada commit

- Seleccionar rutas o hunks concretos; evitar `git add .` cuando existan cambios no relacionados.
- Revisar el diff staged antes de confirmar.
- Ejecutar las verificaciones focales apropiadas para esa unidad.
- Comprobar que no se incluyen secretos, caches, artefactos generados ni resultados accidentales.
- Usar un asunto en espanol, sencillo, expresivo y sin punto final.
- No usar prefijos como `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:` ni variantes con ambito.

## Finalizar

1. Crear un commit por unidad funcional.
2. Revisar el commit creado con `git show --stat --oneline HEAD`.
3. Repetir para las unidades restantes solicitadas.
4. Informar de los hashes, asuntos, verificaciones y cambios que hayan quedado sin incluir.
