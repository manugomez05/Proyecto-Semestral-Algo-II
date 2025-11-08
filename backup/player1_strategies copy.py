import collections

class Player1ResourceStrategy:
    """
    Estrategia: cada vehículo recoge el recurso más cercano por ruta real en la grilla.
    Cuando se queda sin capacidad → retorna a la base por camino más corto.
    """

    def __init__(self, map, resources):
        self.map = map  # Mapa que tiene rows, cols y place_vehicle / graph.place_vehicle
        self.resources = resources


    # ------------------------------------------------------------
    # BFS para obtener ruta más corta en grilla
    # ------------------------------------------------------------
    def bfs(self, start, goal):
        if start == goal:
            return [start]

        rows = self.map.rows
        cols = self.map.cols

        queue = collections.deque([start])
        visited = {start: None}

        while queue:
            r, c = queue.popleft()

            for nr, nc in ((r+1,c), (r-1,c), (r,c+1), (r,c-1)):
                if 0 <= nr < rows and 0 <= nc < cols:
                    if (nr, nc) not in visited:

                        # Aquí puedes agregar condiciones de terreno si querés
                        # por ahora todo es transitable

                        visited[(nr, nc)] = (r, c)
                        queue.append((nr, nc))

                        if (nr, nc) == goal:
                            # reconstruir camino
                            path = [(nr, nc)]
                            while path[-1] != start:
                                path.append(visited[path[-1]])
                            path.reverse()
                            return path

        return None  # no hay camino


    # ------------------------------------------------------------
    # Buscar recurso más cercano usando BFS (distancia real)
    # ------------------------------------------------------------
    def encontrar_recurso_mas_cercano(self, vehiculo, recursos):
        mejor_recurso = None
        mejor_ruta = None

        for recurso in recursos:
            ruta = self.bfs(vehiculo.position, recurso.position)
            if ruta is not None:
                if mejor_ruta is None or len(ruta) < len(mejor_ruta):
                    mejor_recurso = recurso
                    mejor_ruta = ruta

        return mejor_recurso, mejor_ruta


    # ------------------------------------------------------------
    # Mover vehículo siguiendo self.route paso a paso
    # ------------------------------------------------------------
    def mover_por_ruta(self, vehiculo):
        if not hasattr(vehiculo, "route") or not vehiculo.route:
            return

        # Tomar siguiente paso
        next_pos = vehiculo.route.pop(0)
        nr, nc = next_pos
        r, c = vehiculo.position

        placed = False
        try:
            if hasattr(self.map, "graph") and callable(getattr(self.map.graph, "place_vehicle", None)):
                placed = self.map.graph.place_vehicle(vehiculo, nr, nc)
            elif callable(getattr(self.map, "place_vehicle", None)):
                placed = self.map.place_vehicle(vehiculo, nr, nc)
        except:
            placed = False

        if not placed:
            if hasattr(vehiculo, "move_to"):
                vehiculo.move_to(nr, nc)
            else:
                vehiculo.position = (nr, nc)


    # ------------------------------------------------------------
    # MAIN STRATEGY LOOP
    # ------------------------------------------------------------
    def update(self, player):
        recursos = player.resources  # Asegúrate que exista player.resources = lista de recursos
        base = player.base_position  # (row, col)

        for v in player.vehicles.values():

            if v.status == "destroyed":
                continue

            # Si sin capacidad → volver base
            if v.capacity <= 0 and v.status not in ("returning", "need_return"):
                v.status = "need_return"
                v.route = self.bfs(v.position, base)

            # Caso 1 → ir a base
            if v.status in ("need_return", "returning"):
                if v.position == base:
                    v.status = "idle"
                    v.capacity = v.max_capacity  # recargar
                    v.route = []
                else:
                    self.mover_por_ruta(v)
                continue

            # Caso 2 → si no tiene ruta, buscar recurso más cercano
            if not hasattr(v, "route") or not v.route:
                recurso, ruta = self.encontrar_recurso_mas_cercano(v, recursos)
                if recurso is not None and ruta is not None:
                    # eliminar primer paso si es la posición actual (evita "no moverse")
                    if ruta and ruta[0] == v.position:
                        ruta = ruta[1:]
                    v.route = ruta
                    v.target = recurso
                    v.status = "moving"

            # Caso 3 → mover
            self.mover_por_ruta(v)

            # Si llegó al recurso
            if hasattr(v, "target") and v.target in recursos and v.position == v.target.position:
                recursos.remove(v.target)
                v.capacity -= 1
                v.target = None
                v.route = []
                if v.capacity <= 0:
                    v.status = "need_return"
