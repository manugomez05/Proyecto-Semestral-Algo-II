
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
import pickle
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
        # Determinar qué jugador es (1 o 2) según el nombre
        player_num = 1 if self.name == "Jugador_1" else 2
        vm.create_default_fleet(player_num)

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
        
    def __getstate__(self):
        """Método especial para pickle"""
        state = self.__dict__.copy()
        # Eliminamos la referencia a pygame.font que no es serializable
        state['_font'] = None
        return state
        
    def __setstate__(self, state):
        """Método especial para pickle"""
        self.__dict__.update(state)
        # Recreamos la fuente al deserializar
        root_path = Path(__file__).resolve().parents[1]
        font_path = root_path / "assets" / "Press_Start_2P" / "PressStart2P-Regular.ttf"
        self._font = pygame.font.Font(str(font_path), 14)
    
    def get_vehicle(self, vehicle_id):
        return self.vehicles.get(vehicle_id)
    
    def drawPlayerBase(self, surface, x, y):
        if not hasattr(self, '_font'):
            root_path = Path(__file__).resolve().parents[1]  # sube de src/ a rescue-simulator/
            font_path = root_path / "assets" / "Press_Start_2P" / "PressStart2P-Regular.ttf"
            self._font = pygame.font.Font(str(font_path), 14)
        
        font = self._font

        #Dibujo el nombre del jugador
        name_text = font.render(f"{self.name}", True, PALETTE_1)
        surface.blit(name_text, (x, y-30))

        margin = y + 20

        pygame.draw.line(surface, PALETTE_1, (x, 200), (x, 650), 2)

        for key, vehicle in self.vehicles.items():
            # Dibujar imagen del vehículo en lugar del color
            img_path = getattr(vehicle, "img_path", None)
            if img_path:
                try:
                    img = pygame.image.load(img_path).convert_alpha()
                    img = pygame.transform.scale(img, (64, 64))  # Tamaño el doble de grande
                    # Cada jugador tiene sus propias imágenes que ya apuntan hacia el centro
                    # Jugador_1: usa *1.png (apuntan a la derecha →)
                    # Jugador_2: usa *2.png (apuntan a la izquierda ←)
                    surface.blit(img, (x+20, margin-16))
                except:
                    # Fallback: dibujar rectángulo con color si hay error
                    rect = pygame.Rect(x+20, margin, 64, 64)
                    pygame.draw.rect(surface, vehicle.color, rect)
            else:
                # Fallback: dibujar rectángulo con color
                rect = pygame.Rect(x+20, margin, 64, 64)
                pygame.draw.rect(surface, vehicle.color, rect)

            key_text = font.render(f"{key}, {vehicle.status}", True, PALETTE_1)
            surface.blit(key_text, (x+95, margin))

            margin += 45

        score_text = font.render(f"Score:{self.score}", True, PALETTE_1)

        surface.blit(score_text, (x, 700))
