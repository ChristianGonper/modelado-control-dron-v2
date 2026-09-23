---
name: commits
description: Organiza cambios pendientes en commits pequeños, coherentes y fáciles de comprender.
---

# Commits

Organiza los cambios pendientes en commits pequeños y coherentes según lo que representan.

## Principios

- Cada commit debe corresponder a una unidad de cambio comprensible por sí misma.
- La cantidad y el tamaño de los commits surgen de los cambios reales; no siguen una estructura predeterminada.
- Agrupa en un mismo commit los cambios que forman una unidad lógica y separa los que representan responsabilidades distintas.
- Cuando un mismo archivo contenga cambios pertenecientes a unidades diferentes, utiliza preparación selectiva por fragmentos cuando resulte útil.
- Comprueba el contenido preparado antes de crear cada commit.

## Archivos no textuales

Los PDF, DOCX, imágenes, datasets y otros archivos no textuales se agrupan según su relación con el cambio.

Pueden compartir commit con otros archivos cuando formen parte natural de la misma unidad. Sepáralos cuando constituyan un cambio independiente o cuando hacerlo facilite claramente la revisión.

## Mensajes

Escribe los mensajes en español sencillo, breves y descriptivos.

No utilices prefijos como `feat:`, `fix:` o `chore:` salvo indicación expresa del usuario.

El mensaje debe permitir comprender qué cambia sin depender de una taxonomía concreta.

## Propuesta y ejecución

Antes de crear los commits, revisa el estado actual de los cambios y presenta una propuesta de agrupación con los mensajes previstos para que el usuario pueda revisarla.

Después de su aprobación, prepara y crea cada commit de acuerdo con esa agrupación. Utiliza selección por rutas o por fragmentos según resulte más adecuado para separar correctamente las unidades de cambio.
