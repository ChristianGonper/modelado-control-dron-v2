from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .common import as_array, load_json
from .export import save_figure
from .style import COLORS, get_controller_style, use_style

COMPARISON_JITTER_SEED = 42
MEMORY_PRIMARY_CONTROLLERS = (
    "classic_pid_representative",
    "neural_outer_force_mlp",
    "neural_outer_force_gru",
    "neural_outer_force_lstm",
)
OOD_FAMILY_ORDER = ("lemniscate", "lissajous", "composite", "waypoint")
DEFAULT_REPRESENTATIVE_OOD_TRAJECTORY: tuple[str, tuple[tuple[str, str], ...]] = (
    "lemniscate_fast_center_yaw",
    (
        ("MLP", "data/neural_ood/battery_v1/results/lemniscate_fast_center_yaw_neural_mlp/telemetry.json"),
        ("LSTM", "data/neural_ood/battery_v1/results/lemniscate_fast_center_yaw_neural_lstm/telemetry.json"),
    ),
)
PRIMARY_CONTROLLER_PREFIXES = (
    "classic_pid_",
    "neural_outer_force_",
    "neural_position_",
    "outer_force_oracle",
)

ALL_FIGURE_IDS = (
    "res_pid_transfer_matrix",
    "res_id_rmse_family",
    "res_ood_rmse_family",
    "res_ood_scenario_matrix",
    "res_ood_termination_summary",
    "res_trajectory_lemniscate_mlp_lstm",
    "res_protections_ood",
    "atlas_trayectorias_id",
    "atlas_trayectorias_ood",
    "atlas_trayectoria_helix_3d",
)


@dataclass(frozen=True)
class ComparisonPlotResult:
    paths: list[str]
    generated: tuple[str, ...] = ()
    skipped: tuple[tuple[str, str], ...] = ()
    warnings: tuple[str, ...] = ()


def _normalize_controller(row: pd.Series) -> str:
    ctrl = str(row["controller"])
    if ctrl.startswith("classic_transfer_"):
        return ctrl.replace("classic_transfer_", "classic_pid_", 1)
    return ctrl


def _prepare_comparison_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    prepared = df.copy()
    warnings: list[str] = []

    ambiguous_mask = prepared["controller"].astype(str) == "classic_family_pid"
    if ambiguous_mask.any():
        dropped = int(ambiguous_mask.sum())
        warnings.append(
            f"Omitidas {dropped} filas con classic_family_pid: el PID real no puede inferirse con seguridad."
        )
        prepared = prepared.loc[~ambiguous_mask].copy()

    prepared["controller"] = prepared.apply(_normalize_controller, axis=1)
    return prepared, warnings


def _is_primary_controller(controller: str) -> bool:
    if controller == "outer_force_oracle":
        return True
    return any(
        controller.startswith(prefix)
        for prefix in PRIMARY_CONTROLLER_PREFIXES
        if prefix != "outer_force_oracle"
    )


def _has_mission_success_column(frame: pd.DataFrame) -> bool:
    return "mission_success" in frame.columns or "success" in frame.columns


def _mission_success_series(frame: pd.DataFrame, warnings: list[str] | None = None) -> pd.Series:
    if "mission_success" in frame.columns:
        return frame["mission_success"].astype(float)
    if "success" in frame.columns:
        if warnings is not None:
            fallback_msg = (
                "Columna mission_success ausente; se usa success como proxy de éxito de misión."
            )
            if fallback_msg not in warnings:
                warnings.append(fallback_msg)
        return frame["success"].astype(float)
    return pd.Series(dtype=float)


def _title_from_id(value: str) -> str:
    words = str(value).replace("_", " ").split()
    small_words = {"id", "ood", "pd", "mlp", "gru", "lstm"}
    return " ".join(word.upper() if word.lower() in small_words else word.capitalize() for word in words)


def _short_scenario_label(scenario_id: str) -> str:
    label = str(scenario_id).replace("_outer_expert", "")
    for suffix in (
        "_neural_mlp",
        "_neural_gru",
        "_neural_lstm",
        "_with_pid_hold",
        "_with_pid_circle",
        "_with_pid_lissajous",
        "_with_pid_waypoint",
    ):
        label = label.replace(suffix, "")
    return label.replace("_", " ")


def _ordered_categories(values: pd.Series, preferred: Sequence[str]) -> list[str]:
    present = [str(v) for v in values.dropna().unique()]
    ordered = [v for v in preferred if v in present]
    ordered.extend(sorted(v for v in present if v not in ordered))
    return ordered


def _controller_labels(controllers: Sequence[str]) -> list[str]:
    short = {
        "classic_pid_representative": "PD rep.",
        "neural_outer_force_mlp": "MLP",
        "neural_outer_force_gru": "GRU",
        "neural_outer_force_lstm": "LSTM",
    }
    return [short.get(str(ctrl), get_controller_style(str(ctrl))["label"]) for ctrl in controllers]


def _termination_class(reason: str) -> str:
    reason_l = str(reason).lower()
    if "completed" in reason_l:
        return "Completada"
    if "attitude" in reason_l or "ángulo" in reason_l or "angle" in reason_l:
        return "Actitud"
    if "saturation" in reason_l:
        return "Saturación"
    if "time limit" in reason_l or "límite" in reason_l:
        return "Tiempo"
    return "Otra"


def _load_trajectory_series(path: Path, label: str) -> tuple[str, np.ndarray, np.ndarray, np.ndarray] | None:
    if not path.exists():
        return None
    telemetry = load_json(path)
    if not telemetry:
        return None
    time_s = as_array(telemetry, "time_s")
    position_W_m = as_array(telemetry, "state", "position_W_m")
    reference_W_m = as_array(telemetry, "reference", "position_W_m")
    if time_s is None or position_W_m is None or reference_W_m is None:
        return None
    return label, time_s, position_W_m, reference_W_m


def _plot_xy_panel(ax, series: tuple[str, np.ndarray, np.ndarray, np.ndarray], *, title: str) -> None:
    _, _, position_W_m, reference_W_m = series
    ax.plot(
        reference_W_m[:, 0],
        reference_W_m[:, 1],
        "--",
        color=COLORS["reference"],
        linewidth=1.0,
        label="Referencia",
    )
    ax.plot(position_W_m[:, 0], position_W_m[:, 1], color=COLORS["real"], linewidth=1.2, label="Seguimiento")
    ax.scatter(position_W_m[0, 0], position_W_m[0, 1], color=COLORS["start"], s=18, zorder=4)
    ax.scatter(position_W_m[-1, 0], position_W_m[-1, 1], color=COLORS["failure"], s=18, zorder=4)
    ax.set_title(title, fontsize=8)
    ax.set_xlabel("Este [m]")
    ax.set_ylabel("Norte [m]")
    ax.axis("equal")
    x_span = float(np.ptp(np.r_[position_W_m[:, 0], reference_W_m[:, 0]]))
    y_span = float(np.ptp(np.r_[position_W_m[:, 1], reference_W_m[:, 1]]))
    if x_span < 1e-3 and y_span < 1e-3:
        x0 = float(np.mean(reference_W_m[:, 0]))
        y0 = float(np.mean(reference_W_m[:, 1]))
        ax.set_xlim(x0 - 0.5, x0 + 0.5)
        ax.set_ylim(y0 - 0.5, y0 + 0.5)


def _default_trajectory_paths() -> dict[str, Path]:
    return {
        "Hold": Path("data/classic_dataset/v1/results/hold/hold_g01_P0_nominal_s1042/telemetry.json"),
        "Circle": Path("data/classic_dataset/v1/results/circle/circle_g01_P0_nominal_s1060/telemetry.json"),
        "Lissajous": Path("data/classic_dataset/v1/results/lissajous/lissajous_g01_P0_nominal_s1108/telemetry.json"),
        "Waypoint": Path("data/classic_dataset/v1/results/waypoint/waypoint_g01_P0_nominal_s1156/telemetry.json"),
        "Lemniscate": Path("data/neural_ood/battery_v1/results/lemniscate_fast_center_yaw_neural_mlp/telemetry.json"),
        "Lissajous 3D": Path("data/neural_ood/battery_v1/results/lissajous_3d_speedy_neural_mlp/telemetry.json"),
        "Composite": Path("data/neural_ood/battery_v1/results/composite_circle_to_lemniscate_neural_gru/telemetry.json"),
        "Helix": Path("data/neural_ood/battery_v1/results/helix_ascending_fast_neural_mlp/telemetry.json"),
    }


def _memory_controller_list(df: pd.DataFrame, split: str) -> list[str]:
    available = set(df.loc[df["split"] == split, "controller"].astype(str))
    return [ctrl for ctrl in MEMORY_PRIMARY_CONTROLLERS if ctrl in available]


def _grouped_rmse_bars(
    ax,
    frame: pd.DataFrame,
    *,
    category_col: str,
    categories: list[str],
    controllers: list[str],
) -> None:
    x_coords = np.arange(len(categories))
    width = 0.16
    for idx, ctrl in enumerate(controllers):
        ctrl_data = frame[frame["controller"] == ctrl]
        means: list[float] = []
        valid_x: list[float] = []
        for c_idx, category in enumerate(categories):
            subset = ctrl_data[ctrl_data[category_col] == category]["position_rmse_m"].dropna()
            if subset.empty:
                continue
            means.append(float(subset.mean()))
            valid_x.append(c_idx + (idx - (len(controllers) - 1) / 2.0) * width)
        if means:
            style = get_controller_style(ctrl)
            ax.bar(
                valid_x,
                means,
                width=width * 0.9,
                label=style["label"],
                color=style["color"],
                alpha=0.88,
            )
    ax.set_xticks(x_coords)
    ax.set_xticklabels([c.capitalize() for c in categories], rotation=15)
    ax.set_ylabel("RMSE posición medio [m]")


def _resolve_trajectory_sources(
    trajectory_telemetry: Sequence[tuple[str, str | os.PathLike[str]]] | None,
) -> tuple[str, list[tuple[str, Path]]]:
    if trajectory_telemetry:
        scenario_id = DEFAULT_REPRESENTATIVE_OOD_TRAJECTORY[0]
        sources = [(label, Path(path)) for label, path in trajectory_telemetry]
        return scenario_id, sources
    scenario_id, default_sources = DEFAULT_REPRESENTATIVE_OOD_TRAJECTORY
    return scenario_id, [(label, Path(path)) for label, path in default_sources]


def _plot_res_id_rmse_family(df: pd.DataFrame, output_dir: Path, formats: list[str] | None) -> list[str]:
    frame = df[(df["split"] == "test") & df["controller"].isin(MEMORY_PRIMARY_CONTROLLERS)].copy()
    if frame.empty or "family" not in frame.columns or "position_rmse_m" not in frame.columns:
        return []
    families = _ordered_categories(frame["family"], ("hold", "circle", "lissajous", "waypoint"))
    controllers = _memory_controller_list(frame, "test")
    if not families or not controllers:
        return []

    fig, ax = plt.subplots(figsize=(6.3, 3.5))
    _grouped_rmse_bars(ax, frame, category_col="family", categories=families, controllers=controllers)
    ax.set_xlabel("Familia evaluada en test")
    ax.set_ylim(bottom=0)
    _legend_outside(ax, ncol=2)
    return save_figure(fig, output_dir, "res_id_rmse_family", formats)


def _plot_res_ood_rmse_family(df: pd.DataFrame, output_dir: Path, formats: list[str] | None) -> list[str]:
    frame = df[(df["split"] == "ood") & df["controller"].isin(MEMORY_PRIMARY_CONTROLLERS)].copy()
    if frame.empty or "family" not in frame.columns or "position_rmse_m" not in frame.columns:
        return []
    families = _ordered_categories(frame["family"], OOD_FAMILY_ORDER)
    controllers = _memory_controller_list(frame, "ood")
    if not families or not controllers:
        return []

    fig, ax = plt.subplots(figsize=(6.3, 3.6))
    _grouped_rmse_bars(ax, frame, category_col="family", categories=families, controllers=controllers)
    ax.set_xlabel("Familia fuera de distribución")
    ax.set_ylim(bottom=0)
    _legend_outside(ax, ncol=2)
    return save_figure(fig, output_dir, "res_ood_rmse_family", formats)


def _plot_res_pid_transfer_matrix(pid_df: pd.DataFrame, output_dir: Path, formats: list[str] | None) -> list[str]:
    if pid_df.empty or "family" not in pid_df.columns or "position_rmse_m" not in pid_df.columns:
        return []
    pid_df = pid_df.copy()
    pid_df["tuned_family"] = pid_df["controller"].str.replace("classic_pid_", "", regex=False)
    families = [f for f in ("hold", "circle", "lissajous", "waypoint") if f in set(pid_df["family"]) or f in set(pid_df["tuned_family"])]
    if len(families) < 2:
        return []

    matrix = np.full((len(families), len(families)), np.nan)
    for r_idx, tuned in enumerate(families):
        for c_idx, tested in enumerate(families):
            subset = pid_df[(pid_df["tuned_family"] == tuned) & (pid_df["family"] == tested)]
            if not subset.empty:
                matrix[r_idx, c_idx] = float(subset["position_rmse_m"].mean())

    fig, ax = plt.subplots(figsize=(5.5, 4.4))
    cmap = plt.get_cmap("cividis_r")
    image = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=np.nanmin(matrix), vmax=np.nanmax(matrix))
    fig.colorbar(image, ax=ax, label="RMSE medio [m]", fraction=0.046, pad=0.04)
    ax.set_xticks(np.arange(len(families)))
    ax.set_xticklabels([_title_from_id(f) for f in families])
    ax.set_yticks(np.arange(len(families)))
    ax.set_yticklabels([_title_from_id(f) for f in families])
    ax.set_xlabel("Familia evaluada")
    ax.set_ylabel("PD sintonizado para")
    for idx in range(len(families)):
        ax.add_patch(plt.Rectangle((idx - 0.5, idx - 0.5), 1, 1, fill=False, edgecolor="#F2F2F2", linewidth=2.0))
    threshold = float(np.nanpercentile(matrix, 55))
    for r in range(len(families)):
        for c in range(len(families)):
            val = matrix[r, c]
            if not np.isnan(val):
                ax.text(
                    c,
                    r,
                    f"{val:.3f}",
                    ha="center",
                    va="center",
                    color="white" if val > threshold else "#222222",
                    fontweight="bold" if r == c else "normal",
                )
    return save_figure(fig, output_dir, "res_pid_transfer_matrix", formats)


def _plot_res_ood_scenario_matrix(df: pd.DataFrame, output_dir: Path, formats: list[str] | None) -> list[str]:
    frame = df[(df["split"] == "ood") & df["controller"].isin(MEMORY_PRIMARY_CONTROLLERS)].copy()
    required = {"scenario_id", "controller", "position_rmse_m"}
    if frame.empty or not required.issubset(frame.columns):
        return []
    controllers = _memory_controller_list(frame, "ood")
    scenario_order = (
        frame.groupby("scenario_id")["position_rmse_m"]
        .mean()
        .sort_values()
        .index.astype(str)
        .tolist()
    )
    matrix = np.full((len(scenario_order), len(controllers)), np.nan)
    success = np.full((len(scenario_order), len(controllers)), np.nan)
    for r_idx, scenario in enumerate(scenario_order):
        for c_idx, ctrl in enumerate(controllers):
            subset = frame[(frame["scenario_id"].astype(str) == scenario) & (frame["controller"] == ctrl)]
            if not subset.empty:
                matrix[r_idx, c_idx] = float(subset["position_rmse_m"].mean())
                if "mission_success" in subset.columns:
                    success[r_idx, c_idx] = float(subset["mission_success"].mean())

    fig_height = max(4.8, 0.34 * len(scenario_order) + 1.2)
    fig, ax = plt.subplots(figsize=(6.4, fig_height))
    cmap = plt.get_cmap("viridis")
    vmin = 0.0
    vmax = float(np.nanpercentile(matrix, 95))
    image = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=vmin, vmax=vmax)
    fig.colorbar(image, ax=ax, label="RMSE [m]", fraction=0.046, pad=0.04)
    ax.set_xticks(np.arange(len(controllers)))
    ax.set_xticklabels(_controller_labels(controllers), rotation=0)
    ax.set_yticks(np.arange(len(scenario_order)))
    ax.set_yticklabels([_short_scenario_label(s) for s in scenario_order], fontsize=7)
    ax.set_xlabel("Controlador")
    ax.set_ylabel("Escenario OOD")
    for r in range(len(scenario_order)):
        for c in range(len(controllers)):
            val = matrix[r, c]
            if np.isnan(val):
                continue
            failed = not np.isnan(success[r, c]) and success[r, c] < 0.5
            rgba = cmap((val - vmin) / max(vmax - vmin, 1e-9))
            luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
            text_color = "white" if luminance < 0.48 else "#111111"
            ax.text(
                c,
                r,
                f"{val:.2f}" + ("*" if failed else ""),
                ha="center",
                va="center",
                fontsize=7,
                color=text_color,
            )
    return save_figure(fig, output_dir, "res_ood_scenario_matrix", formats)


def _plot_res_ood_termination_summary(df: pd.DataFrame, output_dir: Path, formats: list[str] | None) -> list[str]:
    frame = df[(df["split"] == "ood") & df["controller"].isin(MEMORY_PRIMARY_CONTROLLERS)].copy()
    if frame.empty or "termination_reason" not in frame.columns:
        return []
    frame["termination_class"] = frame["termination_reason"].map(_termination_class)
    classes = ["Completada", "Tiempo", "Actitud", "Saturación", "Otra"]
    controllers = _memory_controller_list(frame, "ood")
    counts = (
        frame.groupby(["controller", "termination_class"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=controllers, columns=classes, fill_value=0)
    )
    colors = {
        "Completada": COLORS["gru"],
        "Tiempo": "#7A869A",
        "Actitud": COLORS["failure"],
        "Saturación": COLORS["mlp"],
        "Otra": COLORS["secondary"],
    }
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    bottom = np.zeros(len(controllers))
    x = np.arange(len(controllers))
    for cls in classes:
        values = counts[cls].to_numpy(dtype=float)
        if np.any(values):
            ax.bar(x, values, bottom=bottom, label=cls, color=colors[cls], alpha=0.88)
            bottom += values
    ax.set_xticks(x)
    ax.set_xticklabels(_controller_labels(controllers), rotation=18, ha="right")
    ax.set_ylabel("Número de escenarios OOD")
    ax.set_xlabel("Controlador")
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.24),
        ncol=3,
        fontsize=7,
        frameon=False,
    )
    return save_figure(fig, output_dir, "res_ood_termination_summary", formats)


def _plot_res_protections_ood(df: pd.DataFrame, output_dir: Path, formats: list[str] | None) -> list[str]:
    frame = df[(df["split"] == "ood") & df["controller"].isin(MEMORY_PRIMARY_CONTROLLERS)].copy()
    metrics = [
        ("degradation_percentage", "Degradación mixer"),
        ("force_norm_clip_percentage", "Clip fuerza"),
        ("force_tilt_clip_percentage", "Clip inclinación"),
        ("saturation_percentage", "Saturación actuadores"),
    ]
    metrics = [(col, label) for col, label in metrics if col in frame.columns and frame[col].notna().any()]
    if frame.empty or not metrics:
        return []
    controllers = _memory_controller_list(frame, "ood")
    y = np.arange(len(controllers))
    height = 0.18
    palette = ["#6B7280", "#0072B2", "#009E73", "#D55E00"]
    fig, ax = plt.subplots(figsize=(6.1, 3.4))
    for idx, (column, label) in enumerate(metrics):
        values = [float(frame[frame["controller"] == ctrl][column].mean()) for ctrl in controllers]
        offsets = y + (idx - (len(metrics) - 1) / 2.0) * height
        ax.barh(offsets, values, height=height * 0.9, label=label, color=palette[idx % len(palette)], alpha=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels(_controller_labels(controllers))
    ax.set_xlabel("Porcentaje medio en OOD [%]")
    _legend_outside(ax, ncol=1)
    return save_figure(fig, output_dir, "res_protections_ood", formats)


def _plot_res_trajectory_lemniscate(
    output_dir: Path,
    formats: list[str] | None,
    *,
    trajectory_telemetry: Sequence[tuple[str, str | os.PathLike[str]]] | None = None,
) -> tuple[list[str], str | None]:
    paths = _resolve_trajectory_sources(trajectory_telemetry)[1]
    series = [_load_trajectory_series(Path(path), label) for label, path in paths]
    series = [item for item in series if item is not None]
    if not series:
        return [], "telemetría ausente o incompleta"
    label_colors = {"MLP": COLORS["mlp"], "LSTM": COLORS["lstm"], "GRU": COLORS["gru"]}
    fig, axes = plt.subplots(2, 1, figsize=(6.2, 5.0))
    ref = series[0][3]
    axes[0].plot(ref[:, 0], ref[:, 1], "--", color=COLORS["reference"], linewidth=1.1, label="Referencia")
    for label, _, position_W_m, _ in series:
        axes[0].plot(position_W_m[:, 0], position_W_m[:, 1], color=label_colors.get(label, COLORS["secondary"]), label=label, linewidth=1.2)
    axes[0].axis("equal")
    axes[0].set_xlabel("Este [m]")
    axes[0].set_ylabel("Norte [m]")
    axes[0].legend(loc="upper right", fontsize=7)
    for label, time_s, position_W_m, reference_W_m in series:
        error = np.linalg.norm(reference_W_m - position_W_m, axis=1)
        axes[1].plot(time_s, error, color=label_colors.get(label, COLORS["secondary"]), label=label, linewidth=1.2)
    axes[1].set_xlabel("Tiempo [s]")
    axes[1].set_ylabel("Error de posición [m]")
    axes[1].legend(loc="upper left", fontsize=7)
    return save_figure(fig, output_dir, "res_trajectory_lemniscate_mlp_lstm", formats), None


def _plot_atlas_trajectories(output_dir: Path, formats: list[str] | None) -> tuple[list[str], list[tuple[str, str]]]:
    generated: list[str] = []
    skipped: list[tuple[str, str]] = []
    paths = _default_trajectory_paths()

    id_items = [(name, paths[name]) for name in ("Hold", "Circle", "Lissajous", "Waypoint")]
    ood_items = [(name, paths[name]) for name in ("Lemniscate", "Lissajous 3D", "Composite", "Helix")]
    for figure_id, items in (("atlas_trayectorias_id", id_items), ("atlas_trayectorias_ood", ood_items)):
        loaded = [(name, _load_trajectory_series(path, name)) for name, path in items]
        loaded = [(name, item) for name, item in loaded if item is not None]
        if not loaded:
            skipped.append((figure_id, "telemetrías ausentes"))
            continue
        fig, axes = plt.subplots(2, 2, figsize=(6.4, 5.0))
        for ax, (name, item) in zip(axes.flat, loaded):
            _plot_xy_panel(ax, item, title=name)
        for ax in axes.flat[len(loaded):]:
            ax.axis("off")
        handles, labels = axes.flat[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper center", ncol=2, fontsize=7)
        generated.extend(save_figure(fig, output_dir, figure_id, formats))
        plt.close(fig)

    helix = _load_trajectory_series(paths["Helix"], "Helix")
    if helix is None:
        skipped.append(("atlas_trayectoria_helix_3d", "telemetría ausente"))
    else:
        _, _, position_W_m, reference_W_m = helix
        fig = plt.figure(figsize=(5.4, 4.5))
        ax = fig.add_subplot(111, projection="3d")
        ax.plot(reference_W_m[:, 0], reference_W_m[:, 1], reference_W_m[:, 2], "--", color=COLORS["reference"], label="Referencia", linewidth=1.0)
        ax.plot(position_W_m[:, 0], position_W_m[:, 1], position_W_m[:, 2], color=COLORS["real"], label="Seguimiento", linewidth=1.2)
        ax.set_xlabel("Este [m]")
        ax.set_ylabel("Norte [m]")
        ax.set_zlabel("Altura [m]")
        ax.legend(fontsize=7)
        generated.extend(save_figure(fig, output_dir, "atlas_trayectoria_helix_3d", formats))
        plt.close(fig)
    return generated, skipped


def _legend_outside(ax, *, ncol: int = 1) -> None:
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0.0,
        ncol=ncol,
        fontsize=7,
    )


def _scatter_controller_points(ax, df: pd.DataFrame, x_column: str, controllers: list[str]) -> None:
    for ctrl in controllers:
        ctrl_data = df[df["controller"] == ctrl]
        if ctrl_data.empty:
            continue
        style = get_controller_style(str(ctrl))
        ax.scatter(
            ctrl_data[x_column],
            ctrl_data["position_rmse_m"],
            color=style["color"],
            label=style["label"],
            alpha=0.65,
            edgecolors="none",
            s=28,
        )


def plot_comparison(
    comparison_csv_path: str | os.PathLike[str],
    output_dir: str | os.PathLike[str],
    formats: list[str] | None = None,
    trajectory_telemetry: Sequence[tuple[str, str | os.PathLike[str]]] | None = None,
) -> ComparisonPlotResult:
    """
    Generate comparison plots C1 to C7 from aggregated campaign runs.

    Figures are conditional on the available columns and splits in the CSV.
    The returned ``ComparisonPlotResult`` lists generated figure ids and skipped
    ones with a short reason.
    """
    csv_path = Path(comparison_csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Comparison CSV not found: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        raise ValueError(f"Could not read comparison CSV ({csv_path}): {exc}") from exc

    if df.empty:
        raise ValueError(f"Comparison CSV is empty: {csv_path}")

    generated_paths: list[str] = []
    generated_ids: list[str] = []
    skipped: dict[str, str] = {figure_id: "datos insuficientes en el CSV" for figure_id in ALL_FIGURE_IDS}

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    df, preparation_warnings = _prepare_comparison_dataframe(df)
    runtime_warnings: list[str] = list(preparation_warnings)
    if df.empty:
        raise ValueError(
            "Comparison CSV no contiene filas utilizables tras omitir controladores ambiguos."
        )

    if "success" in df.columns:
        df["success"] = df["success"].astype(float)

    with use_style("report"):
        plotters = (
            ("res_id_rmse_family", _plot_res_id_rmse_family(df, out, formats)),
            ("res_ood_rmse_family", _plot_res_ood_rmse_family(df, out, formats)),
            (
                "res_pid_transfer_matrix",
                _plot_res_pid_transfer_matrix(
                    df[(df["controller"].str.startswith("classic_pid_")) & (df["split"] == "test")],
                    out,
                    formats,
                ),
            ),
            ("res_ood_scenario_matrix", _plot_res_ood_scenario_matrix(df, out, formats)),
            ("res_ood_termination_summary", _plot_res_ood_termination_summary(df, out, formats)),
            ("res_protections_ood", _plot_res_protections_ood(df, out, formats)),
        )
        for figure_id, paths in plotters:
            if paths:
                generated_paths.extend(paths)
                generated_ids.append(figure_id)
                skipped.pop(figure_id, None)
                plt.close("all")

        traj_paths, traj_skip_reason = _plot_res_trajectory_lemniscate(
            out,
            formats,
            trajectory_telemetry=trajectory_telemetry,
        )
        if traj_paths:
            generated_paths.extend(traj_paths)
            generated_ids.append("res_trajectory_lemniscate_mlp_lstm")
            skipped.pop("res_trajectory_lemniscate_mlp_lstm", None)
            plt.close("all")
        elif traj_skip_reason:
            skipped["res_trajectory_lemniscate_mlp_lstm"] = traj_skip_reason

        atlas_paths, atlas_skipped = _plot_atlas_trajectories(out, formats)
        generated_paths.extend(atlas_paths)
        for atlas_id in ("atlas_trayectorias_id", "atlas_trayectorias_ood", "atlas_trayectoria_helix_3d"):
            if any(Path(path).stem == atlas_id for path in atlas_paths):
                generated_ids.append(atlas_id)
                skipped.pop(atlas_id, None)
        for figure_id, reason in atlas_skipped:
            skipped[figure_id] = reason

    return ComparisonPlotResult(
        paths=generated_paths,
        generated=tuple(generated_ids),
        skipped=tuple(skipped.items()),
        warnings=tuple(runtime_warnings),
    )
