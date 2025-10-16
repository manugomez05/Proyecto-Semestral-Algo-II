"""
Gestor de minas para el simulador de rescate.
Maneja la colección de minas, verificación de superposiciones y generación aleatoria.
"""
from __future__ import annotations
from typing import List
import random
from .mines import Mine, MineType, MINE_PARAMS, Cell

# Gestor principal de minas del simulador
class MineManager: 
    def __init__(self) -> None:
        self.mines: List[Mine] = []  # Colección de minas
        self.next_id: int = 1  # Contador de IDs

    def addMine(self, type: MineType, center: Cell) -> Mine:
        """Agrega una nueva mina al simulador"""
        params = MINE_PARAMS[type]
        mine = Mine(
            id=self.next_id,
            type=type,
            center=center,
            radius=params.get("radius", 0),
            half_width=params.get("half_width", 0),
            period=params.get("period", 0),
            static=params.get("static", True),
            active=True,
            next_activation=params.get("period", 0)
        )
        self.next_id += 1
        self.mines.append(mine)
        return mine 
    
    def removeMine(self, mine_id: int) -> bool:
        """Elimina una mina por su ID"""
        for i, m in enumerate(self.mines):
            if m.id == mine_id:
                self.mines.pop(i)
                return True 
        return False 

    def updateAll(self, tick: int) -> None:
        """Actualiza todas las minas dinámicas"""
        for m in self.mines:
            m.update(tick)

    def isCellMined(self, cell: Cell, tick: int) -> bool:
        """Verifica si una celda está afectada por alguna mina"""
        return any(m.contains(cell, tick) for m in self.mines)

    def minesAffecting(self, cell: Cell, tick: int) -> List[Mine]:
        """Obtiene todas las minas que afectan una celda"""
        return [m for m in self.mines if m.contains(cell, tick)]

    def all(self) -> List[Mine]:
        """Retorna todas las minas del simulador"""
        return list(self.mines)

    # Función para dibujar las minas en la superficie de pygame
def drawMines(surface, mines: "MinesManager", rows: int, cols: int, cell_size: int, offset_x: int = 0, offset_y: int = 0) -> None:
    try:
        import pygame
    except ImportError:
        raise RuntimeError("pygame no está disponible para dibujar minas")

    # Colores para diferentes estados de las minas
    COLOR_ACTIVE = (220, 80, 80)    # Rojo para minas activas
    COLOR_INACTIVE = (160, 160, 160)  # Gris para minas inactivas
    COLOR_T = (80, 120, 220)        # Azul para bandas T1 y T2

    # Convierte coordenadas de celda a píxeles considerando los offsets
    def cellToPx(row: int, col: int) -> tuple[int, int]:
        return offset_x + col * cell_size, offset_y + row * cell_size

    # Dibuja cada mina según su tipo
    for mine in mines.all():
        # Determina el color basado en el estado de la mina
        if mine.type in (MineType.T1, MineType.T2):
            color = COLOR_T
        else:
            color = COLOR_ACTIVE if mine.static or mine.active else COLOR_INACTIVE
            
        mine_row, mine_col = mine.center

        # Dibujo para minas circulares (O1, O2, G1)
        if mine.type in (MineType.O1, MineType.O2, MineType.G1):
            radius = mine.radius
            for delta_row in range(-radius, radius + 1):
                for delta_col in range(-radius, radius + 1):
                    current_row = mine_row + delta_row
                    current_col = mine_col + delta_col
                    if 0 <= current_row < rows and 0 <= current_col < cols:
                        if (delta_row * delta_row + delta_col * delta_col) <= radius * radius:
                            x, y = cellToPx(current_row, current_col)
                            # Dibuja un rectángulo con borde para que se vea la cuadrícula
                            rect = pygame.Rect(x, y, cell_size, cell_size)
                            pygame.draw.rect(surface, color, rect, 0)
                            # Dibuja un borde sutil para mantener la cuadrícula visible
                            pygame.draw.rect(surface, (0, 0, 0), rect, 1)

        # Dibujo para banda horizontal (T1)
        elif mine.type is MineType.T1:
            half_width = mine.half_width
            # Limita la extensión horizontal de la banda
            band_length = min(15, cols // 3)  # Máximo 15 celdas o 1/3 del ancho del mapa
            start_col = max(0, mine_col - band_length // 2)
            end_col = min(cols - 1, mine_col + band_length // 2)
            
            start_row = max(0, mine_row - half_width)
            end_row = min(rows - 1, mine_row + half_width)
            for current_row in range(start_row, end_row + 1):
                for current_col in range(start_col, end_col + 1):
                    x, y = cellToPx(current_row, current_col)
                    rect = pygame.Rect(x, y, cell_size, cell_size)
                    pygame.draw.rect(surface, color, rect, 0)
                    pygame.draw.rect(surface, (0, 0, 0), rect, 1)

        # Dibujo para banda vertical (T2)
        elif mine.type is MineType.T2:
            half_width = mine.half_width
            # Limita la extensión vertical de la banda
            band_length = min(15, rows // 3)  # Máximo 15 celdas o 1/3 del alto del mapa
            start_row = max(0, mine_row - band_length // 2)
            end_row = min(rows - 1, mine_row + band_length // 2)
            
            start_col = max(0, mine_col - half_width)
            end_col = min(cols - 1, mine_col + half_width)
            for current_col in range(start_col, end_col + 1):
                for current_row in range(start_row, end_row + 1):
                    x, y = cellToPx(current_row, current_col)
                    rect = pygame.Rect(x, y, cell_size, cell_size)
                    pygame.draw.rect(surface, color, rect, 0)
                    pygame.draw.rect(surface, (0, 0, 0), rect, 1)

    def _overlap(self, a: Mine, b: Mine) -> bool:
        """Verifica si dos minas se superponen"""
        ar, ac = a.center
        br, bc = b.center
        
        # Círculo–Círculo: distancia entre centros <= suma de radios
        if a.type in (MineType.O1, MineType.O2, MineType.G1) and b.type in (MineType.O1, MineType.O2, MineType.G1):
            dr, dc = ar - br, ac - bc
            return (dr*dr + dc*dc) <= (a.radius + b.radius) * (a.radius + b.radius)

        # Círculo–Banda horizontal (T1): verifica si el círculo intersecta la banda
        if a.type in (MineType.O1, MineType.O2, MineType.G1) and b.type is MineType.T1:
            # El círculo intersecta la banda si:
            # 1. La distancia vertical <= radio del círculo
            # 2. La distancia horizontal <= half_width de la banda
            return (abs(ar - br) <= a.radius) and (abs(ac - bc) <= b.half_width)
            
        if b.type in (MineType.O1, MineType.O2, MineType.G1) and a.type is MineType.T1:
            return (abs(br - ar) <= b.radius) and (abs(bc - ac) <= a.half_width)

        # Círculo–Banda vertical (T2): verifica si el círculo intersecta la banda
        if a.type in (MineType.O1, MineType.O2, MineType.G1) and b.type is MineType.T2:
            # El círculo intersecta la banda si:
            # 1. La distancia horizontal <= radio del círculo  
            # 2. La distancia vertical <= half_width de la banda
            return (abs(ac - bc) <= a.radius) and (abs(ar - br) <= b.half_width)
            
        if b.type in (MineType.O1, MineType.O2, MineType.G1) and a.type is MineType.T2:
            return (abs(bc - ac) <= b.radius) and (abs(br - ar) <= a.half_width)

        # Banda horizontal–Banda horizontal (T1–T1)
        if a.type is MineType.T1 and b.type is MineType.T1:
            # Se superponen si las distancias verticales se solapan
            return abs(ar - br) <= (a.half_width + b.half_width)

        # Banda vertical–Banda vertical (T2–T2)
        if a.type is MineType.T2 and b.type is MineType.T2:
            # Se superponen si las distancias horizontales se solapan
            return abs(ac - bc) <= (a.half_width + b.half_width)

        # Banda horizontal–Banda vertical (T1–T2): siempre se cruzan si están en la misma intersección
        if (a.type is MineType.T1 and b.type is MineType.T2) or (a.type is MineType.T2 and b.type is MineType.T1):
            # Se cruzan si el centro de una está dentro del rango de la otra
            if a.type is MineType.T1:  # a es horizontal, b es vertical
                return (abs(ar - br) <= a.half_width) and (abs(ac - bc) <= b.half_width)
            else:  # a es vertical, b es horizontal
                return (abs(ar - br) <= b.half_width) and (abs(ac - bc) <= a.half_width)

        return False

    def _would_overlap_any(self, candidate: Mine) -> bool:
        """Verifica si una mina candidata se superpone con alguna existente"""
        return any(self._overlap(candidate, existing) for existing in self.mines)

    def addRandomMine(self, type: MineType, rows: int, cols: int, margin: int = 0, max_attempts: int = 100) -> Mine:
        """Crea una mina en posición aleatoria sin superposición"""
        params = MINE_PARAMS[type]
        radius = params.get("radius", 0)
        half_width = params.get("half_width", 0)

        # rangos seguros para el centro según el tipo
        if type in (MineType.O1, MineType.O2, MineType.G1):
            min_row = radius + margin
            max_row = rows - 1 - (radius + margin)
            min_col = radius + margin
            max_col = cols - 1 - (radius + margin)
        elif type is MineType.T1:
            # franja horizontal: limitamos solo fila
            min_row = half_width + margin
            max_row = rows - 1 - (half_width + margin)
            min_col = 0 + margin
            max_col = cols - 1 - margin
        elif type is MineType.T2:
            # franja vertical: limitamos solo columna
            min_row = 0 + margin
            max_row = rows - 1 - margin
            min_col = half_width + margin
            max_col = cols - 1 - (half_width + margin)
        else:
            min_row = 0 + margin
            max_row = rows - 1 - margin
            min_col = 0 + margin
            max_col = cols - 1 - margin

        # sanity por si el mapa es muy chico
        min_row = max(0, min_row)
        min_col = max(0, min_col)
        max_row = max(min_row, max_row)
        max_col = max(min_col, max_col)

        # Intenta encontrar una posición sin superposición
        for attempt in range(max_attempts):
            row = random.randint(min_row, max_row)
            col = random.randint(min_col, max_col)
            
            # Crea una mina temporal para verificar superposición
            temp_mine = Mine(
                id=0,  # ID temporal
                type=type,
                center=(row, col),
                radius=radius,
                half_width=half_width,
                period=params.get("period", 0),
                static=params.get("static", True),
                active=True,
                next_activation=params.get("period", 0)
            )
            
            # Si no se superpone con ninguna mina existente, la agregamos
            if not self._would_overlap_any(temp_mine):
                return self.addMine(type, (row, col))
        
        # Si no se encontró una posición válida, lanza una excepción
        raise RuntimeError(f"No se pudo encontrar una posición válida para la mina {type} después de {max_attempts} intentos")

    def addRandomSet(self, rows: int, cols: int, spec: dict[MineType, int], margin: int = 0) -> None:
        """Crea múltiples minas aleatorias según especificación"""
        for type_, count in spec.items():
            for _ in range(count):
                self.addRandomMine(type_, rows, cols, margin=margin)


