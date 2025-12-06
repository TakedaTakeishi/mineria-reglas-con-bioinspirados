# 🔍 Guía de Verificación de Reproducibilidad

## ⚠️ Problema Detectado
Diferentes ejecuciones con el mismo `config` están produciendo resultados diferentes en distintas computadoras.

## 🎯 Checklist de Reproducibilidad

### 1. **Verificar Archivos Críticos**
Estos archivos DEBEN ser idénticos en ambas máquinas:

```bash
# En Windows (PowerShell)
Get-FileHash "data/processed/pregenerated/valid_rules_1m.csv" -Algorithm SHA256
Get-FileHash "data/processed/diabetes_dataset/diabetes_dataset_processed.csv" -Algorithm SHA256
Get-FileHash "data/processed/diabetes_dataset/supports.json" -Algorithm SHA256

# En Mac/Linux
sha256sum data/processed/pregenerated/valid_rules_1m.csv
sha256sum data/processed/diabetes_dataset/diabetes_dataset_processed.csv
sha256sum data/processed/diabetes_dataset/supports.json
```

**Hash Esperado del Pool**:
```
5D3D98ED2401A8220173A97D36728CBE54FEC062F768D92CD13E91504FDBCC71  valid_rules_1m.csv
```

Si los hashes NO coinciden → **diferentes pools = diferentes resultados garantizados**.

---

### 2. **Verificar Versiones de Dependencias**
```bash
# Ejecutar en ambas máquinas
python --version
pip list | grep -E "numpy|pymoo|pandas"

# O en Windows:
python --version
pip list | Select-String -Pattern "numpy|pymoo|pandas"
```

**Versiones esperadas** (según `requirements.txt`):
- Python: 3.8+
- NumPy: (verificar versión exacta)
- Pymoo: (verificar versión exacta)
- Pandas: (verificar versión exacta)

---

### 3. **Ejecutar Script de Diagnóstico**
```bash
# En la computadora con problemas
python diagnose_reproducibility.py
```

Este script:
- ✅ Verifica versiones de librerías
- ✅ Comprueba que el seed de NumPy funciona
- ✅ Calcula hash de archivos críticos
- ✅ Prueba determinismo del sampling
- ✅ (Opcional) Ejecuta 2 runs completos y compara

---

### 4. **Verificar Configuración**
Asegúrate que ambas máquinas usan **exactamente el mismo config**:

```bash
# Comparar configs
cat config/escenario_1.json

# Verificar seed
grep -A2 "experiment" config/escenario_1.json | grep random_seed
```

**Seeds por escenario**:
- Escenario 1: `"random_seed": 42`
- Escenario 2: `"random_seed": 3`

---

### 5. **Verificar Modo Reproducible**
En ambos configs, debe estar:
```json
{
  "mutation": {
    "method": "fallback",
    "reproducible_mode": true,  // ✅ DEBE ser true
    "max_operations": 500
  }
}
```

Si está en `false` → resultados dependen del tiempo de CPU.

---

## 🐛 Causas Comunes de Diferencias

### 1. **Pool Diferente** (MÁS PROBABLE)
- El archivo `valid_rules_1m.csv` no está en el repo
- Diferentes máquinas generaron diferentes pools
- **Solución**: Copiar el archivo de una máquina a otra y verificar hash

### 2. **Seed de NumPy No Seteado** (SOLUCIONADO)
- El código ahora setea `np.random.seed()` al inicio en `orchestrator.py`
- **Verificar**: El log debe mostrar `🎲 Random seed set to: 42`

### 3. **Versiones Diferentes de NumPy**
- Diferentes versiones pueden tener diferentes implementaciones de RNG
- **Solución**: Usar exactamente la misma versión

### 4. **BloomFilter con Colisiones**
- El BloomFilter puede tener falsos positivos (por diseño)
- Probabilidad baja pero posible
- **Solución**: Desactivar BloomFilter temporalmente

---

## 🛠️ Pasos de Solución

### Paso 1: Verificar Hash del Pool
```bash
# En compu A (funciona)
Get-FileHash "data/processed/pregenerated/valid_rules_1m.csv" -Algorithm SHA256

# En compu B (con problemas)
Get-FileHash "data/processed/pregenerated/valid_rules_1m.csv" -Algorithm SHA256

# Si son diferentes → copiar de A a B
```

### Paso 2: Verificar Versiones
```bash
# En ambas máquinas
pip freeze > requirements_actual.txt

# Comparar archivos
# Si difieren → instalar mismas versiones
```

### Paso 3: Test Simple
```bash
# En ambas máquinas, ejecutar EXACTAMENTE:
python main.py run --config config/escenario_1.json --no-report

# Comparar salidas
diff results/MOEAD_ARM_Diabetes_Scenario_1/exp_XXX/final_pareto.csv
```

### Paso 4: Si Persiste el Problema
```bash
# Desactivar BloomFilter temporalmente
# En src/operators/sampling.py línea 97, cambiar:
use_bloom_filter: bool = False  # Era True

# Y re-ejecutar
```

---

## 📊 Test de Reproducibilidad Rápido

```python
# test_quick_reproducibility.py
import numpy as np

# Test 1: Seed básico
np.random.seed(42)
a = np.random.rand(10)
np.random.seed(42)
b = np.random.rand(10)
assert np.allclose(a, b), "❌ Seed no funciona"
print("✅ Seed básico funciona")

# Test 2: Choice
np.random.seed(42)
c = np.random.choice(100, 5, replace=False)
np.random.seed(42)
d = np.random.choice(100, 5, replace=False)
assert np.array_equal(c, d), "❌ Choice no es determinista"
print("✅ Choice es determinista")

print("\n✅ Todos los tests pasaron - NumPy está OK")
```

---

## 🔑 Hash de Referencia (Compu Principal)

Guarda estos hashes de tu computadora que funciona:

```
SHA256 Hashes (Compu A - Referencia):
- valid_rules_1m.csv:              5D3D98ED2401A8220173A97D36728CBE54FEC062F768D92CD13E91504FDBCC71
- diabetes_dataset_processed.csv:  [PENDIENTE]
- supports.json:                   [PENDIENTE]
- metadata.json:                   [PENDIENTE]
```

**TODO**: Ejecutar en tu compu y llenar los hashes faltantes.

---

## 📞 Contacto
Si después de seguir estos pasos aún hay diferencias, reporta:
1. Hashes de los 4 archivos críticos (ambas compus)
2. Output de `python diagnose_reproducibility.py` (ambas compus)
3. Output de `pip list` (ambas compus)
4. Primera línea del log que dice `🎲 Random seed set to: X`
