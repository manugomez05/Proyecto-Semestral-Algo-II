"""
Módulo: state_manager
-------------------------------------------------
Gestiona la persistencia de estados de simulación usando Pickle
para serialización eficiente de objetos complejos.

Responsabilidades:
- Guardar estados completos de simulación
- Cargar estados guardados
- Gestionar snapshots automáticos
- Permitir reanudar simulaciones interrumpidas
- Limpieza de estados antiguos
"""

import pickle
import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib


class StateManager:
    """
    Gestiona la persistencia de estados de simulación.
    Utiliza Pickle para serialización eficiente.
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Inicializa el gestor de estados.
        
        Args:
            base_dir: Directorio base para almacenar estados.
                     Por defecto usa rescue-simulator/saved_states/
        """
        if base_dir is None:
            # Obtener directorio raíz del proyecto
            project_root = Path(__file__).resolve().parents[1]
            base_dir = project_root / "saved_states"
        
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Directorio para snapshots automáticos
        self.snapshots_dir = self.base_dir / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
        
        # Directorio para guardados manuales
        self.manual_saves_dir = self.base_dir / "manual_saves"
        self.manual_saves_dir.mkdir(exist_ok=True)
        
        # Directorio para checkpoints de recuperación
        self.checkpoints_dir = self.base_dir / "checkpoints"
        self.checkpoints_dir.mkdir(exist_ok=True)
        
    def save_state(self, state_data: Dict[str, Any], 
                   tick: int,
                   simulation_id: Optional[str] = None,
                   is_checkpoint: bool = False) -> Optional[str]:
        """
        Guarda un estado de simulación.
        
        Args:
            state_data: Diccionario con el estado completo
            tick: Tick actual de la simulación
            simulation_id: ID de la simulación (opcional)
            is_checkpoint: Si es un checkpoint de recuperación automática
            
        Returns:
            Path del archivo guardado o None si falla
        """
        try:
            # Preparar estado para guardar
            state = {
                "saved_at": datetime.now().isoformat(),
                "tick": tick,
                "simulation_id": simulation_id,
                "state": state_data
            }
            
            # Determinar directorio y nombre de archivo
            if is_checkpoint:
                target_dir = self.checkpoints_dir
                filename = f"checkpoint_tick_{tick}.pkl"
            else:
                target_dir = self.snapshots_dir
                if simulation_id:
                    filename = f"{simulation_id}_tick_{tick}.pkl"
                else:
                    filename = f"state_tick_{tick}.pkl"
            
            filepath = target_dir / filename
            temp_filepath = target_dir / f"{filename}.tmp"
            
            # Escribir a archivo temporal primero (seguridad)
            with open(temp_filepath, 'wb') as f:
                pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass  # os.fsync puede fallar en algunos entornos
            
            # Mover de forma atómica
            os.replace(str(temp_filepath), str(filepath))
            
            # Verificar que el archivo existe
            if filepath.exists():
                return str(filepath)
            else:
                return None
                
        except Exception as e:
            return None
    
    def load_state(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Carga un estado desde un archivo.
        
        Args:
            filepath: Path al archivo de estado
            
        Returns:
            Diccionario con el estado o None si falla
        """
        try:
            with open(filepath, 'rb') as f:
                state = pickle.load(f)
            
            # Validar estructura
            if not isinstance(state, dict) or "state" not in state:
                return None
            
            return state
            
        except (EOFError, pickle.UnpicklingError, FileNotFoundError):
            return None
        except Exception:
            return None
    
    def save_manual(self, state_data: Dict[str, Any],
                   name: str,
                   description: Optional[str] = None) -> Optional[str]:
        """
        Guarda un estado manualmente con nombre personalizado.
        
        Args:
            state_data: Estado a guardar
            name: Nombre del guardado
            description: Descripción opcional
            
        Returns:
            Path del archivo guardado o None si falla
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}.pkl"
            filepath = self.manual_saves_dir / filename
            
            state = {
                "saved_at": datetime.now().isoformat(),
                "name": name,
                "description": description,
                "state": state_data
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            
            return str(filepath) if filepath.exists() else None
            
        except Exception:
            return None
    
    def load_manual(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Carga un estado guardado manualmente.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Estado cargado o None si falla
        """
        filepath = self.manual_saves_dir / filename
        return self.load_state(str(filepath))
    
    def list_snapshots(self, simulation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista todos los snapshots disponibles.
        
        Args:
            simulation_id: Filtrar por ID de simulación (opcional)
            
        Returns:
            Lista de diccionarios con información de snapshots
        """
        snapshots = []
        
        for filepath in self.snapshots_dir.glob("*.pkl"):
            try:
                state = self.load_state(str(filepath))
                if state is None:
                    continue
                
                # Filtrar por simulation_id si se especifica
                if simulation_id and state.get("simulation_id") != simulation_id:
                    continue
                
                snapshot_info = {
                    "filename": filepath.name,
                    "filepath": str(filepath),
                    "tick": state.get("tick", 0),
                    "saved_at": state.get("saved_at"),
                    "simulation_id": state.get("simulation_id"),
                    "size_bytes": filepath.stat().st_size
                }
                snapshots.append(snapshot_info)
                
            except Exception:
                continue
        
        # Ordenar por tick
        snapshots.sort(key=lambda x: x["tick"])
        
        return snapshots
    
    def list_manual_saves(self) -> List[Dict[str, Any]]:
        """
        Lista todos los guardados manuales.
        
        Returns:
            Lista de diccionarios con información de guardados
        """
        saves = []
        
        for filepath in self.manual_saves_dir.glob("*.pkl"):
            try:
                state = self.load_state(str(filepath))
                if state is None:
                    continue
                
                save_info = {
                    "filename": filepath.name,
                    "filepath": str(filepath),
                    "name": state.get("name", "Sin nombre"),
                    "description": state.get("description"),
                    "saved_at": state.get("saved_at"),
                    "size_bytes": filepath.stat().st_size
                }
                saves.append(save_info)
                
            except Exception:
                continue
        
        # Ordenar por fecha (más recientes primero)
        saves.sort(key=lambda x: x["saved_at"], reverse=True)
        
        return saves
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """
        Lista todos los checkpoints disponibles.
        
        Returns:
            Lista de diccionarios con información de checkpoints
        """
        checkpoints = []
        
        for filepath in self.checkpoints_dir.glob("checkpoint_tick_*.pkl"):
            try:
                state = self.load_state(str(filepath))
                if state is None:
                    continue
                
                checkpoint_info = {
                    "filename": filepath.name,
                    "filepath": str(filepath),
                    "tick": state.get("tick", 0),
                    "saved_at": state.get("saved_at"),
                    "size_bytes": filepath.stat().st_size
                }
                checkpoints.append(checkpoint_info)
                
            except Exception:
                continue
        
        # Ordenar por tick
        checkpoints.sort(key=lambda x: x["tick"])
        
        return checkpoints
    
    def get_latest_checkpoint(self) -> Optional[str]:
        """
        Obtiene el checkpoint más reciente.
        
        Returns:
            Path al checkpoint más reciente o None
        """
        checkpoints = self.list_checkpoints()
        
        if not checkpoints:
            return None
        
        # Retornar el de mayor tick
        latest = max(checkpoints, key=lambda x: x["tick"])
        return latest["filepath"]
    
    def find_state_by_tick(self, target_tick: int,
                          simulation_id: Optional[str] = None) -> Optional[str]:
        """
        Busca un estado por su tick.
        
        Args:
            target_tick: Tick objetivo
            simulation_id: ID de simulación (opcional)
            
        Returns:
            Path al estado más cercano o None
        """
        snapshots = self.list_snapshots(simulation_id)
        
        if not snapshots:
            return None
        
        # Buscar el snapshot con tick exacto o el más cercano inferior
        best_match = None
        for snapshot in snapshots:
            if snapshot["tick"] <= target_tick:
                if best_match is None or snapshot["tick"] > best_match["tick"]:
                    best_match = snapshot
        
        return best_match["filepath"] if best_match else None
    
    def cleanup_old_snapshots(self, keep_count: int = 50,
                             simulation_id: Optional[str] = None):
        """
        Limpia snapshots antiguos manteniendo solo los más recientes.
        
        Args:
            keep_count: Número de snapshots a mantener
            simulation_id: Filtrar por simulación (opcional)
        """
        snapshots = self.list_snapshots(simulation_id)
        
        # Si hay más snapshots de los que queremos mantener
        if len(snapshots) > keep_count:
            # Mantener los más recientes (por tick)
            to_delete = snapshots[:-keep_count]
            
            for snapshot in to_delete:
                try:
                    Path(snapshot["filepath"]).unlink()
                except Exception:
                    pass
    
    def cleanup_checkpoints(self, keep_count: int = 10):
        """
        Limpia checkpoints antiguos manteniendo solo los más recientes.
        
        Args:
            keep_count: Número de checkpoints a mantener
        """
        checkpoints = self.list_checkpoints()
        
        if len(checkpoints) > keep_count:
            to_delete = checkpoints[:-keep_count]
            
            for checkpoint in to_delete:
                try:
                    Path(checkpoint["filepath"]).unlink()
                except Exception:
                    pass
    
    def delete_snapshot(self, filename: str) -> bool:
        """
        Elimina un snapshot específico.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            True si se eliminó, False si no
        """
        filepath = self.snapshots_dir / filename
        try:
            if filepath.exists():
                filepath.unlink()
                return True
        except Exception:
            pass
        return False
    
    def delete_manual_save(self, filename: str) -> bool:
        """
        Elimina un guardado manual.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            True si se eliminó, False si no
        """
        filepath = self.manual_saves_dir / filename
        try:
            if filepath.exists():
                filepath.unlink()
                return True
        except Exception:
            pass
        return False
    
    def clear_all_states(self, confirm: bool = False):
        """
        Elimina todos los estados guardados (PELIGROSO).
        
        Args:
            confirm: Debe ser True para confirmar la acción
        """
        if not confirm:
            raise ValueError("Debe confirmar la acción con confirm=True")
        
        # Eliminar todos los directorios y recrearlos
        try:
            if self.snapshots_dir.exists():
                shutil.rmtree(self.snapshots_dir)
            if self.checkpoints_dir.exists():
                shutil.rmtree(self.checkpoints_dir)
            
            self.snapshots_dir.mkdir(exist_ok=True)
            self.checkpoints_dir.mkdir(exist_ok=True)
        except Exception:
            pass
    
    def get_total_size(self) -> Dict[str, int]:
        """
        Calcula el tamaño total de todos los estados guardados.
        
        Returns:
            Diccionario con tamaños por categoría en bytes
        """
        sizes = {
            "snapshots": 0,
            "manual_saves": 0,
            "checkpoints": 0,
            "total": 0
        }
        
        # Calcular tamaño de snapshots
        for filepath in self.snapshots_dir.glob("*.pkl"):
            try:
                sizes["snapshots"] += filepath.stat().st_size
            except Exception:
                pass
        
        # Calcular tamaño de guardados manuales
        for filepath in self.manual_saves_dir.glob("*.pkl"):
            try:
                sizes["manual_saves"] += filepath.stat().st_size
            except Exception:
                pass
        
        # Calcular tamaño de checkpoints
        for filepath in self.checkpoints_dir.glob("*.pkl"):
            try:
                sizes["checkpoints"] += filepath.stat().st_size
            except Exception:
                pass
        
        sizes["total"] = sizes["snapshots"] + sizes["manual_saves"] + sizes["checkpoints"]
        
        return sizes
    
    def create_checkpoint(self, state_data: Dict[str, Any], tick: int) -> Optional[str]:
        """
        Crea un checkpoint de recuperación automática.
        Mantiene solo los últimos 10 checkpoints.
        
        Args:
            state_data: Estado a guardar
            tick: Tick actual
            
        Returns:
            Path del checkpoint creado
        """
        filepath = self.save_state(state_data, tick, is_checkpoint=True)
        
        # Limpiar checkpoints antiguos
        self.cleanup_checkpoints(keep_count=10)
        
        return filepath

