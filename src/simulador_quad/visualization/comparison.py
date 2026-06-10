from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .export import save_figure
from .style import COLORS, get_controller_style, use_style

COMPARISON_JITTER_SEED = 42
PRIMARY_CONTROLLER_PREFIXES = (
    "classic_pid_",
    "neural_outer_force_",
    "neural_position_",
    "outer_force_oracle",
)

ALL_FIGURE_IDS = (
    "c1_rmse_comparison",
    "c2_success_rate",
    "c3_generalization_ood",
    "c4_pid_transfer",
    "c5_tracking_vs_effort",
    "c6_saturation_clipping",
    "c7_error_distribution",
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
    if df.empty:
        raise ValueError(
            "Comparison CSV no contiene filas utilizables tras omitir controladores ambiguos."
        )

    if "success" in df.columns:
        df["success"] = df["success"].astype(float)

    rng = np.random.default_rng(COMPARISON_JITTER_SEED)

    with use_style("report"):
        test_df = df[df["split"] == "test"].copy()
        primary_test_df = test_df[test_df["controller"].map(_is_primary_controller)]

        if (
            not primary_test_df.empty
            and "position_rmse_m" in primary_test_df.columns
            and "family" in primary_test_df.columns
        ):
            fig, ax = plt.subplots()
            families = sorted(primary_test_df["family"].unique())
            controllers = sorted(primary_test_df["controller"].unique())
            x_coords = np.arange(len(families))
            width_offset = 0.12

            for idx, ctrl in enumerate(controllers):
                ctrl_data = primary_test_df[primary_test_df["controller"] == ctrl]
                means: list[float] = []
                stds: list[float] = []
                valid_x: list[float] = []

                for f_idx, fam in enumerate(families):
                    fam_data = ctrl_data[ctrl_data["family"] == fam]["position_rmse_m"].dropna()
                    if not fam_data.empty:
                        means.append(float(fam_data.mean()))
                        stds.append(float(fam_data.std()) if len(fam_data) > 1 else 0.0)
                        valid_x.append(f_idx + (idx - len(controllers) / 2.0 + 0.5) * width_offset)

                if means:
                    style = get_controller_style(ctrl)
                    ax.errorbar(
                        valid_x,
                        means,
                        yerr=stds,
                        fmt="o",
                        label=style["label"],
                        color=style["color"],
                        capsize=3,
                        markersize=5,
                        elinewidth=1.2,
                    )

            ax.set_xticks(x_coords)
            ax.set_xticklabels([f.capitalize() for f in families])
            ax.set_ylabel("RMSE Posición [m]")
            ax.set_xlabel("Familia de Trayectoria")
            _legend_outside(ax, ncol=2)
            generated_paths.extend(save_figure(fig, out, "c1_rmse_comparison", formats))
            generated_ids.append("c1_rmse_comparison")
            skipped.pop("c1_rmse_comparison", None)
            plt.close(fig)

        if (
            not primary_test_df.empty
            and "success" in primary_test_df.columns
            and "family" in primary_test_df.columns
        ):
            fig, ax = plt.subplots()
            families = sorted(primary_test_df["family"].unique())
            controllers = sorted(primary_test_df["controller"].unique())
            x_coords = np.arange(len(families))
            width = 0.12

            for idx, ctrl in enumerate(controllers):
                ctrl_data = primary_test_df[primary_test_df["controller"] == ctrl]
                rates: list[float] = []
                valid_x: list[float] = []

                for f_idx, fam in enumerate(families):
                    fam_data = ctrl_data[ctrl_data["family"] == fam]["success"].dropna()
                    if not fam_data.empty:
                        rates.append(float(fam_data.mean() * 100.0))
                        valid_x.append(f_idx + (idx - len(controllers) / 2.0 + 0.5) * width)

                if rates:
                    style = get_controller_style(ctrl)
                    ax.bar(
                        valid_x,
                        rates,
                        width=width * 0.9,
                        label=style["label"],
                        color=style["color"],
                        alpha=0.85,
                    )

            ax.set_xticks(x_coords)
            ax.set_xticklabels([f.capitalize() for f in families])
            ax.set_ylabel("Tasa de Éxito [%]")
            ax.set_ylim(0, 105)
            ax.set_xlabel("Familia de Trayectoria")
            _legend_outside(ax, ncol=2)
            generated_paths.extend(save_figure(fig, out, "c2_success_rate", formats))
            generated_ids.append("c2_success_rate")
            skipped.pop("c2_success_rate", None)
            plt.close(fig)

        if "split" in df.columns and "position_rmse_m" in df.columns:
            c3_df = df[df["controller"].map(_is_primary_controller)]
            agg_df = c3_df.groupby(["controller", "split"])["position_rmse_m"].mean().unstack().dropna(how="all")

            if "test" in agg_df.columns and "ood" in agg_df.columns:
                fig, ax = plt.subplots()
                controllers = list(agg_df.index)
                y_coords = np.arange(len(controllers))

                for idx, ctrl in enumerate(controllers):
                    test_val = agg_df.loc[ctrl, "test"]
                    ood_val = agg_df.loc[ctrl, "ood"]
                    style = get_controller_style(str(ctrl))

                    ax.plot([test_val, ood_val], [idx, idx], color="#CCCCCC", zorder=1, linewidth=1.5)
                    ax.scatter(
                        test_val,
                        idx,
                        color=style["color"],
                        marker="o",
                        s=50,
                        label="Nominal (Test)" if idx == 0 else "",
                        zorder=2,
                    )
                    ax.scatter(
                        ood_val,
                        idx,
                        color=style["color"],
                        marker="^",
                        s=50,
                        label="Fuera de Dist. (OOD)" if idx == 0 else "",
                        zorder=2,
                    )

                ax.set_yticks(y_coords)
                ax.set_yticklabels([get_controller_style(str(c))["label"] for c in controllers], fontsize=7)
                ax.set_xlabel("RMSE Posición Medio [m]")
                ax.legend(loc="lower right")
                generated_paths.extend(save_figure(fig, out, "c3_generalization_ood", formats))
                generated_ids.append("c3_generalization_ood")
                skipped.pop("c3_generalization_ood", None)
                plt.close(fig)
            else:
                missing = []
                if "test" not in agg_df.columns:
                    missing.append("test")
                if "ood" not in agg_df.columns:
                    missing.append("ood")
                skipped["c3_generalization_ood"] = f"faltan splits {', '.join(missing)}"

        pid_df = df[(df["controller"].str.startswith("classic_pid_")) & (df["split"] == "test")]

        if not pid_df.empty and "family" in pid_df.columns and "position_rmse_m" in pid_df.columns:
            pid_df = pid_df.copy()
            pid_df["tuned_family"] = pid_df["controller"].str.replace("classic_pid_", "", regex=False)

            families = ["hold", "circle", "lissajous", "waypoint"]
            families = [f for f in families if f in pid_df["tuned_family"].unique() or f in pid_df["family"].unique()]

            if len(families) >= 2:
                matrix = np.full((len(families), len(families)), np.nan)
                for r_idx, tuned in enumerate(families):
                    for c_idx, tested in enumerate(families):
                        subset = pid_df[(pid_df["tuned_family"] == tuned) & (pid_df["family"] == tested)]
                        if not subset.empty:
                            matrix[r_idx, c_idx] = subset["position_rmse_m"].mean()

                fig, ax = plt.subplots(figsize=(5.5, 4.5))
                cax = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
                fig.colorbar(cax, label="RMSE Posición Medio [m]")

                ax.set_xticks(np.arange(len(families)))
                ax.set_xticklabels([f.capitalize() for f in families])
                ax.set_yticks(np.arange(len(families)))
                ax.set_yticklabels([f.capitalize() for f in families])
                ax.set_xlabel("Evaluado en Familia")
                ax.set_ylabel("Sintonizado para Familia")

                for r in range(len(families)):
                    for c in range(len(families)):
                        val = matrix[r, c]
                        if not np.isnan(val):
                            color = "white" if val > np.nanpercentile(matrix, 60) else "black"
                            ax.text(c, r, f"{val:.3f}", ha="center", va="center", color=color, fontweight="bold")

                generated_paths.extend(save_figure(fig, out, "c4_pid_transfer", formats))
                generated_ids.append("c4_pid_transfer")
                skipped.pop("c4_pid_transfer", None)
                plt.close(fig)

        thrust_column = "collective_thrust_mean_N"
        moment_column = "body_moment_norm_mean_Nm"
        has_thrust = thrust_column in test_df.columns and test_df[thrust_column].notna().any()
        has_moments = moment_column in test_df.columns and test_df[moment_column].notna().any()

        if has_thrust and has_moments and "position_rmse_m" in test_df.columns:
            effort_df = test_df[
                test_df[thrust_column].notna()
                & test_df[moment_column].notna()
                & test_df["position_rmse_m"].notna()
            ]
            if not effort_df.empty:
                fig, axes = plt.subplots(1, 2, sharey=True, figsize=(7.2, 3.6))
                controllers = sorted(effort_df["controller"].unique())

                _scatter_controller_points(axes[0], effort_df, thrust_column, controllers)
                axes[0].set_xlabel("Empuje colectivo medio [N]")
                axes[0].set_ylabel("RMSE Posición [m]")

                _scatter_controller_points(axes[1], effort_df, moment_column, controllers)
                axes[1].set_xlabel("Norma media de momentos [N·m]")
                _legend_outside(axes[1], ncol=2)

                generated_paths.extend(save_figure(fig, out, "c5_tracking_vs_effort", formats))
                generated_ids.append("c5_tracking_vs_effort")
                skipped.pop("c5_tracking_vs_effort", None)
                plt.close(fig)
        else:
            missing_cols = []
            if not has_thrust:
                missing_cols.append(thrust_column)
            if not has_moments:
                missing_cols.append(moment_column)
            skipped["c5_tracking_vs_effort"] = f"faltan columnas {', '.join(missing_cols)}"

        clip_columns = [
            col
            for col in ("saturation_percentage", "force_norm_clip_percentage", "force_tilt_clip_percentage")
            if col in test_df.columns
        ]
        if not primary_test_df.empty and clip_columns:
            fig, ax = plt.subplots()
            controllers = sorted(primary_test_df["controller"].unique())
            y_pos = np.arange(len(controllers))
            bar_height = 0.22
            metric_styles = {
                "saturation_percentage": {"color": COLORS["failure"], "label": "Saturación actuadores"},
                "force_norm_clip_percentage": {"color": COLORS["mlp"], "label": "Clipping norma fuerza"},
                "force_tilt_clip_percentage": {"color": COLORS["gru"], "label": "Clipping inclinación"},
            }

            for metric_idx, column in enumerate(clip_columns):
                means = [
                    float(primary_test_df[primary_test_df["controller"] == c][column].mean())
                    for c in controllers
                ]
                offsets = y_pos + (metric_idx - (len(clip_columns) - 1) / 2.0) * bar_height
                style = metric_styles.get(column, {"color": COLORS["secondary"], "label": column})
                ax.barh(
                    offsets,
                    means,
                    height=bar_height * 0.9,
                    color=style["color"],
                    alpha=0.85,
                    label=style["label"],
                )

            ax.set_yticks(y_pos)
            ax.set_yticklabels([get_controller_style(str(c))["label"] for c in controllers], fontsize=7)
            ax.set_xlabel("Porcentaje medio [%]")
            ax.legend(loc="lower right", fontsize=7)
            generated_paths.extend(save_figure(fig, out, "c6_saturation_clipping", formats))
            generated_ids.append("c6_saturation_clipping")
            skipped.pop("c6_saturation_clipping", None)
            plt.close(fig)

        if not primary_test_df.empty and "position_rmse_m" in primary_test_df.columns:
            fig, ax = plt.subplots()
            controllers = sorted(primary_test_df["controller"].unique())

            data_list: list[np.ndarray] = []
            labels: list[str] = []
            colors: list[str] = []

            for ctrl in controllers:
                c_data = primary_test_df[primary_test_df["controller"] == ctrl]["position_rmse_m"].dropna().values
                if len(c_data) > 0:
                    data_list.append(c_data)
                    style = get_controller_style(str(ctrl))
                    labels.append(style["label"])
                    colors.append(style["color"])

            if data_list:
                try:
                    bp = ax.boxplot(
                        data_list,
                        orientation="vertical",
                        patch_artist=True,
                        tick_labels=labels,
                        showfliers=False,
                        medianprops={"color": "#333333", "linewidth": 1.5},
                        boxprops={"linewidth": 1.2},
                    )
                except TypeError:
                    bp = ax.boxplot(
                        data_list,
                        vert=True,
                        patch_artist=True,
                        labels=labels,
                        showfliers=False,
                        medianprops={"color": "#333333", "linewidth": 1.5},
                        boxprops={"linewidth": 1.2},
                    )

                for patch, color in zip(bp["boxes"], colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.5)
                    patch.set_edgecolor(color)

                for i, data in enumerate(data_list):
                    x = rng.normal(i + 1, 0.04, size=len(data))
                    ax.scatter(x, data, color=colors[i], alpha=0.6, s=15, zorder=3, edgecolors="none")

                ax.set_ylabel("RMSE Posición [m]")
                plt.xticks(rotation=25, ha="right", fontsize=7)

                generated_paths.extend(save_figure(fig, out, "c7_error_distribution", formats))
                generated_ids.append("c7_error_distribution")
                skipped.pop("c7_error_distribution", None)
                plt.close(fig)

    return ComparisonPlotResult(
        paths=generated_paths,
        generated=tuple(generated_ids),
        skipped=tuple(skipped.items()),
        warnings=tuple(preparation_warnings),
    )