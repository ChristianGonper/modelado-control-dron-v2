# Presentación de la defensa (TFG)

Presentación oral del TFG en formato programable: **Quarto + Reveal.js**.
El artefacto principal es el **HTML** (`deck.html`); el **PDF** (`deck.pdf`) es un respaldo para impresión o entrega.

## Qué es este stack

| Pieza | Rol |
| --- | --- |
| **Quarto** | Herramienta que convierte el fuente `deck.qmd` en una presentación HTML (y puede integrar código, ecuaciones y estilo). |
| **Reveal.js** | Motor de diapositivas en el navegador (navegación, fragmentos, notas del presentador, etc.). Quarto lo empaqueta al renderizar. |
| **Decktape** | Utilidad CLI (vía `npx`) que abre el HTML Reveal.js y exporta un PDF página a página. |

No hace falta un servidor web externo: todo se genera y se abre en local.

## Estructura mínima

```text
TFG_Presentacion/
├── deck.qmd          # Fuente de la presentación (editar aquí)
├── _quarto.yml       # Opciones globales de Quarto / Reveal.js
├── theme.scss        # Tema visual
├── deck.html         # Salida HTML (generada)
├── deck.pdf          # Salida PDF de respaldo (generada)
├── assets/generated/ # Figuras SVG ya generadas
└── scripts/          # Pipeline de regeneración de assets
```

## Requisitos

1. **Quarto** (obligatorio para renderizar el HTML).

   En Windows:

   ```powershell
   winget install --id Posit.Quarto --exact
   ```

   Comprueba la instalación:

   ```powershell
   quarto --version
   ```

2. **Node.js** (solo si vas a generar el PDF con Decktape; aporta `npx`).

   Comprueba:

   ```powershell
   node --version
   npx --version
   ```

No hace falta Python ni el entorno del simulador solo para ver o regenerar el deck, salvo que quieras regenerar los assets con `scripts/build_assets.py`.

## Generar el HTML

Desde esta carpeta:

```powershell
cd TFG_Presentacion
quarto render deck.qmd
```

Eso produce (o actualiza) `deck.html`. Con la configuración actual (`embed-resources: true`), el HTML es autocontenido y se puede abrir con doble clic o copiar a otro equipo.

### Vista previa mientras editas

```powershell
quarto preview deck.qmd
```

Abre el navegador y recarga al guardar cambios en `deck.qmd` o en el tema.

### Abrir la presentación

Abre `deck.html` en un navegador moderno (Chrome, Edge, Firefox).

Atajos útiles de Reveal.js:

- **← / →** o **espacio**: avanzar / retroceder
- **F**: pantalla completa
- **S**: vista de presentador (notas del orador, si las hay)
- **Esc** / **O**: vista general de diapositivas

## Generar el PDF de respaldo

Primero genera el HTML; después:

```powershell
cd TFG_Presentacion
npx -y decktape reveal deck.html deck.pdf
```

- `npx -y` descarga Decktape si no está instalado de forma global.
- El PDF resultante es `deck.pdf` en la misma carpeta.
- Es un volcado visual del deck: útil como respaldo, no sustituye la defensa en HTML (fragmentos, ritmo y notas se aprovechan mejor en el navegador).

## Flujo recomendado

```powershell
cd TFG_Presentacion

# 1. Editar deck.qmd (y theme.scss si hace falta)
# 2. Renderizar HTML
quarto render deck.qmd

# 3. Revisar en el navegador
start deck.html   # Windows

# 4. PDF de respaldo (opcional pero recomendado antes de la defensa)
npx -y decktape reveal deck.html deck.pdf
```

## Notas

- **Fuente de verdad del contenido de las diapositivas**: `deck.qmd`. No edites a mano `deck.html` ni `deck.pdf`.
- **Figuras**: viven en `assets/generated/`. No las retoces a mano; regenerarlas es responsabilidad del script de assets si cambian datos o figuras de la memoria.
- **Memoria LaTeX** (`../TFG_Memoria/`): se usa solo como fuente cerrada de narrativa y figuras; no es parte del pipeline de Quarto.
