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
from pathlib import Path

# Importar sistema de persistencia
try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from persistence.persistence_manager import PersistenceManager
except ImportError:
    PersistenceManager = None  # Si no está disponible, continuar sin persistencia

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
        self._project_root = Path(__file__).resolve().parents[1]
        self._saved_states_dir = self._project_root / 'saved_states'
        
        # Sistema de persistencia
        if PersistenceManager is not None:
            try:
                self.persistence = PersistenceManager(self._project_root)
            except Exception:
                self.persistence = None
        else:
            self.persistence = None
        
        # Estado del juego terminado
        self.game_over_info = None  # Información del ganador
        
        # Sistema de animaciones de colisiones
        self.collision_animations = []  # Lista de animaciones activas

        # Generar posiciones
        base_positions = self.map.generate_bases()

        # Crear jugadores con sus bases
        self.player1 = Player("Jugador_1", base_positions["player1"])
        self.player2 = Player("Jugador_2", base_positions["player2"])

    def add_collision_animation(self, position, animation_type="vehicle"):
        """Agrega una animación de colisión en la posición especificada
        
        Args:
            position: Tupla (row, col) donde ocurrió la colisión
            animation_type: 'vehicle' para colisión entre vehículos, 'mine' para colisión con mina
        """
        animation = {
            'position': position,
            'type': animation_type,
            'frame': 0,  # Frame actual de la animación
            'max_frames': 20,  # Duración total de la animación en frames
        }
        self.collision_animations.append(animation)
    
    def update_collision_animations(self):
        """Actualiza todas las animaciones de colisión activas"""
        # Incrementar frame de cada animación y eliminar las completadas
        animations_to_remove = []
        for i, anim in enumerate(self.collision_animations):
            anim['frame'] += 1
            if anim['frame'] >= anim['max_frames']:
                animations_to_remove.append(i)
        
        # Eliminar animaciones completadas (en orden inverso para no alterar índices)
        for i in reversed(animations_to_remove):
            self.collision_animations.pop(i)
    
    def init_game(self):
        self.map.clear_map()
        self.collision_animations = []  # Limpiar animaciones al iniciar nuevo juego
        self.tick = 0  # Resetear tick a 0
        self.start_time = time.time()  # Resetear tiempo de inicio
        self.game_over_info = None  # Resetear información de game over
        # Variables de timeout para detectar juegos estancados
        self._last_score_change_tick = 0
        self._last_total_score = 0
        
        # Resetear puntajes de los jugadores
        self.player1.score = 0
        self.player2.score = 0
        
        # Recrear flotas de vehículos (resetear estado de vehículos)
        self.player1.vehicles = self.player1._create_fleet()
        self.player2.vehicles = self.player2._create_fleet()
        
        # Limpiar estados guardados anteriores para evitar confusión
        try:
            if self._saved_states_dir.exists():
                import shutil
                shutil.rmtree(self._saved_states_dir)
        except Exception:
            pass  # Silenciar error, no es crítico
        
        resources = self.map.generate_random_map()

        self.player1.resources = resources
        self.player2.resources = resources

        # Asignar estrategias a los jugadores
        try:
            # Estrategia 1 para player1: motos destruyen camiones, resto usa BFS
            self.player1.strategy = Strategy1(self.map.cols, self.map.rows, self.map, self.player2)
            
            # Estrategia 2 para player2: usa Dijkstra
            self.player2.strategy = Strategy2(self.map.cols, self.map.rows, self.map, self.player1)
        except Exception:
            self.player1.strategy = None
            self.player2.strategy = None

        # Inicializar vehículos en la base
        self._initialize_vehicles_at_base()
        
        # Iniciar registro de simulación en la base de datos
        if self.persistence is not None:
            try:
                config = {
                    "map": {
                        "rows": self.map.rows,
                        "cols": self.map.cols
                    }
                }
                self.persistence.start_new_simulation(config)
            except Exception:
                pass  # Si falla, continuar sin persistencia

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
            
            # Guardar las estrategias temporalmente y eliminarlas antes de serializar
            # (tienen referencias circulares que causan RecursionError)
            strategy1 = self.player1.strategy
            strategy2 = self.player2.strategy
            self.player1.strategy = None
            self.player2.strategy = None
            
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
            
            # Restaurar las estrategias
            self.player1.strategy = strategy1
            self.player2.strategy = strategy2
            
            # Verificar que el archivo existe
            if final_path.exists():
                return str(final_path)
            else:
                return None
        except Exception:
            # Asegurar que restauramos las estrategias incluso si hay error
            try:
                if 'strategy1' in locals():
                    self.player1.strategy = strategy1
                if 'strategy2' in locals():
                    self.player2.strategy = strategy2
            except:
                pass
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
            
            # Restaurar las estrategias (no se guardan por referencias circulares)
            try:
                self.player1.strategy = Strategy1(self.map.cols, self.map.rows, self.map, self.player2)
                self.player2.strategy = Strategy2(self.map.cols, self.map.rows, self.map, self.player1)
            except Exception:
                self.player1.strategy = None
                self.player2.strategy = None
            
            return True
        except (EOFError, pickle.UnpicklingError):
            return False
        except Exception:
            return False

    def step_forward(self):
        """Avanza un paso en la simulación"""
        # Ejecutar un único tick aunque el motor esté en pausa
        # (update ya guarda el estado cuando force=True)
        self.update(force=True)
        
    def step_backward(self):
        """Retrocede un paso en la simulación"""
        # Verificar que exista la carpeta de estados
        if not self._saved_states_dir.exists():
            return
        
        if self.tick <= 0:
            return
        
        # Buscar el estado guardado más cercano antes del tick actual
        target_tick = self.tick - 1
        filename = str(self._saved_states_dir / f'state_{target_tick}.pickle')
        
        if os.path.exists(filename):
            ok = self.load_state(filename)
            if ok:
                return
        
        # Si no existe ese tick exacto, buscar el más cercano anterior
        for t in range(target_tick - 1, -1, -1):
            filename = str(self._saved_states_dir / f'state_{t}.pickle')
            if os.path.exists(filename):
                ok = self.load_state(filename)
                if ok:
                    break
    
    def _check_game_over_conditions(self):
        """Verifica si se cumplen las condiciones de fin de juego"""
        # Condición 1: No hay más recursos en el mapa
        resources_remaining = sum(1 for row in range(self.map.rows) 
                                 for col in range(self.map.cols) 
                                 if self.map.graph.get_node(row, col).state == "resource")
        
        # Condición 2: Contar vehículos por estado
        p1_active_vehicles = sum(1 for v in self.player1.vehicles.values() 
                                if v.status not in ["destroyed"])
        p2_active_vehicles = sum(1 for v in self.player2.vehicles.values() 
                                if v.status not in ["destroyed"])
        
        # Contar vehículos en misión/retorno (que no están en base)
        p1_vehicles_outside_base = sum(1 for v in self.player1.vehicles.values() 
                                       if v.status in ["in_mission", "returning", "need_return", "moving"])
        p2_vehicles_outside_base = sum(1 for v in self.player2.vehicles.values() 
                                       if v.status in ["in_mission", "returning", "need_return", "moving"])
        
        # Contar vehículos con recursos recolectados
        p1_vehicles_with_resources = sum(1 for v in self.player1.vehicles.values() 
                                         if v.status not in ["destroyed"] and getattr(v, "collected_value", 0) > 0)
        p2_vehicles_with_resources = sum(1 for v in self.player2.vehicles.values() 
                                         if v.status not in ["destroyed"] and getattr(v, "collected_value", 0) > 0)
        
        # El juego termina por falta de vehículos si ambos equipos no tienen vehículos activos
        if p1_active_vehicles == 0 and p2_active_vehicles == 0:
            return True, "Todos los vehículos han sido destruidos"
        
        # Contar vehículos en estado "job_done" (terminaron su trabajo)
        p1_job_done = sum(1 for v in self.player1.vehicles.values() 
                         if v.status == "job_done")
        p2_job_done = sum(1 for v in self.player2.vehicles.values() 
                         if v.status == "job_done")
        
        # Condición nueva: Si todos los vehículos no destruidos están en "job_done", terminar el juego
        if p1_active_vehicles > 0 and p2_active_vehicles > 0:
            # Ambos jugadores tienen vehículos activos
            if p1_job_done == p1_active_vehicles and p2_job_done == p2_active_vehicles:
                return True, "Todos los vehículos han completado su trabajo"
        elif p1_active_vehicles > 0:
            # Solo jugador 1 tiene vehículos activos
            if p1_job_done == p1_active_vehicles:
                return True, "Todos los vehículos han completado su trabajo"
        elif p2_active_vehicles > 0:
            # Solo jugador 2 tiene vehículos activos
            if p2_job_done == p2_active_vehicles:
                return True, "Todos los vehículos han completado su trabajo"
        
        # El juego termina por falta de recursos solo si:
        # 1. No hay recursos en el mapa
        # 2. No hay vehículos fuera de base (todos están en base, destruidos o terminaron)
        # 3. No hay vehículos con recursos sin entregar
        if resources_remaining == 0:
            vehicles_outside = p1_vehicles_outside_base + p2_vehicles_outside_base
            vehicles_with_resources = p1_vehicles_with_resources + p2_vehicles_with_resources
            
            if vehicles_outside == 0 and vehicles_with_resources == 0:
                return True, "No quedan recursos y todos los vehículos han retornado"
            else:
                # Hay recursos sin entregar, esperar a que los vehículos regresen
                pass
        
        # Timeout: si pasan muchos ticks sin cambios, terminar el juego
        # (Para evitar juegos infinitos donde vehículos no recogen recursos disponibles)
        if not hasattr(self, '_last_score_change_tick'):
            self._last_score_change_tick = 0
            self._last_total_score = 0
        
        current_total_score = self.player1.score + self.player2.score
        if current_total_score != self._last_total_score:
            self._last_score_change_tick = self.tick
            self._last_total_score = current_total_score
        
        # Si pasan 500 ticks sin cambio en el puntaje y hay recursos disponibles, hay un problema
        ticks_without_progress = self.tick - self._last_score_change_tick
        
        if ticks_without_progress > 500 and resources_remaining > 0:
            return True, f"Juego detenido por inactividad (quedan {resources_remaining} recursos)"
        
        return False, None
    
    def _determine_winner(self, reason):
        """Determina el ganador basándose en los puntos"""
        p1_score = self.player1.score
        p2_score = self.player2.score
        
        # Contar vehículos por estado para cada jugador
        p1_vehicles_status = {
            "in_base": 0,
            "in_mission": 0,
            "returning": 0,
            "job_done": 0,
            "destroyed": 0
        }
        
        p2_vehicles_status = {
            "in_base": 0,
            "in_mission": 0,
            "returning": 0,
            "job_done": 0,
            "destroyed": 0
        }
        
        for v in self.player1.vehicles.values():
            if v.status in p1_vehicles_status:
                p1_vehicles_status[v.status] += 1
        
        for v in self.player2.vehicles.values():
            if v.status in p2_vehicles_status:
                p2_vehicles_status[v.status] += 1
        
        # Determinar ganador
        if p1_score > p2_score:
            winner = "Jugador 1"
            winner_color = "blue"
        elif p2_score > p1_score:
            winner = "Jugador 2"
            winner_color = "red"
        else:
            winner = "Empate"
            winner_color = "gray"
        
        return {
            "winner": winner,
            "winner_color": winner_color,
            "reason": reason,
            "player1": {
                "name": "Jugador 1",
                "score": p1_score,
                "vehicles": p1_vehicles_status
            },
            "player2": {
                "name": "Jugador 2",
                "score": p2_score,
                "vehicles": p2_vehicles_status
            }
        }
    
    def update(self, force: bool = False):
        """Actualiza el estado del juego.

        Si force=True, ejecuta un único tick aunque el motor no esté en "running".
        """
        # No actualizar si el juego ya terminó
        if self.state == "game_over":
            return
            
        if self.state != "running" and not force:
            return
        
        # Guardar el estado actual antes de avanzar (para poder retroceder)
        # Guardar siempre en modo paso a paso, o cada 5 ticks en modo automático
        should_save = force or (self.state == "running" and self.tick % 5 == 0)
        if should_save:
            self.save_state()

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
        except Exception:
            pass  # Silenciar error

        # Verificar si algún vehículo está en una posición minada después de actualizar las minas
        self._check_vehicles_on_mines()

        resources = self.map.all_resources()
        
        # Mover vehículos del jugador 1 usando su estrategia si está presente
        strategy1 = getattr(self.player1, "strategy", None)
        if strategy1 is not None and callable(getattr(strategy1, "update", None)):
            try:
                strategy1.update(self.player1)
            except Exception:
                pass  # Silenciar error
        
        # Mover vehículos del jugador 2 usando su estrategia si está presente
        strategy2 = getattr(self.player2, "strategy", None)
        if strategy2 is not None and callable(getattr(strategy2, "update", None)):
            try:
                strategy2.update(self.player2)
            except Exception:
                pass  # Silenciar error
        
        # Verificar colisiones entre vehículos de equipos distintos
        self._check_vehicle_collisions()
        
        # Verificar colisiones entre vehículos del mismo equipo (no deben destruirse)
        self._check_same_team_collisions()
        
        # Verificar consistencia de vehículos (detectar "fantasmas")
        self._check_vehicle_consistency()
        
        # Limpiar vehículos destruidos del mapa
        self._cleanup_destroyed_vehicles()
        
        # Verificar condiciones de fin de juego
        game_over, reason = self._check_game_over_conditions()
        if game_over:
            self.state = "game_over"
            self.game_over_info = self._determine_winner(reason)
            
            # Guardar simulación en la base de datos
            self._save_simulation_to_database(reason)
    
    def _check_vehicles_on_mines(self):
        """Verifica si algún vehículo está en una posición minada y lo destruye"""
        for row in range(self.map.rows):
            for col in range(self.map.cols):
                node = self.map.graph.get_node(row, col)
                if node and (node.state == "vehicle" or node.state in ("base_p1", "base_p2")) and node.content:
                    vehicle_content = node.content
                    
                    # Manejar listas de vehículos (mismo equipo en misma celda)
                    vehicles_to_check = []
                    if isinstance(vehicle_content, list):
                        vehicles_to_check = vehicle_content
                    else:
                        vehicles_to_check = [vehicle_content]
                    
                    for vehicle_data in vehicles_to_check:
                        vehicle_obj = None
                        
                        if isinstance(vehicle_data, dict):
                            vehicle_obj = vehicle_data.get("object")
                        else:
                            vehicle_obj = vehicle_data
                        
                        if vehicle_obj and hasattr(vehicle_obj, "status") and vehicle_obj.status != "destroyed":
                            # Verificar si la posición actual del vehículo está minada
                            if self.map.mine_manager.isCellMined((row, col), self.tick):
                                vehicle_obj.status = "destroyed"
                                vehicle_obj.collected_value = 0
                                # Agregar animación de colisión con mina
                                self.add_collision_animation((row, col), animation_type="mine")

    def _check_vehicle_collisions(self):
        """Detecta y procesa colisiones entre vehículos de equipos distintos"""
        # Crear diccionario de posiciones -> vehículos activos para cada jugador
        player1_positions = {}
        player2_positions = {}
        
        # Recopilar posiciones de vehículos activos del jugador 1 (no destruidos)
        for vehicle_id, vehicle in self.player1.vehicles.items():
            if vehicle.status != "destroyed":
                pos = vehicle.position
                # Verificar que la posición sea válida
                if isinstance(pos, tuple) and len(pos) == 2:
                    if pos not in player1_positions:
                        player1_positions[pos] = []
                    player1_positions[pos].append(vehicle)
        
        # Recopilar posiciones de vehículos activos del jugador 2 (no destruidos)
        for vehicle_id, vehicle in self.player2.vehicles.items():
            if vehicle.status != "destroyed":
                pos = vehicle.position
                # Verificar que la posición sea válida
                if isinstance(pos, tuple) and len(pos) == 2:
                    if pos not in player2_positions:
                        player2_positions[pos] = []
                    player2_positions[pos].append(vehicle)
        
        # Detectar colisiones: si hay vehículos de ambos jugadores en la misma posición
        for pos in player1_positions:
            if pos in player2_positions:
                # Hay colisión en esta posición - destruir TODOS los vehículos involucrados
                vehicles1_ids = []
                for vehicle1 in player1_positions[pos]:
                    # Solo destruir si no está ya destruido
                    if vehicle1.status != "destroyed":
                        vehicle1.status = "destroyed"
                        vehicle1.collected_value = 0
                        vehicles1_ids.append(vehicle1.id)
                
                vehicles2_ids = []
                for vehicle2 in player2_positions[pos]:
                    # Solo destruir si no está ya destruido
                    if vehicle2.status != "destroyed":
                        vehicle2.status = "destroyed"
                        vehicle2.collected_value = 0
                        vehicles2_ids.append(vehicle2.id)
                
                # Agregar animación de colisión entre vehículos
                if vehicles1_ids or vehicles2_ids:
                    self.add_collision_animation(pos, animation_type="vehicle")
    
    def _check_same_team_collisions(self):
        """Detecta colisiones entre vehículos del mismo equipo y reporta (NO deben destruirse)"""
        # Verificar colisiones dentro del equipo 1
        player1_positions = {}
        for vehicle_id, vehicle in self.player1.vehicles.items():
            if vehicle.status not in ["destroyed", "in_base"]:
                pos = vehicle.position
                if isinstance(pos, tuple) and len(pos) == 2:
                    if pos not in player1_positions:
                        player1_positions[pos] = []
                    player1_positions[pos].append(vehicle)
        
        # Verificar colisiones dentro del equipo 2
        player2_positions = {}
        for vehicle_id, vehicle in self.player2.vehicles.items():
            if vehicle.status not in ["destroyed", "in_base"]:
                pos = vehicle.position
                if isinstance(pos, tuple) and len(pos) == 2:
                    if pos not in player2_positions:
                        player2_positions[pos] = []
                    player2_positions[pos].append(vehicle)
    
    def _check_vehicle_consistency(self):
        """Verifica que vehículos activos realmente existan en el mapa, marca como destruidos los 'fantasmas'"""
        for player in [self.player1, self.player2]:
            for vehicle_id, vehicle in player.vehicles.items():
                # Solo verificar vehículos que dicen estar en misión o regresando
                # No verificar vehículos en base, destruidos, o terminados
                if vehicle.status not in ["in_base", "destroyed", "job_done"]:
                    pos = vehicle.position
                    
                    # Verificar que la posición sea válida
                    if not (isinstance(pos, tuple) and len(pos) == 2):
                        vehicle.status = "destroyed"
                        vehicle.collected_value = 0
                        continue
                    
                    row, col = pos
                    
                    # Verificar que esté dentro de los límites del mapa
                    if not (0 <= row < self.map.rows and 0 <= col < self.map.cols):
                        vehicle.status = "destroyed"
                        vehicle.collected_value = 0
                        continue
                    
                    # Verificar que el vehículo realmente exista en esa posición del mapa
                    node = self.map.graph.get_node(row, col)
                    if node:
                        vehicle_found = False
                        
                        # Buscar el vehículo en el nodo
                        # Puede estar en estado "vehicle" o en una base
                        if node.content:
                            vehicle_content = node.content
                            
                            # Manejar listas de vehículos (mismo equipo en misma celda)
                            if isinstance(vehicle_content, list):
                                for vehicle_data in vehicle_content:
                                    node_vehicle_id = None
                                    if isinstance(vehicle_data, dict):
                                        node_vehicle_id = vehicle_data.get("id")
                                    else:
                                        node_vehicle_id = getattr(vehicle_data, "id", None)
                                    
                                    if node_vehicle_id == vehicle_id:
                                        vehicle_found = True
                                        break
                            else:
                                node_vehicle_id = None
                                
                                if isinstance(vehicle_content, dict):
                                    node_vehicle_id = vehicle_content.get("id")
                                else:
                                    node_vehicle_id = getattr(vehicle_content, "id", None)
                                
                                if node_vehicle_id == vehicle_id:
                                    vehicle_found = True
                        
                        # Si el vehículo no está en el mapa pero dice estar activo, marcarlo como destruido
                        # PERO solo si no está en una posición de base (puede estar retornando)
                        if not vehicle_found:
                            # Verificar si está en una posición de base
                            is_base_position = node.state in ("base_p1", "base_p2")
                            
                            # Solo marcar como fantasma si no está en una base
                            # (puede estar retornando y acaba de llegar a la base)
                            if not is_base_position:
                                vehicle.status = "destroyed"
                                vehicle.collected_value = 0

    def _cleanup_destroyed_vehicles(self):
        """Limpia los vehículos destruidos del mapa"""
        for row in range(self.map.rows):
            for col in range(self.map.cols):
                node = self.map.graph.get_node(row, col)
                if node and (node.state == "vehicle" or node.state in ("base_p1", "base_p2")) and node.content:
                    vehicle_content = node.content
                    
                    # Manejar listas de vehículos (mismo equipo en misma celda)
                    if isinstance(vehicle_content, list):
                        # Filtrar vehículos destruidos de la lista
                        vehicles_to_keep = []
                        for vehicle_data in vehicle_content:
                            vehicle_obj = None
                            if isinstance(vehicle_data, dict):
                                vehicle_obj = vehicle_data.get("object")
                            else:
                                vehicle_obj = vehicle_data
                            
                            # Mantener solo vehículos no destruidos
                            if vehicle_obj and hasattr(vehicle_obj, "status"):
                                if vehicle_obj.status != "destroyed":
                                    vehicles_to_keep.append(vehicle_data)
                        
                        # Actualizar contenido del nodo
                        if vehicles_to_keep:
                            # Si quedan vehículos vivos, mantener la lista (o convertir a single si es 1)
                            if len(vehicles_to_keep) == 1:
                                node.content = vehicles_to_keep[0]
                            else:
                                node.content = vehicles_to_keep
                        else:
                            # Si no quedan vehículos vivos, limpiar el nodo
                            if node.state in ("base_p1", "base_p2"):
                                node.state = node.state
                                node.content = {}
                            else:
                                node.state = "empty"
                                node.content = {}
                    else:
                        # Manejar vehículo único
                        vehicle_obj = None
                        
                        if isinstance(vehicle_content, dict):
                            vehicle_obj = vehicle_content.get("object")
                        else:
                            vehicle_obj = vehicle_content
                        
                        if vehicle_obj and hasattr(vehicle_obj, "status"):
                            if vehicle_obj.status == "destroyed":
                                # Limpiar el nodo
                                if node.state in ("base_p1", "base_p2"):
                                    # Restaurar estado de base sin vehículo
                                    node.state = node.state
                                    node.content = {}
                                else:
                                    node.state = "empty"
                                    node.content = {}
    
    def _save_simulation_to_database(self, reason):
        """Guarda la simulación en la base de datos cuando termina el juego"""
        if self.persistence is None:
            return
        
        try:
            # Obtener información del ganador
            winner_name = self.game_over_info.get("winner", "Empate")
            if winner_name == "Jugador 1":
                winner_name = "Jugador_1"
            elif winner_name == "Jugador 2":
                winner_name = "Jugador_2"
            
            # Calcular estadísticas de jugadores
            p1_stats = self._calculate_player_stats(self.player1)
            p2_stats = self._calculate_player_stats(self.player2)
            
            # Finalizar simulación
            self.persistence.finish_simulation(
                total_ticks=self.tick,
                winner=winner_name,
                final_score_p1=self.player1.score,
                final_score_p2=self.player2.score,
                end_reason=reason
            )
            
            # Registrar estadísticas de jugadores
            self.persistence.record_player_stats("Jugador_1", p1_stats)
            self.persistence.record_player_stats("Jugador_2", p2_stats)
            
        except Exception as e:
            # Silenciar errores de persistencia, no es crítico para el juego
            pass
    
    def _calculate_player_stats(self, player):
        """Calcula las estadísticas de un jugador para guardar en la base de datos"""
        vehicles_destroyed = sum(1 for v in player.vehicles.values() if v.status == "destroyed")
        vehicles_survived = sum(1 for v in player.vehicles.values() if v.status != "destroyed")
        
        # Contar recursos recolectados (sumar valores de recursos recolectados)
        resources_collected = 0
        total_distance = 0.0
        collisions = 0
        mine_hits = 0
        
        for vehicle in player.vehicles.values():
            # Recursos recolectados (valor total entregado)
            if hasattr(vehicle, 'collected_value'):
                resources_collected += vehicle.collected_value
            
            # Distancia recorrida
            if hasattr(vehicle, 'distance_traveled'):
                total_distance += vehicle.distance_traveled
            
            # Colisiones y minas (si están registradas)
            if hasattr(vehicle, 'collision_count'):
                collisions += vehicle.collision_count
            if hasattr(vehicle, 'mine_hit_count'):
                mine_hits += vehicle.mine_hit_count
        
        return {
            "final_score": player.score,
            "vehicles_destroyed": vehicles_destroyed,
            "vehicles_survived": vehicles_survived,
            "resources_collected": resources_collected,
            "total_distance_traveled": total_distance,
            "collisions": collisions,
            "mine_hits": mine_hits
        }
