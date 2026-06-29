from __future__ import annotations

import contextlib
import hashlib
from typing import Any, Generator

import matplotlib as mpl
import matplotlib.pyplot as plt

# Professional color palette (Okabe-Ito inspired, colorblind friendly)
COLORS = {
    "real": "#0072B2",        # State/real trajectory (Blue)
    "reference": "#4D4D4D",   # Reference trajectory (Dark Grey)
    "pid": "#0072B2",         # PID controller (Blue)
    "mlp": "#E69F00",         # MLP network (Orange)
    "gru": "#009E73",         # GRU network (Teal/Green)
    "lstm": "#D55E00",        # LSTM network (Vermilion)
    "failure": "#CC3311",     # Failure/saturation/clipping (Red)
    "start": "#009E73",       # Start point marker (Teal/Green)
    "secondary": "#999999",   # Secondary/info/oracle (Light Grey)
}

FAMILY_COLORS = {
    "hold": "#0072B2",
    "circle": "#56B4E9",
    "lissajous": "#009E73",
    "waypoint": "#D55E00",
}

# Mapping from controller identifier to styling details (color, label, line_style)
CONTROLLER_STYLE: dict[str, dict[str, Any]] = {
    "classic_family_pid": {"color": COLORS["pid"], "label": "PID Familiar", "linestyle": "-"},
    "classic_pid_hold": {"color": FAMILY_COLORS["hold"], "label": "PID Hold", "linestyle": "-"},
    "classic_pid_circle": {"color": FAMILY_COLORS["circle"], "label": "PID Circle", "linestyle": "-"},
    "classic_pid_lissajous": {"color": FAMILY_COLORS["lissajous"], "label": "PID Lissajous", "linestyle": "-"},
    "classic_pid_waypoint": {"color": FAMILY_COLORS["waypoint"], "label": "PID Waypoint", "linestyle": "-"},
    "classic_pid_representative": {"color": COLORS["pid"], "label": "PD representativo", "linestyle": "-"},
    "outer_force_oracle": {"color": COLORS["secondary"], "label": "Oráculo Fuerza", "linestyle": "-."},
    "neural_outer_force_mlp": {"color": COLORS["mlp"], "label": "MLP Fuerza", "linestyle": "-"},
    "neural_outer_force_gru": {"color": COLORS["gru"], "label": "GRU Fuerza", "linestyle": "-"},
    "neural_outer_force_lstm": {"color": COLORS["lstm"], "label": "LSTM Fuerza", "linestyle": "-"},
    "neural_position_mlp": {"color": COLORS["mlp"], "label": "MLP Posición", "linestyle": "--"},
    "neural_position_gru": {"color": COLORS["gru"], "label": "GRU Posición", "linestyle": "--"},
    "neural_position_lstm": {"color": COLORS["lstm"], "label": "LSTM Posición", "linestyle": "--"},
    "classic_transfer_hold": {"color": "#56B4E9", "label": "PID Transf. (Hold)", "linestyle": ":"},
    "classic_transfer_circle": {"color": "#009E73", "label": "PID Transf. (Circle)", "linestyle": ":"},
    "classic_transfer_lissajous": {"color": "#CC79A7", "label": "PID Transf. (Lissa.)", "linestyle": ":"},
    "classic_transfer_waypoint": {"color": "#D55E00", "label": "PID Transf. (Wayp.)", "linestyle": ":"},
}

FALLBACK_COLORS = ["#56B4E9", "#009E73", "#CC79A7", "#D55E00", "#E69F00", "#0072B2"]


def _stable_color_index(name: str, palette_size: int) -> int:
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    return int(digest, 16) % palette_size


def get_controller_style(controller_name: str) -> dict[str, Any]:
    """Retrieve color, label, and linestyle for a controller name."""
    if controller_name in CONTROLLER_STYLE:
        return CONTROLLER_STYLE[controller_name]

    if controller_name.startswith("classic_pid_"):
        family = controller_name.replace("classic_pid_", "")
        family_color = FAMILY_COLORS.get(family, COLORS["pid"])
        return {
            "color": family_color,
            "label": f"PID {family.capitalize()}",
            "linestyle": "-",
        }

    if controller_name.startswith("classic_transfer_"):
        fam = controller_name.replace("classic_transfer_", "")
        lbl = f"PID Transf. ({fam.capitalize()})"
        c_idx = _stable_color_index(fam, len(FALLBACK_COLORS))
        return {"color": FALLBACK_COLORS[c_idx], "label": lbl, "linestyle": ":"}

    return {"color": COLORS["secondary"], "label": controller_name, "linestyle": "-"}


@contextlib.contextmanager
def use_style(profile: str = "diagnostic") -> Generator[None, None, None]:
    """
    Context manager to safely apply Matplotlib visual styles temporarily.

    Args:
        profile: The visual profile ('diagnostic', 'report', or 'report-half').
    """
    font_family = "serif"
    font_serif = ["Latin Modern Roman", "DejaVu Serif", "Computer Modern Roman", "Times New Roman", "serif"]

    base_params = {
        "font.family": font_family,
        "font.serif": font_serif,
        "text.usetex": False,
        "mathtext.fontset": "dejavuserif",
        "axes.grid": True,
        "grid.alpha": 0.15,
        "grid.linestyle": ":",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
    }

    if profile == "report":
        profile_params = {
            "figure.figsize": (6.10, 4.0),
            "font.size": 9.0,
            "axes.labelsize": 9.0,
            "legend.fontsize": 8.0,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "lines.linewidth": 1.4,
            "figure.constrained_layout.use": True,
        }
    elif profile == "report-half":
        profile_params = {
            "figure.figsize": (2.95, 2.5),
            "font.size": 9.0,
            "axes.labelsize": 9.0,
            "legend.fontsize": 8.0,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "lines.linewidth": 1.2,
            "figure.constrained_layout.use": True,
        }
    else:
        profile_params = {
            "figure.figsize": (9.0, 6.0),
            "font.size": 10.0,
            "axes.labelsize": 10.0,
            "legend.fontsize": 9.0,
            "xtick.labelsize": 9.0,
            "ytick.labelsize": 9.0,
            "lines.linewidth": 1.5,
            "figure.constrained_layout.use": False,
        }

    combined_params = {**base_params, **profile_params}

    with plt.style.context("default"):
        with mpl.rc_context(combined_params):
            yield