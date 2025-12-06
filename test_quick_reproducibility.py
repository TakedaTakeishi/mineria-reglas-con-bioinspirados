"""
Test rápido de reproducibilidad básica.

Verifica que NumPy y las operaciones básicas sean deterministas.
"""
import numpy as np
import sys


def test_numpy_seed():
    """Test básico de seed de NumPy."""
    print("🧪 Test 1: Seed básico de NumPy")
    
    np.random.seed(42)
    a = np.random.rand(10)
    
    np.random.seed(42)
    b = np.random.rand(10)
    
    if np.allclose(a, b):
        print("  ✅ Seed básico funciona correctamente")
        return True
    else:
        print("  ❌ FALLO: Seed no funciona")
        print(f"     Array 1: {a[:3]}...")
        print(f"     Array 2: {b[:3]}...")
        return False


def test_numpy_choice():
    """Test de np.random.choice (usado extensivamente)."""
    print("\n🧪 Test 2: np.random.choice")
    
    np.random.seed(42)
    c = np.random.choice(100, 5, replace=False)
    
    np.random.seed(42)
    d = np.random.choice(100, 5, replace=False)
    
    if np.array_equal(c, d):
        print("  ✅ np.random.choice es determinista")
        return True
    else:
        print("  ❌ FALLO: choice no es determinista")
        print(f"     Choice 1: {c}")
        print(f"     Choice 2: {d}")
        return False


def test_numpy_permutation():
    """Test de permutación (usado en MOEAD)."""
    print("\n🧪 Test 3: np.random.permutation")
    
    np.random.seed(42)
    p1 = np.random.permutation(20)
    
    np.random.seed(42)
    p2 = np.random.permutation(20)
    
    if np.array_equal(p1, p2):
        print("  ✅ np.random.permutation es determinista")
        return True
    else:
        print("  ❌ FALLO: permutation no es determinista")
        print(f"     Perm 1: {p1[:5]}...")
        print(f"     Perm 2: {p2[:5]}...")
        return False


def test_hash_consistency():
    """Test de consistencia de hash SHA256."""
    print("\n🧪 Test 4: Hash SHA256 consistency")
    import hashlib
    
    data = "test_rule_42"
    
    h1 = hashlib.sha256(data.encode()).hexdigest()
    h2 = hashlib.sha256(data.encode()).hexdigest()
    
    if h1 == h2:
        print("  ✅ SHA256 es consistente")
        print(f"     Hash: {h1[:16]}...")
        return True
    else:
        print("  ❌ FALLO: SHA256 no es consistente")
        return False


def main():
    print("=" * 60)
    print("🔍 TEST RÁPIDO DE REPRODUCIBILIDAD")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"NumPy: {np.__version__}")
    print()
    
    results = [
        test_numpy_seed(),
        test_numpy_choice(),
        test_numpy_permutation(),
        test_hash_consistency()
    ]
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ TODOS LOS TESTS PASARON")
        print("   El entorno básico de Python está OK.")
        print("   Si aún hay diferencias, revisar:")
        print("   1. Hash del archivo valid_rules_1m.csv")
        print("   2. Versiones exactas de librerías (pip freeze)")
        print("   3. Ejecutar diagnose_reproducibility.py")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("   Problema grave con el entorno de Python.")
        print("   Posibles causas:")
        print("   - NumPy instalado incorrectamente")
        print("   - Versión incompatible de Python")
        print("   - Problema con el sistema operativo")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
