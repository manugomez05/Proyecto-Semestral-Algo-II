import pygame 
import sys #para cerrar el programa correctamente.

#----------------------------Inicializando el display-------------------------------
pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("Simulador de Rescate")

CELL_SIZE = 40 #TAMAÑO DE LAS CUADRICULAS (pixeles de 40x40) QUE REPRESENTARIAN A LOS NODOS, lo podemos cambiar!!!!!!!!

ROWS = HEIGHT // CELL_SIZE #hago la cuenta de cuantas cuadrículas entran en la pantalla, altura dividido tamaño
COLS = WIDTH // CELL_SIZE

WHITE = (255,255,255)

running = True
while running:
    for event in pygame.event.get(): #obtiene todos los eventos (teclado, ratón, etc.).
        if event.type == pygame.QUIT:
            running = False

    screen.fill(WHITE)# Pinta el fondo de blanco 

# Dibujar líneas horizontales
    for row in range(ROWS + 1):
        y = row * CELL_SIZE
        pygame.draw.line(screen, (200, 200, 200), (0, y), (WIDTH, y))

    # Dibujar líneas verticales
    for col in range(COLS + 1):
        x = col * CELL_SIZE
        pygame.draw.line(screen, (200, 200, 200), (x, 0), (x, HEIGHT))
    pygame.display.flip() # Actualiza la pantalla
pygame.quit()
sys.exit()
#----------------------------------------------------------------------------------



