"""
Módulo de utilidades de hashing optimizadas para el simulador de rescate.

Proporciona funciones hash personalizadas y estructuras de datos hash
optimizadas para casos de uso específicos del proyecto.

Estrategias de resolución de colisiones:
- Para hash tables de posiciones: Encadenamiento (Python dict nativo - óptimo)
- Para búsquedas espaciales: Hashing espacial con cuadrícula
"""

from typing import Tuple, Dict, List, Set, Optional, Any
import hashlib


class SpatialHashTable:
    """
    Tabla hash espacial optimizada para búsquedas de proximidad en 2D.
    
    Usa una cuadrícula virtual para dividir el espacio en celdas hash,
    permitiendo búsquedas rápidas de objetos cercanos en O(1) amortizado.
    
    Ideal para:
    - Detección de colisiones entre vehículos
    - Búsqueda de recursos cercanos
    - Verificación de proximidad a minas
    
    Estrategia: Hashing espacial con encadenamiento
    Complejidad: O(1) inserción, O(1) búsqueda en promedio
    """
    
    def __init__(self, cell_size: int = 5):
        """
        Args:
            cell_size: Tamaño de las celdas de la cuadrícula hash.
                      Valores más pequeños = más precisión pero más overhead.
                      Valores más grandes = menos precisión pero menos overhead.
        """
        self.cell_size = cell_size
        self.table: Dict[Tuple[int, int], List[Any]] = {}
    
    def _hash_position(self, row: int, col: int) -> Tuple[int, int]:
        """
        Función hash para posiciones 2D.
        Mapea coordenadas continuas a celdas de cuadrícula discreta.
        
        Args:
            row, col: Coordenadas de la posición
            
        Returns:
            Tupla (cell_x, cell_y) de la celda hash
        """
        cell_row = row // self.cell_size
        cell_col = col // self.cell_size
        return (cell_row, cell_col)
    
    def insert(self, row: int, col: int, obj: Any) -> None:
        """Inserta un objeto en la posición dada - O(1)"""
        cell = self._hash_position(row, col)
        if cell not in self.table:
            self.table[cell] = []
        self.table[cell].append((row, col, obj))
    
    def remove(self, row: int, col: int, obj: Any) -> bool:
        """Elimina un objeto de la posición dada - O(k) donde k = objetos en la celda"""
        cell = self._hash_position(row, col)
        if cell not in self.table:
            return False
        
        items = self.table[cell]
        for i, (r, c, o) in enumerate(items):
            if r == row and c == col and o == obj:
                items.pop(i)
                if not items:
                    del self.table[cell]
                return True
        return False
    
    def query_radius(self, row: int, col: int, radius: int) -> List[Tuple[int, int, Any]]:
        """
        Busca todos los objetos dentro de un radio dado - O(k) donde k = objetos en rango
        
        Args:
            row, col: Centro de búsqueda
            radius: Radio de búsqueda (en unidades de mapa)
            
        Returns:
            Lista de (row, col, obj) de objetos encontrados
        """
        results = []
        
        # Calcular rango de celdas a buscar
        cell_center = self._hash_position(row, col)
        cell_radius = (radius // self.cell_size) + 1
        
        # Buscar en todas las celdas vecinas dentro del radio
        for dr in range(-cell_radius, cell_radius + 1):
            for dc in range(-cell_radius, cell_radius + 1):
                cell = (cell_center[0] + dr, cell_center[1] + dc)
                if cell in self.table:
                    for r, c, obj in self.table[cell]:
                        if abs(r - row) + abs(c - col) <= radius:
                            results.append((r, c, obj))
        
        return results
    
    def query_cell(self, row: int, col: int) -> List[Any]:
        """Busca todos los objetos en una posición exacta - O(k)"""
        cell = self._hash_position(row, col)
        if cell not in self.table:
            return []
        
        return [obj for r, c, obj in self.table[cell] if r == row and c == col]
    
    def clear(self):
        """Limpia la tabla hash - O(1)"""
        self.table.clear()
    
    def __len__(self) -> int:
        """Retorna el número total de objetos - O(n)"""
        return sum(len(items) for items in self.table.values())


class FastIDHashTable:
    """
    Tabla hash optimizada para IDs de objetos (vehículos, minas, etc.).
    
    Usa hashing directo con resolución de colisiones por encadenamiento.
    Implementada sobre dict de Python (altamente optimizado en C).
    
    Complejidad: O(1) para insert, get, delete en promedio
    """
    
    def __init__(self):
        self._table: Dict[str, Any] = {}
        self._count = 0
    
    def insert(self, key: str, value: Any) -> None:
        """Inserta o actualiza un valor - O(1) amortizado"""
        if key not in self._table:
            self._count += 1
        self._table[key] = value
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor por clave - O(1) amortizado"""
        return self._table.get(key)
    
    def delete(self, key: str) -> bool:
        """Elimina un valor por clave - O(1) amortizado"""
        if key in self._table:
            del self._table[key]
            self._count -= 1
            return True
        return False
    
    def contains(self, key: str) -> bool:
        return key in self._table
    
    def keys(self) -> List[str]:
        return list(self._table.keys())
    
    def values(self) -> List[Any]:
        return list(self._table.values())
    
    def items(self) -> List[Tuple[str, Any]]:
        return list(self._table.items())
    
    def clear(self):
        self._table.clear()
        self._count = 0
    
    def __len__(self) -> int:
        return self._count
    
    def __contains__(self, key: str) -> bool:
        return key in self._table


def hash_position(row: int, col: int) -> int:
    """
    Función hash para posiciones 2D usando emparejamiento de Cantor.
    
    Mapea dos enteros (row, col) a un único entero sin colisiones.
    Útil para crear claves hash únicas para posiciones.
    
    Fórmula: (row + col) * (row + col + 1) / 2 + col
    
    Complejidad: O(1)
    """
    return ((row + col) * (row + col + 1) // 2) + col


def hash_vehicle_id(player_id: str, vehicle_type: str, index: int) -> str:
    """
    Genera un ID hash único para un vehículo.
    
    Args:
        player_id: ID del jugador (ej: "Jugador_1")
        vehicle_type: Tipo de vehículo (ej: "jeep", "moto")
        index: Índice del vehículo de ese tipo
        
    Returns:
        ID único en formato "{player_id}_{vehicle_type}_{index}"
        
    Complejidad: O(1)
    """
    return f"{player_id}_{vehicle_type}_{index}"


def hash_string(s: str) -> int:
    """
    Hash rápido para strings usando el algoritmo DJB2.
    
    Alternativa más rápida que hash() de Python para strings cortos.
    Útil para comparaciones y búsquedas rápidas.
    
    Complejidad: O(n) donde n = longitud del string
    """
    h = 5381
    for char in s:
        h = ((h << 5) + h) + ord(char)
    return h & 0xFFFFFFFF 


class BloomFilter:
    """
    Filtro de Bloom para verificación rápida de membresía con falsos positivos.
    
    Útil para:
    - Verificar rápidamente si una celda "probablemente" tiene un recurso
    - Filtrar búsquedas costosas antes de verificar en estructuras exactas
    
    Ventajas:
    - O(1) inserción y búsqueda
    - Uso mínimo de memoria
    
    Desventajas:
    - Puede tener falsos positivos (dice "sí" cuando es "no")
    - No puede eliminar elementos
    """
    
    def __init__(self, size: int = 10000, num_hashes: int = 3):
        """
        Args:
            size: Tamaño del array de bits
            num_hashes: Número de funciones hash a usar
        """
        self.size = size
        self.num_hashes = num_hashes
        self.bit_array = [False] * size
    
    def _hash_functions(self, item: Any) -> List[int]:
        """Genera múltiples hashes para un item"""
        base_hash = hash(str(item))
        hashes = []
        for i in range(self.num_hashes):
            h = (base_hash + i * hash_string(str(item) + str(i))) % self.size
            hashes.append(h)
        return hashes
    
    def add(self, item: Any) -> None:
        """Agrega un item al filtro - O(k) donde k = num_hashes"""
        for h in self._hash_functions(item):
            self.bit_array[h] = True
    
    def contains(self, item: Any) -> bool:
        """
        Verifica si un item probablemente está en el filtro - O(k)
        
        Returns:
            True: El item PROBABLEMENTE está (puede ser falso positivo)
            False: El item DEFINITIVAMENTE NO está (100% seguro)
        """
        return all(self.bit_array[h] for h in self._hash_functions(item))
    
    def clear(self):
        """Limpia el filtro - O(n)"""
        self.bit_array = [False] * self.size


# Funciones de utilidad para el proyecto

def create_position_hash_key(row: int, col: int) -> str:
    """Crea una clave hash string para una posición - O(1)"""
    return f"{row}:{col}"


def parse_position_hash_key(key: str) -> Tuple[int, int]:
    """Parsea una clave hash de posición - O(1)"""
    row, col = key.split(':')
    return (int(row), int(col))


def manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """Calcula la distancia Manhattan entre dos posiciones - O(1)"""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def euclidean_distance_squared(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """
    Calcula el cuadrado de la distancia Euclidiana (evita sqrt) - O(1)
    Útil para comparaciones de distancia sin calcular la raíz cuadrada.
    """
    dr = pos1[0] - pos2[0]
    dc = pos1[1] - pos2[1]
    return dr * dr + dc * dc

