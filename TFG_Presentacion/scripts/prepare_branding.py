"""Prepara copias de los logos institucionales para la presentación."""

from collections import deque
from pathlib import Path
import shutil

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "TFG_Memoria" / "Figuras"
OUTPUT_DIR = ROOT / "TFG_Presentacion" / "assets" / "branding"


def remove_connected_white_background(source: Path, destination: Path) -> None:
    """Vuelve transparente solo el blanco conectado con los bordes."""
    image = Image.open(source).convert("RGBA")
    pixels = image.load()
    width, height = image.size
    visited = bytearray(width * height)
    pending: deque[tuple[int, int]] = deque()

    def is_background(x: int, y: int) -> bool:
        red, green, blue, _ = pixels[x, y]
        return min(red, green, blue) >= 238 and max(red, green, blue) - min(red, green, blue) <= 10

    def enqueue(x: int, y: int) -> None:
        index = y * width + x
        if not visited[index] and is_background(x, y):
            visited[index] = 1
            pending.append((x, y))

    for x in range(width):
        enqueue(x, 0)
        enqueue(x, height - 1)
    for y in range(height):
        enqueue(0, y)
        enqueue(width - 1, y)

    while pending:
        x, y = pending.popleft()
        red, green, blue, _ = pixels[x, y]
        # Conserva una transición suave en el contorno procedente del JPEG.
        alpha = min(255, (255 - min(red, green, blue)) * 16)
        pixels[x, y] = (red, green, blue, alpha)
        if x:
            enqueue(x - 1, y)
        if x + 1 < width:
            enqueue(x + 1, y)
        if y:
            enqueue(x, y - 1)
        if y + 1 < height:
            enqueue(x, y + 1)

    alpha = image.getchannel("A")
    bounds = alpha.getbbox()
    if bounds:
        padding = 12
        left, top, right, bottom = bounds
        bounds = (
            max(0, left - padding),
            max(0, top - padding),
            min(width, right + padding),
            min(height, bottom + padding),
        )
        image = image.crop(bounds)

    image.save(destination, optimize=True)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    remove_connected_white_background(
        SOURCE_DIR / "ule.jpg",
        OUTPUT_DIR / "ule-transparent.png",
    )
    shutil.copy2(
        SOURCE_DIR / "escudo-ingenierias.png",
        OUTPUT_DIR / "escudo-ingenierias.png",
    )


if __name__ == "__main__":
    main()
