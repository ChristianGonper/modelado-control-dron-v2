from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

from simulador_quad.visualization.comparison import plot_comparison


REPO_ROOT = Path(__file__).resolve().parents[2]
PRESENTATION_DIR = Path(__file__).resolve().parents[1]
SVG_DIR = PRESENTATION_DIR / "assets" / "generated" / "svg"
MANIFEST_PATH = PRESENTATION_DIR / "assets" / "generated" / "asset_manifest.json"

PDF_ASSETS = {
    "FIG-001": REPO_ROOT / "TFG_Memoria" / "Figuras" / "diagramas" / "FIG-001.pdf",
    "FIG-003": REPO_ROOT / "TFG_Memoria" / "Figuras" / "diagramas" / "FIG-003.pdf",
    "FIG-004": REPO_ROOT / "TFG_Memoria" / "Figuras" / "diagramas" / "FIG-004.pdf",
    "FIG-005": REPO_ROOT / "TFG_Memoria" / "Figuras" / "diagramas" / "FIG-005.pdf",
    "FIG-006": REPO_ROOT / "TFG_Memoria" / "Figuras" / "diagramas" / "FIG-006.pdf",
    "FIG-008": REPO_ROOT / "TFG_Memoria" / "Figuras" / "diagramas" / "FIG-008.pdf",
    "FIG-013": REPO_ROOT / "TFG_Memoria" / "Figuras" / "diagramas" / "FIG-013.pdf",
    "FIG-015": REPO_ROOT / "TFG_Memoria" / "Figuras" / "diagramas" / "FIG-015.pdf",
}

# FIG-002 se genera con Matplotlib (no con el .tex de la memoria).
FIG002_PY = REPO_ROOT / "TFG_Memoria" / "Figuras" / "diagramas" / "FIG-002.py"

COMPARISON_CSV = REPO_ROOT / "results" / "comparison_all_runs.csv"


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


@contextmanager
def _repo_working_directory():
    previous = Path.cwd()
    os.chdir(REPO_ROOT)
    try:
        yield
    finally:
        os.chdir(previous)


def _count_embedded_raster_images(pdf_path: Path) -> int | None:
    pdfimages = shutil.which("pdfimages")
    if not pdfimages:
        return None
    result = _run([pdfimages, "-list", str(pdf_path)])
    return sum(1 for line in result.stdout.splitlines() if line.strip()[:1].isdigit())


def _convert_pdf_to_svg(pdf_path: Path, output_svg: Path) -> dict[str, object]:
    pdftocairo = shutil.which("pdftocairo")
    if not pdftocairo:
        raise RuntimeError("pdftocairo no esta disponible en PATH; no se pueden convertir PDF a SVG.")
    output_svg.parent.mkdir(parents=True, exist_ok=True)
    _run([pdftocairo, "-svg", str(pdf_path), str(output_svg)])
    return {
        "source": str(pdf_path.relative_to(REPO_ROOT)),
        "output": str(output_svg.relative_to(REPO_ROOT)),
        "method": "pdftocairo -svg",
        "embedded_raster_images": _count_embedded_raster_images(pdf_path),
    }


def _build_fig002_svg() -> dict[str, object] | None:
    """Genera FIG-002.svg desde el script Python/Matplotlib de la memoria."""
    if not FIG002_PY.exists():
        return None
    output_svg = SVG_DIR / "FIG-002.svg"
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["FIG002_SVG_OUT"] = str(output_svg)
    subprocess.run(
        ["uv", "run", "python", str(FIG002_PY)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    if not output_svg.exists():
        raise RuntimeError(f"FIG-002.py no generó el SVG esperado en {output_svg}")
    return {
        "source": str(FIG002_PY.relative_to(REPO_ROOT)),
        "output": str(output_svg.relative_to(REPO_ROOT)),
        "method": "matplotlib svg (FIG-002.py)",
    }


def _build_comparison_svgs() -> list[dict[str, object]]:
    if not COMPARISON_CSV.exists():
        return []
    with _repo_working_directory():
        result = plot_comparison(
            COMPARISON_CSV,
            SVG_DIR,
            formats=["svg"],
            trajectory_label_colors={"MLP": "#173B63", "LSTM": "#A33B4B"},
        )
    return [
        {
            "source": str(COMPARISON_CSV.relative_to(REPO_ROOT)),
            "output": str(Path(path).relative_to(REPO_ROOT)),
            "method": "matplotlib svg",
        }
        for path in result.paths
        if Path(path).suffix.lower() == ".svg"
    ]


def _postprocess_svg_transparency(svg_path: Path) -> None:
    if not svg_path.exists():
        return
    content = svg_path.read_text(encoding="utf-8")
    # Pattern to find a path that fills from (0, y) representing the figure background in matplotlib/TikZ
    pattern = r'<path[^>]*fill="rgb\(100%,\s*100%,\s*100%\)"[^>]*d="M\s*0\s+[^"]+"[^>]*/>'
    match = re.search(pattern, content)
    if match:
        new_path = match.group(0).replace('fill="rgb(100%, 100%, 100%)"', 'fill="none"').replace('fill-opacity="1"', 'fill-opacity="0"')
        new_content = content.replace(match.group(0), new_path)
        svg_path.write_text(new_content, encoding="utf-8")


def build_assets() -> dict[str, object]:
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[dict[str, object]] = []

    for asset_name, pdf_path in PDF_ASSETS.items():
        if pdf_path.exists():
            output_path = SVG_DIR / f"{asset_name}.svg"
            generated.append(_convert_pdf_to_svg(pdf_path, output_path))
            _postprocess_svg_transparency(output_path)

    fig002 = _build_fig002_svg()
    if fig002 is not None:
        generated.append(fig002)
        _postprocess_svg_transparency(REPO_ROOT / fig002["output"])

    generated.extend(_build_comparison_svgs())
    for item in generated:
        out_path = REPO_ROOT / item["output"]
        _postprocess_svg_transparency(out_path)

    manifest = {
        "policy": "Assets generados desde datos/codigo o convertidos desde PDF vectorial de la memoria; no editar salidas a mano.",
        "generated": generated,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera assets SVG para el MVP de presentacion.")
    parser.add_argument("--manifest", action="store_true", help="Imprime el manifiesto generado.")
    args = parser.parse_args()

    manifest = build_assets()
    print(f"Assets generados: {len(manifest['generated'])}")
    print(f"Manifiesto: {MANIFEST_PATH}")
    if args.manifest:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
