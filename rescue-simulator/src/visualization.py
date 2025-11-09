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
from pathlib import Path

from src import PALETTE_6



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
        # Cache de imágenes para evitar cargar desde disco en cada frame
        self.image_cache = {}
        #self.font = pygame.font.Font('paraIntegrar/assets/PressStart2P-Regular.ttf', 12)
        self.create_buttons()

    def get_cached_image(self, img_path, size):
        """
        Obtiene una imagen del caché. Si no existe, la carga, escala y guarda en caché.
        
        Args:
            img_path: Ruta de la imagen
            size: Tupla (ancho, alto) para escalar
        
        Returns:
            Superficie pygame con la imagen escalada
        """
        cache_key = (img_path, size)
        
        if cache_key not in self.image_cache:
            try:
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.scale(img, size)
                self.image_cache[cache_key] = img
            except Exception as e:
                # Si hay error al cargar, devolver None
                return None
        
        return self.image_cache[cache_key]

    def create_buttons(self):

        # 📁 Ruta base del archivo actual (src/visualization.py)
        base_path = Path(__file__).resolve().parent

        # 📁 Ruta absoluta a la carpeta assets (un nivel arriba de src)
        assets_path = base_path.parent / 'assets'

        from functools import partial
        self.buttons = [

            Button(str(assets_path / 'initBtn.png'), 'bottom', (-220,0), partial(self.engine.init_game)),
            Button(str(assets_path / 'playBtn.png'), 'bottom', (-50,0), partial(self.engine.start_game)),
            Button(str(assets_path / 'backwardsBtn.png'), 'bottom', (80,0), partial(self.engine.step_backward)),
            Button(str(assets_path / 'forwardsBtn.png'), 'bottom', (170,0), partial(self.engine.step_forward)),
            Button(str(assets_path / 'stopBtn.png'), 'bottom', (270,0), partial(self.engine.stop_game)),
            Button(str(assets_path / 'saveBtn.png'), 'bottomLeft', (40,0), """partial(self.engine.save_game)"""),
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
        #self.drawTickInfo()  # Mostrar información del tick

        for b in self.buttons:
            b.draw(self.screen)
        pygame.display.flip()

    def drawMap(self):
        graph = self.engine.map.graph
        
        # Dibujar las minas con radio completo (TEMPORAL para verificación)
        from src.mines_manager import drawMines
        drawMines(self.screen, self.engine.map.mine_manager, graph.rows, graph.cols, CELL_SIZE, 390, 20)
        
        #Dibuja bases de los jugadores
        self.engine.player1.drawPlayerBase(self.screen, 49,190)
        self.engine.player2.drawPlayerBase(self.screen, 1270,190)

        # Dibujar recursos y otros elementos
        for row in range(graph.rows):
            for col in range(graph.cols):
                node = graph.get_node(row, col)
                x, y = col * CELL_SIZE + 390, row * CELL_SIZE + 20
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                
                # Dibujar bases con color diferente (gris oscuro/azul oscuro)
                # Dibujar la base primero para que esté debajo de los vehículos
                if node.state in ("base_p1", "base_p2"):
                    # Color para las bases: un gris/azul más oscuro que el fondo
                    BASE_COLOR = (30, 40, 60)  # Color oscuro para las bases
                    pygame.draw.rect(self.screen, BASE_COLOR, rect, 0)  # Relleno sólido
                
                if node.state == 'resource' and node.content:
                    img = self.get_cached_image(node.content.img_path, (CELL_SIZE, CELL_SIZE))
                    if img:
                        self.screen.blit(img, (x, y))
                # Ya no dibujamos las minas aquí porque drawMines se encarga
                # Dibujar vehículos (pueden estar en estado "vehicle" o en bases con contenido)
                if (node.state == "vehicle" or node.state in ("base_p1", "base_p2")) and node.content:
                    v = node.content
                    # Obtener el objeto vehículo real para verificar status
                    vehicle_obj = None
                    if isinstance(v, dict):
                        vehicle_obj = v.get("object")
                    else:
                        vehicle_obj = v
                    
                    # Verificar que el vehículo no esté destruido
                    if vehicle_obj:
                        status = getattr(vehicle_obj, "status", None)
                        if status == "destroyed":
                            continue  # No dibujar vehículos destruidos
                        
                        # Obtener la ruta de imagen del vehículo
                        img_path = getattr(vehicle_obj, "img_path", None)
                        if img_path:
                            # Cargar y renderizar la imagen del vehículo con tamaño aumentado
                            VEHICLE_SCALE = 2.5  # Factor de escala para hacer vehículos más grandes
                            vehicle_size = int(CELL_SIZE * VEHICLE_SCALE)
                            img = self.get_cached_image(img_path, (vehicle_size, vehicle_size))
                            
                            if img:
                                # Cada jugador ya tiene sus propias imágenes que apuntan hacia el centro
                                # Jugador_1: usa *1.png (apuntan a la derecha →)
                                # Jugador_2: usa *2.png (apuntan a la izquierda ←)
                                # No es necesario voltear las imágenes
                                
                                # Centrar la imagen más grande en la celda
                                offset_x = x - (vehicle_size - CELL_SIZE) // 2
                                offset_y = y - (vehicle_size - CELL_SIZE) // 2
                                self.screen.blit(img, (offset_x, offset_y))
                        else:
                            # Fallback: dibujar círculo si no hay imagen
                            color = getattr(vehicle_obj, "color", (255, 255, 255))
                            pygame.draw.circle(self.screen, color, rect.center, 6)

                pygame.draw.rect(self.screen, PALETTE_6, rect, 1)




    def drawTickInfo(self):
        """Dibuja información del tick y estado de minas dinámicas"""
        try:
            font = pygame.font.Font('Proyecto-Semestral-Algo-II/rescue-simulator/assets/Press_Start_2P/PressStart2P-Regular.ttf', 14)
            
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
    # Cache compartido de imágenes para todos los botones
    _image_cache = {}
    
    def __init__(self, image_path, position, offset=(0,0), action=None):
        # Usar caché para cargar imagen solo una vez
        if image_path not in Button._image_cache:
            Button._image_cache[image_path] = pygame.image.load(image_path).convert_alpha()
        
        self.image = Button._image_cache[image_path]
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
    elif position == "bottomLeft":
        rect.bottomleft = screen_rect.bottomleft
        rect.x += margin
        rect.y -= margin
    
    rect.move_ip(offset)
    return rect