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

    # Convenciones:
    # Externo (lo que proveen Vehicle / Resource / Player): (row, col)
    # Interno (usado por la estrategia y BFS): (col, row) == (x, y)

    def hola(self):
        print("hola")


    
    def _to_internal(self, pos):
        """Normaliza cualquier representación externa a la convención interna (col,row).
        Acepta tuplas (row,col), objetos con .position/.row/.col/.x/.y o iterables."""
        if pos is None:
            return None
        # si ya es tupla/lista: asumimos (row,col) externo -> devolver (col,row)
        if isinstance(pos, (tuple, list)):
            if len(pos) >= 2:
                try:
                    r, c = int(pos[0]), int(pos[1])
                    return (c, r)
                except Exception:
                    return None
            return None
        # objetos que contienen .position
        p = getattr(pos, "position", None)
        if p is not None:
            return self._to_internal(p)
        # atributos comunes
        if hasattr(pos, "row") and hasattr(pos, "col"):
            try:
                return (int(getattr(pos, "col")), int(getattr(pos, "row")))
            except Exception:
                return None
        if hasattr(pos, "x") and hasattr(pos, "y"):
            try:
                return (int(getattr(pos, "x")), int(getattr(pos, "y")))
            except Exception:
                return None
        # último recurso: intentar iterar sobre el objeto
        try:
            it = tuple(pos)
            if len(it) >= 2:
                return self._to_internal(it)
        except Exception:
            pass
        return None

    def _to_move_args(self, internal_pos):
        """Convierte posición interna (col,row) -> (row,col) para move/place APIs."""
        if internal_pos is None:
            return None, None
        x, y = internal_pos
        return y, x

    def bfs(self, start, goal):
        # BFS robusta: siempre trabaja con tuplas internas (col,row).
        def coerce_pos(p):
            if p is None:
                return None
            # Si ya es tupla/lista, asumimos (row,col) externo -> convertimos a (col,row)
            if isinstance(p, (tuple, list)):
                if len(p) >= 2:
                    r, c = int(p[0]), int(p[1])
                    return (c, r)
                return None
            # objetos con atributo position (frecuente en Resource/Tile)
            pos = getattr(p, "position", None)
            if pos is not None:
                return coerce_pos(pos)
            # atributos comunes
            if hasattr(p, "row") and hasattr(p, "col"):
                return (int(getattr(p, "col")), int(getattr(p, "row")))
            if hasattr(p, "x") and hasattr(p, "y"):
                # x=col, y=row
                return (int(getattr(p, "x")), int(getattr(p, "y")))
            # fallback: intentar iterar
            try:
                it = tuple(p)
                if len(it) >= 2:
                    return coerce_pos(it)
            except Exception:
                pass
            return None

        s = coerce_pos(start)
        g = coerce_pos(goal)
        if s is None or g is None:
            return None
        if s == g:
            return [s]

        width = getattr(self.map, "cols", None) or self.map_width
        height = getattr(self.map, "rows", None) or self.map_height
        if width is None or height is None:
            return None

        from collections import deque
        q = deque([s])
        visited = {s: None}

        while q:
            cur = q.popleft()
            # asegurar que cur es una tupla (col,row)
            if not isinstance(cur, tuple):
                cur = coerce_pos(cur)
                if cur is None:
                    continue
            x, y = cur
            for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                    visited[(nx, ny)] = (x, y)
                    if (nx, ny) == g:
                        path = [(nx, ny)]
                        while path[-1] != s:
                            path.append(visited[path[-1]])
                        path.reverse()
                        return path
                    q.append((nx, ny))
        return None

    def ensure_vehicle_state(self, v):
        """
        Inicializa atributos mínimos del vehículo para evitar AttributeError y comportamientos
        aleatorios: route, target, collected_value, status y capacity.
        """
        if not hasattr(v, "route") or v.route is None:
            v.route = []
        if not hasattr(v, "target"):
            v.target = None
        if not hasattr(v, "collected_value"):
            v.collected_value = 0
        if getattr(v, "capacity", None) is None:
            # asumir una capacidad por defecto (ajustar si tu modelo usa otro)
            v.capacity = 1
        if not hasattr(v, "status") or getattr(v, "status", None) is None:
            v.status = "idle"

    def encontrar_recurso_mas_cercano(self, vehiculo, recursos):
        mejor = None
        mejor_ruta = None
        start = self._to_internal(getattr(vehiculo, "position", None))
        for recurso in recursos:
            pos = getattr(recurso, "position", None)
            if pos is None:
                continue
            goal = self._to_internal(pos)
            ruta = self.bfs(start, goal)
            if ruta:
                if mejor_ruta is None or len(ruta) < len(mejor_ruta):
                    mejor = recurso
                    mejor_ruta = ruta
        return mejor, mejor_ruta

    def mover_por_ruta(self, vehiculo):
        if not hasattr(vehiculo, "route") or not vehiculo.route:
            return
        # eliminar prefijos iguales a la posición actual para evitar quedarse quieto
        try:
            cur = self._to_internal(getattr(vehiculo, "position", None))
        except Exception:
            cur = None
        while vehiculo.route and cur is not None and vehiculo.route[0] == cur:
            vehiculo.route.pop(0)
        if not vehiculo.route:
            return
        nx, ny = vehiculo.route.pop(0)  # internos (col,row)
        placed = False
        try:
            # Las APIs de movimiento/colocación esperan (row,col): convertimos
            r, c = self._to_move_args((nx, ny))
            if hasattr(self.map, "graph") and callable(getattr(self.map.graph, "place_vehicle", None)):
                placed = self.map.graph.place_vehicle(vehiculo, r, c)
            elif callable(getattr(self.map, "place_vehicle", None)):
                placed = self.map.place_vehicle(vehiculo, r, c)
        except Exception:
            placed = False

        if not placed:
            # fallback: actualizar la posición externa (row,col)
            r, c = self._to_move_args((nx, ny))
            if hasattr(vehiculo, "move_to"):
                try:
                    vehiculo.move_to(r, c)
                except Exception:
                    vehiculo.position = (r, c)
            else:
                vehiculo.position = (r, c)
            print(f"DEBUG mover_por_ruta: fallback moved vehicle {getattr(vehiculo,'id',None)} -> {(r,c)}")

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

        #print("RECURSOS", resources)

        base = getattr(player, "base_position", None)
        base_internal = self._to_internal(base) if base is not None else None

        for v in vehicles_iterable:
            if getattr(v, "status", None) == "destroyed":
                continue

            # asegurar estado mínimo del vehículo para evitar atributos faltantes
            self.ensure_vehicle_state(v)

            # Si debe volver a base, asegurar ruta y moverse
            if getattr(v, "status", None) in ("need_return", "returning"):
                if base is None:
                    continue
                if not hasattr(v, "route") or not v.route:
                    v.route = self.bfs(self._to_internal(v.position), base_internal) or []
                    # quitar primer paso si es la misma posición (interno)
                    if v.route and v.route[0] == self._to_internal(v.position):
                        v.route = v.route[1:]
                if self._to_internal(v.position) == base_internal:
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
                    if ruta and ruta[0] == self._to_internal(v.position):
                        ruta = ruta[1:]
                    v.route = ruta or []
                    v.target = recurso
                    print("target", recurso)
                    print("ruta", ruta)
                    v.status = "moving"

            # mover un paso
            self.mover_por_ruta(v)

            # si llegó al recurso, recogerlo
            if getattr(v, "target", None) is not None and v.target in (resources if isinstance(resources, list) else list(resources)):
                recurso = v.target
                if self._to_internal(v.position) == self._to_internal(getattr(recurso, "position", None)):
                    # intentar recoger: usar atributos del recurso si existen
                    item_type = getattr(recurso, "type", "people")
                    value = getattr(recurso, "value", 1)
                    picked = False
                    if hasattr(v, "pick_up"):
                        try:
                            picked = v.pick_up(item_type, value)
                        except Exception:
                            picked = False
                    else:
                        # fallback simple
                        v.capacity = max(0, getattr(v, "capacity", 0) - 1)
                        picked = True

                    # actualizar collected_value si recogió
                    if picked:
                        v.collected_value = getattr(v, "collected_value", 0) + value

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

                    # limpiar objetivo/route y preparar retorno si corresponde
                    v.target = None
                    v.route = []
                    if getattr(v, "capacity", 1) <= 0 or getattr(v, "status", None) in ("need_return"):
                        if base_internal is not None:
                            v.route = self.bfs(self._to_internal(v.position), base_internal) or []
                            v.status = "need_return"
                    else:
                        # si aún puede cargar, seguir buscando
                        v.status = "idle"
