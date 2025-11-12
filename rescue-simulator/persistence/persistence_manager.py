"""
Módulo: persistence_manager
-------------------------------------------------
Gestor principal del sistema de persistencia.
Coordina todos los componentes de persistencia y proporciona
una interfaz unificada para el GameEngine.

Responsabilidades:
- Coordinar ConfigManager y SimulationHistory
- Proporcionar interfaz simple para GameEngine
- Gestionar el ciclo completo de una simulación
- Registrar partidas en base de datos
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import uuid

from .config_manager import ConfigManager
from .simulation_history import SimulationHistory


class PersistenceManager:
    """
    Gestor principal del sistema de persistencia.
    Proporciona interfaz unificada para todas las operaciones de persistencia.
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Inicializa el gestor de persistencia.
        
        Args:
            base_dir: Directorio base del proyecto (opcional)
        """
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[1]
        
        self.base_dir = Path(base_dir)
        
        # Inicializar componentes
        self.config_manager = ConfigManager(self.base_dir / "config")
        self.history = SimulationHistory(self.base_dir / "data" / "simulation_history.db")
        
        # ID de simulación actual
        self.current_simulation_id: Optional[str] = None
        
    def start_new_simulation(self, config: Dict[str, Any]) -> str:
        """
        Inicia una nueva simulación y la registra en el historial.
        
        Args:
            config: Configuración de la simulación
            
        Returns:
            ID único de la simulación
        """
        # Generar ID único
        simulation_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.current_simulation_id = simulation_id
        
        # Guardar configuración activa
        self.config_manager.save_active_config(config)
        
        # Registrar inicio en el historial
        map_config = config.get('map', {})
        self.history.start_simulation(
            simulation_id,
            map_config.get('rows', 50),
            map_config.get('cols', 50),
            config
        )
        
        return simulation_id
    
    def finish_simulation(self, total_ticks: int, winner: str,
                         final_score_p1: int, final_score_p2: int,
                         end_reason: Optional[str] = None) -> bool:
        """
        Finaliza la simulación actual y registra resultados.
        
        Args:
            total_ticks: Total de ticks ejecutados
            winner: Nombre del ganador
            final_score_p1: Puntaje final jugador 1
            final_score_p2: Puntaje final jugador 2
            end_reason: Razón de finalización
            
        Returns:
            True si se registró correctamente
        """
        if self.current_simulation_id is None:
            return False
        
        success = self.history.finish_simulation(
            self.current_simulation_id,
            total_ticks,
            winner,
            final_score_p1,
            final_score_p2,
            end_reason
        )
        
        return success
    
    def record_player_stats(self, player_name: str, stats: Dict[str, Any]) -> bool:
        """
        Registra estadísticas de un jugador.
        
        Args:
            player_name: Nombre del jugador
            stats: Diccionario con estadísticas
            
        Returns:
            True si se registró correctamente
        """
        if self.current_simulation_id is None:
            return False
        
        return self.history.add_player_stats(
            self.current_simulation_id,
            player_name,
            stats
        )
    
    def record_vehicle_stats(self, player_name: str, vehicle_id: str,
                            vehicle_type: str, stats: Dict[str, Any]) -> bool:
        """
        Registra estadísticas de un vehículo.
        
        Args:
            player_name: Nombre del jugador
            vehicle_id: ID del vehículo
            vehicle_type: Tipo de vehículo
            stats: Diccionario con estadísticas
            
        Returns:
            True si se registró correctamente
        """
        if self.current_simulation_id is None:
            return False
        
        return self.history.add_vehicle_stats(
            self.current_simulation_id,
            player_name,
            vehicle_id,
            vehicle_type,
            stats
        )
    
    def record_event(self, tick: int, event_type: str,
                    event_data: Optional[Dict] = None) -> bool:
        """
        Registra un evento de la simulación.
        
        Args:
            tick: Tick en que ocurrió
            event_type: Tipo de evento
            event_data: Datos adicionales
            
        Returns:
            True si se registró correctamente
        """
        if self.current_simulation_id is None:
            return False
        
        return self.history.add_event(
            self.current_simulation_id,
            tick,
            event_type,
            event_data
        )
    
    def get_simulation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de simulaciones.
        
        Args:
            limit: Número máximo de resultados
            
        Returns:
            Lista de simulaciones
        """
        return self.history.list_simulations(limit)
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen estadístico.
        
        Returns:
            Diccionario con estadísticas agregadas
        """
        return self.history.get_statistics_summary()
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """
        Limpia datos antiguos de la base de datos.
        
        Args:
            days_to_keep: Días de simulaciones a mantener
            
        Returns:
            Diccionario con cantidad de elementos eliminados
        """
        deleted = {
            "simulations": self.history.cleanup_old_simulations(days_to_keep)
        }
        
        return deleted
    
