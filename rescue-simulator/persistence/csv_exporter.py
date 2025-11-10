"""
Módulo: csv_exporter
-------------------------------------------------
Exporta estadísticas y datos de simulaciones a formato CSV
para análisis externo.

Responsabilidades:
- Exportar historial de simulaciones a CSV
- Exportar estadísticas de jugadores a CSV
- Exportar estadísticas de vehículos a CSV
- Exportar eventos de simulación a CSV
- Formato claro y ordenado para análisis
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class CSVExporter:
    """
    Exporta datos de simulaciones a formato CSV.
    Proporciona múltiples formatos de exportación según necesidad.
    """
    
    def __init__(self, export_dir: Optional[Path] = None):
        """
        Inicializa el exportador CSV.
        
        Args:
            export_dir: Directorio para guardar archivos CSV.
                       Por defecto usa rescue-simulator/exports/
        """
        if export_dir is None:
            project_root = Path(__file__).resolve().parents[1]
            export_dir = project_root / "exports"
        
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_simulations(self, simulations: List[Dict[str, Any]],
                          filename: Optional[str] = None) -> str:
        """
        Exporta lista de simulaciones a CSV.
        
        Args:
            simulations: Lista de diccionarios con datos de simulaciones
            filename: Nombre del archivo (opcional)
            
        Returns:
            Path al archivo CSV generado
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"simulations_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        if not simulations:
            # Crear archivo vacío con headers
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'simulation_id', 'started_at', 'finished_at', 'duration_seconds',
                    'total_ticks', 'winner', 'final_score_p1', 'final_score_p2',
                    'status', 'end_reason', 'map_rows', 'map_cols'
                ])
            return str(filepath)
        
        # Determinar campos a exportar
        headers = [
            'simulation_id', 'started_at', 'finished_at', 'duration_seconds',
            'total_ticks', 'winner', 'final_score_p1', 'final_score_p2',
            'status', 'end_reason', 'map_rows', 'map_cols'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            
            for sim in simulations:
                writer.writerow(sim)
        
        return str(filepath)
    
    def export_player_stats(self, player_stats: List[Dict[str, Any]],
                           filename: Optional[str] = None) -> str:
        """
        Exporta estadísticas de jugadores a CSV.
        
        Args:
            player_stats: Lista de estadísticas de jugadores
            filename: Nombre del archivo (opcional)
            
        Returns:
            Path al archivo CSV generado
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"player_stats_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        headers = [
            'simulation_id', 'player_name', 'final_score', 'vehicles_destroyed',
            'vehicles_survived', 'resources_collected', 'total_distance_traveled',
            'collisions', 'mine_hits'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            
            for stats in player_stats:
                writer.writerow(stats)
        
        return str(filepath)
    
    def export_vehicle_stats(self, vehicle_stats: List[Dict[str, Any]],
                            filename: Optional[str] = None) -> str:
        """
        Exporta estadísticas de vehículos a CSV.
        
        Args:
            vehicle_stats: Lista de estadísticas de vehículos
            filename: Nombre del archivo (opcional)
            
        Returns:
            Path al archivo CSV generado
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"vehicle_stats_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        headers = [
            'simulation_id', 'player_name', 'vehicle_id', 'vehicle_type',
            'status', 'distance_traveled', 'resources_collected',
            'collision_count', 'final_position'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            
            for stats in vehicle_stats:
                writer.writerow(stats)
        
        return str(filepath)
    
    def export_events(self, events: List[Dict[str, Any]],
                     filename: Optional[str] = None) -> str:
        """
        Exporta eventos de simulación a CSV.
        
        Args:
            events: Lista de eventos
            filename: Nombre del archivo (opcional)
            
        Returns:
            Path al archivo CSV generado
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"events_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        headers = [
            'simulation_id', 'tick', 'event_type', 'event_data', 'timestamp'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            
            for event in events:
                writer.writerow(event)
        
        return str(filepath)
    
    def export_complete_simulation(self, simulation_data: Dict[str, Any],
                                   base_filename: Optional[str] = None) -> Dict[str, str]:
        """
        Exporta todos los datos de una simulación en múltiples archivos CSV.
        
        Args:
            simulation_data: Datos completos de una simulación
            base_filename: Nombre base para los archivos (opcional)
            
        Returns:
            Diccionario con paths a todos los archivos generados
        """
        if base_filename is None:
            sim_id = simulation_data.get('simulation_id', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"{sim_id}_{timestamp}"
        
        files = {}
        
        # Exportar datos principales de la simulación
        sim_data = {k: v for k, v in simulation_data.items() 
                   if k not in ['player_stats', 'vehicle_stats', 'events']}
        files['simulation'] = self.export_simulations(
            [sim_data], 
            f"{base_filename}_simulation.csv"
        )
        
        # Exportar estadísticas de jugadores
        if 'player_stats' in simulation_data and simulation_data['player_stats']:
            files['player_stats'] = self.export_player_stats(
                simulation_data['player_stats'],
                f"{base_filename}_player_stats.csv"
            )
        
        # Exportar estadísticas de vehículos
        if 'vehicle_stats' in simulation_data and simulation_data['vehicle_stats']:
            files['vehicle_stats'] = self.export_vehicle_stats(
                simulation_data['vehicle_stats'],
                f"{base_filename}_vehicle_stats.csv"
            )
        
        # Exportar eventos
        if 'events' in simulation_data and simulation_data['events']:
            files['events'] = self.export_events(
                simulation_data['events'],
                f"{base_filename}_events.csv"
            )
        
        return files
    
    def export_summary_statistics(self, summary: Dict[str, Any],
                                  filename: Optional[str] = None) -> str:
        """
        Exporta resumen estadístico a CSV.
        
        Args:
            summary: Diccionario con estadísticas resumidas
            filename: Nombre del archivo (opcional)
            
        Returns:
            Path al archivo CSV generado
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"summary_stats_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        # Convertir diccionario de resumen a formato CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            
            # Escribir métricas simples
            for key, value in summary.items():
                if not isinstance(value, dict):
                    writer.writerow([key, value])
            
            # Escribir diccionarios anidados
            for key, value in summary.items():
                if isinstance(value, dict):
                    writer.writerow([])  # Línea en blanco
                    writer.writerow([key, ''])
                    for sub_key, sub_value in value.items():
                        writer.writerow([f"  {sub_key}", sub_value])
        
        return str(filepath)
    
    def export_comparison(self, simulations: List[Dict[str, Any]],
                         filename: Optional[str] = None) -> str:
        """
        Exporta comparación entre múltiples simulaciones.
        
        Args:
            simulations: Lista de simulaciones a comparar
            filename: Nombre del archivo (opcional)
            
        Returns:
            Path al archivo CSV generado
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"comparison_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        headers = [
            'simulation_id', 'started_at', 'winner', 
            'score_p1', 'score_p2', 'score_difference',
            'total_ticks', 'duration_seconds', 'end_reason'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for sim in simulations:
                score_p1 = sim.get('final_score_p1', 0) or 0
                score_p2 = sim.get('final_score_p2', 0) or 0
                score_diff = abs(score_p1 - score_p2)
                
                writer.writerow([
                    sim.get('simulation_id', ''),
                    sim.get('started_at', ''),
                    sim.get('winner', ''),
                    score_p1,
                    score_p2,
                    score_diff,
                    sim.get('total_ticks', 0),
                    sim.get('duration_seconds', 0),
                    sim.get('end_reason', '')
                ])
        
        return str(filepath)
    
    def export_vehicle_performance(self, vehicle_stats: List[Dict[str, Any]],
                                   filename: Optional[str] = None) -> str:
        """
        Exporta análisis de rendimiento de vehículos.
        Agrupa y compara estadísticas por tipo de vehículo.
        
        Args:
            vehicle_stats: Lista de estadísticas de vehículos
            filename: Nombre del archivo (opcional)
            
        Returns:
            Path al archivo CSV generado
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"vehicle_performance_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        # Agrupar por tipo de vehículo
        by_type = {}
        for stats in vehicle_stats:
            vtype = stats.get('vehicle_type', 'unknown')
            if vtype not in by_type:
                by_type[vtype] = []
            by_type[vtype].append(stats)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'vehicle_type', 'total_vehicles', 'destroyed', 'survived',
                'avg_distance', 'avg_resources', 'avg_collisions'
            ])
            
            for vtype, stats_list in by_type.items():
                total = len(stats_list)
                destroyed = sum(1 for s in stats_list if s.get('status') == 'destroyed')
                survived = total - destroyed
                
                avg_distance = sum(s.get('distance_traveled', 0) for s in stats_list) / total if total > 0 else 0
                avg_resources = sum(s.get('resources_collected', 0) for s in stats_list) / total if total > 0 else 0
                avg_collisions = sum(s.get('collision_count', 0) for s in stats_list) / total if total > 0 else 0
                
                writer.writerow([
                    vtype, total, destroyed, survived,
                    f"{avg_distance:.2f}",
                    f"{avg_resources:.2f}",
                    f"{avg_collisions:.2f}"
                ])
        
        return str(filepath)
    
    def export_player_comparison(self, player_stats: List[Dict[str, Any]],
                                filename: Optional[str] = None) -> str:
        """
        Exporta comparación de rendimiento entre jugadores.
        
        Args:
            player_stats: Lista de estadísticas de jugadores
            filename: Nombre del archivo (opcional)
            
        Returns:
            Path al archivo CSV generado
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"player_comparison_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        # Agrupar por jugador
        by_player = {}
        for stats in player_stats:
            player = stats.get('player_name', 'unknown')
            if player not in by_player:
                by_player[player] = []
            by_player[player].append(stats)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'player_name', 'games_played', 'avg_score', 'total_resources',
                'avg_distance', 'avg_vehicles_destroyed', 'avg_mine_hits'
            ])
            
            for player, stats_list in by_player.items():
                games = len(stats_list)
                avg_score = sum(s.get('final_score', 0) for s in stats_list) / games if games > 0 else 0
                total_resources = sum(s.get('resources_collected', 0) for s in stats_list)
                avg_distance = sum(s.get('total_distance_traveled', 0) for s in stats_list) / games if games > 0 else 0
                avg_destroyed = sum(s.get('vehicles_destroyed', 0) for s in stats_list) / games if games > 0 else 0
                avg_mine_hits = sum(s.get('mine_hits', 0) for s in stats_list) / games if games > 0 else 0
                
                writer.writerow([
                    player, games,
                    f"{avg_score:.2f}",
                    total_resources,
                    f"{avg_distance:.2f}",
                    f"{avg_destroyed:.2f}",
                    f"{avg_mine_hits:.2f}"
                ])
        
        return str(filepath)
    
    def list_exports(self) -> List[Dict[str, Any]]:
        """
        Lista todos los archivos CSV exportados.
        
        Returns:
            Lista de diccionarios con información de archivos
        """
        exports = []
        
        for filepath in self.export_dir.glob("*.csv"):
            exports.append({
                "filename": filepath.name,
                "filepath": str(filepath),
                "size_bytes": filepath.stat().st_size,
                "modified": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
            })
        
        # Ordenar por fecha de modificación (más recientes primero)
        exports.sort(key=lambda x: x["modified"], reverse=True)
        
        return exports
    
    def delete_export(self, filename: str) -> bool:
        """
        Elimina un archivo CSV exportado.
        
        Args:
            filename: Nombre del archivo a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        filepath = self.export_dir / filename
        
        try:
            if filepath.exists():
                filepath.unlink()
                return True
        except Exception:
            pass
        
        return False
