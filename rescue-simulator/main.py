import pygame #importa la libreria
import sys #libreria para cerrar ventana
import random
from resources import *
from map_graph import *


pygame.init() #inicializa la libreria, usar siempre

screenWidth = 1600
screenHeight = 960

size = (screenWidth, screenHeight) #tamaño de la ventana

BLACK = (22,33,60)
WHITE = (238,238,238)
GREEN = (0,255,0)
RED = (255,0,0)
BLUE = (0,0,255)
PALETTE = (46,68,96)


textFont = pygame.font.Font('prueba\Press_Start_2P\PressStart2P-Regular.ttf', 12) #None para usar la fuente de pygame

def align(surface, position, offset=(0,0), margin=10): #alinea una superficie dada

    screen_rect = pygame.display.get_surface().get_rect() 
    rect = surface.get_rect() #obtiene su rectangulo

    if position == "center":
        rect.center = screen_rect.center
    elif position == "top":
        rect.midtop = screen_rect.midtop
        rect.y += margin
    elif position == "bottom":
        rect.midbottom = screen_rect.midbottom
        rect.y -= margin
    elif position == "bottomRight":
        rect.bottomright = screen_rect.bottomright
        rect.x -= margin
        rect.y -= margin
    elif position == "bottomLeft":
        rect.bottomleft = screen_rect.bottomleft
        rect.x += margin
        rect.y -= margin
    elif position == "topRight":
        rect.topright = screen_rect.topright
        rect.x -= margin
        rect.y += margin
    elif position == "topLeft":
        rect.topleft = screen_rect.topleft
        rect.x += margin
        rect.y += margin

    rect.move_ip(offset)  # aplicar desplazamiento opcional
    return rect


screen = pygame.display.set_mode(size) #crea ventana
pygame.display.set_caption('Simulador')


DATOS = [
    ((0, 255, 0), 50),     # Verde brillante
    ((255, 0, 0), 40),     # Rojo
    ((0, 0, 255), 30),     # Azul
    ((255, 255, 0), 90),   # Amarillo
    ((255, 128, 0), 10)    # Naranja
]


clock = pygame.time.Clock() #crea un reloj

speed = 5

running = True

posX = 50
posY = 50

class Button():
    def __init__(self, image_path, position, offset=(0, 0), action=None):
        self.image = pygame.image.load(image_path).convert_alpha() #carga la imagen
        self.position = position
        self.offset = offset
        self.rect = align(self.image, position, offset)
        self.action = action  # función que se ejecuta al hacer clic

    def draw(self, screen):
        # Redibuja el rect por si cambia el tamaño de ventana
        self.rect = align(self.image, self.position, self.offset)
        screen.blit(self.image, self.rect)

    def handle_event(self, event):
        # Verifica si se clickeó el botón
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: #si se presiono el left click
            if self.rect.collidepoint(event.pos): #verifica que el mouse este dentro del rect del boton
                if self.action:
                    self.action() #ejecuta la accion
        """if self.rect.collidepoint(event.pos) and pygame.mouse.get_pressed()[0] == 1:
            if self.action:
                    self.action() #ejecuta la accion"""
    


def play():
    print('A jugar')
    return

def init():
    print('Inicializar el juego')
    return

def stop():
    print('Detener el juego')
    return



buttons = [
    Button('prueba/assets/initBtn.png', 'bottom', (-220,0), init),
    Button('prueba/assets/playBtn.png', 'bottom', (-50,0), play),
    Button('prueba/assets/backwardsBtn.png', 'bottom', (80,0)),
    Button('prueba/assets/forwardsBtn.png', 'bottom', (170,0)),
    Button('prueba/assets/stopBtn.png', 'bottom', (270,0), stop),
]

"""def drawMap(graph, surface, start_x=100, start_y=100, cell_size=17):
    end_x = start_x + graph.cols * cell_size
    end_y = start_y + graph.rows * cell_size

    # Líneas horizontales
    for row in range(graph.rows + 1):
        y = start_y + row * cell_size
        pygame.draw.line(surface, PALETTE, (start_x, y), (end_x, y))

    # Líneas verticales
    for col in range(graph.cols + 1):
        x = start_x + col * cell_size
        pygame.draw.line(surface, PALETTE, (x, start_y), (x, end_y))"""


CELL_SIZE = 17  # tamaño de cada celda

def drawMap(graph, screen, center_x=0, center_y=0):
    for row in range(graph.rows):
        for col in range(graph.cols):
            node = graph.get_node(row, col)

            # Calcular posición en píxeles
            x = col * CELL_SIZE + center_x
            y = row * CELL_SIZE + center_y

            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

            # Elegir color según el estado
            if node.state == 'ocuppied' and node.content:      # con recurso
                
                resource = node.content
                img = pygame.image.load(resource.img_path).convert_alpha()
                img = pygame.transform.scale(img, (CELL_SIZE, CELL_SIZE))
                screen.blit(img, (x, y))

            elif node.state == 'mine':
                pygame.draw.rect(screen, (200, 0, 0), rect)  # rojo
            else:
                pygame.draw.rect(screen, BLACK, rect)  # gris (vacío)

            # Borde del rectángulo
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)

    pygame.display.flip()


def drawImg(url, position, offset=(0,0)):

    playImg = pygame.image.load(url).convert_alpha()
    
    surfaceRect = align(playImg, position, offset)
    screen.blit(playImg, surfaceRect)


graph = MapGraph(50,50)

center_x = 390
center_y = 20

resources = generate_resources(map_width=50, map_height=50, occupied_positions=set())

for re in resources:

    x,y = re.position    
    graph.set_node_state(y, x, 'ocuppied', re)

while running:

    screen.fill(BLACK)

    for event in pygame.event.get(): #obtiene los eventos de pygame
        if event.type == pygame.QUIT: #si el tipo de evento es cerrar el juego
            sys.exit() #cierra la ventana

        for button in buttons:
            button.handle_event(event)


    for button in buttons:
        button.draw(screen)

    drawMap(graph, screen, center_x, center_y)


    #print(pygame.mouse.get_pos())

    clock.tick(60)

    pygame.display.flip() #actualiza el display