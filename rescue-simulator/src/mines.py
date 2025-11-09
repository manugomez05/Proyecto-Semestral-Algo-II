"""
Módulo de definiciones para el sistema de minas del simulador.
Contiene tipos, enums, clases de datos y funciones de visualización.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple, List, Dict, Optional

# Tipos de minas disponibles en el simulador
class MineType(Enum): 
    O1 = auto()  # Círculo estático grande
    O2 = auto()  # Círculo estático pequeño
    T1 = auto()  # Banda horizontal
    T2 = auto()  # Banda vertical
    G1 = auto()  # Círculo dinámico (aparece/desaparece)

# Configuración de parámetros para cada tipo de mina
MINE_PARAMS: Dict[MineType, Dict[str, int]] = {
    MineType.O1: {"radius": 3, "static": True},
    MineType.O2: {"radius": 2, "static": True},
    MineType.T1: {"half_width": 3, "static": True},
    MineType.T2: {"half_width": 2, "static": True},
    MineType.G1: {"radius": 2, "period": 5, "static": False, "time_based": True},  # 5 segundos
} 

# Tipo para coordenadas de celda (fila, columna)
Cell = Tuple[int, int]

# Representa una mina individual con su estado y propiedades
@dataclass 
class Mine: 
    id: int  # ID único
    type: MineType  # Tipo de mina
    center: Cell  # Posición central
    radius: int = 0  # Radio para círculos
    half_width: int = 0  # Mitad del ancho para bandas
    period: int = 0  # Período de activación (minas dinámicas)
    static: bool = True  # Si es estática o dinámica
    active: bool = True  # Estado actual
    next_activation: int = 0  # Tiempo para próxima activación


    def update(self, tick: int) -> None: 
        """Actualiza el estado de minas dinámicas según el tiempo"""
        if not self.static and tick >= self.next_activation:
            self.active = not self.active
            self.next_activation = tick + self.period

    def update_time_based(self, elapsed_time: float) -> None:
        """Actualiza el estado de minas dinámicas según tiempo real (segundos)"""
        if not self.static and elapsed_time >= self.next_activation:
            self.active = not self.active
            self.next_activation = elapsed_time + self.period

    def contains(self, cell: Cell, tick: int) -> bool:
        """Verifica si una celda está dentro del área de efecto"""
        # Calcula estado de activación
        if not self.static:
            if tick >= self.next_activation:
                toggles = (tick - self.next_activation) // self.period + 1 if self.period > 0 else 0
                is_active = (self.active if toggles % 2 == 0 else (not self.active))
            else:
                is_active = self.active
        else:
            is_active = self.active
            
        if not is_active:
            return False

        r0, c0 = self.center
        r, c = cell 

        # Verificación para círculos
        if self.type in (MineType.O1, MineType.O2, MineType.G1):
            dr, dc = r-r0, c-c0
            return (dr * dr + dc * dc) <= (self.radius * self.radius)

        # Verificación para bandas (líneas finas)
        if self.type is MineType.T1:
            # Banda horizontal: 1 fila × 15 columnas (±7 desde el centro)
            band_half_length = 7  # Se extiende 7 celdas a cada lado del centro
            return r == r0 and abs(c-c0) <= band_half_length
        if self.type is MineType.T2:
            # Banda vertical: 11 filas (±5 desde el centro) × 1 columna
            band_half_length = 5  # Se extiende 5 celdas arriba y abajo del centro
            return c == c0 and abs(r-r0) <= band_half_length
        
        return False


