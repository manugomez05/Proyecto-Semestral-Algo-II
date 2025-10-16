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
    MineType.G1: {"radius": 2, "period": 60, "static": False},
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

        # Verificación para bandas
        if self.type is MineType.T1:
            return abs(r-r0) <= self.half_width
        if self.type is MineType.T2:
            return abs(c-c0) <= self.half_width

        return False 


