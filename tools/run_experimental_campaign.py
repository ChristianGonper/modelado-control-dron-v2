import argparse
import os
import subprocess
import sys


def run_command(cmd, dry_run=False, check=True):
    cmd_str = " ".join(cmd)
    print(f"\n>>> Executing: {cmd_str}")
    if dry_run:
        print("[DRY-RUN] Command skipped.")
        return True
    try:
        subprocess.run(cmd, check=check)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"Error executing command: {exc}", file=sys.stderr)
        if check:
            sys.exit(exc.returncode if exc.returncode else 1)
        return False
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        if check:
            sys.exit(1)
        return False


def main():
    parser = argparse.ArgumentParser(description="Orchestrator for the TFG simulation and neural control experimental campaign.")
    parser.add_argument("--phase", type=str, default="all", help="Phase(s) to run (e.g. '1', '1-3', 'all', '1,3,5')")
    parser.add_argument("--workers", type=int, default=16, help="Number of CPU workers for parallel simulations (default: 16)")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cpu", "cuda"], help="PyTorch device (default: auto)")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them")
    parser.add_argument("--rerun", action="store_true", help="Rerun simulations even if they are already completed")
    
    args = parser.parse_args()
    
    # Parsear fases a ejecutar
    phases_to_run = set()
    total_phases = 10
    
    if args.phase == "all":
        phases_to_run = set(range(1, total_phases + 1))
    elif "-" in args.phase:
        try:
            start, end = map(int, args.phase.split("-"))
            phases_to_run = set(range(start, end + 1))
        except ValueError:
            print("Invalid range format. Use e.g. '1-5'")
            sys.exit(1)
    else:
        try:
            phases_to_run = set(map(int, args.phase.split(",")))
        except ValueError:
            print("Invalid phase format. Use e.g. '1,3,5'")
            sys.exit(1)
            
    # Validar fases
    for p in phases_to_run:
        if p < 1 or p > total_phases:
            print(f"Error: Phase {p} is out of bounds (valid range: 1-{total_phases})")
            sys.exit(1)
            
    print("=" * 80)
    print(f"Starting TFG Experimental Campaign Orchestrator")
    print(f"Phases to execute: {sorted(list(phases_to_run))}")
    print(f"Resources: workers={args.workers}, device={args.device}")
    if args.dry_run:
        print("Mode: DRY-RUN (no commands will be run)")
    print("=" * 80)
    
    rerun_flag = ["--rerun"] if args.rerun else []
    
    # --- PHASE 1: Sanity Checks ---
    if 1 in phases_to_run:
        print("\n--- PHASE 1: Sanity Checks (pytest and single scenarios) ---")
        ok = run_command([sys.executable, "-m", "pytest", "-q"], dry_run=args.dry_run)
        if not ok:
            print("Phase 1 failed (tests). Aborting.")
            sys.exit(1)
        ok = run_command([sys.executable, "-m", "simulador_quad.app", "run", "scenarios/hover_clean.yaml", "--no-visualization"], dry_run=args.dry_run)
        if not ok:
            print("Phase 1 failed (hover_clean). Aborting.")
            sys.exit(1)
        ok = run_command([sys.executable, "-m", "simulador_quad.app", "run", "scenarios/composite_ood.yaml", "--no-visualization"], dry_run=args.dry_run)
        if not ok:
            print("Phase 1 failed (composite_ood). Aborting.")
            sys.exit(1)
            
    # --- PHASE 2: Classic Dataset generation and run ---
    if 2 in phases_to_run:
        print("\n--- PHASE 2: Classic Dataset Generation and Execution ---")
        run_command([sys.executable, "tools/generate_classic_dataset.py", "--version", "v1", "--out", "data/classic_dataset/v1"] + (["--overwrite"] if args.rerun else []), dry_run=args.dry_run)
        run_command([sys.executable, "tools/run_classic_dataset.py", "--dataset", "data/classic_dataset/v1", "--no-visualization", "--workers", str(args.workers)] + rerun_flag, dry_run=args.dry_run)
        run_command([sys.executable, "tools/summarize_classic_dataset.py", "--dataset", "data/classic_dataset/v1"], dry_run=args.dry_run)
        
    # --- PHASE 3: Outer-force expert selection ---
    if 3 in phases_to_run:
        print("\n--- PHASE 3: Generating Outer-Force Dataset (PID bank & selection) ---")
        run_command([sys.executable, "tools/generate_outer_force_pid_bank.py", "--dataset", "data/classic_dataset/v1", "--out", "data/outer_force_pid_bank/v1"] + (["--overwrite"] if args.rerun else []), dry_run=args.dry_run)
        run_command([sys.executable, "tools/generate_outer_force_dataset.py", "--source-dataset", "data/classic_dataset/v1", "--pid-bank", "data/outer_force_pid_bank/v1", "--out", "data/outer_force_dataset/v1"] + (["--overwrite"] if args.rerun else []), dry_run=args.dry_run)
        
    # --- PHASE 4: Position Gain Dataset generation ---
    if 4 in phases_to_run:
        print("\n--- PHASE 4: Generating Position-Gain Dataset (neural_position) ---")
        run_command([sys.executable, "tools/generate_pid_bank.py", "--dataset", "data/classic_dataset/v1", "--out", "data/pid_bank/v1"], dry_run=args.dry_run)
        run_command([sys.executable, "tools/generate_position_gain_dataset_from_bank.py", "--source-dataset", "data/classic_dataset/v1", "--pid-bank", "data/pid_bank/v1", "--out", "data/position_gain_dataset/v1"] + (["--overwrite"] if args.rerun else []), dry_run=args.dry_run)
        run_command([sys.executable, "tools/run_classic_dataset.py", "--dataset", "data/position_gain_dataset/v1", "--no-visualization", "--workers", str(args.workers)] + rerun_flag, dry_run=args.dry_run)
        
    # --- PHASE 5: Sequential Neural Training ---
    if 5 in phases_to_run:
        print("\n--- PHASE 5: Neural Training (sequential GPU/CPU) ---")
        # Outer-force
        run_command([sys.executable, "tools/train_neural_controller.py", "--dataset", "data/outer_force_dataset/v1", "--architecture", "mlp", "--feature-version", "outer_force_min_v1", "--out", "data/neural_control/outer_force_mlp_min_v1", "--device", args.device], dry_run=args.dry_run)
        run_command([sys.executable, "tools/train_neural_controller.py", "--dataset", "data/outer_force_dataset/v1", "--architecture", "gru", "--feature-version", "outer_force_min_v1", "--out", "data/neural_control/outer_force_gru_min_v1", "--device", args.device], dry_run=args.dry_run)
        run_command([sys.executable, "tools/train_neural_controller.py", "--dataset", "data/outer_force_dataset/v1", "--architecture", "lstm", "--feature-version", "outer_force_min_v1", "--out", "data/neural_control/outer_force_lstm_min_v1", "--device", args.device], dry_run=args.dry_run)
        # Position
        run_command([sys.executable, "tools/train_neural_position_controller.py", "--dataset", "data/position_gain_dataset/v1", "--architecture", "mlp", "--out", "data/neural_control/position_mlp_v1", "--device", args.device], dry_run=args.dry_run)
        run_command([sys.executable, "tools/train_neural_position_controller.py", "--dataset", "data/position_gain_dataset/v1", "--architecture", "gru", "--out", "data/neural_control/position_gru_v1", "--device", args.device], dry_run=args.dry_run)
        run_command([sys.executable, "tools/train_neural_position_controller.py", "--dataset", "data/position_gain_dataset/v1", "--architecture", "lstm", "--out", "data/neural_control/position_lstm_v1", "--device", args.device], dry_run=args.dry_run)
        
    # --- PHASE 6: Supervised Evaluation ---
    if 6 in phases_to_run:
        print("\n--- PHASE 6: Supervised Evaluation ---")
        # Outer-force
        run_command([sys.executable, "tools/evaluate_neural_controller.py", "--dataset", "data/outer_force_dataset/v1", "--run", "data/neural_control/outer_force_mlp_min_v1", "--device", args.device], dry_run=args.dry_run)
        run_command([sys.executable, "tools/evaluate_neural_controller.py", "--dataset", "data/outer_force_dataset/v1", "--run", "data/neural_control/outer_force_gru_min_v1", "--device", args.device], dry_run=args.dry_run)
        run_command([sys.executable, "tools/evaluate_neural_controller.py", "--dataset", "data/outer_force_dataset/v1", "--run", "data/neural_control/outer_force_lstm_min_v1", "--device", args.device], dry_run=args.dry_run)
        # Position
        run_command([sys.executable, "tools/evaluate_neural_position_controller.py", "--dataset", "data/position_gain_dataset/v1", "--run", "data/neural_control/position_mlp_v1", "--device", args.device], dry_run=args.dry_run)
        run_command([sys.executable, "tools/evaluate_neural_position_controller.py", "--dataset", "data/position_gain_dataset/v1", "--run", "data/neural_control/position_gru_v1", "--device", args.device], dry_run=args.dry_run)
        run_command([sys.executable, "tools/evaluate_neural_position_controller.py", "--dataset", "data/position_gain_dataset/v1", "--run", "data/neural_control/position_lstm_v1", "--device", args.device], dry_run=args.dry_run)
        
    # --- PHASE 7: Closed-Loop In-Distribution (Test Split) ---
    if 7 in phases_to_run:
        print("\n--- PHASE 7: Closed-Loop Simulation on Test Set ---")
        # Outer-force
        for arch in ["mlp", "gru", "lstm"]:
            run_command([
                sys.executable, "tools/run_neural_outer_force_dataset.py",
                "--dataset", "data/outer_force_dataset/v1",
                "--split", "test",
                "--checkpoint", f"data/neural_control/outer_force_{arch}_min_v1/checkpoints/{arch}_best.pt",
                "--normalization", f"data/neural_control/outer_force_{arch}_min_v1/normalization.json",
                "--architecture", arch,
                "--device", "cpu",
                "--workers", str(args.workers),
                "--no-visualization"
            ] + rerun_flag, dry_run=args.dry_run)
        # Position
        for arch in ["mlp", "gru", "lstm"]:
            run_command([
                sys.executable, "tools/run_neural_position_dataset.py",
                "--dataset", "data/position_gain_dataset/v1",
                "--split", "test",
                "--checkpoint", f"data/neural_control/position_{arch}_v1/checkpoints/{arch}_best.pt",
                "--normalization", f"data/neural_control/position_{arch}_v1/normalization.json",
                "--architecture", arch,
                "--device", "cpu",
                "--workers", str(args.workers),
                "--no-visualization"
            ] + rerun_flag, dry_run=args.dry_run)
            
    # --- PHASE 8: Out-of-Distribution (OOD) ---
    if 8 in phases_to_run:
        print("\n--- PHASE 8: OOD Battery Execution ---")
        run_command([sys.executable, "tools/generate_ood_battery.py", "--out", "data/neural_ood/battery_v1", "--overwrite"], dry_run=args.dry_run)
        # Classic baseline over OOD
        run_command([sys.executable, "tools/run_classic_dataset.py", "--dataset", "data/neural_ood/battery_v1", "--no-visualization", "--workers", str(args.workers)] + rerun_flag, dry_run=args.dry_run)
        # Outer force models over OOD
        for arch in ["mlp", "gru", "lstm"]:
            run_command([
                sys.executable, "tools/run_neural_outer_force_dataset.py",
                "--dataset", "data/neural_ood/battery_v1",
                "--split", "ood",
                "--checkpoint", f"data/neural_control/outer_force_{arch}_min_v1/checkpoints/{arch}_best.pt",
                "--normalization", f"data/neural_control/outer_force_{arch}_min_v1/normalization.json",
                "--architecture", arch,
                "--device", "cpu",
                "--workers", str(args.workers),
                "--no-visualization"
            ] + rerun_flag, dry_run=args.dry_run)
        # Position gain models over OOD
        for arch in ["mlp", "gru", "lstm"]:
            run_command([
                sys.executable, "tools/run_neural_position_dataset.py",
                "--dataset", "data/neural_ood/battery_v1",
                "--split", "ood",
                "--checkpoint", f"data/neural_control/position_{arch}_v1/checkpoints/{arch}_best.pt",
                "--normalization", f"data/neural_control/position_{arch}_v1/normalization.json",
                "--architecture", arch,
                "--device", "cpu",
                "--workers", str(args.workers),
                "--no-visualization"
            ] + rerun_flag, dry_run=args.dry_run)
            
    # --- PHASE 9: Classic Transfer ---
    if 9 in phases_to_run:
        print("\n--- PHASE 9: Classic PID Transfer Execution ---")
        run_command([sys.executable, "tools/run_classic_transfer_dataset.py", "--dataset", "data/classic_dataset/v1", "--no-visualization", "--workers", str(args.workers)] + rerun_flag, dry_run=args.dry_run)
        
    # --- PHASE 10: Consolidation & LaTeX Tables ---
    if 10 in phases_to_run:
        print("\n--- PHASE 10: Consolidation and LaTeX Tables Generation ---")
        run_command([
            sys.executable, "tools/summarize_comparison.py",
            "--dataset-classic", "data/classic_dataset/v1",
            "--dataset-neural", "data/outer_force_dataset/v1",
            "--dataset-position", "data/position_gain_dataset/v1",
            "--dataset-ood", "data/neural_ood/battery_v1",
            "--out-dir", "results"
        ], dry_run=args.dry_run)
        
    print("\n" + "="*80)
    print("Orchestrated campaign execution complete.")
    print("="*80)


if __name__ == "__main__":
    main()
