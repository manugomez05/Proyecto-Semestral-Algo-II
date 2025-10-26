from dataclasses import dataclass, field
from typing import Tuple, List, Dict

##Falta agregar el atributo collected_value que cada vez que se recoge una carga, suma los puntos

TRUCK_COLOR = (30, 144, 255)
JEEP_COLOR = (34, 139, 34)
CAR_COLOR = (240, 240, 240)
MOTORCYCLE_COLOR = (255, 140, 0)

@dataclass
class Vehicle:
    """Clase que representa un vehículo en el simulador.

    Atributos principales:
    - id: identificador único
    - type: 'jeep' | 'moto' | 'camion' | 'auto'
    - color: descripción del color
    - position: (row, col)
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

    def move_to(self, row: int, col: int):
        self.position = (row, col)
        self.status = "moving"

    def arrive_base(self):
        self.status = "in_base"
        self.trips_done_since_base = 0
        self.collected_value = 0

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


class VehicleManager:
    """Gestiona la flota de vehículos y los almacena en una hash table (dict).

    La hash table usa el id del vehículo como clave y el objeto Vehicle como valor.
    Se provee un método para crear la flota base según las especificaciones del proyecto.
    """
    def __init__(self):
        self.vehicles: Dict[str, Vehicle] = {}

    def add_vehicle(self, vehicle: Vehicle):
        self.vehicles[vehicle.id] = vehicle

    def get_vehicle(self, vehicle_id: str) -> Vehicle | None:
        return self.vehicles.get(vehicle_id)

    def remove_vehicle(self, vehicle_id: str):
        if vehicle_id in self.vehicles:
            del self.vehicles[vehicle_id]

    def create_default_fleet(self):
        """Crea la flota según las especificaciones del proyecto:

        - 3 Jeeps: todo tipo de carga, hasta 2 viajes sin volver
        - 2 Motos: solo personas, deben volver tras recoger persona
        - 2 Camiones: todo tipo de carga, hasta 3 viajes sin volver
        - 3 Autos: personas y cargas; si recogen carga deben volver a base
        """
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
            )
            self.add_vehicle(v)

    def all_vehicles(self) -> Dict[str, Vehicle]:
        return dict(self.vehicles)

    def check_vehicle_collision(self) -> List[Tuple[str, str]]:
        collisions = [] #Lista que guarda las colisiones
        active_vehicles = {
            vehicle_id: vehicle for vehicle_id, vehicle in self.vehicles.items()
            if vehicle.status not in ["in_base", "destroyed"]
        }

        checked_pairs = set()

        for vehicle_id_1, vehicle_1 in active_vehicles.items():
            for vehicle_id_2, vehicle_2 in active_vehicles.items():
                if vehicle_id_1 == vehicle_id_2:
                    continue  # No comparar un vehículo consigo mismo
                pair = tuple(sorted([vehicle_id_1, vehicle_id_2]))
                if pair in checked_pairs:
                    continue # Ya revisamos este par
                if vehicle_1.position == vehicle_2.position:
                    # Colisión detectada
                    vehicle_1.status = "destroyed"
                    vehicle_2.status = "destroyed"
                    vehicle_1.collected_value = 0
                    vehicle_2.collected_value = 0
                    collisions.append(pair)
                    checked_pairs.add(pair)
        return collisions


# from src.vehicle import VehicleManager

# vm = VehicleManager()
# vm.create_default_fleet()

# # Mostrar ids
# print(list(vm.vehicles.keys()))
# # Obtener un vehículo y ver sus datos
# v = vm.get_vehicle('jeep_1')
# print(v.to_dict())

# # Simular que recoge una persona y finaliza el viaje
# v.start_trip()
# v.end_trip(picked_up='people')
# print(v.status, v.trips_done_since_base)

# # Si necesita volver, llamar:
# if v.status == 'need_return':
#     v.arrive_base()
#     print('Volvió a base:', v.status, v.trips_done_since_base)