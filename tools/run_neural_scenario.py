"""
Script para ejecutar un escenario existente con un controlador neuronal.
"""
import argparse
import os
import yaml
from simulador_quad.app import run_simulation
from simulador_quad.scenarios.loader import load_scenario

def main():
    parser = argparse.ArgumentParser(description="Run a scenario with a neural controller.")
    parser.add_argument("--scenario", type=str, required=True, help="Base scenario YAML path.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to the neural checkpoint (.pt).")
    parser.add_argument("--normalization", type=str, required=True, help="Path to normalization.json.")
    parser.add_argument("--architecture", type=str, choices=["mlp", "gru", "lstm"], default="mlp", help="Architecture.")
    parser.add_argument("--out", type=str, help="Override output directory.")
    parser.add_argument("--no-visualization", action="store_false", dest="visualization", default=True, help="Disable visualization.")
    
    args = parser.parse_args()
    
    # 1. Cargar el escenario base
    with open(args.scenario, 'r') as f:
        config = yaml.safe_load(f)
    
    # 2. Modificar el controlador en memoria
    config['controller'] = {
        "type": "neural",
        "architecture": args.architecture,
        "checkpoint_path": args.checkpoint,
        "normalization_path": args.normalization,
        "clip_to_classic_limits": True
    }
    
    # 3. Modificar salida si se solicita
    if args.out:
        config['output']['dir'] = args.out
    else:
        # Por defecto, anadimos sufijo _neural al directorio original
        config['output']['dir'] = config['output'].get('dir', 'results/temp') + f"_neural_{args.architecture}"
    
    # 4. Guardar temporalmente el escenario modificado
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        yaml.dump(config, tmp)
        temp_scenario_path = tmp.name
    
    try:
        # 5. Ejecutar
        command = f"uv run python tools/run_neural_scenario.py --scenario {args.scenario} --checkpoint {args.checkpoint} --normalization {args.normalization} --architecture {args.architecture}"
        run_simulation(temp_scenario_path, visualization=args.visualization, command=command)
    finally:
        # Limpiar
        if os.path.exists(temp_scenario_path):
            os.remove(temp_scenario_path)

if __name__ == "__main__":
    main()
