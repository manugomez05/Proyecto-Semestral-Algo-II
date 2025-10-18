"""
Módulo: visualization
-------------------------------------------------
Maneja todo lo relacionado con la visualización y la interfaz 
gráfica del simulador usando Pygame.

Responsabilidades:
- Dibujar el mapa, recursos, minas y bases en pantalla.
- Definir y manejar los botones de la interfaz.
- Capturar los eventos de usuario (clics, cierre de ventana).
- Coordinarse con el `GameEngine` para mostrar el estado actual.
"""


import pygame
import time

# Definir las constantes directamente para evitar problemas de importación
BLACK = (22, 33, 60)
PALETTE = (46, 68, 96)
CELL_SIZE = 17

#from map_graph import MapGraph

class Visualization:
    def __init__(self, screen, engine):
        self.screen = screen
        self.engine = engine
        self.buttons = []
        #self.font = pygame.font.Font('paraIntegrar/assets/PressStart2P-Regular.ttf', 12)
        self.create_buttons()

    def create_buttons(self):
        from functools import partial
        self.buttons = [
            Button('paraIntegrar/assets/initBtn.png', 'bottom', (-220,0), partial(self.engine.init_game)),
            Button('paraIntegrar/assets/playBtn.png', 'bottom', (-50,0), partial(self.engine.start_game)),
            Button('paraIntegrar/assets/backwardsBtn.png', 'bottom', (80,0)),
            Button('paraIntegrar/assets/forwardsBtn.png', 'bottom', (170,0)),
            Button('paraIntegrar/assets/stopBtn.png', 'bottom', (270,0), partial(self.engine.stop_game)),
        ]

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            for b in self.buttons:
                b.handle_event(event)

    def render(self):
        self.screen.fill(BLACK)
        self.drawMap()
        self.drawTickInfo()  # Mostrar información del tick
        for b in self.buttons:
            b.draw(self.screen)
        pygame.display.flip()

    def drawMap(self):
        graph = self.engine.map.graph
        
        # Dibujar las minas con radio completo (TEMPORAL para verificación)
        from src.minesmanager import drawMines
        drawMines(self.screen, self.engine.map.mine_manager, graph.rows, graph.cols, CELL_SIZE, 390, 20)
        
        # Dibujar recursos y otros elementos
        for row in range(graph.rows):
            for col in range(graph.cols):
                node = graph.get_node(row, col)
                x, y = col * CELL_SIZE + 390, row * CELL_SIZE + 20
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                if node.state == 'occupied' and node.content:
                    img = pygame.image.load(node.content.img_path).convert_alpha()
                    img = pygame.transform.scale(img, (CELL_SIZE, CELL_SIZE))
                    self.screen.blit(img, (x, y))
                # Ya no dibujamos las minas aquí porque drawMines se encarga
                pygame.draw.rect(self.screen, (0,0,0), rect, 1)

    def drawTickInfo(self):
        """Dibuja información del tick y estado de minas dinámicas"""
        try:
            import pygame
            font = pygame.font.Font(None, 24)
            
            # Mostrar tick actual y tiempo transcurrido
            elapsed_time = time.time() - self.engine.start_time
            tick_text = font.render(f"Tick: {self.engine.tick}", True, (255, 255, 255))
            time_text = font.render(f"Tiempo: {elapsed_time:.1f}s", True, (255, 255, 255))
            self.screen.blit(tick_text, (10, 10))
            self.screen.blit(time_text, (10, 25))
            
            # Mostrar estado de minas G1
            g1_mines = [mine for mine in self.engine.map.mine_manager.all() if mine.type.name == 'G1']
            if g1_mines:
                g1_mine = g1_mines[0]  # Primera mina G1
                status = "ACTIVA" if g1_mine.active else "INACTIVA"
                color = (0, 255, 0) if g1_mine.active else (255, 0, 0)
                status_text = font.render(f"G1: {status}", True, color)
                self.screen.blit(status_text, (10, 50))
                
                # Mostrar posición de la mina G1
                row, col = g1_mine.center
                pos_text = font.render(f"Posición: ({row}, {col})", True, (255, 255, 255))
                self.screen.blit(pos_text, (10, 75))
                
                # Mostrar próximo cambio en segundos
                next_change = g1_mine.next_activation - elapsed_time
                if next_change > 0:
                    change_text = font.render(f"Próximo cambio en: {next_change:.1f}s", True, (255, 255, 255))
                    self.screen.blit(change_text, (10, 100))
        except:
            pass  # Si hay error, no mostrar información

class Button:
    def __init__(self, image_path, position, offset=(0,0), action=None):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.position = position
        self.offset = offset
        self.rect = align(self.image, position, offset)
        self.action = action

    def draw(self, screen):
        self.rect = align(self.image, self.position, self.offset)
        screen.blit(self.image, self.rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()

def align(surface, position, offset=(0,0), margin=10):
    screen_rect = pygame.display.get_surface().get_rect()
    rect = surface.get_rect()
    if position == "bottom":
        rect.midbottom = screen_rect.midbottom
        rect.y -= margin
    rect.move_ip(offset)
    return rect