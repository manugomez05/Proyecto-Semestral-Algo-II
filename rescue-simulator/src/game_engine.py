"""
Módulo: game_engine
-------------------------------------------------
Contiene la clase GameEngine, que maneja la lógica general 
de la simulación y el flujo del juego.

Responsabilidades:
- Controlar los estados del simulador: "init", "running", "stopped".
- Comunicar la generación del mapa (`MapManager`) con la visualización.
- Actualizar el estado del juego (vehículos, recursos, minas, etc).
- Procesar las acciones de los botones (iniciar, detener, etc).
"""


from src.map_manager import MapManager
from src.player import Player
from config.strategies.player1_strategies import Strategy1
import sys
import importlib.util
import os
import pickle
import time

# Importar Strategy2 desde player2.strategies.py (nombre con punto requiere importación especial)
spec = importlib.util.spec_from_file_location(
    "player2_strategies", 
    os.path.join(os.path.dirname(__file__), "..", "config", "strategies", "player2.strategies.py")
)
player2_strategies_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(player2_strategies_module)
Strategy2 = player2_strategies_module.Strategy2

class GameEngine:
    def __init__(self):
        self.state = "stopped"
        self.map = MapManager(50, 50)
        self.tick = 0  # Contador de tiempo para minas dinámicas
        self.start_time = time.time()  # Tiempo de inicio para minas basadas en tiempo
        # Directorio raíz del proyecto (rescue-simulator)
        from pathlib import Path
        self._project_root = Path(__file__).resolve().parents[1]
        self._saved_states_dir = self._project_root / 'saved_states'

        # Generar posiciones
        base_positions = self.map.generate_bases()

        # Crear jugadores con sus bases
        self.player1 = Player("Jugador_1", base_positions["player1"])
        self.player2 = Player("Jugador_2", base_positions["player2"])

        

    def init_game(self):
        print("Inicializando mapa...")
        self.map.clear_map()
        resources = self.map.generate_random_map()

        self.player1.resources = resources
        self.player2.resources = resources

        # Asignar estrategias a los jugadores
        try:
            # Estrategia 1 para player1: motos destruyen camiones, resto usa BFS
            self.player1.strategy = Strategy1(self.map.cols, self.map.rows, self.map, self.player2)
            
            # Estrategia 2 para player2: DESHABILITADA temporalmente
            # self.player2.strategy = Strategy2(self.map.cols, self.map.rows, self.map, self.player1)
            self.player2.strategy = None
        except Exception as e:
            print(f"Error al asignar estrategias: {e}")
            self.player1.strategy = None
            self.player2.strategy = None

        # Inicializar vehículos en la base
        self._initialize_vehicles_at_base()

        self.state = "init"
    
    def _initialize_vehicles_at_base(self):
        """
        Coloca todos los vehículos de ambos jugadores en sus respectivas bases.
        """
        # Obtener posiciones de las bases
        base_positions_p1 = self.map.get_base_positions_set()
        base_positions_p2 = self.map.get_base_positions_set()
        
        # Para player1: usar posiciones de la base izquierda (col < 2)
        p1_base_cells = [(row, col) for row, col in base_positions_p1 if col < 2]
        # Para player2: usar posiciones de la base derecha (col >= cols - 2)
        p2_base_cells = [(row, col) for row, col in base_positions_p2 if col >= self.map.cols - 2]
        
        # Colocar vehículos de player1 en su base y asignar posición específica
        vehicle_index = 0
        used_positions = set()  # Para evitar superposiciones
        for vehicle_id, vehicle in self.player1.vehicles.items():
            if vehicle_index < len(p1_base_cells):
                base_row, base_col = p1_base_cells[vehicle_index]
                
                # Verificar que la posición no esté ocupada
                while (base_row, base_col) in used_positions and vehicle_index < len(p1_base_cells) - 1:
                    vehicle_index += 1
                    base_row, base_col = p1_base_cells[vehicle_index]
                
                used_positions.add((base_row, base_col))
                
                # Asignar posición específica de base al vehículo
                vehicle.base_position = (base_row, base_col)
                # Asegurar que el vehículo esté en estado "in_base" antes de colocarlo
                vehicle.status = "in_base"
                # Colocar vehículo en la base usando place_vehicle
                try:
                    self.map.graph.place_vehicle(vehicle, base_row, base_col, player1=self.player1, player2=self.player2)
                except Exception as e:
                    # Fallback: actualizar posición directamente
                    vehicle.position = (base_row, base_col)
                    vehicle.status = "in_base"
                vehicle_index += 1
        
        # Colocar vehículos de player2 en su base y asignar posición específica
        vehicle_index = 0
        used_positions_p2 = set()  # Para evitar superposiciones
        for vehicle_id, vehicle in self.player2.vehicles.items():
            if vehicle_index < len(p2_base_cells):
                base_row, base_col = p2_base_cells[vehicle_index]
                
                # Verificar que la posición no esté ocupada
                while (base_row, base_col) in used_positions_p2 and vehicle_index < len(p2_base_cells) - 1:
                    vehicle_index += 1
                    base_row, base_col = p2_base_cells[vehicle_index]
                
                used_positions_p2.add((base_row, base_col))
                
                # Asignar posición específica de base al vehículo
                vehicle.base_position = (base_row, base_col)
                # Asegurar que el vehículo esté en estado "in_base" antes de colocarlo
                vehicle.status = "in_base"
                # Colocar vehículo en la base usando place_vehicle
                try:
                    self.map.graph.place_vehicle(vehicle, base_row, base_col, player1=self.player1, player2=self.player2)
                except Exception as e:
                    # Fallback: actualizar posición directamente
                    vehicle.position = (base_row, base_col)
                    vehicle.status = "in_base"
                vehicle_index += 1

    def start_game(self):
        self.state = "running"
        
        self.start_time = time.time()  # Reiniciar tiempo al iniciar

    def stop_game(self):
        self.state = "stopped"

    def save_state(self):
        """Guarda el estado actual de la simulación"""
        try:
            os.makedirs(self._saved_states_dir, exist_ok=True)
            state = {
                'state': self.state,
                'tick': self.tick,
                'start_time': self.start_time,
                'elapsed_time': time.time() - self.start_time,
                'player1': self.player1,
                'player2': self.player2,
                'map': self.map
            }
            final_path = self._saved_states_dir / f'state_{self.tick}.pickle'
            temp_path = self._saved_states_dir / f'state_{self.tick}.pickle.tmp'
            # Escribir en archivo temporal y mover de forma atómica
            with open(temp_path, 'wb') as f:
                pickle.dump(state, f)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    # os.fsync puede fallar en algunos entornos, no crítico
                    pass
            os.replace(str(temp_path), str(final_path))
            filename = str(final_path)
            print(f"Estado guardado en {filename}")
            return filename
        except Exception as e:
            print(f"Error al guardar estado: {e}")
            return None

    def load_state(self, filename):
        """Carga un estado previo de la simulación"""
        try:
            with open(filename, 'rb') as f:
                state = pickle.load(f)
            # asignar estado solo después de cargar correctamente
            self.state = state['state']
            self.tick = state['tick']
            self.start_time = time.time() - state['elapsed_time']
            self.player1 = state['player1']
            self.player2 = state['player2']
            self.map = state['map']
            # Actualizar el tick en el mapa después de cargar
            self.map.current_tick = self.tick
            print(f"Estado cargado desde {filename}")
            return True
        except (EOFError, pickle.UnpicklingError) as e:
            print(f"Error al cargar estado (archivo corrupto o incompleto): {e}")
            return False
        except Exception as e:
            print(f"Error inesperado al cargar estado: {e}")
            return False

    def step_forward(self):
        """Avanza un paso en la simulación"""
        # Guardar el estado actual antes de avanzar
        self.save_state()
        # Ejecutar un único tick aunque el motor esté en pausa
        self.update(force=True)
        
    def step_backward(self):
        """Retrocede un paso en la simulación"""
        print(f"step_backward() called at tick={self.tick}")
        if self.tick <= 0:
            print("Ya estás en el tick 0; no hay pasos anteriores")
            return
        # Intentar encontrar el último snapshot válido bajando desde tick-1 hacia 0
        found = False
        for t in range(self.tick - 1, -1, -1):
            filename = str(self._saved_states_dir / f'state_{t}.pickle')
            print(f"Probando archivo: {filename}")
            if os.path.exists(filename):
                ok = self.load_state(filename)
                if ok:
                    print(f"Retrocedido a tick {self.tick}")
                    found = True
                    break
                else:
                    print(f"Archivo corrupto: {filename}, intentando anterior...")
                    continue

        if not found:
            try:
                files = [str(p) for p in self._saved_states_dir.iterdir()] if self._saved_states_dir.exists() else []
            except Exception:
                files = []
            print("No se pudo retroceder. Archivos en saved_states:", files)
    
    def update(self, force: bool = False):
        """Actualiza el estado del juego.

        Si force=True, ejecuta un único tick aunque el motor no esté en "running".
        """
        if self.state != "running" and not force:
            return

        # Incrementar el contador de tiempo (tick)
        self.tick += 1
        
        # Actualizar el tick en el mapa para que las estrategias puedan accederlo
        self.map.current_tick = self.tick

        # Calcular tiempo transcurrido en segundos respecto a start_time
        current_time = time.time()
        elapsed_time = current_time - self.start_time

        # Actualizar minas dinámicas (G1) basadas en ticks
        try:
            self.map.mine_manager.updateAll(self.tick, self.map.rows, self.map.cols, elapsed_time, self.map)
        except Exception as e:
            print(f"Error al actualizar minas: {e}")

        # Verificar si algún vehículo está en una posición minada después de actualizar las minas
        self._check_vehicles_on_mines()

        resources = self.map.all_resources()
        
        # Limpiar vehículos destruidos del mapa
        self._cleanup_destroyed_vehicles()
        
        # Mover vehículos del jugador 1 usando su estrategia si está presente
        strategy1 = getattr(self.player1, "strategy", None)
        if strategy1 is not None and callable(getattr(strategy1, "update", None)):
            try:
                strategy1.update(self.player1)
            except Exception as e:
                print(f"Error al ejecutar estrategia player1: {e}")
        
        # Mover vehículos del jugador 2 usando su estrategia si está presente
        # DESHABILITADO temporalmente
        # strategy2 = getattr(self.player2, "strategy", None)
        # if strategy2 is not None and callable(getattr(strategy2, "update", None)):
        #     try:
        #         strategy2.update(self.player2)
        #     except Exception as e:
        #         print(f"Error al ejecutar estrategia player2: {e}")
    
    def _check_vehicles_on_mines(self):
        """Verifica si algún vehículo está en una posición minada y lo destruye"""
        for row in range(self.map.rows):
            for col in range(self.map.cols):
                node = self.map.graph.get_node(row, col)
                if node and (node.state == "vehicle" or node.state in ("base_p1", "base_p2")) and node.content:
                    vehicle_content = node.content
                    vehicle_obj = None
                    
                    if isinstance(vehicle_content, dict):
                        vehicle_obj = vehicle_content.get("object")
                    else:
                        vehicle_obj = vehicle_content
                    
                    if vehicle_obj and hasattr(vehicle_obj, "status") and vehicle_obj.status != "destroyed":
                        # Verificar si la posición actual del vehículo está minada
                        if self.map.mine_manager.isCellMined((row, col), self.tick):
                            vehicle_id = getattr(vehicle_obj, "id", "unknown")
                            vehicle_obj.status = "destroyed"
                            vehicle_obj.collected_value = 0

    def _cleanup_destroyed_vehicles(self):
        """Limpia los vehículos destruidos del mapa"""
        for row in range(self.map.rows):
            for col in range(self.map.cols):
                node = self.map.graph.get_node(row, col)
                if node and (node.state == "vehicle" or node.state in ("base_p1", "base_p2")) and node.content:
                    vehicle_content = node.content
                    vehicle_obj = None
                    
                    if isinstance(vehicle_content, dict):
                        vehicle_obj = vehicle_content.get("object")
                    else:
                        vehicle_obj = vehicle_content
                    
                    if vehicle_obj and hasattr(vehicle_obj, "status"):
                        if vehicle_obj.status == "destroyed":
                            # Debug: reportar vehículo destruido
                            vehicle_id = getattr(vehicle_obj, "id", "unknown")
                            
                            # Limpiar el nodo
                            if node.state in ("base_p1", "base_p2"):
                                # Restaurar estado de base sin vehículo
                                node.state = node.state
                                node.content = {}
                            else:
                                node.state = "empty"
                                node.content = {}
