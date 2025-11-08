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

    def ensure_vehicle_state(self, v):
        """
        Inicializa atributos/estado mínimos en el vehículo para evitar AttributeError
        y comportamientos aleatorios: route, target, collected_value, status y capacity.
        """
        if not hasattr(v, "route") or v.route is None:
            v.route = []
        if not hasattr(v, "target"):
            v.target = None
        if not hasattr(v, "collected_value"):
            v.collected_value = 0
        # si no hay capacity definido, damos 1 como valor por defecto (ajustable)
        if getattr(v, "capacity", None) is None:
            v.capacity = 1
        if not hasattr(v, "status") or getattr(v, "status", None) is None:
            v.status = "idle"

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
        # eliminar pasos redundantes que son la posición actual
        if not hasattr(vehiculo, "route") or not vehiculo.route:
            return
        # descartar prefijos iguales a la posición actual
        try:
            cur = getattr(vehiculo, "position", None)
        except Exception:
            cur = None
        while vehiculo.route and cur is not None and vehiculo.route[0] == cur:
            vehiculo.route.pop(0)
        if not vehiculo.route:
            return

        nr, nc = vehiculo.route.pop(0)
        placed = False
        try:
            if hasattr(self.map, "graph") and callable(getattr(self.map.graph, "place_vehicle", None)):
                placed = self.map.graph.place_vehicle(vehiculo, nr, nc)
            elif callable(getattr(self.map, "place_vehicle", None)):
                placed = self.map.place_vehicle(vehiculo, nr, nc)
        except Exception:
            placed = False

        if not placed:
            # fallback que actualiza la posición local y marca movimiento
            if hasattr(vehiculo, "move_to"):
                vehiculo.move_to(nr, nc)
            else:
                vehiculo.position = (nr, nc)
            # opcional: registrar para debug si place_vehicle falla frecuentemente
            print(f"DEBUG: place_vehicle falló para {getattr(vehiculo,'id',None)} -> {(nr,nc)}")

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

            # asegurar estado mínimo del vehículo para evitar atributos faltantes
            self.ensure_vehicle_state(v)

            # obtener posición actual de forma segura (usada en cálculo de desplazamientos)
            try:
                row, col = v.position
            except Exception:
                # si no tiene posición, saltar este vehículo
                continue

            # Si el vehículo está marcado para volver y no tiene ruta, crearla (evita bloque muerto)
            if getattr(v, "status", None) == "need_return" and (not hasattr(v, "route") or not v.route):
                if base is not None:
                    v.route = self.bfs(v.position, base) or []
                    # marcar como returning para que el bloque de movimiento lo procese correctamente
                    v.status = "returning"

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
                        try:
                            picked = v.pick_up(item_type, value)
                        except Exception:
                            picked = False
                    else:
                        # fallback simple: decrementar capacidad si existe
                        cap = getattr(v, "capacity", None)
                        if cap is None:
                            # si no existe capacity, asumir que puede recoger y acumular collected_value
                            picked = True
                        else:
                            v.capacity = max(0, cap - 1)
                            picked = True

                    # si logró recoger, actualizar collected_value y preparar retorno si corresponde
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

                        # si quedó sin capacidad o el vehículo decidió que debe volver, crear ruta a base
                        if getattr(v, "capacity", 1) <= 0 or getattr(v, "status", None) in ("need_return",):
                            if base is not None:
                                v.route = self.bfs(v.position, base) or []
                                v.status = "returning"
                        else:
                            # limpiamos target/route para seguir buscando si queda capacidad
                            v.target = None
                            v.route = []
                    else:
                        # no pudo recoger: limpiar target para intentar otro recurso
                        v.target = None

            # Si debe volver a base o está en retorno, mover paso a paso (bloque principal de retorno)
            if getattr(v, "status", None) in ("need_return", "returning"):
                # obtener posición actual del vehículo (seguro)
                try:
                    row, col = v.position
                except Exception:
                    continue

                # obtener posición de la base (fallback a (0,0) si no disponible)
                target = base if base is not None else (0, 0)
                target_row, target_col = target

                # si no hay ruta activa, crearla
                if not hasattr(v, "route") or not v.route:
                    v.route = self.bfs(v.position, target) or []

                # intentar mover usando la API del mapa (limpia celda anterior) a través de mover_por_ruta
                self.mover_por_ruta(v)

                # si llegó a la base (comprobación por posición), transferir puntaje y resetear vehículo
                if getattr(v, "position", None) == (target_row, target_col):
                    collected = getattr(v, "collected_value", 0)
                    if collected:
                        player.score = getattr(player, "score", 0) + collected
                        setattr(v, "collected_value", 0)
                    if hasattr(v, "arrive_base"):
                        v.arrive_base()
                    else:
                        v.status = "in_base"
                    v.route = []
