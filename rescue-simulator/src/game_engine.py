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
from config.strategies.player1_strategies import BasicMoveStrategy
import os
import pickle
#from config.strategies.player1_strategies import Player1ResourceStrategy
#from config.strategies.player1_strategies import NearestResourceStrategy
import time

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

        # Asignar estrategia de movimiento al player1
        # BasicMoveStrategy espera (map_width, map_height, map)
        try:
            #self.player1.strategy = NearestResourceStrategy(self.map.cols, self.map.rows, self.map)
            #self.player1.strategy = Player1ResourceStrategy(self.map.cols, self.map.rows, self.map)
            self.player1.strategy = BasicMoveStrategy(self.map.cols, self.map.rows, self.map)
        except Exception:
            # Fallback: no strategy asignada si falla la instanciación
            self.player1.strategy = None

        self.state = "init"

    def start_game(self):
        print("Simulación iniciada")
        self.state = "running"
        
        self.start_time = time.time()  # Reiniciar tiempo al iniciar

    def stop_game(self):
        print("Simulación detenida")
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

        # Calcular tiempo transcurrido en segundos respecto a start_time
        current_time = time.time()
        elapsed_time = current_time - self.start_time

        # Actualizar minas dinámicas (G1) con tiempo real
        try:
            self.map.mine_manager.updateAll(self.tick, self.map.rows, self.map.cols, elapsed_time, self.map)
        except Exception as e:
            print(f"Error al actualizar minas: {e}")

        resources = self.map.all_resources()
        
        # Mover vehículos del jugador 1 usando su estrategia si está presente
        strategy = getattr(self.player1, "strategy", None)
        if strategy is not None and callable(getattr(strategy, "update", None)):
            try:
                #print("resources", resources)
                #strategy.hola()
                #strategy.update(self.player1, resources, "jeep_1")
                strategy.update(self.player1)
            except Exception as e:
                print(f"Error al ejecutar estrategia player1: {e}")
