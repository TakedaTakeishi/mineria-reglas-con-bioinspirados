"""
Script de diagnóstico para verificar reproducibilidad.

Ejecuta el mismo config múltiples veces y compara:
- Seeds usadas
- Hash del pool pregenerado
- Primeras 10 reglas generadas
- Final pareto hashes
"""
import json
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path


def hash_file(path: Path) -> str:
    """Calcula SHA256 de un archivo."""
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def check_environment():
    """Verifica entorno y versiones."""
    import sys
    import pymoo
    
    print("=" * 60)
    print("🔍 DIAGNÓSTICO DE REPRODUCIBILIDAD")
    print("=" * 60)
    
    print("\n📦 Versiones:")
    print(f"  Python: {sys.version}")
    print(f"  NumPy: {np.__version__}")
    print(f"  Pandas: {pd.__version__}")
    print(f"  Pymoo: {pymoo.__version__}")
    
    print("\n🎲 Estado de Random:")
    print(f"  NumPy random state: {np.random.get_state()[0]}")
    
    # Check if seed is set
    np.random.seed(42)
    test1 = np.random.rand(5)
    np.random.seed(42)
    test2 = np.random.rand(5)
    
    if np.allclose(test1, test2):
        print(f"  ✅ NumPy seed funciona correctamente")
    else:
        print(f"  ❌ NumPy seed NO funciona (problema grave)")
    
    print("\n📁 Archivos Críticos:")
    critical_files = [
        "data/processed/pregenerated/valid_rules_1m.csv",
        "data/processed/diabetes_dataset/diabetes_dataset_processed.csv",
        "data/processed/diabetes_dataset/metadata.json",
        "data/processed/diabetes_dataset/supports.json",
    ]
    
    for fpath in critical_files:
        path = Path(fpath)
        if path.exists():
            fhash = hash_file(path)
            size = path.stat().st_size
            print(f"  ✅ {fpath}")
            print(f"     SHA256: {fhash[:16]}... ({size:,} bytes)")
        else:
            print(f"  ❌ FALTA: {fpath}")


def test_sampling_determinism():
    """Prueba si el sampling es determinista."""
    print("\n" + "=" * 60)
    print("🧪 TEST: Determinismo de Sampling")
    print("=" * 60)
    
    from src.operators.sampling import ARMSampling
    from src.representation import RuleIndividual
    from src.representation.rule import Rule
    from src.loggers import DiscardedRulesLogger
    
    # Load metadata
    with open("data/processed/diabetes_dataset/metadata.json", 'r') as f:
        metadata = json.load(f)
    
    # Create dummy validator and logger
    class DummyValidator:
        def is_valid(self, rule):
            return True
        
        def validate(self, *args, **kwargs):
            """Validate method usado por sampling - retorna (is_valid, reason, metrics)."""
            return (True, None, {})
    
    class DummyLogger:
        def log(self, *args, **kwargs):
            """Log method - acepta cualquier argumento."""
            pass
    
    results = []
    for run in range(3):
        print(f"\n  Run {run + 1}:")
        np.random.seed(42)  # Reset seed
        
        sampler = ARMSampling(
            metadata=metadata,
            validator=DummyValidator(),
            logger=DummyLogger(),
            max_attempts=100,
            use_bloom_filter=True
        )
        
        # Sample 5 individuals
        X = sampler._do(None, 5)
        
        # Get hashes
        hashes = []
        for i, genome in enumerate(X):
            ind = RuleIndividual(metadata)
            ind.X = genome
            try:
                rule: Rule = ind.to_rule()  # to_rule() retorna Rule, decode() retorna str
                rule_hash_str = rule.hash[:8]
                hashes.append(rule_hash_str)
                print(f"    Individual {i}: {rule_hash_str}...")
            except Exception as e:
                hashes.append("INVALID")
                print(f"    Individual {i}: INVALID ({str(e)[:30]}...)")
        
        results.append(hashes)
    
    # Compare results
    print("\n  📊 Comparación:")
    if all(r == results[0] for r in results):
        print("  ✅ Sampling es DETERMINISTA")
    else:
        print("  ❌ Sampling es NO-DETERMINISTA")
        print(f"     Run 1: {results[0]}")
        print(f"     Run 2: {results[1]}")
        print(f"     Run 3: {results[2]}")


def compare_runs():
    """Compara múltiples runs del algoritmo."""
    print("\n" + "=" * 60)
    print("🏃 TEST: Múltiples Runs Completos")
    print("=" * 60)
    print("⚠️  Este test ejecutará el algoritmo 2 veces con el mismo config")
    print("    Esto puede tomar varios minutos...\n")
    
    import subprocess
    import time
    
    config = "config/escenario_1.json"
    results_dir = Path("results/MOEAD_ARM_Diabetes_Scenario_1")
    
    # Find the latest experiment folder
    if results_dir.exists():
        exp_folders = sorted(results_dir.glob("exp_*"))
        if exp_folders:
            print(f"  Carpetas existentes: {len(exp_folders)}")
    
    # Run 1
    print("\n  🏃 Ejecutando Run 1...")
    start = time.time()
    subprocess.run([
        "python", "main.py", "run",
        "--config", config,
        "--no-report"
    ], capture_output=True)
    time1 = time.time() - start
    
    # Get latest folder
    exp_folders = sorted(results_dir.glob("exp_*"))
    run1_folder = exp_folders[-1]
    run1_pareto = run1_folder / "final_pareto.csv"
    
    # Run 2
    print(f"  ✅ Run 1 completado en {time1:.1f}s")
    print(f"     Output: {run1_folder}")
    
    print("\n  🏃 Ejecutando Run 2...")
    start = time.time()
    subprocess.run([
        "python", "main.py", "run",
        "--config", config,
        "--no-report"
    ], capture_output=True)
    time2 = time.time() - start
    
    exp_folders = sorted(results_dir.glob("exp_*"))
    run2_folder = exp_folders[-1]
    run2_pareto = run2_folder / "final_pareto.csv"
    
    print(f"  ✅ Run 2 completado en {time2:.1f}s")
    print(f"     Output: {run2_folder}")
    
    # Compare pareto fronts
    print("\n  📊 Comparando Resultados:")
    
    df1 = pd.read_csv(run1_pareto)
    df2 = pd.read_csv(run2_pareto)
    
    print(f"    Run 1: {len(df1)} soluciones")
    print(f"    Run 2: {len(df2)} soluciones")
    
    # Compare hashes if available
    if 'rule_hash' in df1.columns and 'rule_hash' in df2.columns:
        hashes1 = set(df1['rule_hash'])
        hashes2 = set(df2['rule_hash'])
        
        common = hashes1 & hashes2
        only1 = hashes1 - hashes2
        only2 = hashes2 - hashes1
        
        print(f"\n    Soluciones comunes: {len(common)}")
        print(f"    Solo en Run 1: {len(only1)}")
        print(f"    Solo en Run 2: {len(only2)}")
        
        if len(common) == len(hashes1) == len(hashes2):
            print(f"\n  ✅ RESULTADOS IDÉNTICOS (100% reproducible)")
        elif len(common) / len(hashes1) > 0.9:
            print(f"\n  ⚠️  RESULTADOS CASI IDÉNTICOS ({len(common)/len(hashes1)*100:.1f}% overlap)")
        else:
            print(f"\n  ❌ RESULTADOS DIFERENTES (solo {len(common)/len(hashes1)*100:.1f}% overlap)")
    else:
        print("    ⚠️  No se puede comparar (columna rule_hash faltante)")
    
    # Compare objectives
    obj_cols = [c for c in df1.columns if c.startswith('F_')]
    if obj_cols:
        print(f"\n    Comparando objetivos:")
        for col in obj_cols:
            diff = abs(df1[col].mean() - df2[col].mean())
            print(f"      {col}: diff = {diff:.6f}")


def main():
    """Ejecuta todos los diagnósticos."""
    check_environment()
    
    try:
        test_sampling_determinism()
    except Exception as e:
        print(f"  ❌ Error en test de sampling: {e}")
    
    # Ask user if they want full test
    print("\n" + "=" * 60)
    response = input("¿Ejecutar test completo de 2 runs? (s/n): ")
    if response.lower() in ['s', 'si', 'y', 'yes']:
        try:
            compare_runs()
        except Exception as e:
            print(f"  ❌ Error en test de runs: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Diagnóstico completado")
    print("=" * 60)


if __name__ == "__main__":
    main()
