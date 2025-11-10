"""
Módulo: persistence_manager
-------------------------------------------------
Gestor principal del sistema de persistencia.
Coordina todos los componentes de persistencia y proporciona
una interfaz unificada para el GameEngine.

Responsabilidades:
- Coordinar ConfigManager, StateManager, SimulationHistory y CSVExporter
- Proporcionar interfaz simple para GameEngine
- Gestionar el ciclo completo de una simulación
- Automatizar guardados y recuperación
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import uuid

from .config_manager import ConfigManager
from .state_manager import StateManager
from .simulation_history import SimulationHistory
from .csv_exporter import CSVExporter


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
        self.state_manager = StateManager(self.base_dir / "saved_states")
        self.history = SimulationHistory(self.base_dir / "data" / "simulation_history.db")
        self.csv_exporter = CSVExporter(self.base_dir / "exports")
        
        # ID de simulación actual
        self.current_simulation_id: Optional[str] = None
        
        # Auto-save configurado
        self.auto_save_enabled = True
        self.auto_save_interval = 5  # Cada cuántos ticks guardar
        
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
    
    def save_simulation_state(self, state_data: Dict[str, Any], tick: int,
                             is_checkpoint: bool = False) -> Optional[str]:
        """
        Guarda el estado actual de la simulación.
        
        Args:
            state_data: Estado completo del juego
            tick: Tick actual
            is_checkpoint: Si es checkpoint de recuperación
            
        Returns:
            Path del archivo guardado o None si falla
        """
        if self.current_simulation_id is None:
            return None
        
        return self.state_manager.save_state(
            state_data,
            tick,
            self.current_simulation_id,
            is_checkpoint
        )
    
    def load_simulation_state(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Carga un estado de simulación.
        
        Args:
            filepath: Path al archivo de estado
            
        Returns:
            Estado cargado o None si falla
        """
        return self.state_manager.load_state(filepath)
    
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
    
    def get_latest_checkpoint(self) -> Optional[str]:
        """
        Obtiene el último checkpoint guardado.
        
        Returns:
            Path al checkpoint más reciente o None
        """
        return self.state_manager.get_latest_checkpoint()
    
    def find_state_by_tick(self, target_tick: int) -> Optional[str]:
        """
        Busca un estado por tick.
        
        Args:
            target_tick: Tick objetivo
            
        Returns:
            Path al estado más cercano
        """
        return self.state_manager.find_state_by_tick(
            target_tick,
            self.current_simulation_id
        )
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        Lista snapshots de la simulación actual.
        
        Returns:
            Lista de snapshots
        """
        return self.state_manager.list_snapshots(self.current_simulation_id)
    
    def list_manual_saves(self) -> List[Dict[str, Any]]:
        """
        Lista guardados manuales.
        
        Returns:
            Lista de guardados
        """
        return self.state_manager.list_manual_saves()
    
    def save_manual(self, state_data: Dict[str, Any],
                   name: str, description: Optional[str] = None) -> Optional[str]:
        """
        Guarda estado manualmente.
        
        Args:
            state_data: Estado a guardar
            name: Nombre del guardado
            description: Descripción opcional
            
        Returns:
            Path del archivo guardado
        """
        return self.state_manager.save_manual(state_data, name, description)
    
    def load_manual(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Carga un guardado manual.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Estado cargado
        """
        return self.state_manager.load_manual(filename)
    
    def export_current_simulation_csv(self) -> Optional[Dict[str, str]]:
        """
        Exporta la simulación actual a CSV.
        
        Returns:
            Diccionario con paths de archivos generados
        """
        if self.current_simulation_id is None:
            return None
        
        # Obtener datos de la simulación
        sim_data = self.history.get_simulation(self.current_simulation_id)
        
        if sim_data is None:
            return None
        
        # Exportar a CSV
        return self.csv_exporter.export_complete_simulation(sim_data)
    
    def export_all_simulations_csv(self, limit: int = 50) -> str:
        """
        Exporta todas las simulaciones a CSV.
        
        Args:
            limit: Número máximo de simulaciones a exportar
            
        Returns:
            Path al archivo CSV
        """
        simulations = self.history.list_simulations(limit)
        return self.csv_exporter.export_simulations(simulations)
    
    def export_summary_csv(self) -> str:
        """
        Exporta resumen estadístico a CSV.
        
        Returns:
            Path al archivo CSV
        """
        summary = self.history.get_statistics_summary()
        return self.csv_exporter.export_summary_statistics(summary)
    
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
    
    def cleanup_old_data(self, days_to_keep: int = 30,
                        keep_snapshots: int = 50) -> Dict[str, int]:
        """
        Limpia datos antiguos.
        
        Args:
            days_to_keep: Días de simulaciones a mantener
            keep_snapshots: Número de snapshots a mantener
            
        Returns:
            Diccionario con cantidad de elementos eliminados
        """
        deleted = {
            "simulations": self.history.cleanup_old_simulations(days_to_keep),
            "snapshots": 0
        }
        
        # Limpiar snapshots
        self.state_manager.cleanup_old_snapshots(keep_snapshots)
        self.state_manager.cleanup_checkpoints(10)
        
        return deleted
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el almacenamiento usado.
        
        Returns:
            Diccionario con información de almacenamiento
        """
        sizes = self.state_manager.get_total_size()
        
        # Convertir bytes a formato legible
        def format_size(bytes_size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_size < 1024.0:
                    return f"{bytes_size:.2f} {unit}"
                bytes_size /= 1024.0
            return f"{bytes_size:.2f} TB"
        
        return {
            "snapshots_bytes": sizes["snapshots"],
            "snapshots_formatted": format_size(sizes["snapshots"]),
            "manual_saves_bytes": sizes["manual_saves"],
            "manual_saves_formatted": format_size(sizes["manual_saves"]),
            "checkpoints_bytes": sizes["checkpoints"],
            "checkpoints_formatted": format_size(sizes["checkpoints"]),
            "total_bytes": sizes["total"],
            "total_formatted": format_size(sizes["total"])
        }
    
    def resume_last_simulation(self) -> Optional[Dict[str, Any]]:
        """
        Intenta reanudar la última simulación interrumpida.
        
        Returns:
            Estado de la última simulación o None
        """
        checkpoint = self.get_latest_checkpoint()
        
        if checkpoint is None:
            return None
        
        state = self.load_simulation_state(checkpoint)
        
        if state is not None:
            # Restaurar ID de simulación
            self.current_simulation_id = state.get("simulation_id")
        
        return state
    
    def create_checkpoint(self, state_data: Dict[str, Any], tick: int) -> Optional[str]:
        """
        Crea un checkpoint de recuperación automática.
        
        Args:
            state_data: Estado a guardar
            tick: Tick actual
            
        Returns:
            Path del checkpoint creado
        """
        return self.state_manager.create_checkpoint(state_data, tick)
    
    def should_auto_save(self, tick: int) -> bool:
        """
        Determina si debe guardar automáticamente en este tick.
        
        Args:
            tick: Tick actual
            
        Returns:
            True si debe guardar
        """
        if not self.auto_save_enabled:
            return False
        
        return tick % self.auto_save_interval == 0
    
    def set_auto_save_config(self, enabled: bool, interval: int = 5):
        """
        Configura el auto-guardado.
        
        Args:
            enabled: Si está habilitado
            interval: Intervalo de ticks entre guardados
        """
        self.auto_save_enabled = enabled
        self.auto_save_interval = max(1, interval)

