"""
Simulador de Rescate - Gestor del mapa principal.
Maneja la visualización del mapa, cuadrícula y minas.
"""
import random
import pygame 
import sys
from mines import *
from minesmanager import *

# Configuración de la ventana
pygame.init()
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulador de Rescate")

# Configuración del mapa
ROWS = 50  # Filas de la cuadrícula
COLS = 50  # Columnas de la cuadrícula
CELL_SIZE = min(WIDTH // COLS, HEIGHT // ROWS)  # Tamaño de celda

# Dimensiones de la cuadrícula
GRID_WIDTH = CELL_SIZE * COLS
GRID_HEIGHT = CELL_SIZE * ROWS

# Centrado de la cuadrícula en la ventana
OFFSET_X = (WIDTH - GRID_WIDTH) // 2
OFFSET_Y = (HEIGHT - GRID_HEIGHT) // 2

# Colores
WHITE = (255, 255, 255)
GRID_COLOR = (200, 200, 200)


# Inicialización del sistema de minas
mines = MineManager()
# Configuración de minas para pruebas
mines.addRandomSet(ROWS, COLS, {
    MineType.O1: 1,    # Círculo grande
    MineType.O2: 1,    # Círculo pequeño
    MineType.T1: 1,    # Banda horizontal
    MineType.T2: 1,    # Banda vertical
    MineType.G1: 1,    # Círculo dinámico
}, margin=5)

tick = 0  # Contador de tiempo del simulador

# Bucle principal del simulador
running = True
while running:
    # Manejo de eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Limpiar pantalla
    screen.fill(WHITE)

    # Dibujar cuadrícula horizontal
    for row in range(ROWS + 1):
        y = OFFSET_Y + row * CELL_SIZE
        pygame.draw.line(screen, GRID_COLOR, (OFFSET_X, y), (OFFSET_X + GRID_WIDTH, y))

    # Dibujar cuadrícula vertical
    for col in range(COLS + 1):
        x = OFFSET_X + col * CELL_SIZE
        pygame.draw.line(screen, GRID_COLOR, (x, OFFSET_Y), (x, OFFSET_Y + GRID_HEIGHT))

    # Actualizar sistema de minas
    tick += 1
    mines.updateAll(tick)

    # Dibujar minas
    drawMines(screen, mines, ROWS, COLS, CELL_SIZE, OFFSET_X, OFFSET_Y)

    # Actualizar pantalla
    pygame.display.flip()

# Limpieza y salida
pygame.quit()
sys.exit()



