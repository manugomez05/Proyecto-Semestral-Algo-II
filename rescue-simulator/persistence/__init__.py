"""
Sistema de Persistencia para Rescue Simulator
==============================================

Este módulo proporciona un sistema completo de persistencia de datos
para el simulador de rescate, incluyendo:

- Gestión de configuraciones (JSON)
- Gestión de estados de simulación (Pickle)
- Historial de simulaciones (SQLite)
- Exportación de estadísticas (CSV)
- Gestor principal unificado (PersistenceManager)
"""

from .config_manager import ConfigManager
from .state_manager import StateManager
from .simulation_history import SimulationHistory
from .csv_exporter import CSVExporter
from .persistence_manager import PersistenceManager

__all__ = [
    'ConfigManager',
    'StateManager',
    'SimulationHistory',
    'CSVExporter',
    'PersistenceManager'
]

