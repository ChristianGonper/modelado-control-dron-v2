import argparse
import sys
from simulador_quad.datasets.classic import write_dataset_files

def main():
    parser = argparse.ArgumentParser(description="Generate classical control dataset.")
    parser.add_argument("--version", type=str, default="v1", help="Dataset version (e.g., v1)")
    parser.add_argument("--out", type=str, required=True, help="Output directory")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing directory")
    parser.add_argument("--reset-pids", action="store_true", help="Reset PID configs to default initial values")
    
    args = parser.parse_args()
    
    try:
        write_dataset_files(args.version, args.out, overwrite=args.overwrite, reset_pids=args.reset_pids)
        print(f"Successfully generated dataset {args.version} in {args.out}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
