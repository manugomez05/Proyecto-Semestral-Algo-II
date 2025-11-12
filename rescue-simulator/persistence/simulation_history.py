"""
Módulo: simulation_history
-------------------------------------------------
Gestiona el historial de simulaciones usando SQLite
para almacenamiento estructurado y consultable.

Responsabilidades:
- Registrar simulaciones completadas
- Almacenar estadísticas detalladas
- Permitir consultas y análisis de datos históricos
- Mantener integridad referencial de datos
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class SimulationHistory:
    """
    Gestiona el historial de simulaciones usando SQLite.
    Almacena datos estructurados para análisis posterior.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa el gestor de historial.
        
        Args:
            db_path: Path a la base de datos SQLite.
                    Por defecto usa rescue-simulator/data/simulation_history.db
        """
        if db_path is None:
            project_root = Path(__file__).resolve().parents[1]
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "simulation_history.db"
        else:
            # Si se pasa un path explícito, asegurarse de que el directorio padre existe
            db_path = Path(db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """
        Inicializa la estructura de la base de datos.
        Crea las tablas necesarias si no existen.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabla principal de simulaciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id TEXT UNIQUE NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                duration_seconds REAL,
                total_ticks INTEGER,
                winner TEXT,
                final_score_p1 INTEGER,
                final_score_p2 INTEGER,
                status TEXT,
                end_reason TEXT,
                map_rows INTEGER,
                map_cols INTEGER,
                config_data TEXT,
                notes TEXT
            )
        """)
        
        # Tabla de estadísticas por jugador
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                final_score INTEGER,
                vehicles_destroyed INTEGER,
                vehicles_survived INTEGER,
                resources_collected INTEGER,
                total_distance_traveled REAL,
                collisions INTEGER,
                mine_hits INTEGER,
                FOREIGN KEY (simulation_id) REFERENCES simulations(simulation_id)
            )
        """)
        
        # Tabla de eventos de la simulación
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id TEXT NOT NULL,
                tick INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                timestamp TEXT,
                FOREIGN KEY (simulation_id) REFERENCES simulations(simulation_id)
            )
        """)
        
        # Tabla de estadísticas de vehículos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                vehicle_id TEXT NOT NULL,
                vehicle_type TEXT NOT NULL,
                status TEXT NOT NULL,
                distance_traveled REAL,
                resources_collected INTEGER,
                collision_count INTEGER,
                final_position TEXT,
                FOREIGN KEY (simulation_id) REFERENCES simulations(simulation_id)
            )
        """)
        
        # Índices para mejorar rendimiento de consultas
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_simulations_date 
            ON simulations(finished_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_player_stats_simulation 
            ON player_stats(simulation_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_simulation 
            ON simulation_events(simulation_id, tick)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vehicle_stats_simulation 
            ON vehicle_stats(simulation_id)
        """)
        
        conn.commit()
        conn.close()
    
    def start_simulation(self, simulation_id: str,
                        map_rows: int, map_cols: int,
                        config_data: Optional[Dict] = None) -> bool:
        """
        Registra el inicio de una nueva simulación.
        
        Args:
            simulation_id: ID único de la simulación
            map_rows: Filas del mapa
            map_cols: Columnas del mapa
            config_data: Configuración adicional (opcional)
            
        Returns:
            True si se registró correctamente
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO simulations 
                (simulation_id, started_at, status, map_rows, map_cols, config_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                simulation_id,
                datetime.now().isoformat(),
                "running",
                map_rows,
                map_cols,
                json.dumps(config_data) if config_data else None
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception:
            return False
    
    def finish_simulation(self, simulation_id: str,
                         total_ticks: int,
                         winner: str,
                         final_score_p1: int,
                         final_score_p2: int,
                         end_reason: Optional[str] = None) -> bool:
        """
        Registra la finalización de una simulación.
        
        Args:
            simulation_id: ID de la simulación
            total_ticks: Total de ticks ejecutados
            winner: Nombre del ganador
            final_score_p1: Puntaje final del jugador 1
            final_score_p2: Puntaje final del jugador 2
            end_reason: Razón de finalización (opcional)
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Obtener tiempo de inicio para calcular duración
            cursor.execute("""
                SELECT started_at FROM simulations WHERE simulation_id = ?
            """, (simulation_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False
            
            started_at = datetime.fromisoformat(result[0])
            finished_at = datetime.now()
            duration = (finished_at - started_at).total_seconds()
            
            cursor.execute("""
                UPDATE simulations
                SET finished_at = ?,
                    duration_seconds = ?,
                    total_ticks = ?,
                    winner = ?,
                    final_score_p1 = ?,
                    final_score_p2 = ?,
                    status = ?,
                    end_reason = ?
                WHERE simulation_id = ?
            """, (
                finished_at.isoformat(),
                duration,
                total_ticks,
                winner,
                final_score_p1,
                final_score_p2,
                "completed",
                end_reason,
                simulation_id
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception:
            return False
    
    def add_player_stats(self, simulation_id: str,
                        player_name: str,
                        stats: Dict[str, Any]) -> bool:
        """
        Registra estadísticas de un jugador.
        
        Args:
            simulation_id: ID de la simulación
            player_name: Nombre del jugador
            stats: Diccionario con estadísticas
            
        Returns:
            True si se registró correctamente
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO player_stats
                (simulation_id, player_name, final_score, vehicles_destroyed,
                 vehicles_survived, resources_collected, total_distance_traveled,
                 collisions, mine_hits)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                simulation_id,
                player_name,
                stats.get("final_score", 0),
                stats.get("vehicles_destroyed", 0),
                stats.get("vehicles_survived", 0),
                stats.get("resources_collected", 0),
                stats.get("total_distance_traveled", 0.0),
                stats.get("collisions", 0),
                stats.get("mine_hits", 0)
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception:
            return False
    
    def add_event(self, simulation_id: str,
                 tick: int,
                 event_type: str,
                 event_data: Optional[Dict] = None) -> bool:
        """
        Registra un evento de la simulación.
        
        Args:
            simulation_id: ID de la simulación
            tick: Tick en el que ocurrió el evento
            event_type: Tipo de evento
            event_data: Datos adicionales del evento
            
        Returns:
            True si se registró correctamente
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO simulation_events
                (simulation_id, tick, event_type, event_data, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                simulation_id,
                tick,
                event_type,
                json.dumps(event_data) if event_data else None,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception:
            return False
    
    def add_vehicle_stats(self, simulation_id: str,
                         player_name: str,
                         vehicle_id: str,
                         vehicle_type: str,
                         stats: Dict[str, Any]) -> bool:
        """
        Registra estadísticas de un vehículo.
        
        Args:
            simulation_id: ID de la simulación
            player_name: Nombre del jugador propietario
            vehicle_id: ID del vehículo
            vehicle_type: Tipo de vehículo
            stats: Diccionario con estadísticas del vehículo
            
        Returns:
            True si se registró correctamente
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO vehicle_stats
                (simulation_id, player_name, vehicle_id, vehicle_type, status,
                 distance_traveled, resources_collected, collision_count, final_position)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                simulation_id,
                player_name,
                vehicle_id,
                vehicle_type,
                stats.get("status", "unknown"),
                stats.get("distance_traveled", 0.0),
                stats.get("resources_collected", 0),
                stats.get("collision_count", 0),
                json.dumps(stats.get("final_position")) if stats.get("final_position") else None
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception:
            return False
    
    def get_simulation(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos completos de una simulación.
        
        Args:
            simulation_id: ID de la simulación
            
        Returns:
            Diccionario con datos de la simulación o None
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM simulations WHERE simulation_id = ?
            """, (simulation_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            
            simulation = dict(row)
            
            # Obtener estadísticas de jugadores
            cursor.execute("""
                SELECT * FROM player_stats WHERE simulation_id = ?
            """, (simulation_id,))
            
            simulation["player_stats"] = [dict(r) for r in cursor.fetchall()]
            
            # Obtener estadísticas de vehículos
            cursor.execute("""
                SELECT * FROM vehicle_stats WHERE simulation_id = ?
            """, (simulation_id,))
            
            simulation["vehicle_stats"] = [dict(r) for r in cursor.fetchall()]
            
            conn.close()
            return simulation
            
        except Exception:
            return None
    
    def list_simulations(self, limit: int = 50,
                        status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista las simulaciones almacenadas.
        
        Args:
            limit: Número máximo de resultados
            status: Filtrar por estado (opcional)
            
        Returns:
            Lista de simulaciones
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT * FROM simulations 
                    WHERE status = ?
                    ORDER BY started_at DESC 
                    LIMIT ?
                """, (status, limit))
            else:
                cursor.execute("""
                    SELECT * FROM simulations 
                    ORDER BY started_at DESC 
                    LIMIT ?
                """, (limit,))
            
            simulations = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return simulations
            
        except Exception:
            return []
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen estadístico de todas las simulaciones.
        
        Returns:
            Diccionario con estadísticas agregadas
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Total de simulaciones
            cursor.execute("SELECT COUNT(*) FROM simulations")
            total_simulations = cursor.fetchone()[0]
            
            # Simulaciones completadas
            cursor.execute("""
                SELECT COUNT(*) FROM simulations WHERE status = 'completed'
            """)
            completed_simulations = cursor.fetchone()[0]
            
            # Victorias por jugador
            cursor.execute("""
                SELECT winner, COUNT(*) as wins 
                FROM simulations 
                WHERE status = 'completed' AND winner != 'Empate'
                GROUP BY winner
            """)
            wins_by_player = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Duración promedio
            cursor.execute("""
                SELECT AVG(duration_seconds) 
                FROM simulations 
                WHERE status = 'completed'
            """)
            avg_duration = cursor.fetchone()[0] or 0
            
            # Ticks promedio
            cursor.execute("""
                SELECT AVG(total_ticks) 
                FROM simulations 
                WHERE status = 'completed'
            """)
            avg_ticks = cursor.fetchone()[0] or 0
            
            # Puntaje promedio
            cursor.execute("""
                SELECT AVG(final_score_p1) as avg_p1, AVG(final_score_p2) as avg_p2
                FROM simulations 
                WHERE status = 'completed'
            """)
            scores = cursor.fetchone()
            
            conn.close()
            
            return {
                "total_simulations": total_simulations,
                "completed_simulations": completed_simulations,
                "wins_by_player": wins_by_player,
                "average_duration_seconds": avg_duration,
                "average_ticks": avg_ticks,
                "average_score_p1": scores[0] or 0,
                "average_score_p2": scores[1] or 0
            }
            
        except Exception:
            return {}
    
    def delete_simulation(self, simulation_id: str) -> bool:
        """
        Elimina una simulación y todos sus datos relacionados.
        
        Args:
            simulation_id: ID de la simulación a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Eliminar en orden por integridad referencial
            cursor.execute("DELETE FROM vehicle_stats WHERE simulation_id = ?", 
                         (simulation_id,))
            cursor.execute("DELETE FROM simulation_events WHERE simulation_id = ?", 
                         (simulation_id,))
            cursor.execute("DELETE FROM player_stats WHERE simulation_id = ?", 
                         (simulation_id,))
            cursor.execute("DELETE FROM simulations WHERE simulation_id = ?", 
                         (simulation_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception:
            return False
    
    def cleanup_old_simulations(self, days_to_keep: int = 30) -> int:
        """
        Elimina simulaciones más antiguas que el número de días especificado.
        
        Args:
            days_to_keep: Días de antigüedad para mantener
            
        Returns:
            Número de simulaciones eliminadas
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Calcular fecha límite
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            # Obtener IDs a eliminar
            cursor.execute("""
                SELECT simulation_id FROM simulations 
                WHERE started_at < ?
            """, (cutoff_date,))
            
            sim_ids = [row[0] for row in cursor.fetchall()]
            count = len(sim_ids)
            
            # Eliminar cada simulación
            for sim_id in sim_ids:
                cursor.execute("DELETE FROM vehicle_stats WHERE simulation_id = ?", 
                             (sim_id,))
                cursor.execute("DELETE FROM simulation_events WHERE simulation_id = ?", 
                             (sim_id,))
                cursor.execute("DELETE FROM player_stats WHERE simulation_id = ?", 
                             (sim_id,))
                cursor.execute("DELETE FROM simulations WHERE simulation_id = ?", 
                             (sim_id,))
            
            conn.commit()
            conn.close()
            return count
            
        except Exception:
            return 0
    
    def export_to_dict(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """
        Exporta todos los datos de una simulación a un diccionario.
        Útil para exportación a JSON o CSV.
        
        Args:
            simulation_id: ID de la simulación
            
        Returns:
            Diccionario completo con todos los datos
        """
        return self.get_simulation(simulation_id)

