"""
Sistema de Persistencia para Rescue Simulator
==============================================

Este módulo proporciona un sistema completo de persistencia de datos
para el simulador de rescate, incluyendo:

- Gestión de configuraciones (JSON)
- Historial de simulaciones (SQLite)
- Gestor principal unificado (PersistenceManager)
"""

from .config_manager import ConfigManager
from .simulation_history import SimulationHistory
from .persistence_manager import PersistenceManager

__all__ = [
    'ConfigManager',
    'SimulationHistory',
    'PersistenceManager'
]

