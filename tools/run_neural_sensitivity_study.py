"""
Orchestrate neural outer-force sensitivity studies without overwriting v1 baseline.

Blocks (sequential):
  A - hidden_dim=128 (MLP, GRU, LSTM)
  B - sequence_length 10/40 (GRU, LSTM)
  C - seed 7/123 (MLP only)
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field


DATASET = "data/outer_force_dataset/v1"
OOD_DATASET = "data/neural_ood/battery_v1"
FEATURE_VERSION = "outer_force_min_v1"
NEURAL_CONTROL_ROOT = "data/neural_control"


@dataclass
class VariantSpec:
    tag: str
    block: str
    architecture: str
    hidden_dim: int = 64
    sequence_length: int = 20
    seed: int = 42
    extra_args: list[str] = field(default_factory=list)

    @property
    def run_dir(self) -> str:
        return os.path.join(NEURAL_CONTROL_ROOT, f"outer_force_{self.architecture}_min_v1_{self.tag}")

    @property
    def checkpoint(self) -> str:
        return os.path.join(self.run_dir, "checkpoints", f"{self.architecture}_best.pt")

    @property
    def normalization(self) -> str:
        return os.path.join(self.run_dir, "normalization.json")


VARIANTS: list[VariantSpec] = [
    # Block A: hidden_dim=128
    VariantSpec(tag="h128", block="h128", architecture="mlp", hidden_dim=128),
    VariantSpec(tag="h128", block="h128", architecture="gru", hidden_dim=128),
    VariantSpec(tag="h128", block="h128", architecture="lstm", hidden_dim=128),
    # Block B: sequence length
    VariantSpec(tag="L10", block="L10", architecture="gru", sequence_length=10),
    VariantSpec(tag="L10", block="L10", architecture="lstm", sequence_length=10),
    VariantSpec(tag="L40", block="L40", architecture="gru", sequence_length=40),
    VariantSpec(tag="L40", block="L40", architecture="lstm", sequence_length=40),
    # Block C: seeds (MLP only)
    VariantSpec(tag="seed7", block="seed7", architecture="mlp", seed=7),
    VariantSpec(tag="seed123", block="seed123", architecture="mlp", seed=123),
]

BLOCK_ORDER = ["h128", "L10", "L40", "seed7", "seed123"]

BASELINE_RUNS = {
    arch: os.path.join(NEURAL_CONTROL_ROOT, f"outer_force_{arch}_min_v1")
    for arch in ("mlp", "gru", "lstm")
}


def run_command(cmd: list[str], dry_run: bool = False) -> None:
    cmd_str = " ".join(cmd)
    print(f"\n>>> {cmd_str}")
    if dry_run:
        print("[DRY-RUN] skipped")
        return
    subprocess.run(cmd, check=True)


def _train_cmd(variant: VariantSpec, device: str) -> list[str]:
    cmd = [
        sys.executable,
        "tools/train_neural_controller.py",
        "--dataset", DATASET,
        "--architecture", variant.architecture,
        "--feature-version", FEATURE_VERSION,
        "--out", variant.run_dir,
        "--hidden-dim", str(variant.hidden_dim),
        "--seed", str(variant.seed),
        "--device", device,
    ]
    if variant.architecture != "mlp":
        cmd.extend(["--sequence-length", str(variant.sequence_length)])
    cmd.extend(variant.extra_args)
    return cmd


def _eval_cmd(variant: VariantSpec, device: str) -> list[str]:
    return [
        sys.executable,
        "tools/evaluate_neural_controller.py",
        "--dataset", DATASET,
        "--run", variant.run_dir,
        "--splits", "train,val,test",
        "--device", device,
    ]


def _closed_loop_cmd(
    variant: VariantSpec,
    dataset: str,
    split: str,
    workers: int,
) -> list[str]:
    return [
        sys.executable,
        "tools/run_neural_outer_force_dataset.py",
        "--dataset", dataset,
        "--split", split,
        "--checkpoint", variant.checkpoint,
        "--normalization", variant.normalization,
        "--architecture", variant.architecture,
        "--device", "cpu",
        "--workers", str(workers),
        "--no-visualization",
        "--variant-tag", variant.tag,
    ]


def check_prerequisites(workers: int, dry_run: bool) -> None:
    missing = []
    for arch, run_dir in BASELINE_RUNS.items():
        cp = os.path.join(run_dir, "checkpoints", f"{arch}_best.pt")
        norm = os.path.join(run_dir, "normalization.json")
        if not os.path.exists(cp):
            missing.append(cp)
        if not os.path.exists(norm):
            missing.append(norm)

    if not os.path.exists(os.path.join(DATASET, "manifest.csv")):
        missing.append(os.path.join(DATASET, "manifest.csv"))

    if missing and not dry_run:
        print("ERROR: Missing v1 baseline artifacts:")
        for path in missing:
            print(f"  - {path}")
        print("Run the main campaign (phases 5-7) before sensitivity studies.")
        sys.exit(1)

    ood_manifest = os.path.join(OOD_DATASET, "manifest.csv")
    if not os.path.exists(ood_manifest) and not dry_run:
        print("OOD battery missing; generating with classic workers=16...")
        run_command([
            sys.executable,
            "tools/generate_ood_battery.py",
            "--out", OOD_DATASET,
            "--pid-source-dataset", "data/classic_dataset/v1",
            "--overwrite",
        ], dry_run=False)
        run_command([
            sys.executable,
            "tools/run_classic_dataset.py",
            "--dataset", OOD_DATASET,
            "--no-visualization",
            "--workers", str(workers),
        ], dry_run=False)


def run_variant(variant: VariantSpec, device: str, workers: int, dry_run: bool) -> None:
    print("=" * 72)
    print(
        f"Variant {variant.tag} | {variant.architecture} | "
        f"h={variant.hidden_dim} L={variant.sequence_length} seed={variant.seed}"
    )
    print("=" * 72)

    run_command(_train_cmd(variant, device), dry_run=dry_run)
    run_command(_eval_cmd(variant, device), dry_run=dry_run)
    run_command(_closed_loop_cmd(variant, DATASET, "test", workers), dry_run=dry_run)
    run_command(_closed_loop_cmd(variant, OOD_DATASET, "ood", workers), dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run neural outer-force sensitivity study (sequential).")
    parser.add_argument(
        "--blocks",
        type=str,
        default="all",
        help="Comma-separated block tags or 'all' (default: all). Options: h128,L10,L40,seed7,seed123",
    )
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Workers for closed-loop neural runs (default: 1, no parallelization).",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.blocks == "all":
        selected_blocks = set(BLOCK_ORDER)
    else:
        selected_blocks = {b.strip() for b in args.blocks.split(",") if b.strip()}
        unknown = selected_blocks - set(BLOCK_ORDER)
        if unknown:
            print(f"Unknown blocks: {sorted(unknown)}. Valid: {BLOCK_ORDER}")
            sys.exit(1)

    check_prerequisites(workers=16, dry_run=args.dry_run)

    variants_to_run = [v for v in VARIANTS if v.block in selected_blocks]
    print(f"Blocks: {[b for b in BLOCK_ORDER if b in selected_blocks]}")
    print(f"Variants to run: {len(variants_to_run)}")
    print(f"Device: {args.device}, closed-loop workers: {args.workers}")

    for block in BLOCK_ORDER:
        if block not in selected_blocks:
            continue
        block_variants = [v for v in variants_to_run if v.block == block]
        print(f"\n### BLOCK {block} ({len(block_variants)} variants) ###")
        for variant in block_variants:
            run_variant(variant, device=args.device, workers=args.workers, dry_run=args.dry_run)

    print("\nSensitivity study execution complete.")
    if not args.dry_run:
        print("Run: uv run python tools/summarize_neural_sensitivity.py")


if __name__ == "__main__":
    main()