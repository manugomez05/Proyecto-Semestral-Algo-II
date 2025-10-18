"""
Paquete principal: src
-------------------------------------------------
Este archivo convierte la carpeta `src/` en un paquete Python 
importable y centraliza los módulos del simulador de rescate.

Puede incluir configuraciones globales, metadatos o inicializaciones.
"""

# ==============================================================
# 🎨 PALETA DE COLORES GLOBAL
# ==============================================================

BLACK = (22, 33, 60)
WHITE = (238, 238, 238)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
PALETTE = (46, 68, 96)
GRAY = (80, 80, 80)
YELLOW = (255, 255, 0)

# ==============================================================
# ⚙️ CONFIGURACIÓN GENERAL
# ==============================================================

CELL_SIZE = 17          # tamaño de celda del mapa
SCREEN_WIDTH = 1600     # ancho de ventana
SCREEN_HEIGHT = 960     # alto de ventana
FPS = 60                # cuadros por segundo