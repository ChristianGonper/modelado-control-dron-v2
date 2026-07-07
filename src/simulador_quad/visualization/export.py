from __future__ import annotations

import os
from pathlib import Path
import matplotlib.pyplot as plt

def save_figure(
    fig: plt.Figure,
    output_dir: str | os.PathLike[str],
    filename_base: str,
    formats: list[str] | None = None,
    dpi: int = 300,
) -> list[str]:
    """
    Save a Matplotlib figure in multiple formats (e.g., PDF, PNG, SVG) to the target directory.

    Args:
        fig: The Matplotlib Figure object.
        output_dir: Path to the directory where the figure will be saved.
        filename_base: Base filename without extension (e.g. 'trajectory_xy').
        formats: List of file extensions to export (e.g. ['png', 'pdf', 'svg']).
                 Defaults to ['png'].
        dpi: Dots per inch for raster formats (PNG). Defaults to 300.

    Returns:
        list[str]: Absolute paths to the generated files.
    """
    if formats is None:
        formats = ["png"]

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Strip any extension user might have passed accidentally
    filename_base = Path(filename_base).stem

    generated_paths = []
    for ext in formats:
        clean_ext = ext.strip().lower().lstrip(".")
        filename = f"{filename_base}.{clean_ext}"
        filepath = out_path / filename

        # Save options: bbox_inches="tight" ensures no labels are cut off.
        # pad_inches=0.05 gives a neat margin.
        fig.savefig(
            filepath,
            dpi=dpi,
            bbox_inches="tight",
            pad_inches=0.05,
        )
        generated_paths.append(str(filepath.resolve()))

    plt.close(fig)
    return generated_paths
