# ...existing code...
class NearestResourceStrategy:
    """
    Estrategia: cada vehículo busca el recurso más cercano (BFS) desde su posición actual,
    sigue la ruta paso a paso (guardada en v.route) y al recoger marca need_return si corresponde.
    Usa map.graph.place_vehicle o map.place_vehicle cuando esté disponible.
    """

    def __init__(self, map_width, map_height, map):
        self.map_width = map_width
        self.map_height = map_height
        self.map = map

    def bfs(self, start, goal):
        if start == goal:
            return [start]
        rows = getattr(self.map, "rows", None)
        cols = getattr(self.map, "cols", None)
        # si no hay rows/cols no podemos hacer BFS
        if rows is None or cols is None:
            return None

        from collections import deque
        q = deque([start])
        visited = {start: None}

        while q:
            r, c = q.popleft()
            for nr, nc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                if 0 <= nr < rows and 0 <= nc < cols and (nr,nc) not in visited:
                    visited[(nr,nc)] = (r,c)
                    if (nr,nc) == goal:
                        path = [(nr,nc)]
                        while path[-1] != start:
                            path.append(visited[path[-1]])
                        path.reverse()
                        return path
                    q.append((nr,nc))
        return None

    def hola(self):
        print("hola")

    def encontrar_recurso_mas_cercano(self, vehiculo, recursos):
        mejor = None
        mejor_ruta = None
        for recurso in recursos:
            pos = getattr(recurso, "position", None)
            if pos is None:
                continue
            ruta = self.bfs(vehiculo.position, pos)
            if ruta:
                if mejor_ruta is None or len(ruta) < len(mejor_ruta):
                    mejor = recurso
                    mejor_ruta = ruta
        return mejor, mejor_ruta

    def mover_por_ruta(self, vehiculo):
        if not hasattr(vehiculo, "route") or not vehiculo.route:
            return
        next_pos = vehiculo.route.pop(0)
        nr, nc = next_pos
        placed = False
        try:
            if hasattr(self.map, "graph") and callable(getattr(self.map.graph, "place_vehicle", None)):
                placed = self.map.graph.place_vehicle(vehiculo, nr, nc)
            elif callable(getattr(self.map, "place_vehicle", None)):
                placed = self.map.place_vehicle(vehiculo, nr, nc)
        except Exception:
            placed = False

        if not placed:
            if hasattr(vehiculo, "move_to"):
                vehiculo.move_to(nr, nc)
            else:
                vehiculo.position = (nr, nc)

    def update(self, player, resources, vehicle_id=None):
        """
        Actualiza todos los vehículos del player por defecto.
        Si se pasa vehicle_id (string o objeto Vehicle), solo procesa ese vehículo (modo prueba).
        """
        # Normalizar selección de vehículos: si se pide uno solo, buscarlo; si no, usar todos.
        vehicles_iterable = []
        if vehicle_id is None:
            vehicles_iterable = (player.vehicles.values() if hasattr(player.vehicles, "values") else [])
        else:
            # si pasaron un objeto vehicle directamente
            if not isinstance(vehicle_id, str):
                vehicles_iterable = [vehicle_id]
            else:
                target = None
                if hasattr(player, "vehicles"):
                    try:
                        target = player.vehicles.get(vehicle_id)
                    except Exception:
                        target = None
                if target is None:
                    for vv in (player.vehicles.values() if hasattr(player.vehicles, "values") else []):
                        if getattr(vv, "id", None) == vehicle_id or (isinstance(vv, dict) and vv.get("id") == vehicle_id):
                            target = vv
                            break
                if target is None:
                    # no se encontró el vehículo pedido -> nada que hacer
                    return
                vehicles_iterable = [target]

        print("RECURSOS", resources)

        base = getattr(player, "base_position", None)

        for v in vehicles_iterable:
            if getattr(v, "status", None) == "destroyed":
                continue

            # Si debe volver a base, asegurar ruta y moverse
            if getattr(v, "status", None) in ("need_return", "returning"):
                if base is None:
                    continue
                if not hasattr(v, "route") or not v.route:
                    v.route = self.bfs(v.position, base) or []
                    # quitar primer paso si es la misma posición
                    if v.route and v.route[0] == v.position:
                        v.route = v.route[1:]
                if v.position == base:
                    # llegada a base: transferir score si aplica y reset vehículo
                    collected = getattr(v, "collected_value", 0)
                    if collected and hasattr(player, "score"):
                        player.score = getattr(player, "score", 0) + collected
                    v.arrive_base() if hasattr(v, "arrive_base") else setattr(v, "status", "in_base")
                    v.route = []
                else:
                    self.mover_por_ruta(v)
                continue

            # Si no tiene ruta, asignar ruta hacia recurso más cercano
            if not hasattr(v, "route") or not v.route:
                recurso, ruta = self.encontrar_recurso_mas_cercano(v, resources)
                if recurso and ruta:
                    # eliminar primer paso si es la posición actual
                    if ruta and ruta[0] == v.position:
                        ruta = ruta[1:]
                    v.route = ruta or []
                    v.target = recurso
                    v.status = "moving"

            # mover un paso
            self.mover_por_ruta(v)

            # si llegó al recurso, recogerlo
            if hasattr(v, "target") and v.target in (resources if isinstance(resources, list) else list(resources)):
                recurso = v.target
                if v.position == getattr(recurso, "position", None):
                    # intentar recoger: usar atributos del recurso si existen
                    item_type = getattr(recurso, "type", "people")
                    value = getattr(recurso, "value", 1)
                    picked = False
                    if hasattr(v, "pick_up"):
                        picked = v.pick_up(item_type, value)
                    else:
                        # fallback simple
                        v.capacity = max(0, getattr(v, "capacity", 0) - 1)
                        picked = True

                    # eliminar del contenedor original si es posible
                    try:
                        if resources is not None:
                            # si es lista o set o similar
                            if isinstance(resources, list) or isinstance(resources, set):
                                resources.remove(recurso)
                            elif isinstance(resources, dict):
                                # buscar clave por valor
                                keys = [k for k, val in resources.items() if val is recurso or val == recurso]
                                for k in keys:
                                    del resources[k]
                        else:
                            # sin contenedor conocido, intentar eliminar de player.resources si existe
                            if hasattr(player, "resources") and recurso in player.resources:
                                player.resources.remove(recurso)
                    except Exception:
                        pass

                    v.target = None
                    v.route = []
                    # si quedó sin capacidad o pick_up marcó need_return, preparar ruta a base
                    if getattr(v, "capacity", 1) <= 0 or getattr(v, "status", None) in ("need_return",):
                        if base is not None:
                            v.route = self.bfs(v.position, base) or []
