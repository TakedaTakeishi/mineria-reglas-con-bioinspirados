"""
Statistics module for MOEA/D ARM.

Provides statistical analysis tools for tracking evolution:
- HypervolumeTracker: HV evolution over generations
- PopulationStats: Diversity metrics (entropy, Hamming distance)
- ConvergenceMetrics: GD, IGD vs reference front
- ParetoFrontAnalyzer: Spacing, spread, crowding distance
"""
from src.statistics.hypervolume_tracker import HypervolumeTracker
from src.statistics.population_stats import PopulationStats
from src.statistics.convergence_metrics import ConvergenceMetrics
from src.statistics.pareto_front_analyzer import ParetoFrontAnalyzer

__all__ = [
    'HypervolumeTracker',
    'PopulationStats',
    'ConvergenceMetrics',
    'ParetoFrontAnalyzer',
]
