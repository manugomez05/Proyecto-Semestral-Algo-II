from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Optional, Set
from pathlib import Path

TRUCK_COLOR = (30, 144, 255)
JEEP_COLOR = (34, 139, 34)
CAR_COLOR = (240, 240, 240)
MOTORCYCLE_COLOR = (255, 140, 0)

# Rutas a las imágenes de vehículos
base_path = Path(__file__).resolve().parent
assets_path = base_path.parent / 'assets'

# Imágenes específicas para cada jugador
VEHICLE_IMAGES_PLAYER1 = {
    "jeep": str(assets_path / 'jeep1.png'),
    "moto": str(assets_path / 'motorcycle1.png'),
    "camion": str(assets_path / 'truck1.png'),
    "auto": str(assets_path / 'car1.png'),
}

VEHICLE_IMAGES_PLAYER2 = {
    "jeep": str(assets_path / 'jeep2.png'),
    "moto": str(assets_path / 'motorcycle2.png'),
    "camion": str(assets_path / 'truck2.png'),
    "auto": str(assets_path / 'car2.png'),
}

@dataclass
class Vehicle:
    """Clase que representa un vehículo en el simulador.

    Atributos principales:
    - id: identificador único
    - type: 'jeep' | 'moto' | 'camion' | 'auto'
    - color: descripción del color
-    - position: (row, col)
+    - position: (col, row)
    - status: 'idle'|'moving'|'in_base'|'destroyed'|etc
    - capacity: número entero (personas/carga)
    - allowed_load: lista con tipos permitidos ('people','cargo')
    - max_consecutive_trips: cuántos viajes puede realizar sin volver a base
    - must_return_on_cargo: si True, al recoger carga debe volver a base antes de otro viaje
    """
    id: str
    type: str
    color: str
    position: Tuple[int, int] = (0, 0)
    status: str = "in_base"
    capacity: int = 0
    allowed_load: List[str] = field(default_factory=lambda: ["people", "cargo"])
    max_consecutive_trips: int = 1
    must_return_on_cargo: bool = False
    trips_done_since_base: int = 0
    collected_value: int = 0
    # Estado usado por las estrategias: ruta planificada y objetivo actual
    route: List[Tuple[int, int]] = field(default_factory=list)
    target: Optional[object] = None
    # Posición específica en la base (donde sale y debe volver)
    base_position: Optional[Tuple[int, int]] = None
    # Ruta de imagen del vehículo
    img_path: str = ""

    def move_to(self, row: int, col: int):
        self.position = (row, col)
        if self.trips_done_since_base >= self.max_consecutive_trips or self.capacity == 0:
            self.status = "need_return"
        else:
            self.status = "moving"

    def arrive_base(self):
        self.status = "in_base"
        self.trips_done_since_base = 0
        self.collected_value = 0
        # Resetear capacidad según el tipo de vehículo
        vehicle_type = getattr(self, "type", None)
        if vehicle_type == "jeep":
            self.capacity = 4
        elif vehicle_type == "moto":
            self.capacity = 1
        elif vehicle_type == "camion":
            self.capacity = 10
        elif vehicle_type == "auto":
            self.capacity = 4
        else:
            # Fallback: restaurar a un valor por defecto si no se conoce el tipo
            self.capacity = 4

    def start_trip(self):
        self.status = "moving"

    def end_trip(self, picked_up: str | None = None, value: int = 0):
        """Finaliza un viaje; si se recogió algo, actualiza counters y estado.

        picked_up: 'people' | 'cargo' | None
        """
        if picked_up:
            self.trips_done_since_base += 1
            # Si se proporciona un valor (puntos) por lo recogido, lo acumulamos
            if value and value > 0:
                self.collected_value += value
                # Validación: si alcanza o supera la capacidad física del vehículo,
                # forzamos que deba volver a la base y limitamos el valor al máximo.
                if self.collected_value >= self.capacity:
                    self.collected_value = self.capacity
                    self.status = "need_return"
        # Si alcanza el máximo, forzamos volver a base
        if self.trips_done_since_base >= self.max_consecutive_trips:
            self.status = "need_return"
        # Si recogió cargo y debe volver, marcar
        if picked_up == "cargo" and self.must_return_on_cargo:
            self.status = "need_return"

    def can_pick(self, item_type: str) -> bool:
        return item_type in self.allowed_load


    def pick_up(self, item_type: str, value: int = 0) -> bool:
        """
        intenta recoger el recurso:
        - verifica si puede recoger el tipo (people|cargo)
        - incrementa trips_done_since_base (consume un viaje)
        - acumula collected_value según value (si no se pasa, suma 1 como fallback)
        - si alcanza la capacidad física o el número máximo de viajes, marca need_return
        - si recoge cargo y must_return_on_cargo es True, marca need_return
        Devuelve True si la recogida fue posible y realizada, False en caso contrario.
        """
        if not self.can_pick(item_type):
            return False

        # consumir un viaje
        self.trips_done_since_base += 1

        # acumular valor recogido (si no se da 'value', asumimos 1 unidad)
        added = value if isinstance(value, int) and value > 0 else 1
        self.collected_value += added
        self.capacity -= 1

        if self.capacity <= 0:
            self.status = "need_return"

        # no sobrepasar la capacidad física; si se alcanza, forzar regreso
        # if self.capacity is not None and self.collected_value >= self.capacity:
        #     self.collected_value = self.capacity
        #     self.status = "need_return"

        # si se excede el máximo de viajes consecutivos, forzar regreso
        if self.trips_done_since_base >= self.max_consecutive_trips:
            self.status = "need_return"

        # si recogió carga y debe volver en ese caso, marcarlo
        # if item_type == "cargo" and self.must_return_on_cargo:
        #     self.status = "need_return"

        return True

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "color": self.color,
            "position": self.position,
            "status": self.status,
            "capacity": self.capacity,
            "allowed_load": list(self.allowed_load),
            "max_consecutive_trips": self.max_consecutive_trips,
            "must_return_on_cargo": self.must_return_on_cargo,
            "trips_done_since_base": self.trips_done_since_base,
        }

    def remaining_trips(self) -> int:
        """Devuelve cuántos viajes más puede hacer antes de volver a base."""
        return max(0, self.max_consecutive_trips - self.trips_done_since_base)


class VehicleManager:
    """Gestiona la flota de vehículos con múltiples hash tables para búsquedas eficientes.

    Hash tables implementadas:
    - vehicles: Dict[id -> Vehicle] - Búsqueda por ID O(1)
    - vehicles_by_type: Dict[type -> List[Vehicle]] - Búsqueda por tipo O(1)
    - vehicles_by_status: Dict[status -> Set[id]] - Búsqueda por estado O(1)
    
    Todas las hash tables se mantienen sincronizadas automáticamente.
    """
    def __init__(self):
        # Hash table principal: ID -> Vehicle
        self.vehicles: Dict[str, Vehicle] = {}
        
        # Hash table por tipo: type -> [Vehicle IDs]
        self.vehicles_by_type: Dict[str, List[str]] = {
            "jeep": [],
            "moto": [],
            "camion": [],
            "auto": []
        }
        
        # Hash table por estado: status -> {Vehicle IDs}
        self.vehicles_by_status: Dict[str, Set[str]] = {
            "in_base": set(),
            "moving": set(),
            "need_return": set(),
            "destroyed": set()
        }

    def add_vehicle(self, vehicle: Vehicle):
        """Agrega un vehículo y actualiza todas las hash tables - O(1)"""
        self.vehicles[vehicle.id] = vehicle
        
        # Actualizar hash table por tipo
        if vehicle.type in self.vehicles_by_type:
            self.vehicles_by_type[vehicle.type].append(vehicle.id)
        
        # Actualizar hash table por estado
        if vehicle.status in self.vehicles_by_status:
            self.vehicles_by_status[vehicle.status].add(vehicle.id)

    def get_vehicle(self, vehicle_id: str) -> Vehicle | None:
        """Obtiene un vehículo por ID - O(1)"""
        return self.vehicles.get(vehicle_id)

    def remove_vehicle(self, vehicle_id: str):
        """Elimina un vehículo y actualiza todas las hash tables - O(1)"""
        if vehicle_id in self.vehicles:
            vehicle = self.vehicles[vehicle_id]
            
            # Eliminar de hash table principal
            del self.vehicles[vehicle_id]
            
            # Eliminar de hash table por tipo
            if vehicle.type in self.vehicles_by_type:
                try:
                    self.vehicles_by_type[vehicle.type].remove(vehicle.id)
                except ValueError:
                    pass
            
            # Eliminar de hash table por estado
            if vehicle.status in self.vehicles_by_status:
                self.vehicles_by_status[vehicle.status].discard(vehicle.id)
    
    def update_vehicle_status(self, vehicle_id: str, new_status: str) -> bool:
        """Actualiza el estado de un vehículo y sincroniza hash tables - O(1)"""
        vehicle = self.get_vehicle(vehicle_id)
        if not vehicle:
            return False
        
        old_status = vehicle.status
        
        # Eliminar del conjunto de estado antiguo
        if old_status in self.vehicles_by_status:
            self.vehicles_by_status[old_status].discard(vehicle_id)
        
        # Actualizar estado del vehículo
        vehicle.status = new_status
        
        # Agregar al conjunto de nuevo estado
        if new_status not in self.vehicles_by_status:
            self.vehicles_by_status[new_status] = set()
        self.vehicles_by_status[new_status].add(vehicle_id)
        
        return True
    
    def get_vehicles_by_type(self, vehicle_type: str) -> List[Vehicle]:
        """Obtiene todos los vehículos de un tipo específico - O(k) donde k = vehículos de ese tipo"""
        if vehicle_type not in self.vehicles_by_type:
            return []
        
        return [self.vehicles[vid] for vid in self.vehicles_by_type[vehicle_type] if vid in self.vehicles]
    
    def get_vehicles_by_status(self, status: str) -> List[Vehicle]:
        """Obtiene todos los vehículos con un estado específico - O(k) donde k = vehículos en ese estado"""
        if status not in self.vehicles_by_status:
            return []
        
        return [self.vehicles[vid] for vid in self.vehicles_by_status[status] if vid in self.vehicles]
    
    def get_available_vehicles(self) -> List[Vehicle]:
        """Obtiene vehículos disponibles (no destruidos, no necesitan volver urgente) - O(k)"""
        available = []
        for status in ["in_base", "moving"]:
            if status in self.vehicles_by_status:
                for vid in self.vehicles_by_status[status]:
                    vehicle = self.vehicles.get(vid)
                    if vehicle and vehicle.capacity > 0:
                        available.append(vehicle)
        return available
    
    def get_vehicles_needing_return(self) -> List[Vehicle]:
        """Obtiene vehículos que necesitan regresar a base - O(k)"""
        return self.get_vehicles_by_status("need_return")
    
    def get_destroyed_vehicles(self) -> List[Vehicle]:
        """Obtiene vehículos destruidos - O(k)"""
        return self.get_vehicles_by_status("destroyed")
    
    def count_by_type(self, vehicle_type: str) -> int:
        """Cuenta vehículos de un tipo específico - O(1)"""
        return len(self.vehicles_by_type.get(vehicle_type, []))
    
    def count_by_status(self, status: str) -> int:
        """Cuenta vehículos en un estado específico - O(1)"""
        return len(self.vehicles_by_status.get(status, set()))

    def create_default_fleet(self, player_num=1):
        """Crea la flota según las especificaciones del proyecto:

        - 3 Jeeps: todo tipo de carga, hasta 2 viajes sin volver
        - 2 Motos: solo personas, deben volver tras recoger persona
        - 2 Camiones: todo tipo de carga, hasta 3 viajes sin volver
        - 3 Autos: personas y cargas; si recogen carga deben volver a base
        
        :param player_num: 1 para Jugador_1 (usa imágenes *1.png), 2 para Jugador_2 (usa imágenes *2.png)
        """
        # Seleccionar el conjunto de imágenes según el jugador
        vehicle_images = VEHICLE_IMAGES_PLAYER1 if player_num == 1 else VEHICLE_IMAGES_PLAYER2
        
        # 3 Jeeps
        for i in range(1, 4):
            v = Vehicle(
                id=f"jeep_{i}",
                type="jeep",
                color= JEEP_COLOR,
                capacity=4,
                allowed_load=["people", "cargo"],
                max_consecutive_trips=2,
                must_return_on_cargo=False,
                img_path=vehicle_images["jeep"],
            )
            self.add_vehicle(v)

        # 2 Motos
        for i in range(1, 3):
            v = Vehicle(
                id=f"moto_{i}",
                type="moto",
                color= MOTORCYCLE_COLOR,
                capacity=1,
                allowed_load=["people"],
                max_consecutive_trips=1,
                must_return_on_cargo=True,  # irrelevant pero mantener coherencia
                img_path=vehicle_images["moto"],
            )
            self.add_vehicle(v)

        # 2 Camiones
        for i in range(1, 3):
            v = Vehicle(
                id=f"camion_{i}",
                type="camion",
                color= TRUCK_COLOR,
                capacity=10,
                allowed_load=["people", "cargo"],
                max_consecutive_trips=3,
                must_return_on_cargo=False,
                img_path=vehicle_images["camion"],
            )
            self.add_vehicle(v)

        # 3 Autos
        for i in range(1, 4):
            v = Vehicle(
                id=f"auto_{i}",
                type="auto",
                color= CAR_COLOR,
                capacity=4,
                allowed_load=["people", "cargo"],
                max_consecutive_trips=1,
                must_return_on_cargo=True,
                img_path=vehicle_images["auto"],
            )
            self.add_vehicle(v)

    def all_vehicles(self) -> Dict[str, Vehicle]:
        return dict(self.vehicles)