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
import time
from pathlib import Path

# Importar sistema de persistencia
try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from persistence.persistence_manager import PersistenceManager
except ImportError:
    PersistenceManager = None

# Importar Strategy2
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
        
        # Sistema de persistencia
        if PersistenceManager is not None:
            try:
                self.persistence = PersistenceManager(self._project_root)
            except Exception:
                self.persistence = None
        else:
            self.persistence = None
        
<<<<<<< HEAD
        self.debug_events = []
        self.max_debug_events = 15 
        
        self.game_over_info = None 
=======
        # Estado del juego terminado
        self.game_over_info = None  # Información del ganador
>>>>>>> reestructuracion
        
        # Sistema de animaciones de colisiones
        self.collision_animations = [] 

        base_positions = self.map.generate_bases()

        # Crear jugadores con sus bases
        self.player1 = Player("Jugador_1", base_positions["player1"])
        self.player2 = Player("Jugador_2", base_positions["player2"])

<<<<<<< HEAD
        

    def add_debug_event(self, event_type, message, color=(255, 255, 255)):
        """Agrega un evento de debug para mostrar en pantalla"""
        event = {
            'tick': self.tick,
            'type': event_type, 
            'message': message,
            'color': color
        }
        self.debug_events.append(event)
        
        # Mantener solo los últimos N eventos
        if len(self.debug_events) > self.max_debug_events:
            self.debug_events.pop(0)
    
=======
>>>>>>> reestructuracion
    def add_collision_animation(self, position, animation_type="vehicle"):
        """Agrega una animación de colisión en la posición especificada
        
        Args:
            position: Tupla (row, col) donde ocurrió la colisión
            animation_type: 'vehicle' para colisión entre vehículos, 'mine' para colisión con mina
        """
        animation = {
            'position': position,
            'type': animation_type,
            'frame': 0,  
            'max_frames': 20, 
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
<<<<<<< HEAD
        self.debug_events = []  
        self.collision_animations = []  
        self.tick = 0  
        self.start_time = time.time() 
        self.game_over_info = None 
=======
        self.collision_animations = []  # Limpiar animaciones al iniciar nuevo juego
        self.tick = 0  # Resetear tick a 0
        self.start_time = time.time()  # Resetear tiempo de inicio
        self.game_over_info = None  # Resetear información de game over
        # Variables de timeout para detectar juegos estancados
>>>>>>> reestructuracion
        self._last_score_change_tick = 0
        self._last_total_score = 0
        
        self.player1.score = 0
        self.player2.score = 0
        
        # Recrear flotas de vehículos (resetear estado de vehículos)
        self.player1.vehicles = self.player1._create_fleet()
        self.player2.vehicles = self.player2._create_fleet()
        
<<<<<<< HEAD
        try:
            if self._saved_states_dir.exists():
                import shutil
                shutil.rmtree(self._saved_states_dir)
        except Exception:
            pass 
        
=======
>>>>>>> reestructuracion
        resources = self.map.generate_random_map()

        self.player1.resources = resources
        self.player2.resources = resources

        # Asignar estrategias a los jugadores
        try:
            # Estrategia 1 para player1: Usa BFS
            self.player1.strategy = Strategy1(self.map.cols, self.map.rows, self.map, self.player2)
            
            # Estrategia 2 para player2: usa Dijkstra
            self.player2.strategy = Strategy2(self.map.cols, self.map.rows, self.map, self.player1)
        except Exception:
            self.player1.strategy = None
            self.player2.strategy = None

        self._initialize_vehicles_at_base()
        
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
                pass

        self.state = "init"
    
    def _initialize_vehicles_at_base(self):
        """
        Coloca todos los vehículos de ambos jugadores en sus respectivas bases.
        """
        # Obtener posiciones de las bases
        base_positions_p1 = self.map.get_base_positions_set()
        base_positions_p2 = self.map.get_base_positions_set()
        
        p1_base_cells = [(row, col) for row, col in base_positions_p1 if col < 2]
        p2_base_cells = [(row, col) for row, col in base_positions_p2 if col >= self.map.cols - 2]
        
        vehicle_index = 0
        used_positions = set() 
        for vehicle_id, vehicle in self.player1.vehicles.items():
            if vehicle_index < len(p1_base_cells):
                base_row, base_col = p1_base_cells[vehicle_index]
                
                while (base_row, base_col) in used_positions and vehicle_index < len(p1_base_cells) - 1:
                    vehicle_index += 1
                    base_row, base_col = p1_base_cells[vehicle_index]
                
                used_positions.add((base_row, base_col))
                
                vehicle.base_position = (base_row, base_col)
                vehicle.status = "in_base"
                try:
                    self.map.graph.place_vehicle(vehicle, base_row, base_col, player1=self.player1, player2=self.player2)
                except Exception as e:
                    vehicle.position = (base_row, base_col)
                    vehicle.status = "in_base"
                vehicle_index += 1
        
        vehicle_index = 0
        used_positions_p2 = set() 
        for vehicle_id, vehicle in self.player2.vehicles.items():
            if vehicle_index < len(p2_base_cells):
                base_row, base_col = p2_base_cells[vehicle_index]
                
                while (base_row, base_col) in used_positions_p2 and vehicle_index < len(p2_base_cells) - 1:
                    vehicle_index += 1
                    base_row, base_col = p2_base_cells[vehicle_index]
                
                used_positions_p2.add((base_row, base_col))
                
                vehicle.base_position = (base_row, base_col)
                vehicle.status = "in_base"
                try:
                    self.map.graph.place_vehicle(vehicle, base_row, base_col, player1=self.player1, player2=self.player2)
                except Exception as e:
                    # Fallback: actualizar posición directamente
                    vehicle.position = (base_row, base_col)
                    vehicle.status = "in_base"
                vehicle_index += 1

    def start_game(self):
        self.state = "running"
<<<<<<< HEAD
        self.start_time = time.time()
        self.add_debug_event('system', "▶️ Simulación iniciada", (100, 255, 100))

    def stop_game(self):
        self.state = "stopped"
        self.add_debug_event('system', "⏸️ Simulación detenida", (255, 200, 100))

    def save_state(self):
        """Guarda el estado actual de la simulación"""
        try:
            os.makedirs(self._saved_states_dir, exist_ok=True)
            
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
            self.state = state['state']
            self.tick = state['tick']
            self.start_time = time.time() - state['elapsed_time']
            self.player1 = state['player1']
            self.player2 = state['player2']
            self.map = state['map']
            
            # Actualizar el tick en el mapa después de cargar
            self.map.current_tick = self.tick
            
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
        self.update(force=True)
        self.add_debug_event('system', f"⏩ Avanzado a tick {self.tick}", (100, 200, 255))
        
    def step_backward(self):
        """Retrocede un paso en la simulación"""
        if not self._saved_states_dir.exists():
            self.add_debug_event('system', "No hay estados guardados", (255, 100, 100))
            return
        
        if self.tick <= 0:
            self.add_debug_event('system', "Ya en tick 0", (200, 200, 0))
            return
        
        # Buscar el estado guardado más cercano antes del tick actual
        target_tick = self.tick - 1
        filename = str(self._saved_states_dir / f'state_{target_tick}.pickle')
        
        if os.path.exists(filename):
            ok = self.load_state(filename)
            if ok:
                self.add_debug_event('system', f"Retrocedido a tick {self.tick}", (100, 255, 100))
                return
        
        # Si no existe ese tick exacto, buscar el más cercano anterior
        found = False
        for t in range(target_tick - 1, -1, -1):
            filename = str(self._saved_states_dir / f'state_{t}.pickle')
            if os.path.exists(filename):
                ok = self.load_state(filename)
                if ok:
                    self.add_debug_event('system', f"Retrocedido a tick {self.tick}", (100, 255, 100))
                    found = True
                    break

        if not found:
            self.add_debug_event('system', "No hay estados guardados", (255, 100, 100))
=======
        self.start_time = time.time()  # Reiniciar tiempo al iniciar

    def stop_game(self):
        self.state = "stopped"

    def step_forward(self):
        """Avanza un paso en la simulación"""
        # Ejecutar un único tick aunque el motor esté en pausa
        self.update(force=True)
>>>>>>> reestructuracion
    
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
<<<<<<< HEAD
            self.add_debug_event('system', "Fin del juego: No hay más vehículos", (255, 255, 0))
=======
>>>>>>> reestructuracion
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
<<<<<<< HEAD
                self.add_debug_event('system', "Fin del juego: Todos los vehículos completaron su trabajo", (255, 255, 0))
=======
>>>>>>> reestructuracion
                return True, "Todos los vehículos han completado su trabajo"
        elif p1_active_vehicles > 0:
            # Solo jugador 1 tiene vehículos activos
            if p1_job_done == p1_active_vehicles:
<<<<<<< HEAD
                self.add_debug_event('system', "Fin del juego: Todos los vehículos completaron su trabajo", (255, 255, 0))
=======
>>>>>>> reestructuracion
                return True, "Todos los vehículos han completado su trabajo"
        elif p2_active_vehicles > 0:
            # Solo jugador 2 tiene vehículos activos
            if p2_job_done == p2_active_vehicles:
<<<<<<< HEAD
                self.add_debug_event('system', "Fin del juego: Todos los vehículos completaron su trabajo", (255, 255, 0))
=======
>>>>>>> reestructuracion
                return True, "Todos los vehículos han completado su trabajo"
        
        # El juego termina por falta de recursos solo si:
        # 1. No hay recursos en el mapa
        # 2. No hay vehículos fuera de base (todos están en base, destruidos o terminaron)
        # 3. No hay vehículos con recursos sin entregar
        if resources_remaining == 0:
            vehicles_outside = p1_vehicles_outside_base + p2_vehicles_outside_base
            vehicles_with_resources = p1_vehicles_with_resources + p2_vehicles_with_resources
            
            if vehicles_outside == 0 and vehicles_with_resources == 0:
<<<<<<< HEAD
                self.add_debug_event('system', "Fin del juego: No quedan recursos ni vehículos en misión", (255, 255, 0))
=======
>>>>>>> reestructuracion
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
        
        ticks_without_progress = self.tick - self._last_score_change_tick
        
<<<<<<< HEAD
        if ticks_without_progress == 200 and resources_remaining > 0:
            self.add_debug_event('system', f"Sin progreso: {resources_remaining} recursos sin recoger", (255, 200, 0))
        elif ticks_without_progress == 350 and resources_remaining > 0:
            p1_idle = sum(1 for v in self.player1.vehicles.values() if v.status == "in_base")
            p2_idle = sum(1 for v in self.player2.vehicles.values() if v.status == "in_base")
            self.add_debug_event('system', f"P1:{p1_idle} P2:{p2_idle} vehículos inactivos", (255, 200, 0))
        
        if ticks_without_progress > 500 and resources_remaining > 0:
            self.add_debug_event('system', "Timeout: Sin progreso en 500 ticks", (255, 200, 0))
=======
        if ticks_without_progress > 500 and resources_remaining > 0:
>>>>>>> reestructuracion
            return True, f"Juego detenido por inactividad (quedan {resources_remaining} recursos)"
        
        return False, None
    
    def _determine_winner(self, reason):
        """Determina el ganador basándose en los puntos"""
        p1_score = self.player1.score
        p2_score = self.player2.score
        
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
<<<<<<< HEAD
        
        # Guardar el estado actual antes de avanzar (para poder retroceder)
        should_save = force or (self.state == "running" and self.tick % 5 == 0)
        if should_save:
            self.save_state()
=======
>>>>>>> reestructuracion

        self.tick += 1
        self.map.current_tick = self.tick

        current_time = time.time()
        elapsed_time = current_time - self.start_time

        try:
            self.map.mine_manager.updateAll(self.tick, self.map.rows, self.map.cols, elapsed_time, self.map)
        except Exception:
            pass 

        # Verificar si algún vehículo está en una posición minada después de actualizar las minas
        self._check_vehicles_on_mines()

        resources = self.map.all_resources()
        
        # Mover vehículos del jugador 1 usando su estrategia si está presente
        strategy1 = getattr(self.player1, "strategy", None)
        if strategy1 is not None and callable(getattr(strategy1, "update", None)):
            try:
                strategy1.update(self.player1)
            except Exception:
                pass 
        
        # Mover vehículos del jugador 2 usando su estrategia si está presente
        strategy2 = getattr(self.player2, "strategy", None)
        if strategy2 is not None and callable(getattr(strategy2, "update", None)):
            try:
                strategy2.update(self.player2)
            except Exception:
                pass 
        
        self._check_vehicle_collisions()
        self._check_same_team_collisions()
        self._check_vehicle_consistency()
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
                            if self.map.mine_manager.isCellMined((row, col), self.tick):
                                vehicle_obj.status = "destroyed"
                                vehicle_obj.collected_value = 0
<<<<<<< HEAD
                                self.add_debug_event('mine', f" {vehicle_id} destruido por mina en {(row, col)}", (255, 100, 0))
=======
                                # Agregar animación de colisión con mina
>>>>>>> reestructuracion
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
<<<<<<< HEAD
                    v1_str = ", ".join(vehicles1_ids) if vehicles1_ids else "ninguno"
                    v2_str = ", ".join(vehicles2_ids) if vehicles2_ids else "ninguno"
                    self.add_debug_event('collision', f"COLISIÓN en {pos}: P1[{v1_str}] vs P2[{v2_str}]", (255, 50, 50))
                    # Agregar animación de colisión entre vehículos
=======
>>>>>>> reestructuracion
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
        
<<<<<<< HEAD
        # Reportar colisiones en equipo 1 (más de 1 vehículo en la misma posición)
        for pos, vehicles in player1_positions.items():
            if len(vehicles) > 1:
                vehicle_ids = [v.id for v in vehicles]
                self.add_debug_event('same_team', f"Colisión mismo equipo P1 en {pos}: {', '.join(vehicle_ids)}", (255, 200, 0))
        
=======
>>>>>>> reestructuracion
        # Verificar colisiones dentro del equipo 2
        player2_positions = {}
        for vehicle_id, vehicle in self.player2.vehicles.items():
            if vehicle.status not in ["destroyed", "in_base"]:
                pos = vehicle.position
                if isinstance(pos, tuple) and len(pos) == 2:
                    if pos not in player2_positions:
                        player2_positions[pos] = []
                    player2_positions[pos].append(vehicle)
<<<<<<< HEAD
        
        # Reportar colisiones en equipo 2 (más de 1 vehículo en la misma posición)
        for pos, vehicles in player2_positions.items():
            if len(vehicles) > 1:
                vehicle_ids = [v.id for v in vehicles]
                self.add_debug_event('same_team', f"Colisión mismo equipo P2 en {pos}: {', '.join(vehicle_ids)}", (255, 200, 0))
=======
>>>>>>> reestructuracion
    
    def _check_vehicle_consistency(self):
        """Verifica que vehículos activos realmente existan en el mapa, marca como destruidos los 'fantasmas'"""
        for player in [self.player1, self.player2]:
            for vehicle_id, vehicle in player.vehicles.items():
                if vehicle.status not in ["in_base", "destroyed", "job_done"]:
                    pos = vehicle.position
                    
                    if not (isinstance(pos, tuple) and len(pos) == 2):
                        vehicle.status = "destroyed"
                        vehicle.collected_value = 0
<<<<<<< HEAD
                        self.add_debug_event('ghost', f"{vehicle_id} posición inválida: {pos}", (255, 255, 0))
=======
>>>>>>> reestructuracion
                        continue
                    
                    row, col = pos
                    
                    if not (0 <= row < self.map.rows and 0 <= col < self.map.cols):
                        vehicle.status = "destroyed"
                        vehicle.collected_value = 0
<<<<<<< HEAD
                        self.add_debug_event('ghost', f"{vehicle_id} fuera del mapa: {pos}", (255, 255, 0))
=======
>>>>>>> reestructuracion
                        continue
                    
                    node = self.map.graph.get_node(row, col)
                    if node:
                        vehicle_found = False
                        
                        # Buscar el vehículo en el nodo
                        if node.content:
                            vehicle_content = node.content
                            
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
                        
                        if not vehicle_found:
                            is_base_position = node.state in ("base_p1", "base_p2")
                            
                            if not is_base_position:
                                vehicle.status = "destroyed"
                                vehicle.collected_value = 0
<<<<<<< HEAD
                                node_state = node.state if node else "None"
                                self.add_debug_event('ghost', f"{vehicle_id} fantasma en {pos} (nodo: {node_state})", (255, 255, 0))
=======
>>>>>>> reestructuracion

    def _cleanup_destroyed_vehicles(self):
        """Limpia los vehículos destruidos del mapa"""
        for row in range(self.map.rows):
            for col in range(self.map.cols):
                node = self.map.graph.get_node(row, col)
                if node and (node.state == "vehicle" or node.state in ("base_p1", "base_p2")) and node.content:
                    vehicle_content = node.content
                    
                    # Manejar listas de vehículos (mismo equipo en misma celda)
                    if isinstance(vehicle_content, list):
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
                            if len(vehicles_to_keep) == 1:
                                node.content = vehicles_to_keep[0]
                            else:
                                node.content = vehicles_to_keep
                        else:
                            if node.state in ("base_p1", "base_p2"):
                                node.state = node.state
                                node.content = {}
                            else:
                                node.state = "empty"
                                node.content = {}
                    else:
                        vehicle_obj = None
                        
                        if isinstance(vehicle_content, dict):
                            vehicle_obj = vehicle_content.get("object")
                        else:
                            vehicle_obj = vehicle_content
                        
                        if vehicle_obj and hasattr(vehicle_obj, "status"):
                            if vehicle_obj.status == "destroyed":
<<<<<<< HEAD
                                vehicle_id = getattr(vehicle_obj, "id", "unknown")
                                
=======
>>>>>>> reestructuracion
                                # Limpiar el nodo
                                if node.state in ("base_p1", "base_p2"):
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
