from typing import List, Tuple, Dict
from collections import deque

# Tipos esperados para los parámetros
# vehicle: objeto con atributos como position, type, status, allowed_load, etc.
# map_graph: grafo del mapa con nodos y vecinos
# resources: lista de objetos con tipo, puntos, position
# enemy_vehicles: lista de vehículos enemigos con type, position, status
# mine_manager: objeto con método isCellMined(cell, tick)

def bfs_path(start: Tuple[int, int], goal: Tuple[int, int], map_graph, mine_manager=None, tick=0) -> List[Tuple[int, int]]:
    """Busca el camino más corto entre start y goal evitando minas si se especifica."""
    if start == goal:
        return []

    queue = deque()
    queue.append((start, [start]))
    visited = set([start])

    while queue:
        current, path = queue.popleft()
        if current == goal:
            return path[1:]  # Excluir la posición actual

        node = map_graph.get_node(*current)
        if node is None:
            continue

        neighbors = node.neighbors  # lista de Node
        for neighbor_node in neighbors:
            neighbor = (neighbor_node.row, neighbor_node.col)
            if neighbor in visited:
                continue
            if mine_manager and getattr(mine_manager, "isCellMined", None):
                try:
                    if mine_manager.isCellMined(neighbor, tick):
                        continue
                except Exception:
                    pass
            visited.add(neighbor)
            queue.append((neighbor, path + [neighbor]))

    return []  # No se encontró camino

def strategy_moto(vehicle, map_graph, resources, enemy_vehicles, mine_manager=None, tick=0):
    """Las motos buscan camiones enemigos y se mueven hacia ellos para provocar colisión."""
    if getattr(vehicle, "status", None) == "destroyed":
        return None

    camiones_enemigos = [
        v for v in (enemy_vehicles or [])
        if getattr(v, "type", None) == "camion" and getattr(v, "status", None) not in ["destroyed", "in_base"]
    ]

    if not camiones_enemigos:
        return None  # No hay objetivos

    # Buscar el camión más cercano
    mejor_camino = []
    for enemigo in camiones_enemigos:
        camino = bfs_path(vehicle.position, enemigo.position, map_graph, mine_manager, tick)
        if camino and (not mejor_camino or len(camino) < len(mejor_camino)):
            mejor_camino = camino

    if mejor_camino:
        return mejor_camino[0]  # Siguiente paso (row, col)
    return None

def strategy_greedy(vehicle, map_graph, resources, enemy_vehicles, mine_manager=None, tick=0):
    """Estrategia greedy por valor para jeeps, autos y camiones."""
    if getattr(vehicle, "status", None) == "destroyed":
        return None

    # Normalizar allowed_load (lista de tipos aceptables)
    allowed_raw = getattr(vehicle, "allowed_load", []) or []
    try:
        allowed_norm = [str(x).lower().strip() for x in allowed_raw]
    except Exception:
        allowed_norm = []

    # Filtrar recursos admitidos (soporta dicts y objetos)
    recursos_validos = []
    for r in (resources or []):
        tipo = None
        if isinstance(r, dict):
            tipo = r.get("tipo") or r.get("type")
        else:
            tipo = getattr(r, "tipo", None) or getattr(r, "type", None)
        if tipo is None:
            continue
        if str(tipo).lower().strip() in allowed_norm:
            recursos_validos.append(r)

    if not recursos_validos:
        return None

    # Función para obtener el "valor" de un recurso (puntos)
    def puntos_of(r):
        if isinstance(r, dict):
            return r.get("puntos") or r.get("points") or r.get("value") or 0
        return getattr(r, "puntos", getattr(r, "points", getattr(r, "value", 0)))

    recursos_ordenados = sorted(recursos_validos, key=puntos_of, reverse=True)

    mejor_camino = []
    # Obtener posición inicial del vehículo (validar)
    start = getattr(vehicle, "position", None) or (getattr(vehicle, "row", None), getattr(vehicle, "col", None))
    if not start or None in (start if isinstance(start, (list, tuple)) else (None,)):
        return None

    # Buscar el recurso objetivo con camino más corto (entre los ordenados por valor)
    for recurso in recursos_ordenados:
        # Obtener posición objetivo de forma robusta
        objetivo = None
        if isinstance(recurso, dict):
            objetivo = recurso.get("position") or recurso.get("pos") or recurso.get("coord")
        else:
            objetivo = getattr(recurso, "position", None) or getattr(recurso, "pos", None)

        if not objetivo:
            continue

        # Normalizar a tupla (row, col)
        if isinstance(objetivo, dict):
            objetivo = (objetivo.get("row"), objetivo.get("col"))
        if isinstance(objetivo, list):
            objetivo = tuple(objetivo)

        if not (isinstance(objetivo, tuple) and len(objetivo) == 2):
            continue

        try:
            camino = bfs_path(tuple(start), tuple(objetivo), map_graph, mine_manager, tick)
        except Exception:
            camino = []

        if camino and (not mejor_camino or len(camino) < len(mejor_camino)):
            mejor_camino = camino

    if mejor_camino:
        # devolver el siguiente paso (row, col)
        return mejor_camino[0]
    return None

# Alias por tipo de vehículo
def strategy_jeep(vehicle, map_graph, resources, enemy_vehicles, mine_manager=None, tick=0):
    return strategy_greedy(vehicle, map_graph, resources, enemy_vehicles, mine_manager, tick)

def strategy_camion(vehicle, map_graph, resources, enemy_vehicles, mine_manager=None, tick=0):
    return strategy_greedy(vehicle, map_graph, resources, enemy_vehicles, mine_manager, tick)

def strategy_auto(vehicle, map_graph, resources, enemy_vehicles, mine_manager=None, tick=0):
    return strategy_greedy(vehicle, map_graph, resources, enemy_vehicles, mine_manager, tick)

class NearestResourceStrategy:
    """
    Estrategia que puede ser instanciada desde GameEngine:
      NearestResourceStrategy(map_width, map_height, map_graph)
    y expone update(player, resources), que GameEngine llama en cada tick.
    """

    def __init__(self, map_cols, map_rows, map_graph):
        self.map_cols = map_cols
        self.map_rows = map_rows
        self.map_graph = map_graph
        # Si el map_graph tiene mine_manager lo usamos
        self.mine_manager = getattr(map_graph, "mine_manager", None)
        # tick no lo manejamos aquí; GameEngine puede actualizar mines y pasar estado en el map

    def update(self, player, resources):
        """
        Mueve cada vehículo del player un paso hacia su objetivo y usa
        map_graph.place_vehicle para colocar (y permitir recolección mediante los métodos del vehículo).
        """

        if player is None:
            return

        vehicles = getattr(player, "vehicles", None) or getattr(player, "fleet", None) or []
        if vehicles is None:
            vehicles = []

        # Normalizar a lista de objetos Vehicle.
        # player.vehicles puede ser:
        # - dict {id: Vehicle}  -> iterar valores
        # - dict {id: id_str}   -> intentar player.get_vehicle(id_str)
        # - iterable de objetos o ids
        normalized = []
        # caso dict (Player.VehicleManager.all_vehicles() devuelve dict)
        if isinstance(vehicles, dict):
            for k, v in vehicles.items():
                if isinstance(v, str):
                    obj = getattr(player, "get_vehicle", lambda vid: None)(v)
                    if obj:
                        normalized.append(obj)
                else:
                    normalized.append(v)
        else:
            try:
                for item in vehicles:
                    if isinstance(item, str):
                        obj = getattr(player, "get_vehicle", lambda vid: None)(item)
                        if obj:
                            normalized.append(obj)
                        else:
                            # si no encontramos, no añadir el id suelto
                            continue
                    else:
                        normalized.append(item)
            except TypeError:
                # no iterable -> ignorar
                normalized = []

        vehicles = normalized

        # determinar base del jugador (si existe) para estados 'need_return'
        base_pos = getattr(player, "base_position", None)

        print(base_pos)

        for vehicle in vehicles:

            #print("vehicle", vehicle)
            print("vehicle", vehicle.type)
            try:
                # Ignorar vehículos destruidos o en base
                status = getattr(vehicle, "status", None)
                if status in ["destroyed"]:
                    continue

                # Selección de estrategia según tipo
                #vtype = getattr(vehicle, "type", "")
                vtype = vehicle.type
                print("vtype", vtype)      

                next_cell = None
                if vtype == "moto":
                    next_cell = strategy_moto(vehicle, self.map_graph, resources, [], self.mine_manager, 0)
                elif vtype in ("jeep", "auto", "camion", "truck"):
                    next_cell = strategy_greedy(vehicle, self.map_graph, resources, [], self.mine_manager, 0)
                else:
                    # por defecto usar greedy
                    next_cell = strategy_greedy(vehicle, self.map_graph, resources, [], self.mine_manager, 0)

                # Si el vehículo necesita volver a base, dirigirlo a la base
                if getattr(vehicle, "status", None) == "need_return" and base_pos:
                    camino = bfs_path(getattr(vehicle, "position"), base_pos, self.map_graph, self.mine_manager, 0)
                    if camino:
                        next_cell = camino[0]

                print("nextCell", next_cell)

                # Normalizar next_cell y asegurarnos de tener una tupla (r,c)
                tgt = None
                if isinstance(next_cell, tuple) and len(next_cell) == 2:
                    tgt = next_cell
                elif isinstance(next_cell, list) and len(next_cell) > 0:
                    # puede ser una lista de pasos -> tomar el primer paso si es (r,c)
                    first = next_cell[0]
                    if isinstance(first, (tuple, list)) and len(first) == 2:
                        tgt = tuple(first)

                if not tgt:
                    print(f"[strategy] next_cell inválido/no objetivo: {next_cell}")
                else:
                    r, c = tgt
                    try:
                        placed = False
                        place_owner = None
                        mgr = self.map_graph  # MapManager (según tu comentario)
                        # Priorizar MapManager.graph (MapGraph) que contiene place_vehicle
                        graph_obj = getattr(mgr, "graph", None)
                        if graph_obj is not None and callable(getattr(graph_obj, "place_vehicle", None)):
                            # invertir (row, col) -> (col, row) al llamar a MapGraph.place_vehicle
                            placed = graph_obj.place_vehicle(vehicle, c, r)
                            place_owner = graph_obj
                        elif callable(getattr(mgr, "place_vehicle", None)):
                            placed = mgr.place_vehicle(vehicle, c, r)
                            place_owner = mgr

                        print(f"[strategy] try place vehicle id={getattr(vehicle,'id',None)} type={getattr(vehicle,'type',None)} pos={getattr(vehicle,'position',None)} -> target=({r},{c}) placed={placed} owner={type(place_owner).__name__ if place_owner else None}")

                        # Fallback: set_node_state si place_vehicle no existe o devolvió False
                        if not placed:
                            owner = place_owner or graph_obj or mgr
                            set_node = getattr(owner, "set_node_state", None)
                            if callable(set_node):
                                try:
                                    # invertir (row, col) -> (col, row) para set_node_state también
                                    set_node(c, r, "vehicle", {"object": vehicle, "id": getattr(vehicle, "id", None), "type": getattr(vehicle, "type", None), "position": (c, r)})
                                    try:
                                        vehicle.position = (c, r)
                                    except Exception:
                                        if isinstance(vehicle, dict):
                                            vehicle["position"] = (c, r)
                                    print(f"[strategy] fallback: node set at ({r},{c})")
                                    placed = True
                                except Exception as e:
                                    print(f"[strategy] fallback failed: {e}")
                            else:
                                print("[strategy] no place_vehicle ni set_node_state disponibles para dibujar vehículo")
                    except Exception as e:
                        print("[strategy] excepción al intentar colocar vehículo:", e)
            except Exception:
                # proteger la estrategia ante errores en un vehículo concreto
                continue