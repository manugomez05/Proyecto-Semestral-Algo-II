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
        
        # Sistema de debug: lista de eventos (colisiones, destrucciones, etc.)
        self.debug_events = []
        self.max_debug_events = 15  # Máximo de eventos a mostrar
        
        # Estado del juego terminado
        self.game_over_info = None  # Información del ganador

        # Generar posiciones
        base_positions = self.map.generate_bases()

        # Crear jugadores con sus bases
        self.player1 = Player("Jugador_1", base_positions["player1"])
        self.player2 = Player("Jugador_2", base_positions["player2"])

        

    def add_debug_event(self, event_type, message, color=(255, 255, 255)):
        """Agrega un evento de debug para mostrar en pantalla"""
        event = {
            'tick': self.tick,
            'type': event_type,  # 'collision', 'mine', 'ghost', 'resource', etc.
            'message': message,
            'color': color
        }
        self.debug_events.append(event)
        
        # Mantener solo los últimos N eventos
        if len(self.debug_events) > self.max_debug_events:
            self.debug_events.pop(0)
        
        # También imprimir en consola (DESACTIVADO para no saturar)
        # print(f"[Tick {self.tick}] [{event_type.upper()}] {message}")
    
    def init_game(self):
        print("Inicializando mapa...")
        self.map.clear_map()
        self.debug_events = []  # Limpiar eventos al iniciar nuevo juego
        self.tick = 0  # Resetear tick a 0
        self.start_time = time.time()  # Resetear tiempo de inicio
        self.game_over_info = None  # Resetear información de game over
        
        # Limpiar estados guardados anteriores para evitar confusión
        try:
            if self._saved_states_dir.exists():
                import shutil
                shutil.rmtree(self._saved_states_dir)
                print("Estados guardados anteriores limpiados")
        except Exception as e:
            print(f"Advertencia: no se pudieron limpiar estados anteriores: {e}")
        
        resources = self.map.generate_random_map()

        self.player1.resources = resources
        self.player2.resources = resources

        # Asignar estrategias a los jugadores
        try:
            # Estrategia 1 para player1: motos destruyen camiones, resto usa BFS
            self.player1.strategy = Strategy1(self.map.cols, self.map.rows, self.map, self.player2)
            
            # Estrategia 2 para player2: usa Dijkstra
            self.player2.strategy = Strategy2(self.map.cols, self.map.rows, self.map, self.player1)
        except Exception as e:
            print(f"Error al asignar estrategias: {e}")
            self.player1.strategy = None
            self.player2.strategy = None

        # Inicializar vehículos en la base
        self._initialize_vehicles_at_base()

        self.state = "init"
        
        # Mensaje de debug
        self.add_debug_event('system', "🎮 Juego inicializado - Tick reseteado a 0", (100, 255, 100))
    
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
        self.add_debug_event('system', "▶️ Simulación iniciada", (100, 255, 100))

    def stop_game(self):
        self.state = "stopped"
        self.add_debug_event('system', "⏸️ Simulación detenida", (255, 200, 100))

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
                # print(f"✅ Estado guardado: state_{self.tick}.pickle")  # Desactivado para no saturar
                return str(final_path)
            else:
                print(f"❌ Error: archivo no se creó: state_{self.tick}.pickle")
                return None
        except Exception as e:
            print(f"❌ Error al guardar estado del tick {self.tick}: {e}")
            import traceback
            traceback.print_exc()
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
                # print(f"✅ Estado cargado desde {filename}")  # Desactivado
            except Exception as e:
                print(f"⚠️ Estrategias no se pudieron restaurar: {e}")
                self.player1.strategy = None
                self.player2.strategy = None
            
            return True
        except (EOFError, pickle.UnpicklingError) as e:
            print(f"❌ Error al cargar estado (archivo corrupto o incompleto): {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado al cargar estado: {e}")
            return False

    def step_forward(self):
        """Avanza un paso en la simulación"""
        # Ejecutar un único tick aunque el motor esté en pausa
        # (update ya guarda el estado cuando force=True)
        self.update(force=True)
        # print(f"⏩ Avanzado a tick {self.tick}")  # Desactivado
        self.add_debug_event('system', f"⏩ Avanzado a tick {self.tick}", (100, 200, 255))
        
    def step_backward(self):
        """Retrocede un paso en la simulación"""
        # print(f"🔙 step_backward() llamado en tick={self.tick}")  # Desactivado
        
        # Verificar que exista la carpeta de estados
        if not self._saved_states_dir.exists():
            print("❌ No hay carpeta de estados guardados")
            self.add_debug_event('system', "❌ No hay estados guardados", (255, 100, 100))
            return
        
        if self.tick <= 0:
            print("⚠️ Ya estás en el tick 0")
            self.add_debug_event('system', "⚠️ Ya en tick 0", (200, 200, 0))
            return
        
        # Buscar el estado guardado más cercano antes del tick actual
        target_tick = self.tick - 1
        filename = str(self._saved_states_dir / f'state_{target_tick}.pickle')
        
        if os.path.exists(filename):
            ok = self.load_state(filename)
            if ok:
                # print(f"✅ Retrocedido a tick {self.tick}")  # Desactivado
                self.add_debug_event('system', f"⏮️ Retrocedido a tick {self.tick}", (100, 255, 100))
                return
        
        # Si no existe ese tick exacto, buscar el más cercano anterior
        found = False
        for t in range(target_tick - 1, -1, -1):
            filename = str(self._saved_states_dir / f'state_{t}.pickle')
            if os.path.exists(filename):
                ok = self.load_state(filename)
                if ok:
                    # print(f"✅ Retrocedido a tick {self.tick}")  # Desactivado
                    self.add_debug_event('system', f"⏮️ Retrocedido a tick {self.tick}", (100, 255, 100))
                    found = True
                    break

        if not found:
            print("❌ No se encontraron estados guardados")
            self.add_debug_event('system', "❌ No hay estados guardados", (255, 100, 100))
    
    def _check_game_over_conditions(self):
        """Verifica si se cumplen las condiciones de fin de juego"""
        # Condición 1: No hay más recursos en el mapa
        resources_remaining = sum(1 for row in range(self.map.rows) 
                                 for col in range(self.map.cols) 
                                 if self.map.graph.get_node(row, col).state == "resource")
        
        # Condición 2: No hay vehículos activos (ni en base, ni en misión)
        p1_active_vehicles = sum(1 for v in self.player1.vehicles.values() 
                                if v.status not in ["destroyed"])
        p2_active_vehicles = sum(1 for v in self.player2.vehicles.values() 
                                if v.status not in ["destroyed"])
        
        # El juego termina si no hay recursos O si no hay vehículos
        if resources_remaining == 0:
            self.add_debug_event('system', "🏁 Fin del juego: No hay más recursos", (255, 255, 0))
            return True, "No quedan recursos en el mapa"
        
        if p1_active_vehicles == 0 and p2_active_vehicles == 0:
            self.add_debug_event('system', "🏁 Fin del juego: No hay más vehículos", (255, 255, 0))
            return True, "Todos los vehículos han sido destruidos"
        
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
        except Exception as e:
            print(f"Error al actualizar minas: {e}")

        # Verificar si algún vehículo está en una posición minada después de actualizar las minas
        self._check_vehicles_on_mines()

        resources = self.map.all_resources()
        
        # Mover vehículos del jugador 1 usando su estrategia si está presente
        strategy1 = getattr(self.player1, "strategy", None)
        if strategy1 is not None and callable(getattr(strategy1, "update", None)):
            try:
                strategy1.update(self.player1)
            except Exception as e:
                print(f"Error al ejecutar estrategia player1: {e}")
        
        # Mover vehículos del jugador 2 usando su estrategia si está presente
        strategy2 = getattr(self.player2, "strategy", None)
        if strategy2 is not None and callable(getattr(strategy2, "update", None)):
            try:
                strategy2.update(self.player2)
            except Exception as e:
                print(f"Error al ejecutar estrategia player2: {e}")
        
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
            print(f"🏁 JUEGO TERMINADO: {reason}")
            print(f"🏆 GANADOR: {self.game_over_info['winner']}")
    
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
                            # Evento de debug
                            self.add_debug_event('mine', f"💥 {vehicle_id} destruido por mina en {(row, col)}", (255, 100, 0))

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
                
                # Evento de debug solo si hubo destrucción
                if vehicles1_ids or vehicles2_ids:
                    v1_str = ", ".join(vehicles1_ids) if vehicles1_ids else "ninguno"
                    v2_str = ", ".join(vehicles2_ids) if vehicles2_ids else "ninguno"
                    self.add_debug_event('collision', f"💥 COLISIÓN en {pos}: P1[{v1_str}] vs P2[{v2_str}]", (255, 50, 50))
    
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
        
        # Reportar colisiones en equipo 1 (más de 1 vehículo en la misma posición)
        for pos, vehicles in player1_positions.items():
            if len(vehicles) > 1:
                vehicle_ids = [v.id for v in vehicles]
                self.add_debug_event('same_team', f"⚠️ Colisión mismo equipo P1 en {pos}: {', '.join(vehicle_ids)}", (255, 200, 0))
        
        # Verificar colisiones dentro del equipo 2
        player2_positions = {}
        for vehicle_id, vehicle in self.player2.vehicles.items():
            if vehicle.status not in ["destroyed", "in_base"]:
                pos = vehicle.position
                if isinstance(pos, tuple) and len(pos) == 2:
                    if pos not in player2_positions:
                        player2_positions[pos] = []
                    player2_positions[pos].append(vehicle)
        
        # Reportar colisiones en equipo 2 (más de 1 vehículo en la misma posición)
        for pos, vehicles in player2_positions.items():
            if len(vehicles) > 1:
                vehicle_ids = [v.id for v in vehicles]
                self.add_debug_event('same_team', f"⚠️ Colisión mismo equipo P2 en {pos}: {', '.join(vehicle_ids)}", (255, 200, 0))
    
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
                        self.add_debug_event('ghost', f"👻 {vehicle_id} posición inválida: {pos}", (255, 255, 0))
                        continue
                    
                    row, col = pos
                    
                    # Verificar que esté dentro de los límites del mapa
                    if not (0 <= row < self.map.rows and 0 <= col < self.map.cols):
                        vehicle.status = "destroyed"
                        vehicle.collected_value = 0
                        self.add_debug_event('ghost', f"👻 {vehicle_id} fuera del mapa: {pos}", (255, 255, 0))
                        continue
                    
                    # Verificar que el vehículo realmente exista en esa posición del mapa
                    node = self.map.graph.get_node(row, col)
                    if node:
                        vehicle_found = False
                        
                        # Buscar el vehículo en el nodo
                        # Puede estar en estado "vehicle" o en una base
                        if node.content:
                            vehicle_content = node.content
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
                                node_state = node.state if node else "None"
                                self.add_debug_event('ghost', f"👻 {vehicle_id} fantasma en {pos} (nodo: {node_state})", (255, 255, 0))

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
