# Estilo de commits

## Asuntos

Usar preferentemente:

- una frase breve en espanol;
- verbo en presente, tercera persona;
- mayuscula inicial;
- intencion y resultado reconocibles;
- sin prefijo, ambito entre parentesis ni punto final.

Ejemplos acordes al historial reciente:

- `Alinea la documentacion con la evidencia final`
- `Hace reproducible el entrenamiento neuronal`
- `Consolida la evidencia experimental comparable`
- `Generaliza la transferencia de PID congelados`
- `Endurece la generacion atomica de datasets`
- `Documenta el flujo de tuneo PID base`

Evitar:

- `feat: add controller`
- `docs(simulador): update docs`
- `chore: miscellaneous changes`
- `Cambios varios`
- asuntos que enumeren muchos cambios independientes.

## Tamano y agrupacion

Un commit pequeno es una unidad funcional, no necesariamente un numero minimo de lineas o archivos.

Mantener juntos:

- comportamiento y pruebas que lo validan;
- cambio de interfaz y adaptaciones indispensables;
- comportamiento y documentacion viva que debe actualizarse por las reglas del repositorio.

Separar:

- correcciones o funciones independientes;
- limpieza no necesaria para el cambio principal;
- resultados experimentales distintos de la herramienta que los genera, cuando ambos puedan revisarse por separado;
- cambios de memoria no relacionados con el cambio funcional.

Antes de confirmar, poder resumir el commit con una sola frase sin usar `y` para unir dos intenciones independientes.
