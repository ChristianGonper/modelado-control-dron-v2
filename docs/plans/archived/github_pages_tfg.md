# Especificación: página bilingüe del TFG en GitHub Pages

## Objetivo

Publicar una página web académica, sencilla y bilingüe que presente el simulador
6DOF desarrollado por Christian González Pérez, facilite encontrar el proyecto
mediante búsquedas relacionadas con el TFG y permita consultar los informes en
español e inglés sin incorporarlos al historial Git.

La página debe resultar cuidada y personal: composición sobria, tipografía
legible, textos concretos y ausencia de recursos visuales generados o efectos
decorativos innecesarios.

## Stack técnico

- HTML semántico estático.
- CSS propio, sin frameworks ni dependencias de cliente.
- JavaScript mínimo, solo si mejora el visor PDF o la navegación.
- GitHub Actions y GitHub Pages para publicación.
- PDFs procedentes de la release `v1.0.0` durante el despliegue.

## Comandos

```powershell
# Servidor local
uv run python -m http.server 8000 --directory site

# Comprobaciones del repositorio
uv run pytest
git diff --check

# Validación de enlaces internos y HTML
uv run python tools/validate_github_pages.py
```

## Estructura

```text
site/
  index.html          Portada en español
  en/index.html       Portada en inglés
  assets/styles.css   Estilos compartidos
  assets/site.js      Mejora progresiva opcional
.github/workflows/
  pages.yml           Descarga de PDFs y despliegue
tools/
  validate_github_pages.py
```

Los PDFs existirán en `site/assets/reports/` únicamente dentro del artefacto de
despliegue. El workflow los descargará desde la release y no los confirmará en
Git.

## Estilo de código

HTML semántico, clases breves y nombres descriptivos. El contenido debe seguir
siendo usable sin JavaScript.

```html
<nav class="language-nav" aria-label="Idioma">
  <a href="./" lang="es" aria-current="page">Español</a>
  <a href="./en/" lang="en">English</a>
</nav>
```

- Indentación de dos espacios en HTML, CSS y JavaScript.
- Variables CSS para color, espaciado y tipografía.
- Sin estilos en línea ni dependencias remotas imprescindibles.
- Textos redactados específicamente para cada idioma.

## Estrategia de pruebas

- Validador local para comprobar archivos requeridos, enlaces internos,
  metadatos SEO, idiomas y referencias a los dos PDFs.
- `git diff --check` para formato.
- Suite `pytest` del proyecto para detectar regresiones.
- Revisión visual local en anchura de escritorio y móvil.
- Revisión final de las dos rutas publicadas y de ambos visores PDF.

## Límites

- Siempre: diseño responsive, navegación por teclado, contraste suficiente,
  metadatos SEO, enlaces alternativos para abrir y descargar cada PDF.
- Consultar antes: dominio propio, analítica, formularios, cambios de identidad
  institucional o inclusión de contenido de la defensa.
- Nunca: guardar los PDFs compilados en Git, usar seguimiento de usuarios,
  cargar frameworks innecesarios o afirmar resultados no respaldados.

## Criterios de éxito

- La portada española y `/en/` son accesibles públicamente en GitHub Pages.
- Cada ruta incluye título, descripción, URL canónica y alternancia `hreflang`.
- El nombre completo, TFG, Universidad de León y el tema técnico aparecen de
  manera natural, sin repetición artificial de palabras clave.
- Cada idioma muestra el PDF correspondiente dentro de la página cuando el
  navegador lo permite y ofrece apertura directa como alternativa.
- Los informes se descargan desde la release durante el despliegue y no aparecen
  en el historial Git.
- La página funciona en escritorio y móvil y mantiene su contenido sin
  JavaScript.
- El README y el About incorporan una identificación académica breve y enlazan a
  la web sin desplazar el foco técnico del repositorio.

## Decisiones validadas

- Se usa la URL gratuita de GitHub Pages, sin dominio personalizado.
- Español es el idioma principal y el inglés se publica bajo `/en/`.
- Cada idioma incrusta únicamente su informe correspondiente.
- La identidad visual es académica y neutral, sin reutilizar la presentación de
  la defensa.

Validado por el autor el 11 de julio de 2026.
