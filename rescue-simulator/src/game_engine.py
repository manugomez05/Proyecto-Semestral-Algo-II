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

import time

class GameEngine:
    def __init__(self):
        self.state = "stopped"
        self.map = MapManager(50, 50)
        self.tick = 0  # Contador de tiempo para minas dinámicas
        self.start_time = time.time()  # Tiempo de inicio para minas basadas en tiempo

        # Generar posiciones
        base_positions = self.map.generate_bases()

        # Crear jugadores con sus bases
        self.player1 = Player("Jugador_1", base_positions["player1"])
        self.player2 = Player("Jugador_2", base_positions["player2"])

        # Asignar estrategia de movimiento al player1
        # BasicMoveStrategy espera (map_width, map_height, map)
        try:
            self.player1.strategy = BasicMoveStrategy(self.map.cols, self.map.rows, self.map)
        except Exception:
            # Fallback: no strategy asignada si falla la instanciación
            self.player1.strategy = None

    def init_game(self):
        print("Inicializando mapa...")
        self.map.clear_map()
        self.map.generate_random_map()
        self.state = "init"

    def start_game(self):
        print("Simulación iniciada")
        self.state = "running"
        
        self.start_time = time.time()  # Reiniciar tiempo al iniciar

    def stop_game(self):
        print("Simulación detenida")
        self.state = "stopped"

    def update(self):
        if self.state != "running":
            return
        
        # Incrementar el contador de tiempo
        self.tick += 1
        
        # Calcular tiempo transcurrido en segundos
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        # Actualizar minas dinámicas (G1) con tiempo real
        self.map.mine_manager.updateAll(self.tick, self.map.rows, self.map.cols, elapsed_time, self.map)

        # Mover vehículos del jugador 1 usando su estrategia si está presente
        strategy = getattr(self.player1, "strategy", None)
        if strategy is not None and callable(getattr(strategy, "update", None)):
            try:
                strategy.update(self.player1)
            except Exception as e:
                print(f"Error al ejecutar estrategia player1: {e}")
