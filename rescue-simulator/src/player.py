
"""
class Player():
    base
    score
    vehicles

    strategy()

    updateScore()
"""
from src import SCREEN_WIDTH, SCREEN_HEIGHT, PALETTE_1
import pygame
from pathlib import Path
from src.vehicle import VehicleManager # suponiendo que estas clases ya existen

class Player:
    def __init__(self, name: str, base_position: tuple, strategy=None):
        """
        Representa a un jugador del simulador.

        :param name: Nombre del jugador (ej: 'Jugador 1')
        :param base_position: Coordenadas (x, y) de su base en el mapa.
        :param strategy: Función o clase con la estrategia general del jugador.
        """
        self.name = name
        self.base_position = base_position
        self.score = 0
        self.strategy = strategy  # Estrategia global del jugador
        self.vehicles = self._create_fleet()  # Lista de vehículos del jugador

    # -----------------------------------------------------
    # Creación de la flota (10 vehículos en total)
    # -----------------------------------------------------
    def _create_fleet(self):
        """
        Crea la flota inicial del jugador según las especificaciones del proyecto.
        """
        vm = VehicleManager()
        vm.create_default_fleet()

        return vm.all_vehicles()

    # -----------------------------------------------------
    # Actualización del puntaje
    # -----------------------------------------------------
    def update_score(self):
        """
        Recalcula el puntaje total del jugador según la carga entregada por sus vehículos.
        """
        total = 0
        for v in self.vehicles:
            total += v.collected_value  # cada vehículo debe almacenar cuánto valor entregó
        self.score = total

    # -----------------------------------------------------
    # Ejecución de estrategia general
    # -----------------------------------------------------
    def execute_strategy(self, game_state):
        """
        Ejecuta la estrategia global del jugador (si está definida).
        """
        if self.strategy:
            self.strategy(self, game_state)
        else:
            print(f"[WARN] {self.name} no tiene estrategia asignada.")

    # -----------------------------------------------------
    # Reinicio del jugador (para nuevas simulaciones)
    # -----------------------------------------------------
    def reset(self):
        """
        Reinicia el puntaje y reposiciona los vehículos en la base.
        """
        self.score = 0
        for v in self.vehicles:
            v.reset_to_base()

    # -----------------------------------------------------
    # Representación
    # -----------------------------------------------------
    def __repr__(self):
        return f"<Player {self.name} | Score: {self.score} | Vehicles: {len(self.vehicles)}>"
    
    def get_vehicle(self, vehicle_id):
        return self.vehicles.get(vehicle_id)
    
    def drawPlayerBase(self, surface, x, y):

        font = pygame.font.Font('Proyecto-Semestral-Algo-II/rescue-simulator/assets/Press_Start_2P/PressStart2P-Regular.ttf', 14)

        #Dibujo el nombre del jugador
        name_text = font.render(f"{self.name}", True, PALETTE_1)
        surface.blit(name_text, (x, y-30))

        margin = y + 20

        pygame.draw.line(surface, PALETTE_1, (x, 200), (x, 650), 2)

        for key, vehicle in self.vehicles.items():

            rect = pygame.Rect(x+20, margin, 16, 16)
            pygame.draw.rect(surface, vehicle.color, rect)

            key_text = font.render(f"{key}, {vehicle.status}", True, PALETTE_1)

            surface.blit(key_text, (x+50, margin))

            margin += 45

        score_text = font.render(f"Score:{self.score}", True, PALETTE_1)

        surface.blit(score_text, (x, 700))
