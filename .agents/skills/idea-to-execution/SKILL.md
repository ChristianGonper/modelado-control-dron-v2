---
name: idea-to-execution
description: Convierte una idea o necesidad en una definición suficiente, un entregable o una implementación, utilizando solo los pasos que aporten valor.
---

# Idea to Execution

Transforma una idea o necesidad en el siguiente artefacto útil sin imponer una secuencia fija cuando no sea necesaria.

## Definición

Introduce una fase de definición cuando sea útil aclarar la intención, el alcance o el resultado esperado antes de producir el entregable.

Cuando se haya creado una definición, preséntala al usuario y espera su aprobación antes de producir el siguiente artefacto o continuar con la implementación.

La definición puede ser breve o extensa según el trabajo. No tiene que existir cuando la necesidad ya esté suficientemente clara.

Conserva la definición cuando establezca un contrato o contexto que siga siendo relevante para mantener o modificar el resultado. Si solo sirvió como borrador, índice o apoyo para preparar el entregable final, puede retirarse una vez cumplida su función.

## Entregables documentales

Cuando el resultado sea un documento, investigación, propuesta u otro artefacto documental, produce el entregable adecuado una vez que su propósito esté suficientemente definido.

La definición previa, si existió, no tiene por qué conservarse si el documento final absorbe completamente su función.

## Implementación técnica

Cuando el trabajo requiera implementación técnica, crea una especificación suficientemente precisa para construir lo definido. La especificación concreta qué debe existir y cómo debe comportarse, sin convertirla en una descripción exhaustiva de la implementación. Preséntala al usuario y espera su aprobación antes de preparar el plan de implementación y las tareas.

A partir de la especificación aprobada, prepara un plan de implementación y una lista de tareas con un nivel de detalle acorde al trabajo. Organiza el plan en fases cuando ayude a comprender la ejecución y señala las fases que puedan desarrollarse en paralelo cuando sean realmente independientes.

Si durante la planificación o implementación aparece una decisión sustancial que no estaba fijada por la definición o la especificación, vuelve al usuario antes de asumirla.

Si el usuario indica que la implementación puede realizarse de forma autónoma, continúa con la ejecución y los commits necesarios sin detenerte para revisiones intermedias, manteniendo los mismos criterios de calidad y organización.

## Organización de cada unidad

Cada unidad conceptual que necesite estos artefactos vive en una carpeta propia con un nombre descriptivo de lo que se está definiendo o construyendo.

Dentro de esa carpeta utiliza nombres consistentes para los artefactos habituales, por ejemplo:

```text
pagina-inicio/
├── definition.md
├── spec.md
├── plan.md
└── tasks.md
```

No todos los archivos son obligatorios. Crea únicamente los que correspondan al trabajo.

La carpeta aporta el significado de la unidad; los nombres internos comunes facilitan reconocer la función de cada documento.

## Documentación viva

Los documentos que describen la intención, el comportamiento o el contrato vigente de una parte del proyecto se mantienen actualizados mientras sigan cumpliendo esa función.

Cuando un cambio pertenece a una unidad ya descrita, actualiza sus documentos vivos en lugar de crear una especificación nueva para cada modificación pequeña. Crea una unidad distinta cuando el nuevo trabajo represente algo conceptualmente diferente.

Incluye el contexto suficiente para reconocer cómo se materializa la unidad dentro del proyecto y dónde encontrar sus partes principales. Cuando resulte útil, referencia directamente los archivos, carpetas o documentos relevantes, sin convertir la especificación en un inventario exhaustivo.

## Cierre de la implementación

El plan y las tareas son artefactos de trabajo. Una vez completada la implementación, retíralos del estado activo cuando hayan cumplido su función y actualiza la documentación viva para que refleje el resultado actual.
