"""
Gestor de minas para el simulador de rescate.
Maneja la colección de minas, verificación de superposiciones y generación aleatoria.
Optimizado con hash tables para búsqueda eficiente O(1).
"""
from __future__ import annotations
from typing import List, Dict, TYPE_CHECKING
import random
from src.mines import *
from src import PALETTE_5, PALETTE_4

# Evitar importación circular
if TYPE_CHECKING:
    from src.map_graph import MapGraph
# Gestor principal de minas del simulador
class MineManager: 
    def __init__(self) -> None:
        self.mines: List[Mine] = []  # Colección de minas (mantener para compatibilidad)
        self.mines_by_id: Dict[int, Mine] = {}  # Hash table: ID -> Mine (O(1) lookup)
        self.mined_cells_cache: Dict[Cell, List[int]] = {}  # Hash table espacial: Cell -> [mine_ids]
        self.next_id: int = 1  # Contador de IDs

    def addMine(self, type: MineType, center: Cell) -> Mine:
        """Agrega una nueva mina al simulador"""
        params = MINE_PARAMS[type]
        period = params.get("period", 0)
        mine = Mine(
            id=self.next_id,
            type=type,
            center=center,
            radius=params.get("radius", 0),
            half_width=params.get("half_width", 0),
            period=period,
            static=params.get("static", True),
            active=True,
            next_activation=period  # Próxima activación en period ticks
        )
        mine_id = self.next_id
        self.next_id += 1
        
        # Agregar a ambas estructuras
        self.mines.append(mine)
        self.mines_by_id[mine_id] = mine  # Hash table O(1)
        
        # Actualizar cache espacial: precalcular todas las celdas afectadas
        self._update_spatial_cache_for_mine(mine)
        
        return mine
    
    def _update_spatial_cache_for_mine(self, mine: Mine, rows: int = 50, cols: int = 50) -> None:
        """Actualiza el cache espacial para una mina específica.
        Precalcula todas las celdas que esta mina puede afectar.
        """
        # Determinar el área de búsqueda según el tipo de mina
        r0, c0 = mine.center
        
        if mine.type in (MineType.O1, MineType.O2, MineType.G1):
            # Minas circulares: buscar en un cuadrado alrededor del centro
            radius = mine.radius
            for r in range(max(0, r0 - radius), min(rows, r0 + radius + 1)):
                for c in range(max(0, c0 - radius), min(cols, c0 + radius + 1)):
                    if mine.contains((r, c), tick=0):
                        cell = (r, c)
                        if cell not in self.mined_cells_cache:
                            self.mined_cells_cache[cell] = []
                        if mine.id not in self.mined_cells_cache[cell]:
                            self.mined_cells_cache[cell].append(mine.id)
        
        elif mine.type == MineType.T1:
            # Banda horizontal
            band_half_length = 7
            for c in range(max(0, c0 - band_half_length), min(cols, c0 + band_half_length + 1)):
                cell = (r0, c)
                if cell not in self.mined_cells_cache:
                    self.mined_cells_cache[cell] = []
                if mine.id not in self.mined_cells_cache[cell]:
                    self.mined_cells_cache[cell].append(mine.id)
        
        elif mine.type == MineType.T2:
            # Banda vertical
            band_half_length = 5
            for r in range(max(0, r0 - band_half_length), min(rows, r0 + band_half_length + 1)):
                cell = (r, c0)
                if cell not in self.mined_cells_cache:
                    self.mined_cells_cache[cell] = []
                if mine.id not in self.mined_cells_cache[cell]:
                    self.mined_cells_cache[cell].append(mine.id) 
    
    def removeMine(self, mine_id: int) -> bool:
        """Elimina una mina por su ID (optimizado con hash table - O(1))"""
        # Buscar en hash table O(1) en lugar de búsqueda lineal O(n)
        mine = self.mines_by_id.get(mine_id)
        if mine is None:
            return False
        
        # Eliminar de hash table
        del self.mines_by_id[mine_id]
        
        # Eliminar de lista (mantener compatibilidad)
        self.mines.remove(mine)
        
        # Limpiar cache espacial para esta mina
        self._remove_from_spatial_cache(mine)
        
        return True
    
    def _remove_from_spatial_cache(self, mine: Mine) -> None:
        """Elimina una mina del cache espacial."""
        cells_to_clean = []
        for cell, mine_ids in self.mined_cells_cache.items():
            if mine.id in mine_ids:
                mine_ids.remove(mine.id)
                if not mine_ids:  # Si la lista queda vacía, marcar para eliminar
                    cells_to_clean.append(cell)
        
        # Eliminar celdas vacías del cache
        for cell in cells_to_clean:
            del self.mined_cells_cache[cell] 

    def updateAll(self, tick: int, rows: int = 50, cols: int = 50, elapsed_time: float = 0, map_manager=None) -> None:
        """Actualiza todas las minas dinámicas"""
        for m in self.mines:
            if not m.static:
                # Para minas dinámicas basadas en ticks
                if tick >= m.next_activation:
                    # Si es una mina G1 que se está reactivando (pasa de inactiva a activa), moverla a nueva posición
                    if m.type == MineType.G1 and not m.active:
                        self._moveG1Mine(m, tick, rows, cols, map_manager)
                    m.update(tick)

    def isCellMined(self, cell: Cell, tick: int) -> bool:
        """Verifica si una celda está afectada por alguna mina (optimizado con hash table espacial - O(1) amortizado)"""
        # Usar cache espacial: O(1) lookup en lugar de O(n) iteración
        mine_ids = self.mined_cells_cache.get(cell, [])
        if not mine_ids:
            return False
        
        # Verificar si alguna de las minas que afectan esta celda está activa en este tick
        for mine_id in mine_ids:
            mine = self.mines_by_id.get(mine_id)
            if mine and mine.contains(cell, tick):
                return True
        return False

    def minesAffecting(self, cell: Cell, tick: int) -> List[Mine]:
        """Obtiene todas las minas que afectan una celda (optimizado con hash table espacial)"""
        # Usar cache espacial: O(k) donde k es el número de minas en esa celda (típicamente k << n)
        mine_ids = self.mined_cells_cache.get(cell, [])
        result = []
        for mine_id in mine_ids:
            mine = self.mines_by_id.get(mine_id)
            if mine and mine.contains(cell, tick):
                result.append(mine)
        return result

    def all(self) -> List[Mine]:
        """Retorna todas las minas del simulador"""
        return list(self.mines)

    def _overlap(self, a: Mine, b: Mine) -> bool:
        """Verifica si dos minas se superponen.
        - Círculos: disco de radio `radius`.
        - T1/T2: rectángulos finitos. Para longitud usamos `half_length` si existe,
          de lo contrario un valor por defecto pequeño (7)."""
        DEFAULT_BAND_HALF_LENGTH = 7

        def is_circle(m: Mine) -> bool:
            return m.type in (MineType.O1, MineType.O2, MineType.G1)

        def band_rect(m: Mine) -> tuple[int, int, int, int]:
            # Devuelve (min_row, max_row, min_col, max_col)
            r0, c0 = m.center
            half_w = m.half_width
            half_len = getattr(m, 'half_length', DEFAULT_BAND_HALF_LENGTH)
            if m.type is MineType.T1:  # horizontal: alto = 2*half_w+1, largo = 2*half_len+1
                return (r0 - half_w, r0 + half_w, c0 - half_len, c0 + half_len)
            if m.type is MineType.T2:  # vertical: alto = 2*half_len+1, ancho = 2*half_w+1
                return (r0 - half_len, r0 + half_len, c0 - half_w, c0 + half_w)
            # No banda
            return (r0, r0, c0, c0)

        def circle_circle_overlap(a: Mine, b: Mine) -> bool:
            ar, ac = a.center
            br, bc = b.center
            dr, dc = ar - br, ac - bc
            rr = a.radius + b.radius
            return (dr * dr + dc * dc) <= (rr * rr)

        def circle_rect_overlap(circle: Mine, rect_owner: Mine) -> bool:
            # Prueba estándar círculo-rectángulo (por celdas).
            cr, cc = circle.center
            rmin, rmax, cmin, cmax = band_rect(rect_owner)
            # Punto más cercano del rectángulo al centro del círculo
            nr = cr if rmin <= cr <= rmax else (rmin if cr < rmin else rmax)
            nc = cc if cmin <= cc <= cmax else (cmin if cc < cmin else cmax)
            dr, dc = cr - nr, cc - nc
            return (dr * dr + dc * dc) <= (circle.radius * circle.radius)

        def rect_rect_overlap(a_rect: tuple[int, int, int, int], b_rect: tuple[int, int, int, int]) -> bool:
            a_rmin, a_rmax, a_cmin, a_cmax = a_rect
            b_rmin, b_rmax, b_cmin, b_cmax = b_rect
            # Se superponen si hay intersección en ambas dimensiones
            rows_overlap = not (a_rmax < b_rmin or b_rmax < a_rmin)
            cols_overlap = not (a_cmax < b_cmin or b_cmax < a_cmin)
            return rows_overlap and cols_overlap

        # Casos
        if is_circle(a) and is_circle(b):
            return circle_circle_overlap(a, b)

        if is_circle(a) and (b.type in (MineType.T1, MineType.T2)):
            return circle_rect_overlap(a, b)
        if is_circle(b) and (a.type in (MineType.T1, MineType.T2)):
            return circle_rect_overlap(b, a)

        if (a.type in (MineType.T1, MineType.T2)) and (b.type in (MineType.T1, MineType.T2)):
            return rect_rect_overlap(band_rect(a), band_rect(b))

        return False

    def _would_overlap_any(self, candidate: Mine) -> bool:
        """Verifica si una mina candidata se superpone con alguna existente"""
        return any(self._overlap(candidate, existing) for existing in self.mines)

    def _moveG1Mine(self, mine: Mine, tick: int, rows: int, cols: int, map_manager=None) -> None:
        """Mueve una mina G1 a una nueva posición aleatoria"""
        import random
        
        # Parámetros de la mina G1
        radius = mine.radius
        margin = 2  # Margen de seguridad
        
        # Rango seguro para el centro (considerando el radio)
        min_row = radius + margin
        max_row = rows - 1 - (radius + margin)
        min_col = radius + margin
        max_col = cols - 1 - (radius + margin)
        
        # Asegurar que los rangos sean válidos
        min_row = max(0, min_row)
        min_col = max(0, min_col)
        max_row = max(min_row, max_row)
        max_col = max(min_col, max_col)
        
        # Intentar encontrar una nueva posición
        max_attempts = 100
        for _ in range(max_attempts):
            new_row = random.randint(min_row, max_row)
            new_col = random.randint(min_col, max_col)
            
            # Crear mina temporal para verificar superposición
            temp_mine = Mine(
                id=mine.id,
                type=mine.type,
                center=(new_row, new_col),
                radius=mine.radius,
                half_width=mine.half_width,
                period=mine.period,
                static=mine.static,
                active=mine.active,
                next_activation=mine.next_activation
            )
            
            # Verificar que no se superponga con otras minas (excepto consigo misma)
            overlaps = False
            for existing in self.mines:
                if existing.id != mine.id and self._overlap(temp_mine, existing):
                    overlaps = True
                    break
            
            # Verificar que no se superponga con recursos
            if not overlaps:
                # Verificar que el radio de la mina no afecte recursos
                safe_position = True
                if map_manager:
                    for delta_row in range(-radius, radius + 1):
                        for delta_col in range(-radius, radius + 1):
                            check_row = new_row + delta_row
                            check_col = new_col + delta_col
                            if 0 <= check_row < rows and 0 <= check_col < cols:
                                if (delta_row * delta_row + delta_col * delta_col) <= radius * radius:
                                    # Verificar si esta celda tiene un recurso
                                    node = map_manager.graph.get_node(check_row, check_col)
                                    if node.state == 'occupied' and node.content:
                                        #print(f"DEBUG: Posición ({new_row}, {new_col}) no es segura - hay recurso en ({check_row}, {check_col})")
                                        safe_position = False
                                        break
                        if not safe_position:
                            break
                
                if safe_position:
                    # Mover la mina a la nueva posición
                    old_pos = mine.center
                    
                    # Limpiar el cache espacial de la posición anterior
                    self._remove_from_spatial_cache(mine)
                    
                    # Actualizar posición
                    mine.center = (new_row, new_col)
                    
                    # Actualizar cache espacial con la nueva posición
                    self._update_spatial_cache_for_mine(mine, rows, cols)
                    
                    #print(f"DEBUG: G1 movida de {old_pos} a {mine.center}")
                    break

    def addRandomMine(self, type: MineType, rows: int, cols: int, margin: int = 0, max_attempts: int = 100, map_graph: "MapGraph" = None) -> Mine:
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

        # sanity por si el mapa es muy chico
        min_row = max(0, min_row)
        min_col = max(0, min_col)
        max_row = max(min_row, max_row)
        max_col = max(min_col, max_col)

        # Intenta encontrar una posición sin superposición
        for _ in range(max_attempts):
            row = random.randint(min_row, max_row)
            col = random.randint(min_col, max_col)
            
            # Crea una mina temporal para verificar superposición
            temp_mine = Mine(
                id=0,  # ID temporal
                type=type,
                center=(row, col),
                radius=radius,
                half_width=half_width,
                period=params.get("period", 0),  # 0 para estáticas
                static=params.get("static", True),
                active=True,
                next_activation=params.get("period", 0)
            )
            
            # Si no se superpone con ninguna mina existente, la agregamos
            if not self._would_overlap_any(temp_mine):
                if map_graph:
                    map_graph.set_node_state(row, col, "mine", temp_mine)
                return self.addMine(type, (row, col))
        
        # Si no se encontró una posición válida, lanza una excepción
        raise RuntimeError(f"No se pudo encontrar una posición válida para la mina {type} después de {max_attempts} intentos")

    def addRandomSet(self, rows: int, cols: int, spec: dict[MineType, int], margin: int = 0, map_graph: "MapGraph" = None) -> None:
        """Crea múltiples minas aleatorias según especificación"""
        for type_, count in spec.items():
            for _ in range(count):
                self.addRandomMine(type_, rows, cols, margin=margin, map_graph=map_graph)


# Cache global para rectángulos pre-calculados
_rect_cache = {}

# Función para dibujar las minas en la superficie de pygame
def drawMines(surface, mines: MineManager, rows: int, cols: int, cell_size: int, offset_x: int = 0, offset_y: int = 0) -> None:
    try:
        import pygame
    except ImportError:
        raise RuntimeError("pygame no está disponible para dibujar minas")

    # Colores para diferentes estados de las minas
    COLOR_ACTIVE = (170, 150, 150)    # Rojo para minas activas
    COLOR_INACTIVE = (160, 160, 160)  # Gris para minas inactivas
    COLOR_T = (80, 120, 220)        # Azul para bandas T1 y T2

    # Convierte coordenadas de celda a píxeles considerando los offsets
    def cellToPx(row: int, col: int) -> tuple[int, int]:
        return offset_x + col * cell_size, offset_y + row * cell_size
    
    # Obtiene un rectángulo del caché o lo crea
    def get_cached_rect(x: int, y: int) -> pygame.Rect:
        cache_key = (x, y, cell_size)
        if cache_key not in _rect_cache:
            _rect_cache[cache_key] = pygame.Rect(x, y, cell_size, cell_size)
        return _rect_cache[cache_key]

    # Dibuja cada mina según su tipo
    for mine in mines.all():
        # Para minas dinámicas (G1), solo dibujar si están activas
        if not mine.static and not mine.active:
            continue
            
        # Determina el color basado en el estado de la mina
        if mine.type in (MineType.T1, MineType.T2):
            color = COLOR_T
        else:
            color = COLOR_ACTIVE if mine.static or mine.active else COLOR_INACTIVE
            
        mine_row, mine_col = mine.center

        # Dibujo para minas circulares (O1, O2, G1) - TEMPORAL: mostrar radio completo
        if mine.type in (MineType.O1, MineType.O2, MineType.G1):
            radius = mine.radius
            for delta_row in range(-radius, radius + 1):
                for delta_col in range(-radius, radius + 1):
                    current_row = mine_row + delta_row
                    current_col = mine_col + delta_col
                    if 0 <= current_row < rows and 0 <= current_col < cols:
                        if (delta_row * delta_row + delta_col * delta_col) <= radius * radius:
                            x, y = cellToPx(current_row, current_col)
                            rect = get_cached_rect(x, y)
                            
                            # Centro en rojo, radio en amarillo
                            if delta_row == 0 and delta_col == 0:
                                pygame.draw.rect(surface, (140, 0, 0), rect, 0)  # Centro rojo
                            else:
                                pygame.draw.rect(surface, PALETTE_4, rect, 0)  # Radio amarillo
                            
                            # Dibuja un borde para mantener la cuadrícula visible
                            pygame.draw.rect(surface, (0, 0, 0), rect, 1)

        # Dibujo para banda horizontal (T1) - Línea horizontal de 1 fila
        elif mine.type is MineType.T1:
            # Extensión horizontal: ±7 celdas desde el centro
            band_half_length = 7  # Debe coincidir con la lógica en mines.py
            start_col = max(0, mine_col - band_half_length)
            end_col = min(cols - 1, mine_col + band_half_length)
            
            # Solo dibuja la línea horizontal (1 fila)
            for current_col in range(start_col, end_col + 1):
                x, y = cellToPx(mine_row, current_col)
                rect = get_cached_rect(x, y)
                
                # Centro en rojo, resto en amarillo
                if current_col == mine_col:
                    pygame.draw.rect(surface, (140, 0, 0), rect, 0)  # Centro rojo
                else:
                    pygame.draw.rect(surface, PALETTE_4, rect, 0)  # Línea amarilla
                
                pygame.draw.rect(surface, (0, 0, 0), rect, 1)

        # Dibujo para banda vertical (T2) - Línea vertical de 1 columna
        elif mine.type is MineType.T2:
            # Extensión vertical: ±5 celdas desde el centro
            band_half_length = 5  # Debe coincidir con la lógica en mines.py
            start_row = max(0, mine_row - band_half_length)
            end_row = min(rows - 1, mine_row + band_half_length)
            
            # Solo dibuja la línea vertical (1 columna)
            for current_row in range(start_row, end_row + 1):
                x, y = cellToPx(current_row, mine_col)
                rect = get_cached_rect(x, y)
                
                # Centro en rojo, resto en amarillo
                if current_row == mine_row:
                    pygame.draw.rect(surface, (140, 0, 0), rect, 0)  # Centro rojo
                else:
                    pygame.draw.rect(surface, PALETTE_4, rect, 0)  # Línea amarilla
                
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

    def addRandomSet(self, rows: int, cols: int, spec: dict[MineType, int], margin: int = 0, map_graph: "MapGraph" = None) -> None:
        """Crea múltiples minas aleatorias según especificación"""
        for type_, count in spec.items():
            for _ in range(count):
                self.addRandomMine(type_, rows, cols, margin=margin, map_graph=map_graph)


