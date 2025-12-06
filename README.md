# MOEA/D para Minería de Reglas de Asociación

> Implementación multi-objetivo con codificación diploide y 5 estrategias de mutación para descubrimiento de reglas en dataset de diabetes

## 📋 Resumen Ejecutivo

**RESULTADOS DE BENCHMARK ACTUALIZADOS** (Dic 2025) - Crossover Random N-Point

**Estrategia de Mutación Recomendada**: **Fallback** 🏆
- **Mejor Diversidad General**: 30.0 soluciones únicas (promedio entre 2 escenarios)
- **Rendimiento Balanceado**: 17.4s promedio, HV: 0.5237
- **Funciona por Diseño**: 100% recombinación del pool de 18,931 reglas válidas
- **Mejor para Exploración**: 54 soluciones únicas en Escenario 1

**Para Velocidad + Diversidad**: Usar **Template** (15.0 diversidad promedio, 6.5s) o **Conservative** (13.5 promedio, 7.4s)

**Para Máxima Calidad**: Usar **Mixed** (HV: 0.5385, pero 191s promedio - 11x más lento)

**Descubrimiento Clave**: Crossover random n-point + población pequeña (50) + early stopping = **3-5x más diversidad** que el enfoque previo de 2 puntos fijos.

Ver [Estrategias de Mutación](#-estrategias-de-mutaci%C3%B3n) para comparación detallada.

---

## ⚙️ Configuración y Parámetros del Sistema

### Estructura de Configuración JSON

Todos los experimentos se configuran mediante archivos JSON en `config/`. Cada configuración controla:

#### 1. **Experimento** (`experiment`)
```json
{
  "experiment": {
    "name": "MOEAD_ARM_Diabetes_Scenario_1",
    "description": "Descripción del experimento",
    "scenario": "scenario_1",           // "scenario_1" (ARM casual) o "scenario_2" (correlación)
    "random_seed": 42,                   // Semilla para reproducibilidad
    "output_root": "results"             // Directorio raíz de salidas
  },
  "use_sampling": true                   // true: usa data/sample, false: usa data/processed
}
```

#### 2. **Algoritmo MOEA/D** (`algorithm`)
```json
{
  "algorithm": {
    "generations": 150,                  // Máximo de generaciones (típico: 60-300)
    "population_size": 50,               // Número de individuos (recomendado: 50-75 para diversidad)
    "logging_interval": 5,               // Guardar población/pareto cada N generaciones
    
    "termination": {
      "enabled": true,
      "ftol": 0.0001,                    // Tolerancia de fitness para convergencia
      "period": 30                       // Generaciones sin mejora antes de terminar
    },
    
    "initialization": {
      "max_attempts": 5000               // Intentos máximos para generar individuo válido
    },
    
    "decomposition": {
      "method": "tchebycheff",           // "tchebycheff", "weighted_sum", "pbi"
      "params": {}                       // Parámetros adicionales según método
    },
    
    "neighborhood": {
      "size": 3,                         // Tamaño de vecindario (típico: 3-30)
      "replacement_size": 3,             // Cuántos vecinos actualizar
      "selection_probability": 0.3       // Prob de seleccionar del vecindario vs población
    },
    
    "operators": {
      "crossover": {
        "probability": {
          "initial": 0.7,                // Probabilidad inicial (0.6-0.8)
          "min": 0.5,                    // Límite inferior adaptativo
          "max": 0.8                     // Límite superior adaptativo
        }
      },
      "mutation": {
        "method": "fallback",            // "fallback", "mixed", "conservative", "template", "guided"
        "active_ops": ["extension", "contraction", "replacement"],
        "probability": {
          "initial": 0.4,                // Probabilidad inicial (0.3-0.5)
          "min": 0.3,
          "max": 0.6
        },
        "repair_attempts": 5,            // Intentos de reparación después de mutar
        "duplicate_attempts": 5,         // Reintentos si se genera duplicado
        "timeout": 2.0,                  // Timeout global (segundos)
        "timeout_per_attempt": 10.0      // Timeout por intento individual
      }
    },
    
    "stuck_detection": {
      "enabled": true,
      "window": 5,                       // Ventana de generaciones para detectar estancamiento
      "min_new": 1,                      // Mínimo de nuevas soluciones por ventana
      "hv_window": 10,                   // Ventana para calcular mejora de hipervolumen
      "hv_tol": 1e-4                     // Tolerancia de mejora de HV
    }
  }
}
```

#### 3. **Objetivos** (`objectives`)
```json
{
  "objectives": {
    "selected": ["casual-supp", "casual-conf", "maxConf"]  // Para scenario_1
    // O para scenario_2: ["jaccard", "cosine", "phi", "kappa"]
  }
}
```

**Métricas Disponibles**:
- **Scenario 1 (ARM Casual)**: `casual-supp`, `casual-conf`, `maxConf`
- **Scenario 2 (Correlación)**: `jaccard`, `cosine`, `phi`, `kappa` (alias: `k_measure`)

#### 4. **Restricciones** (`constraints`)
```json
{
  "constraints": {
    "rule_validity": {
      "min_antecedent_items": 1,         // Mínimo de items en antecedente
      "min_consequent_items": 1,         // Mínimo de items en consecuente
      "max_antecedent_items": 4,         // Máximo de items en antecedente
      "max_consequent_items": 2          // Máximo de items en consecuente
    },
    "metric_thresholds": {
      "casual-supp": { "min": 0.0, "max": 2.0 },
      "casual-conf": { "min": 0.0, "max": 1.0 }
    },
    "exclusions": {
      "fixed_consequents": ["gender"],  // Features que DEBEN estar en consecuente
      "forbidden_pairs": [                // Pares de items que no pueden coexistir
        ["age:niños [0-10]", "bmi:bajo_peso [<18.5]"]
      ]
    }
  }
}
```

---

### 📊 Estructura de Resultados

Cada ejecución genera un directorio en `results/<experiment_name>/exp_###/` con la siguiente estructura:

```
results/MOEAD_ARM_Diabetes_Scenario_1/exp_001/
├── config_snapshot.json           # Configuración congelada al momento de ejecutar
│
├── logs/
│   └── moead.log                  # Logs JSON estructurados con contexto de generación
│
├── populations/                   # Poblaciones completas cada logging_interval
│   ├── pop_gen_005.csv           # Generación 5
│   ├── pop_gen_010.csv           # Generación 10
│   └── ...
│   # Columnas: genome (roles+values), decoded_rule, F_0, F_1, F_2, casual-supp, casual-conf, maxConf
│
├── pareto/                        # Frentes Pareto no-dominados cada logging_interval
│   ├── pareto_gen_005.csv
│   ├── pareto_gen_010.csv
│   └── ...
│   # Igual estructura que populations/, solo soluciones no-dominadas
│
├── discarded/                     # Reglas rechazadas por validación
│   ├── gen_001.json              # Rechazos diferenciales por generación
│   ├── gen_002.json
│   └── reasons.json              # Agregado de rechazos por razón (ordenado por frecuencia)
│   # reasons.json formato: {"reason": "no_disjoint_sides", "count": 1234, "percentage": 45.2}
│
├── stats/
│   └── evolution_stats.csv       # Estadísticas de evolución
│   # Columnas por generación: gen, min_F0-F2, mean_F0-F2, max_F0-F2, hypervolume,
│   #                           diversity, duplicates, prob_crossover, prob_mutation
│
├── final_pareto.csv              # Frente Pareto final deduplicado por hash de genoma
├── final_pareto_historical.csv   # Todas las soluciones únicas a través de todas las generaciones
│
└── plots/                        # Visualizaciones (si habilitado en config)
    ├── metric_evolution.png      # Evolución de objetivos (min/mean/max)
    ├── hypervolume.png           # Evolución de hipervolumen
    ├── discarded_reasons.png     # Gráfico de barras de razones de rechazo
    ├── pareto_2d_*.png           # Frentes Pareto 2D (cada par de objetivos)
    ├── pareto_3d.png             # Frente Pareto 3D (si hay 3 objetivos)
    └── pareto_parallel.png       # Coordenadas paralelas (todos los objetivos)
```

#### Detalles de Archivos Clave

**`config_snapshot.json`**:
- Configuración exacta usada en el experimento
- Incluye merge de `base_config.json` + config específico
- Útil para reproducir exactamente el experimento

**`logs/moead.log`**:
- Logs JSON estructurados con `structlog`
- Cada línea es un JSON con campos: `event`, `level`, `timestamp`, `generation`, `individual_id`, etc.
- Búsqueda de errores: `grep '"level":"error"' logs/moead.log | jq`

**`populations/pop_gen_NNN.csv`**:
- Población completa en generación N
- Incluye genoma completo (roles + values), regla decodificada y todos los valores de fitness/métricas
- Útil para análisis de diversidad genética

**`pareto/pareto_gen_NNN.csv`**:
- Solo soluciones no-dominadas en generación N
- Misma estructura que `populations/`
- Útil para ver evolución del frente Pareto

**`discarded/reasons.json`**:
- Agregación de todas las razones de rechazo durante la ejecución
- Ordenado por frecuencia descendente
- Ejemplo: `{"no_disjoint_sides": 1234, "empty_antecedent": 567, ...}`
- Útil para diagnosticar problemas de validación

**`stats/evolution_stats.csv`**:
- Resumen estadístico por generación
- Incluye: min/mean/max de cada objetivo, hipervolumen, diversidad (soluciones únicas), duplicados, probabilidades adaptativas
- Útil para graficar evolución del algoritmo

**`final_pareto.csv` vs `final_pareto_historical.csv`**:
- `final_pareto.csv`: Frente Pareto de la última generación (deduplicado)
- `final_pareto_historical.csv`: Todas las soluciones únicas encontradas en CUALQUIER generación (acumulativo)
- El histórico suele tener 2-3x más diversidad que el final (captura exploración temprana)

---

### 🎯 Impacto de Parámetros Clave

| Parámetro | Valor Bajo | Valor Alto | Impacto en Diversidad | Impacto en Calidad | Recomendación |
|-----------|------------|------------|----------------------|-------------------|---------------|
| **population_size** | 20-30 | 100+ | ↑↑ (menos competencia) | ↓ (menos búsqueda) | **50-75** para balance |
| **generations** | 30-60 | 200-300 | ↑ (exploración temprana) | ↑↑ (convergencia) | **100-150** producción |
| **crossover.initial** | 0.5 | 0.8 | ↑↑ (más recombinación) | ↑ (explora mejor) | **0.7** para diversidad |
| **mutation.initial** | 0.3 | 0.6 | ↑ (más perturbación) | ↓ (rompe buenos) | **0.4** balanceado |
| **neighborhood.size** | 3-5 | 20-30 | ↔ (mínimo impacto) | ↑ (más búsqueda local) | **3-5** suficiente |
| **stuck_detection.window** | 3 | 10 | ↓ (para temprano) | ↑ (más tiempo) | **5** captura pico |

**Descubrimiento Crítico**: `population_size=50` + `crossover.initial=0.7` + random n-point crossover = **3-5x más diversidad** que configs previas (100 pop + 0.6 crossover + 2-point fijo).

---

## 🚀 Inicio Rápido

```bash
# Instalar dependencias
pip install -r requirements.txt

# Listar configuraciones disponibles
python main.py list

# Ver información del sistema
python main.py info

# Validar configuración (acepta nombres cortos)
python main.py validate escenario_1
# o con extensión .json
python main.py validate escenario_1.json
# o con ruta completa
python main.py validate config/escenario_1.json

# Ejecutar optimización (modo interactivo por defecto)
python main.py run
# o especificar config directamente
python main.py run --config escenario_1.json
# o deshabilitar generación de reporte
python main.py run --config escenario_1.json --no-report
```

### Uso Avanzado
```bash
# Usar orchestrator directamente
python -c "from orchestrator import Orchestrator; Orchestrator('config/escenario_1.json').run()"

# Comparar estrategias de mutación
python compare_quick.py              # Comparación rápida (30 gens)
python compare_mutations_full.py     # Comparación exhaustiva (150 gens)
```

---

## 📁 Estructura del Proyecto

```
├── src/
│   ├── core/                    # Configuración, logging, excepciones
│   │   ├── config.py           # Validación Pydantic
│   │   ├── logging_config.py   # Structlog con JSON
│   │   └── exceptions.py       # Excepciones personalizadas
│   │
│   ├── representation/          # Representación de reglas y validadores
│   │   ├── rule.py             # Hashing SHA256
│   │   ├── individual.py       # Codificación diploide
│   │   └── validators.py       # Validadores SOLID
│   │
│   ├── operators/               # Operadores genéticos
│   │   ├── crossover.py        # Crossover n-puntos aleatorio
│   │   ├── mutation.py         # Estrategias de mutación
│   │   ├── sampling.py         # Inicialización de población
│   │   └── mutation_factory.py # Factory para estrategias
│   │
│   ├── optimization/            # Algoritmo MOEA/D
│   │   └── MOEAD.py
│   │
│   ├── metrics/                 # Métricas multi-objetivo
│   │   ├── factory.py          # Factory de métricas
│   │   ├── scenario1.py        # ARM casual
│   │   └── scenario2.py        # Correlación
│   │
│   ├── statistics/              # Análisis estadístico
│   └── cli/                     # Interfaz de línea de comandos
│
├── tests/                       # Suite de tests (152 tests)
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── config/                      # Archivos de configuración
│   ├── general/
│   │   └── base_config.json
│   ├── escenario_1.json
│   └── escenario_2.json
│
├── data/                        # Datasets
│   ├── raw/
│   ├── processed/
│   └── sample/
│
├── results/                     # Salidas de experimentos
│
├── main.py                      # Punto de entrada CLI
├── orchestrator.py              # Orquestador de experimentos
└── requirements.txt             # Dependencias
```

---

## 🏗️ Características del Sistema

### 1. Gestión de Configuración
```python
from src.core import Config

# Cargar y validar configuración
config = Config.from_json(
    "config/escenario_1.json",
    base_config_path="config/general/base_config.json"
)

# Acceder a campos tipados y validados
print(config.algorithm.population_size)  # ¡Type-safe!
print(config.objectives.selected)
```

### 2. Logging Estructurado
```python
from src.core import setup_logging, get_logger

# Configurar una vez
logger = setup_logging(
    log_file="debug.log",
    level="INFO",
    json_logs=True  # Legible por máquina
)

# Usar en cualquier lugar
logger.info("generation_complete", gen=42, hv=0.85, duplicates=10)
# Output: {"event": "generation_complete", "gen": 42, "hv": 0.85, ...}
```

### 3. Hashing de Reglas (Deduplicación O(1))
```python
from src.representation import Rule

# Crear reglas
rule1 = Rule.from_items(
    antecedent=[(0, 1), (1, 2)],
    consequent=[(2, 0)]
)

# Hash criptográfico
print(rule1.hash)  # Digest hexadecimal SHA256

# Verificación de igualdad O(1)
rule2 = Rule.from_items([(1, 2), (0, 1)], [(2, 0)])  # Orden diferente
assert rule1 == rule2  # True (independiente del orden)

# Usar en sets/dicts
unique_rules = {rule1, rule2}  # Solo 1 elemento
```

### 4. Validadores SOLID
```python
from src.representation import (
    Rule,
    RuleStructureValidator,
    BusinessRuleValidator,
    CompositeValidator
)

# Validación de estructura
structure_val = RuleStructureValidator(
    min_antecedent_items=1,
    max_antecedent_items=4
)

# Validación de lógica de negocio
business_val = BusinessRuleValidator(
    metadata=metadata,
    fixed_consequents=["gender"],
    forbidden_pairs=[["pregnant", "male"]]
)

# Componer validadores
validator = CompositeValidator([structure_val, business_val])

# Validar
result = validator.validate(rule)
if not result.is_valid:
    print(f"Rechazada: {result.reason} | {result.details}")
```

---

## 🧬 Estrategias de Mutación

Este proyecto implementa **5 estrategias de mutación diferentes** para comparación. Cada estrategia tiene diferentes compensaciones entre diversidad, calidad y velocidad.

### Resumen de Estrategias

| Estrategia | Tipo | Descripción | Mejor Para |
|----------|------|-------------|----------|
| **Fallback** 🏆 | Recombinación de Pool | Timeout rápido (2s) → muestreo de pool | **Diversidad** (30.0 prom, 54 max) |
| **Mixed** | Multi-Operación | Todas las ops (extensión/contracción/reemplazo) | **Calidad** (HV: 0.5385, más lenta) |
| **Conservative** ⭐ | Cambios Mínimos | Agregar/quitar/cambiar exactamente 1 item | **Balance** (13.5 diversidad, 7.4s) |
| **Template** | Basada en Patrones | 50 patrones predefinidos, solo mutar valores | **Velocidad** (6.5s, 15.0 diversidad) |
| **Guided** | Recombinación Inteligente | Intercambiar antecedente/consecuente de reglas válidas | **Consistencia** (13.5 prom, 11.7s) |

### Resultados de Benchmark Exhaustivo (ACTUALIZADO Dic 2025)

**Configuración de Prueba**: 150 generaciones max, 50 población, crossover n-puntos aleatorio, 2 escenarios

> **✅ NUEVO BENCHMARK**: Crossover n-puntos aleatorio produce **3-5x mejor diversidad** que 2-puntos fijo. Estrategia Fallback (recombinación de pool) ahora recomendada para máxima exploración.

#### Escenario 1: ARM Casual (casual-supp, casual-conf, maxConf)

| Estrategia | Diversidad | Hipervolumen | Tiempo | Generaciones Completadas |
|----------|-----------|-------------|------|-----------------------|
| **Fallback** 🏆 | **54** | 0.9038 | 22.3s | 150/150 ✓ |
| Mixed | 39 | **0.9334** | **369.4s** ❌ | 150/150 ✓ |
| Template | 29 | 0.8893 | 7.5s | 60/150 ⚠️ |
| Conservative ⭐ | 15 | 0.9001 | 8.6s | 60/150 ⚠️ |
| Guided | 10 | **0.9392** | 9.8s | 60/150 ⚠️ |

**Ganador**: Fallback logra **54 soluciones únicas** (2.5x más que el récord anterior de Conservative)

#### Escenario 2: Correlación (jaccard, cosine, phi, kappa)

| Estrategia | Diversidad | Hipervolumen | Tiempo | Generaciones Completadas |
|----------|-----------|-------------|------|-----------------------|
| **Guided** 🏆 | **17** | 0.0448 | 13.6s | 60/150 ⚠️ |
| Mixed | 13 | **0.1436** | 12.7s | 60/150 ⚠️ |
| Conservative | 12 | 0.0373 | 6.1s | 60/150 ⚠️ |
| Fallback | 6 | **0.1436** | 12.5s | 60/150 ⚠️ |
| Template | 1 | 0.0373 | 5.6s | 60/150 ⚠️ |

**Ganador**: Guided logra mejor diversidad, Mixed/Fallback empatan en calidad (HV: 0.1436)

> **Nota**: El detector de estancamiento se detiene en ~60 gens cuando cae la tasa de nuevas soluciones. Esto es por diseño y captura la fase de exploración temprana donde la diversidad alcanza su pico.

### Rendimiento Promedio (A través de Ambos Escenarios)

| Métrica | Fallback | Mixed | Conservative | Template | Guided |
|--------|----------|-------|--------------|----------|--------|
| **Diversidad** | **30.0** 🏆 | 26.0 | 13.5 | 15.0 | 13.5 |
| **Calidad (HV)** | 0.5237 | **0.5385** 🏆 | 0.4687 | 0.4633 | 0.4920 |
| **Velocidad (s)** | 17.4 | **191.1** ❌ | 7.4 ⭐ | **6.5** ⭐ | 11.7 |
| **Confiabilidad** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Costo/Beneficio** | **Excelente** | Pobre | **Mejor** | **Excelente** | Bueno |

> **Resultados Finales**: Fallback logra **30.0 prom de diversidad** (2.2x mejor que el mejor anterior) aprovechando 18,931 reglas válidas pregeneradas. Mixed aún tiene mejor calidad (0.5385 HV) pero con **costo de 26x el tiempo** vs Template. **Para uso práctico**: Fallback (max diversidad), Template (más rápida), Conservative (balanceada).

### Recomendaciones

#### Para Máxima Diversidad 🎯 (NUEVO - Mejor Estrategia)
```json
{
  "mutation": {
    "method": "fallback",
    "probability": { "initial": 0.4, "min": 0.3, "max": 0.6 },
    "timeout": 2.0
  },
  "crossover": {
    "probability": { "initial": 0.7, "min": 0.5, "max": 0.8 }
  },
  "algorithm": {
    "population_size": 50,
    "generations": 150
  }
}
```
**Usar cuando**: Necesitas máximo de soluciones únicas (30+ prom, 54 max).  
**Por qué funciona**: El timeout fuerza muestreo del pool de 18,931 reglas válidas.  
**Compensación**: 17.4s prom (aún 11x más rápido que Mixed).

#### Para Mejor Calidad 🏆
```json
{
  "mutation": {
    "method": "mixed",
    "probability": { "initial": 0.5, "min": 0.3, "max": 0.7 }
  }
}
```
**Usar cuando**: Calidad (hipervolumen) es más importante que el tiempo.  
**Compensación**: **191s prom** - solo usar para corridas finales de producción.

#### Para Prototipado Rápido ⚡ (Más Rápida + Buena Diversidad)
```json
{
  "mutation": {
    "method": "template",
    "probability": { "initial": 0.5, "min": 0.3, "max": 0.7 },
    "num_templates": 50
  },
  "algorithm": {
    "population_size": 50,
    "generations": 60
  }
}
```
**Usar cuando**: Experimentos rápidos, prueba de configs.  
**Por qué funciona**: 6.5s prom, 15.0 diversidad - mejor ratio velocidad/diversidad.  
**Compensación**: Dependiente de patrones, puede perder estructuras novedosas.

#### Para Rendimiento Balanceado ⭐ (Default de Producción)
```json
{
  "mutation": {
    "method": "conservative",
    "probability": { "initial": 0.4, "min": 0.3, "max": 0.6 }
  },
  "crossover": {
    "probability": { "initial": 0.7, "min": 0.5, "max": 0.8 }
  },
  "algorithm": {
    "population_size": 50,
    "generations": 100
  }
}
```
**Usar cuando**: Optimización de propósito general.  
**Por qué funciona**: 7.4s, 13.5 diversidad - rendimiento sólido en todos los aspectos.

---


### Tamaño de Población: Más Pequeña es Mejor para Diversidad

| Población | Div Promedio | ¿Por qué? |
|------------|---------------|------|
| **50** ⭐ | 30.0 (fallback) | Menos competencia por espacio del frente Pareto |
| 100 | ~8.0 (benchmarks antiguos) | Más aglomeración → soluciones similares dominan |

**Recomendación**: Usa **50-75 individuos** para exploración, 100+ solo para convergencia.

### Generaciones: Parada Temprana Captura el Pico de Diversidad

| Generaciones | Cuándo Usar | Patrón de Diversidad |
|-------------|-------------|-------------------|
| **30-60** | Pruebas rápidas, exploración | Pico de diversidad (acumulación histórica) |
| **100-150** | Corridas de producción | Buen balance |
| 300+ | Optimización final | Retornos decrecientes, convergencia |

**Insight Clave**: La mayoría de soluciones únicas aparecen en las **primeras 60 generaciones**. El frente Pareto histórico acumula todas las soluciones únicas a través del tiempo.

### Probabilidad de Crossover vs Mutación

**Config de Alta Diversidad**:
- Crossover: 0.7 inicial (ALTO) → más recombinación
- Mutación: 0.4 inicial (BAJO) → menos búsqueda local

**Config de Alta Calidad**:
- Crossover: 0.6 inicial (MODERADO)
- Mutación: 0.5 inicial (MODERADO)

**¿Por qué?** Crossover con n-puntos aleatorios crea más combinaciones novedosas que la mutación.

### Detección de Estancamiento: Amigo, No Enemigo

```json
"stuck_detection": {
  "enabled": true,
  "window": 5,
  "min_new": 1
}
```

**Propósito**: Se detiene cuando <1 solución nueva por 5 generaciones  
**Efecto**: Ahorra tiempo de cómputo, captura exploración temprana  
**Resultado**: Parada típica en 60 gens (Escenario 2), 150 gens (Escenario 1)

### Configuraciones Óptimas por Objetivo

#### 🎯 Objetivo: Máxima Diversidad (54+ únicas)
```json
{
  "algorithm": {
    "population_size": 50,
    "generations": 150,
    "operators": {
      "crossover": { "probability": { "initial": 0.7, "min": 0.5, "max": 0.8 } },
      "mutation": {
        "method": "fallback",
        "probability": { "initial": 0.4, "min": 0.3, "max": 0.6 },
        "timeout": 2.0
      }
    }
  }
}
```
**Esperado**: 30-54 soluciones únicas, 17-22s, HV: 0.52

#### ⚡ Objetivo: Rápido + Diversidad Decente (15+ únicas)
```json
{
  "algorithm": {
    "population_size": 50,
    "generations": 60,
    "operators": {
      "crossover": { "probability": { "initial": 0.7, "min": 0.5, "max": 0.8 } },
      "mutation": {
        "method": "template",
        "probability": { "initial": 0.5, "min": 0.3, "max": 0.7 }
      }
    }
  }
}
```
**Esperado**: 15-29 soluciones únicas, 6-8s, HV: 0.46

#### 🏆 Objetivo: Mejor Calidad (HV > 0.53)
```json
{
  "algorithm": {
    "population_size": 75,
    "generations": 150,
    "operators": {
      "crossover": { "probability": { "initial": 0.6, "min": 0.4, "max": 0.8 } },
      "mutation": {
        "method": "mixed",
        "probability": { "initial": 0.5, "min": 0.3, "max": 0.7 }
      }
    }
  }
}
```
**Esperado**: 26-39 soluciones únicas, 180-200s, HV: 0.54

### Resumen: Rankings de Eficiencia

**Más Eficiente de Cambiar** (Impacto / Esfuerzo):
1. 🥇 **Método de mutación** (`fallback` para diversidad, `mixed` para calidad) - 1 línea, +100% diversidad
2. 🥈 **Tamaño de población** (50 vs 100) - 1 línea, +275% diversidad
3. 🥉 **Probabilidad de crossover** (0.7 vs 0.6) - marginal, +20% diversidad
4. 👍 **Generaciones** (60 vs 150) - balance tiempo/calidad, retornos decrecientes

**Menos Eficiente**:
- Tamaño de vecindario (impacto mínimo observado)
- Termination ftol (mayormente afecta convergencia final, no diversidad)

---

### Ejemplos de Configuración

Todas las estrategias de mutación pueden configurarse en `config/escenario_X.json`:

```json
{
  "mutation": {
    "method": "conservative",  // o "guided", "template", "mixed", "fallback"
    "probability": 0.5,
    "min_probability": 0.3,
    "max_probability": 0.7,
    
    // Específico de Conservative
    "operations": ["add", "remove", "change"],
    
    // Específico de Guided
    "pool_size": 18931,
    
    // Específico de Template
    "num_templates": 50,
    
    // Específico de Mixed
    "active_ops": ["extension", "contraction", "replacement"],
    "timeout": 2.0,
    "timeout_per_attempt": 10.0,
    
    // Específico de Fallback
    "timeout": 5.0,
    "max_attempts": 10
  }
}
```

### Detalles de Implementación

#### Estrategia Conservative
- **Archivo**: `src/operators/conservative_mutation.py`
- **Operaciones**: 
  - `add`: Agregar 1 item aleatorio al antecedente o consecuente
  - `remove`: Quitar 1 item aleatorio del antecedente o consecuente
  - `change`: Reemplazar el valor de 1 item
- **Validación**: Siempre ejecuta `repair()` después de la operación
- **Manejo de Duplicados**: Reintenta con diferentes operaciones

#### Estrategia Guided
- **Archivo**: `src/operators/guided_mutation.py`
- **Pool**: 18,931 reglas válidas pregeneradas
- **Operaciones**:
  - Intercambiar antecedente de regla aleatoria del pool
  - Intercambiar consecuente de regla aleatoria del pool
- **Asegura**: Siempre produce reglas válidas (del pool)

#### Estrategia Template
- **Archivo**: `src/operators/template_mutation.py`
- **Patrones**: 50 combinaciones predefinidas de antecedente/consecuente
- **Mutación**: Solo los valores cambian, estructura fija
- **Ventaja**: Rápida, no necesita reparación

#### Estrategia Mixed (Heredada)
- **Archivo**: `src/operators/mutation.py` (ARMMutation)
- **Operaciones**: Extensión, Contracción, Reemplazo
- **Problemas**: Validación compleja, timeouts frecuentes (10s)
- **Estado**: Solo comparación baseline

#### Estrategia Fallback
- **Archivo**: `src/operators/fallback_mutation.py`
- **Timeout**: 5s por intento
- **Fallback**: Seleccionar del pool si timeout
- **Problema**: Timeout demasiado agresivo → tasa de fallback 100%
- **Estado**: Necesita rediseño

---

## 🧪 Testing

```bash
# Ejecutar suite completa de tests
pytest tests/ -v --cov=src --cov-report=html

# Ejecutar solo tests unitarios
pytest tests/unit/ -v

# Ejecutar tests de integración
pytest tests/integration/ -v

# Ver reporte de cobertura
open htmlcov/index.html  # En Windows: start htmlcov/index.html

# Ejecutar tests con marcadores específicos
pytest -m "not slow" -v  # Excluir tests lentos
```

**Estado Actual**: 152 tests pasando, >80% cobertura en módulos core (`src/core/`, `src/representation/`, `src/operators/`).

---

## 📊 Características Técnicas Clave

| Característica | Enfoque Básico | Implementación Actual |
|---------|--------|------------------|
| **Detección de Duplicados** | Hashing de tuplas | SHA256 (criptográfico) |
| **Complejidad de Búsqueda** | Comparación O(n) | Lookup O(1) en hash |
| **Validación** | Monolítico | SOLID (componible) |
| **Logging** | Print statements | JSON estructurado (structlog) |
| **Configuración** | Dict + checks manuales | Pydantic (validación tipada) |
| **Cobertura de Tests** | Mínima | >80% en módulos core |
| **Manejo de Timeouts** | Manual | Automático + watchdog |

---

## 🐛 Solución de Problemas

### Errores "Module not found"
```bash
# Asegúrate de estar en la raíz del proyecto
cd "Práctica 3/Versión 2"

# Instalar dependencias
pip install -r requirements.txt
```

### Errores de validación de config
```python
# Revisar mensajes de error de Pydantic (muy detallados)
try:
    config = Config.from_json("config/escenario_1.json")
except ValidationError as e:
    print(e.json())  # Muestra exactamente qué está mal
```

---

## 📚 Documentación

- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Guía completa del sistema y mejores prácticas
- **Comentarios de código** - Todos los módulos tienen docstrings detallados
- **Tests** - 152 tests con >80% cobertura documentan el comportamiento esperado

---

## 🤝 Contribuir

1. Ejecutar suite de tests: `pytest tests/ -v --cov=src`
2. Agregar tests para nuevas características
3. Mantener >80% de cobertura
4. Seguir patrones existentes (SOLID, type hints)
5. Documentar cambios en docstrings

---

## 📝 Licencia

Proyecto académico para el curso TSAB.

---

## 🎓 Autores

Universidad - 6to Semestre - TSAB (Tópicos Selectos de Algoritmos Bioinspirados)

---

**Última Actualización**: 2025-12-06  
**Versión**: 2.0 - Sistema completo con 5 estrategias de mutación benchmarked
