"""Versión de presentación de FIG-015: solo alabeo y desplazamiento lateral."""

from __future__ import annotations

import os
import runpy
from pathlib import Path

import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "TFG_Report" / "Figuras" / "diagramas" / "FIG-015.py"


def main() -> None:
    source = runpy.run_path(str(SOURCE), run_name="fig015_source")
    draw_plant_view = source["draw_plant_view"]
    draw_lateral_view = source["draw_lateral_view"]

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), dpi=220, gridspec_kw={"width_ratios": [1, 1.08]})
    for ax in axes:
        ax.set_aspect("equal")
        ax.axis("off")

    draw_plant_view(axes[0], xc=0.0, yc=0.0, thrust_states=["-", "+", "-", "+"], yaw_net_moment=0.0)
    axes[0].set_xlim(-2.0, 2.0)
    axes[0].set_ylim(-1.35, 1.35)
    axes[0].set_title("1 · Diferencia de empuje", fontsize=15, fontweight="bold", pad=16, color="#173b3f")

    draw_lateral_view(axes[1], xc=0.0, yc=0.1, mode="alabeo")
    axes[1].set_xlim(-1.55, 1.55)
    axes[1].set_ylim(-1.35, 1.55)
    axes[1].set_title("2 · Inclinación y componente lateral", fontsize=15, fontweight="bold", pad=16, color="#173b3f")

    fig.text(0.5, 0.015, "El empuje inclinado genera aceleración horizontal", ha="center", fontsize=14, color="#a75d25", weight="bold")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.84, bottom=0.12, wspace=0.02)

    output = Path(os.environ["FIG015_LATERAL_SVG_OUT"])
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, format="svg", transparent=True, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


if __name__ == "__main__":
    main()
