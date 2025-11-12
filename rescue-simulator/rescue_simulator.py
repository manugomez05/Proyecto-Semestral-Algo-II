"""
Archivo principal del simulador de rescate.
-------------------------------------------------
Se encarga de inicializar Pygame, crear la ventana principal y 
gestionar el bucle de ejecución del juego (main loop).

Desde aquí se inicializa el motor del juego (`GameEngine`) 
y el módulo de visualización (`Visualization`).

Responsabilidades:
- Crear y mantener el ciclo principal del juego.
- Delegar la lógica al motor (`GameEngine`).
- Delegar la representación gráfica a (`Visualization`).
"""

import pygame
from src import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from src.visualization import Visualization
from src.game_engine import GameEngine

def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Simulador de Rescate")

    engine = GameEngine()
    view = Visualization(screen, engine)

    running = True
    while running:
        view.handle_events()
        engine.update()
        view.render()
        pygame.time.Clock().tick(FPS)
    

if __name__ == "__main__":
    main()