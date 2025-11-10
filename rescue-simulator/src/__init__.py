"""
Paquete principal: src
-------------------------------------------------
Este archivo convierte la carpeta `src/` en un paquete Python 
importable y centraliza los módulos del simulador de rescate.

Puede incluir configuraciones globales, metadatos o inicializaciones.
"""

# ==============================================================
# 🎨 PALETA DE COLORES GLOBAL (Mejorada para mejor contraste)
# ==============================================================

BLACK = (15, 20, 35)          # Fondo principal más oscuro
WHITE = (245, 245, 250)       # Texto más brillante
GREEN = (50, 255, 100)        # Verde más vibrante
RED = (255, 60, 60)           # Rojo más vivo
BLUE = (80, 140, 255)         # Azul más brillante
PALETTE = (46, 68, 96)
GRAY = (100, 100, 110)        # Gris más visible
YELLOW = (255, 220, 50)       # Amarillo más cálido

PALETTE_1 = (150, 190, 180)   # Verde agua claro (texto principal)
PALETTE_2 = (120, 190, 185)   # Turquesa medio
PALETTE_3 = (80, 140, 160)    # Azul medio (texto secundario)
PALETTE_4 = (50, 75, 105)     # Azul oscuro (minas)
PALETTE_5 = (25, 40, 65)      # Azul muy oscuro
PALETTE_6 = (35, 50, 75)      # Grid mejorado (más visible)

# ==============================================================
# ⚙️ CONFIGURACIÓN GENERAL
# ==============================================================

CELL_SIZE = 17          # tamaño de celda del mapa
SCREEN_WIDTH = 1600     # ancho de ventana
SCREEN_HEIGHT = 960     # alto de ventana
FPS = 40                # cuadros por segundo

# package marker