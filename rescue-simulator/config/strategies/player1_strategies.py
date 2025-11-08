import random


class BasicMoveStrategy:
    """
    Estrategia de movimiento básica para pruebas visuales.
    Los vehículos se mueven en direcciones aleatorias dentro de los límites del mapa.
    """

    def __init__(self, map_width, map_height, map):
        self.map_width = map_width
        self.map_height = map_height
        self.map = map


    """

    Resumen rápido

    Recorre todos los vehículos del jugador y mueve cada uno de forma aleatoria dentro de los límites del mapa.
    Intenta usar la API del mapa (preferiblemente map.graph.place_vehicle, o map.place_vehicle) para realizar el movimiento y que el grafo limpie la celda anterior.
    Si la llamada al mapa falla o no existe, realiza un fallback que solo actualiza el objeto Vehicle localmente (move_to o asignando position y status).
    Paso a paso (líneas lógicas)

    Iteración sobre vehículos

    for v in player.vehicles.values():
    Procesa cada vehículo del jugador.
    Saltar vehículos destruidos

    if v.status == "destroyed": continue
    Si el vehículo está marcado como destruido no se intenta mover.
    Leer posición actual

    row, col = v.position
    Se usa la posición actual del vehículo para calcular el destino y, muy importante, para que place_vehicle pueda limpiar correctamente la celda anterior.
    Calcular desplazamiento aleatorio

    dr = random.choice([-2, -1, 0, 1, 2])
    dc = random.choice([-2, -1, 0, 1, 2])
    El vehículo se mueve entre -2 y +2 celdas en fila y columna.
    Obtener límites del mapa

    max_row = self.map.rows - 1 if hasattr(self.map, "rows") else self.map_height
    max_col = self.map.cols - 1 if hasattr(self.map, "cols") else self.map_width
    Se soportan dos formas del objeto map: uno con atributos rows/cols (graph) o solo dimensiones pasadas al constructor de la estrategia.
    Clamp del destino dentro del mapa

    new_row = max(0, min(max_row, row + dr))
    new_col = max(0, min(max_col, col + dc))
    Asegura que el nuevo destino esté dentro de los límites válidos.
    Intento de mover usando el mapa (útil para limpiar la celda anterior)

    placed = False
    try:
    if hasattr(self.map, "graph") and callable(getattr(self.map.graph, "place_vehicle", None)):
    placed = self.map.graph.place_vehicle(v, new_row, new_col)
    elif callable(getattr(self.map, "place_vehicle", None)):
    placed = self.map.place_vehicle(v, new_row, new_col)
    except Exception:
    placed = False
    Explicación:
    Primero intenta usar map.graph.place_vehicle si existe y es callable (recomendado porque el grafo sabe limpiar nodos).
    Si no existe, prueba map.place_vehicle (wrapper en MapManager).
    Se captura cualquier excepción y se considera que no se colocó (placed = False).
    Se asume que place_vehicle devuelve True si colocó correctamente y que internamente limpia la celda anterior del vehículo.
    Fallback: actualizar solo el objeto Vehicle si place_vehicle no funcionó

    if not placed:
    if hasattr(v, "move_to"):
    v.move_to(new_row, new_col)
    else:
    v.position = (new_row, new_col)
    v.status = "moving"
    Razonamiento:
    Si el mapa no pudo mover el vehículo, al menos actualizamos el objeto para que su posición refleje el intento.
    move_to preferido porque puede actualizar status y lógica interna (por ejemplo, marcar 'moving').
    Puntos importantes y recomendaciones

    No reasignar v.position antes de llamar a place_vehicle: place_vehicle usa la posición actual del vehículo para limpiar la celda anterior. Si cambias v.position antes de llamar, la celda antigua no se limpiará.
    place_vehicle debe:
    comparar correctamente el contenido del nodo (objeto o dict con "id") para limpiar solo si el nodo realmente pertenecía a ese vehículo,
    devolver True/False para que la estrategia sepa si tuvo éxito.
    Si sigues viendo “fantasmas”:
    Verifica que place_vehicle esté implementada y limpia la celda anterior correctamente (comparando id/objeto).
    Asegura que todas las rutas de movimiento en el código (otras estrategias, inicialización, tests) usen place_vehicle y no hagan asignaciones directas a v.position.
    Posible mejora: comprobar si el destino está ocupado antes de sobrescribir y devolver False si está bloqueado, o manejar colisiones explícitamente.
    Si quieres, puedo revisar la implementación actual de MapGraph.place_vehicle y show cómo debe comparar y limpiar el nodo anterior exactamente (incluyendo ejemplos de comparación por id y por objeto).
    """



    def update(self, player):
        """
        Actualiza las posiciones de los vehículos del jugador.
        """
#        for v in player.vehicles.values():
#            if v.status == "destroyed":
#                continue
#
#            # posición actual (la usada para limpiar nodo anterior en place_vehicle)
#            row, col = v.position
#
#            # Si el vehículo debe volver a la base, moverlo 1 paso hacia la base
#            if getattr(v, "status", None) in ("need_return", "returning"):
#                target_row, target_col = player.base_position
#                dr = 0 if target_row == row else (1 if target_row > row else -1)
#                dc = 0 if target_col == col else (1 if target_col > col else -1)
#                new_row = max(0, min(self.map.rows - 1 if hasattr(self.map, "rows") else self.map_height, row + dr))
#                new_col = max(0, min(self.map.cols - 1 if hasattr(self.map, "cols") else self.map_width, col + dc))
#            else:
#                # calcular desplazamiento y destino aleatorio
#                import random
#                dr = random.choice([-2, -1, 0, 1, 2])
#                dc = random.choice([-2, -1, 0, 1, 2])
#
#                max_row = self.map.rows - 1 if hasattr(self.map, "rows") else self.map_height
#                max_col = self.map.cols - 1 if hasattr(self.map, "cols") else self.map_width
#
#                new_row = max(0, min(max_row, row + dr))
#                new_col = max(0, min(max_col, col + dc))
#
#            # Llamada segura a place_vehicle del graph o del map manager
#            placed = False
#            try:
#                if hasattr(self.map, "graph") and callable(getattr(self.map.graph, "place_vehicle", None)):
#                    placed = self.map.graph.place_vehicle(v, new_row, new_col)
#                elif callable(getattr(self.map, "place_vehicle", None)):
#                    placed = self.map.place_vehicle(v, new_row, new_col)
#            except Exception:
#                placed = False
#
#            # fallback: actualizar sólo el objeto si place_vehicle no está disponible o falla
#            if not placed:
#                if hasattr(v, "move_to"):
#                    v.move_to(new_row, new_col)
#                else:
#                    v.position = (new_row, new_col)
#                    v.start_trip()
#
#            break
#            # QUITAR el break para procesar todos los vehículos

        # Nueva versión: mover solo el vehículo con id "moto_1" para debugging
        target_id = "jeep_1"

        # localizar vehículo por llave o por atributo id
        target_vehicle = None
        if hasattr(player, "vehicles"):
            vehicles = player.vehicles
            try:
                # si es dict con keys = ids
                target_vehicle = vehicles.get(target_id)
            except Exception:
                target_vehicle = None

            if target_vehicle is None:
                # buscar por atributo/id en los valores
                for vv in (vehicles.values() if hasattr(vehicles, "values") else []):
                    if getattr(vv, "id", None) == target_id or (isinstance(vv, dict) and vv.get("id") == target_id):
                        target_vehicle = vv
                        break

        if target_vehicle is None:
            # nada que mover
            return

        v = target_vehicle

        if getattr(v, "status", None) == "destroyed":
            return

        # posición actual (no reasignarla antes de place_vehicle)
        row, col = v.position

        # mover hacia la base si está en retorno
        if getattr(v, "status", None) == "need_return":
            #target_row, target_col = player.base_position #PROBLEMA AL OBTENER LA BASE
            #print("BASE: ", player.base_position)
            target_row, target_col = (0,0)
            dr = 0 if target_row == row else (1 if target_row > row else -1)
            dc = 0 if target_col == col else (1 if target_col > col else -1)

            max_row = self.map.rows - 1 if hasattr(self.map, "rows") else (self.map_height - 1)
            max_col = self.map.cols - 1 if hasattr(self.map, "cols") else (self.map_width - 1)

            new_row = max(0, min(max_row, row + dr))
            new_col = max(0, min(max_col, col + dc))

            if new_col == target_col and new_row == target_row:
                # el vehículo llegó a la base: transferir lo recogido al score del jugador
                collected = getattr(v, "collected_value", 0)

                # sumar al score del player (crear atributo si no existe)
                if hasattr(player, "score"):
                    player.score += collected
                else:
                    player.score = collected

                # marcar llegada al base (resetea counters internos del vehículo)
                v.arrive_base()

                # opcional: asegurar que el vehículo tenga la posición de la base
                # (place_vehicle normalmente colocará el vehículo en la celda destino)
                # v.position = (target_row, target_col)
        else:
            import random
            dr = random.choice([-1, 0, 1])
            dc = random.choice([-1, 0, 1])

            max_row = self.map.rows - 1 if hasattr(self.map, "rows") else self.map_height
            max_col = self.map.cols - 1 if hasattr(self.map, "cols") else self.map_width

            new_row = max(0, min(max_row, row + dr))
            new_col = max(0, min(max_col, col + dc))

        placed = False
        try:
            # Obtener tick y mine_manager del mapa para verificación de minas
            tick = getattr(self.map, "current_tick", None)
            mine_manager = getattr(self.map, "mine_manager", None)
            
            if hasattr(self.map, "graph") and callable(getattr(self.map.graph, "place_vehicle", None)):
                placed = self.map.graph.place_vehicle(v, new_row, new_col, tick=tick, mine_manager=mine_manager)
            elif callable(getattr(self.map, "place_vehicle", None)):
                placed = self.map.place_vehicle(v, new_row, new_col, tick=tick, mine_manager=mine_manager)
        except Exception:
            placed = False

        if not placed:
            if hasattr(v, "move_to"):
                v.move_to(new_row, new_col)
            else:
                v.position = (new_row, new_col)
                if hasattr(v, "start_trip"):
                    v.start_trip()
                else:
                    if v.capacity <= 0:
                        print("ENTRO CAPACIDAD player")
                        v.status = "need_return"
                    else:
                        v.status = "moving"
