from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.html_lang: str | None = None
        self.title = ""
        self._in_title = False
        self.links: list[tuple[str, str]] = []
        self.meta: dict[str, str] = {}
        self.alternates: dict[str, str] = {}
        self.pdf_objects: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "html":
            self.html_lang = values.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta" and values.get("name"):
            self.meta[values["name"]] = values.get("content", "")
        elif tag == "link":
            rel = values.get("rel")
            href = values.get("href", "")
            if rel == "alternate" and values.get("hreflang"):
                self.alternates[values["hreflang"]] = href
            elif rel == "canonical":
                self.links.append(("canonical", href))
            elif rel == "stylesheet":
                self.links.append(("stylesheet", href))
        elif tag == "a" and values.get("href"):
            self.links.append(("anchor", values["href"]))
        elif tag == "object" and values.get("type") == "application/pdf":
            self.pdf_objects.append(values.get("data", ""))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def local_target(page: Path, href: str) -> Path | None:
    clean, _ = urldefrag(href)
    if not clean or clean.startswith(("http://", "https://", "mailto:")):
        return None
    target = (page.parent / clean).resolve()
    if clean.endswith("/"):
        target /= "index.html"
    return target


def validate_page(relative: str, lang: str, pdf_name: str) -> list[str]:
    page = SITE / relative
    parser = PageParser()
    parser.feed(page.read_text(encoding="utf-8"))
    errors: list[str] = []

    if parser.html_lang != lang:
        errors.append(f"{relative}: expected lang={lang!r}")
    if len(parser.title.strip()) < 30:
        errors.append(f"{relative}: title is missing or too short")
    if len(parser.meta.get("description", "")) < 80:
        errors.append(f"{relative}: meta description is missing or too short")
    if set(parser.alternates) != {"es", "en", "x-default"}:
        errors.append(f"{relative}: incomplete hreflang set")
    if len(parser.pdf_objects) != 1 or pdf_name not in parser.pdf_objects[0]:
        errors.append(f"{relative}: expected embedded PDF {pdf_name}")

    for kind, href in parser.links:
        target = local_target(page, href)
        if target is not None and "assets/reports" not in target.as_posix() and not target.exists():
            errors.append(f"{relative}: broken {kind} link {href!r}")
    return errors


def main() -> int:
    required = [
        SITE / "index.html",
        SITE / "en" / "index.html",
        SITE / "assets" / "styles.css",
        SITE / "robots.txt",
        SITE / "sitemap.xml",
        SITE / ".nojekyll",
    ]
    errors = [f"missing required file: {path.relative_to(ROOT)}" for path in required if not path.exists()]
    if not errors:
        errors.extend(validate_page("index.html", "es", "TFG_Memoria_es.pdf"))
        errors.extend(validate_page("en/index.html", "en", "TFG_Report_en.pdf"))

    if errors:
        print("GitHub Pages validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("GitHub Pages validation passed for Spanish and English pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
