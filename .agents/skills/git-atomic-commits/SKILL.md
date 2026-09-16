---
name: git-atomic-commits
description: >
  Organiza y ejecuta commits pequeños, atómicos y ordenados cuando el usuario
  pide explícitamente hacer commits o guardar cambios en Git.
---

# Commits atómicos

Esta skill sólo se aplica cuando el usuario ordena hacer commits.

## Principios

1. Un commit representa la unidad lógica mínima completa definida por la
   responsabilidad real del cambio, no por el tipo ni la cantidad de archivos.
2. Implementación, pruebas, recursos y gobernanza que hagan íntegra esa misma
   responsabilidad pueden y deben viajar juntos.
3. Se separan los cambios que respondan a motivos o áreas desacopladas.
4. No se crea por sistema un commit para `spec.md`, otro para `plan.md` y otro
   para `tasks.md`. La fase documental no determina la atomicidad.
5. La documentación de seguimiento vinculada al cambio se incluye con su unidad
   lógica para mantener trazabilidad.

## Procedimiento

1. Ejecutar `git status -u` y revisar el árbol completo sin asumir que todos los
   cambios pertenecen al trabajo actual.
2. Inspeccionar los diffs y agruparlos por responsabilidad. Preservar los cambios
   ajenos del usuario.
3. Preparar cada unidad mediante rutas explícitas:

   ```bash
   git add <ruta-1> <ruta-2>
   ```

   No usar staging indiscriminado.
4. Verificar el área preparada con `git status` y el diff staged antes de
   confirmar.
5. Crear el commit con un mensaje en español, en tercera persona del presente,
   específico, sin prefijos artificiales ni emojis y preferiblemente menor de 72
   caracteres:

   ```bash
   git commit -m "Añade la comparación interactiva de controladores"
   ```

6. Repetir sólo si existen otras unidades lógicas autorizadas. Terminar revisando
   `git status` y `git log -n 5 --oneline`.

No hacer push, reescribir historial ni incluir cambios adicionales sin una orden
explícita.