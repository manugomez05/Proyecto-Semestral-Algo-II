import sys
import pygame
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

from visualization import Visualization
from src import SCREEN_HEIGHT, SCREEN_WIDTH
class FakeEngine:
    def __init__(self):
        self.state = "game_over"
        self.game_over_info = {
            "reason": "Tiempo agotado",
            "winner": "Jugador_1",
            "winner_color": "blue",
            "player1": {
                "name": "Jugador_1",
                "score": 120,
                "vehicles": {"in_base":3,"in_mission":2,"returning":1,"job_done":3,"destroyed":1}
            },
            "player2": {
                "name": "Jugador_2",
                "score": 95,
                "vehicles": {"in_base":4,"in_mission":1,"returning":2,"job_done":2,"destroyed":1}
            }
        }
    def init_game(self): print("init")
    def start_game(self): print("start")
    def step_backward(self): pass
    def step_forward(self): pass
    def stop_game(self): pass
    def save_game(self): pass

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Preview GameOver")
    engine = FakeEngine()
    viz = Visualization(screen, engine)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill((0,0,0))
        viz.drawGameOverScreen()
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == '__main__':
    main()