"""
Módulo: config_manager
-------------------------------------------------
Gestiona la persistencia de configuraciones del simulador
usando JSON para legibilidad y fácil modificación.

Responsabilidades:
- Guardar/cargar configuraciones de mapas
- Guardar/cargar configuraciones de estrategias
- Guardar/cargar parámetros de simulación
- Validar configuraciones al cargar
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ConfigManager:
    """
    Gestiona la persistencia de configuraciones del simulador.
    Utiliza JSON para almacenar configuraciones de forma legible.
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Inicializa el gestor de configuraciones.
        
        Args:
            base_dir: Directorio base para almacenar configuraciones.
                     Por defecto usa rescue-simulator/config/
        """
        if base_dir is None:
            # Obtener directorio raíz del proyecto
            project_root = Path(__file__).resolve().parents[1]
            base_dir = project_root / "config"
        
        self.base_dir = Path(base_dir)
        self.configs_dir = self.base_dir / "saved_configs"
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivo de configuración activa
        self.active_config_file = self.base_dir / "active_config.json"
        
    def save_map_config(self, name: str, rows: int, cols: int, 
                       seed: Optional[int] = None,
                       mine_config: Optional[Dict] = None) -> str:
        """
        Guarda la configuración de un mapa.
        
        Args:
            name: Nombre identificador del mapa
            rows: Número de filas
            cols: Número de columnas
            seed: Semilla para generación aleatoria (opcional)
            mine_config: Configuración de minas (opcional)
            
        Returns:
            Path del archivo guardado
        """
        config = {
            "type": "map",
            "name": name,
            "created_at": datetime.now().isoformat(),
            "parameters": {
                "rows": rows,
                "cols": cols,
                "seed": seed
            },
            "mine_config": mine_config or {}
        }
        
        filename = f"map_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.configs_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def save_strategy_config(self, player_name: str, strategy_name: str,
                            strategy_params: Dict[str, Any]) -> str:
        """
        Guarda la configuración de una estrategia.
        
        Args:
            player_name: Nombre del jugador
            strategy_name: Nombre de la estrategia
            strategy_params: Parámetros de la estrategia
            
        Returns:
            Path del archivo guardado
        """
        config = {
            "type": "strategy",
            "player": player_name,
            "strategy": strategy_name,
            "created_at": datetime.now().isoformat(),
            "parameters": strategy_params
        }
        
        filename = f"strategy_{player_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.configs_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def save_simulation_config(self, config_data: Dict[str, Any],
                               name: Optional[str] = None) -> str:
        """
        Guarda la configuración completa de una simulación.
        
        Args:
            config_data: Diccionario con todos los parámetros de simulación
            name: Nombre opcional para la configuración
            
        Returns:
            Path del archivo guardado
        """
        if name is None:
            name = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        config = {
            "type": "simulation",
            "name": name,
            "created_at": datetime.now().isoformat(),
            "parameters": config_data
        }
        
        filename = f"{name}.json"
        filepath = self.configs_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def load_config(self, filepath: str) -> Dict[str, Any]:
        """
        Carga una configuración desde un archivo JSON.
        
        Args:
            filepath: Path al archivo de configuración
            
        Returns:
            Diccionario con la configuración
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            json.JSONDecodeError: Si el archivo no es JSON válido
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validar estructura básica
        self._validate_config(config)
        
        return config
    
    def _validate_config(self, config: Dict[str, Any]):
        """
        Valida la estructura de una configuración.
        
        Args:
            config: Configuración a validar
            
        Raises:
            ValueError: Si la configuración no es válida
        """
        required_fields = ["type", "created_at"]
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Configuración inválida: falta el campo '{field}'")
        
        valid_types = ["map", "strategy", "simulation"]
        if config["type"] not in valid_types:
            raise ValueError(f"Tipo de configuración inválido: {config['type']}")
    
    def list_configs(self, config_type: Optional[str] = None) -> list:
        """
        Lista todas las configuraciones guardadas.
        
        Args:
            config_type: Filtrar por tipo (map, strategy, simulation)
            
        Returns:
            Lista de tuplas (nombre_archivo, configuración)
        """
        configs = []
        
        for filepath in self.configs_dir.glob("*.json"):
            try:
                config = self.load_config(str(filepath))
                
                if config_type is None or config.get("type") == config_type:
                    configs.append((filepath.name, config))
            except Exception:
                # Ignorar archivos inválidos
                continue
        
        # Ordenar por fecha de creación (más recientes primero)
        configs.sort(key=lambda x: x[1].get("created_at", ""), reverse=True)
        
        return configs
    
    def delete_config(self, filename: str) -> bool:
        """
        Elimina una configuración guardada.
        
        Args:
            filename: Nombre del archivo a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no
        """
        filepath = self.configs_dir / filename
        
        try:
            if filepath.exists():
                filepath.unlink()
                return True
        except Exception:
            pass
        
        return False
    
    def save_active_config(self, config_data: Dict[str, Any]):
        """
        Guarda la configuración activa actual.
        
        Args:
            config_data: Datos de configuración a guardar
        """
        config = {
            "saved_at": datetime.now().isoformat(),
            "config": config_data
        }
        
        with open(self.active_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def load_active_config(self) -> Optional[Dict[str, Any]]:
        """
        Carga la configuración activa si existe.
        
        Returns:
            Diccionario con la configuración o None si no existe
        """
        if not self.active_config_file.exists():
            return None
        
        try:
            with open(self.active_config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("config")
        except Exception:
            return None
    
    def export_config(self, config_data: Dict[str, Any], 
                     output_path: str):
        """
        Exporta una configuración a un archivo específico.
        
        Args:
            config_data: Datos a exportar
            output_path: Path de destino
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def import_config(self, filepath: str) -> Dict[str, Any]:
        """
        Importa una configuración desde un archivo externo.
        
        Args:
            filepath: Path al archivo a importar
            
        Returns:
            Configuración importada
        """
        return self.load_config(filepath)
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Retorna la configuración por defecto del simulador.
        
        Returns:
            Diccionario con configuración por defecto
        """
        return {
            "map": {
                "rows": 50,
                "cols": 50,
                "seed": None
            },
            "simulation": {
                "max_ticks": 10000,
                "auto_save_interval": 5,
                "enable_debug": True
            },
            "players": {
                "player1": {
                    "name": "Jugador_1",
                    "strategy": "Strategy1"
                },
                "player2": {
                    "name": "Jugador_2",
                    "strategy": "Strategy2"
                }
            },
            "mines": {
                "O1": 2,
                "O2": 3,
                "T1": 2,
                "T2": 2,
                "G1": 1
            }
        }

