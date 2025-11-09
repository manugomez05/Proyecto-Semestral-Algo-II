"""
Módulo: map_graph
-------------------------------------------------
Define la estructura de datos del mapa mediante una cuadrícula de nodos.

Contiene la clase `MapGraph`, que representa el grafo del terreno 
y permite acceder o modificar el estado de cada celda.

Responsabilidades:
- Crear y conectar nodos (vecinos adyacentes).
- Proveer funciones de acceso y modificación de estado.
- Servir como base de los algoritmos de búsqueda (pathfinding).
"""



#clase responsable de crear el grafo que va a representar el mapa 2d del simulador, usando la clase node
from src.node import Node
from src.mines_manager import MineManager
from src.mines import MineType
from src.resources import generate_resources

class MapGraph:
    def __init__(self,rows,cols):
        self.rows = rows
        self.cols = cols
        self.grid = [] #matriz de nodos
    def __getstate__(self):
        """Método especial para pickle"""
        return self.__dict__.copy()
        
    def __setstate__(self, state):
        """Método especial para pickle"""
        # Restaurar atributos desde el estado serializado
        self.__dict__.update(state)
        # Asegurar que la cuadrícula y vecinos estén consistentes si faltan
        if not getattr(self, 'grid', None):
            self.grid = []
            self.generate_nodes()
            self.connect_neighbors()

    def __post_init_setup__(self):
        """Helper para inicializar la cuadrícula (usado en el constructor)."""
        # Solo generar nodos si la grid está vacía
        if not getattr(self, 'grid', None):
            self.generate_nodes()
            self.connect_neighbors()

    def __init__(self,rows,cols):
        # Mantener compatibilidad con la firma original en caso de re-creación
        self.rows = rows
        self.cols = cols
        self.grid = [] #matriz de nodos
        # Inicializar la cuadrícula y conexiones
        self.__post_init_setup__()

    def generate_nodes(self):
        for row in range(self.rows):
            row_nodes = []
            for col in range(self.cols):
                node = Node(row,col)
                row_nodes.append(node)
            self.grid.append(row_nodes)


    def connect_neighbors(self):
        """
        Conecta cada nodo con su vecino
        """
        for row in range(self.rows):
            for col in range(self.cols):
                node = self.grid[row][col]

                #Vecino arriba
                if row>0:
                    node.add_neighbor(self.grid[row-1][col])
                #Vecino abajo
                if row < self.rows -1:
                    node.add_neighbor(self.grid[row+1][col])
                #Vecino izq
                if col>0:
                    node.add_neighbor(self.grid[row][col-1])
                #Vecino der
                if col < self.cols - 1:
                    node.add_neighbor(self.grid[row][col + 1])


    def get_node(self, row, col):
        #Devuelve el nodo en la posicion (row, col)
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        return None
    
    def set_node_state(self, row, col, state, content = None):
        #Modifica el estado y contenido de un nodo
        node = self.get_node(row,col)
        if node:
            node.state = state
            node.content = content if content else {}
            
    def all_resources(self):
        """
        Devuelve una lista con los objetos/resources presentes en el mapa.
        Si la lista original (self.resources) existe, la devuelve (copia).
        Si no existe, reconstruye una lista a partir del contenido de los nodos.
        """
        if hasattr(self, "resources") and self.resources is not None:
            return list(self.resources)

        recursos = []
        for r in range(self.rows):
            for c in range(self.cols):
                node = self.get_node(r, c)
                if node and getattr(node, "state", None) == "resource":
                    content = getattr(node, "content", None)
                    # Si el contenido almacena el objeto original bajo alguna clave:
                    if isinstance(content, dict) and ("object" in content or "obj" in content):
                        obj = content.get("object") or content.get("obj")
                        recursos.append(obj)
                    else:
                        # devolver una representación mínima (incluye posición)
                        if isinstance(content, dict):
                            item = dict(content)
                            item.setdefault("position", (r, c))
                            recursos.append(item)
                        else:
                            recursos.append(content)
        return recursos

    def place_vehicle(self, vehicle, new_row, new_col, tick=None, mine_manager=None, player1=None, player2=None):
        """
        Coloca o mueve un vehículo al nodo (row, col).
        Limpia la celda anterior del vehículo (si realmente estaba ese vehículo).
        Verifica si la nueva posición está minada y destruye el vehículo si es así.
        Devuelve True si se colocó correctamente, False si la posición no existe.
        
        Args:
            vehicle: Objeto o dict del vehículo
            new_row: Nueva fila
            new_col: Nueva columna
            tick: Tiempo actual del juego (opcional, necesario para verificar minas dinámicas)
            mine_manager: Gestor de minas (opcional, necesario para verificar minas)
            player1: Jugador 1 (opcional, para verificar colisiones entre equipos)
            player2: Jugador 2 (opcional, para verificar colisiones entre equipos)
        """
        # Determinar posición anterior segura
        old_pos = None
        if isinstance(vehicle, dict):
            old_pos = vehicle.get("position")
        else:
            old_pos = getattr(vehicle, "position", None)

        if isinstance(old_pos, (list, tuple)) and len(old_pos) == 2:
            old_row, old_col = old_pos
        else:
            old_row = old_col = None

        # Limpiar nodo anterior solo si corresponde al mismo vehículo.
        if old_row is not None and 0 <= old_row < self.rows and 0 <= old_col < self.cols:
            old_node = self.get_node(old_row, old_col)
            if old_node:
                # Verificar si el nodo contiene este vehículo (puede estar en estado "vehicle" o en una base)
                should_clear = False
                original_base_state = None
                
                # Guardar el estado original de la base si existe
                if old_node.state in ("base_p1", "base_p2"):
                    original_base_state = old_node.state
                
                # Verificar si el contenido del nodo corresponde a este vehículo
                if old_node.content:
                    try:
                        content = old_node.content
                        if isinstance(content, dict):
                            vid = content.get("id")
                            if vid and ((isinstance(vehicle, dict) and vehicle.get("id") == vid) or (not isinstance(vehicle, dict) and getattr(vehicle, "id", None) == vid)):
                                should_clear = True
                        else:
                            # content puede ser referencia directa al objeto vehicle
                            if not isinstance(vehicle, dict) and getattr(content, "id", None) == getattr(vehicle, "id", None):
                                should_clear = True
                    except Exception:
                        should_clear = True
                
                # Limpiar el contenido del vehículo, pero preservar el estado de la base
                if should_clear:
                    if original_base_state:
                        # Si estaba en una base, restaurar el estado de la base sin el vehículo
                        old_node.state = original_base_state
                        old_node.content = {}
                    else:
                        # Si no estaba en una base, limpiar completamente
                        old_node.state = "empty"
                        old_node.content = {}

        # Obtener destino
        node = self.get_node(new_row, new_col)
        if node is None:
            return False

        # Obtener referencia al objeto Vehicle si es posible
        veh_obj = None
        if isinstance(vehicle, dict):
            veh_obj = vehicle.get("object") or vehicle.get("obj")
        else:
            veh_obj = vehicle
        
        # Obtener ID del vehículo que se está moviendo
        moving_vehicle_id = None
        if isinstance(vehicle, dict):
            moving_vehicle_id = vehicle.get("id")
        else:
            moving_vehicle_id = getattr(vehicle, "id", None)
        
        # Verificar si hay un vehículo en la posición destino (puede estar en estado "vehicle" o en una base)
        if (node.state == "vehicle" or node.state in ("base_p1", "base_p2")) and node.content:
            existing_vehicle_content = node.content
            existing_vehicle_id = None
            existing_vehicle_obj = None
            
            if isinstance(existing_vehicle_content, dict):
                existing_vehicle_id = existing_vehicle_content.get("id")
                existing_vehicle_obj = existing_vehicle_content.get("object")
            else:
                existing_vehicle_id = getattr(existing_vehicle_content, "id", None)
                existing_vehicle_obj = existing_vehicle_content
            
            # Si es el mismo vehículo, permitir el movimiento (ya se limpió la posición anterior)
            if existing_vehicle_id == moving_vehicle_id:
                pass  # Continuar con el movimiento normal
            else:
                # Hay otro vehículo en la posición destino
                # Verificar si el vehículo existente ya está destruido
                existing_is_destroyed = False
                if existing_vehicle_obj and hasattr(existing_vehicle_obj, "status"):
                    existing_is_destroyed = existing_vehicle_obj.status == "destroyed"
                
                # Si el vehículo existente ya está destruido, permitir el movimiento
                if existing_is_destroyed:
                    pass  # Continuar con el movimiento normal
                else:
                    # Verificar si son del mismo equipo
                    same_team = False
                    if player1 and player2:
                        # Obtener IDs de vehículos de cada equipo
                        p1_ids = set()
                        p2_ids = set()
                        
                        if hasattr(player1, "vehicles"):
                            if isinstance(player1.vehicles, dict):
                                p1_ids = set(player1.vehicles.keys())
                            else:
                                p1_ids = {getattr(v, "id", None) for v in player1.vehicles if hasattr(v, "id")}
                        
                        if hasattr(player2, "vehicles"):
                            if isinstance(player2.vehicles, dict):
                                p2_ids = set(player2.vehicles.keys())
                            else:
                                p2_ids = {getattr(v, "id", None) for v in player2.vehicles if hasattr(v, "id")}
                        
                        # Verificar si ambos vehículos pertenecen al mismo equipo
                        moving_in_p1 = moving_vehicle_id in p1_ids
                        moving_in_p2 = moving_vehicle_id in p2_ids
                        existing_in_p1 = existing_vehicle_id in p1_ids
                        existing_in_p2 = existing_vehicle_id in p2_ids
                        
                        same_team = (moving_in_p1 and existing_in_p1) or (moving_in_p2 and existing_in_p2)
                    
                    if same_team:
                        # Vehículos del mismo equipo: no permitir el movimiento, no destruir
                        # print(f"⚠️ Colisión mismo equipo detectada: {moving_vehicle_id} intenta moverse a posición ocupada por {existing_vehicle_id}")
                        return False
                    else:
                        # Vehículos de equipos diferentes: NO destruir aquí, permitir que _check_vehicle_collisions lo maneje
                        # Esto evita destruir vehículos prematuramente cuando ambos se están moviendo simultáneamente
                        # print(f"💥 Colisión entre equipos detectada en place_vehicle: {moving_vehicle_id} vs {existing_vehicle_id} en ({new_row}, {new_col})")
                        # No permitir el movimiento - el vehículo se quedará en su posición anterior
                        return False
        
        # Guardar el estado original de la base si existe
        original_base_state = None
        if node.state in ("base_p1", "base_p2"):
            original_base_state = node.state

        # Si en la celda hay un recurso, intentar recolección
        resource = node.content if node and node.state == "resource" else None
        if resource:
            # Determinar tipo y valor del recurso (soportar dict y objeto)
            # print("Recurso", resource)
            if isinstance(resource, dict):
                # soportar claves comunes: 'type' o 'subtype'; puntos en 'points' o 'value'
                res_type = resource.get("tipo") or resource.get("subtype")
                res_value = resource.get("puntos", resource.get("value", 1))
            else:
                res_type = getattr(resource, "tipo", None)
                res_value = getattr(resource, "puntos", getattr(resource, "value", 1))

            # print("res_type", res_type, "res_value", res_value)

            # Obtener referencia al objeto Vehicle si es posible
            veh_obj = None
            if isinstance(vehicle, dict):
                # si el dict incluye referencia al objeto real bajo clave 'object' o 'obj'
                veh_obj = vehicle.get("object") or vehicle.get("obj")
            else:
                veh_obj = vehicle

            # Intentar que el vehículo recoja el recurso si tenemos el objeto y puede recoger ese tipo
            if veh_obj and hasattr(veh_obj, "can_pick") and res_type and veh_obj.can_pick(res_type):
                try:
                    picked = veh_obj.pick_up(res_type, value=res_value)
                except Exception:
                    picked = False

                if picked:
                    # eliminar recurso del mapa
                    node.state = "empty"
                    node.content = {}

                    # si después de recoger no quedan viajes (trips_done_since_base == 0) o estado exige volver, marcar
                    try:

                        # print("ENTRO")
                        max_consecutive_trips = getattr(veh_obj, "max_consecutive_trips", None)

                        if getattr(veh_obj, "trips_done_since_base", None) and veh_obj.trips_done_since_base >= max_consecutive_trips:
                            veh_obj.status = "need_return"
                        if getattr(veh_obj, "status", None) == "need_return":
                            # marca que debe volver; la lógica de retorno la maneja GameEngine/estrategias
                            pass
                    except Exception:
                        pass

        # Guardar referencia al vehículo (no crear copia) si es dict;
        # si es objeto, guardar un dict ligero que referencia el objeto para visualización.
        # Preservar el estado de la base si el vehículo está en una base
        if original_base_state:
            # Mantener el estado de la base, pero guardar el vehículo en el contenido
            # El estado ya es base_p1 o base_p2, no lo cambiamos
            pass  # El estado ya es base_p1 o base_p2, no lo cambiamos
        else:
            node.state = "vehicle"
        
        # Guardar el vehículo en el contenido (tanto si está en base como si no)
        if isinstance(vehicle, dict):
            node.content = vehicle
        else:
            # dict ligero usado por la visualización; mantenemos referencia al objeto bajo 'object'
            node.content = {
                "id": getattr(vehicle, "id", None),
                "type": getattr(vehicle, "type", None),
                "color": getattr(vehicle, "color", None),
                "position": (new_row, new_col),
                "object": vehicle
            }

        # Actualizar el objeto vehículo (usar move_to si existe)
        if hasattr(vehicle, "move_to"):
            try:
                vehicle.move_to(new_row, new_col)
            except Exception:
                vehicle.position = (new_row, new_col)
        else:
            # si es dict serializado, actualizar posición en dict
            if isinstance(vehicle, dict):
                vehicle["position"] = (new_row, new_col)

        # Verificar si la nueva posición está minada (PASO 3 del flujo)
        if tick is not None and mine_manager is not None:
            # Obtener referencia al objeto Vehicle si es posible
            veh_obj = None
            if isinstance(vehicle, dict):
                veh_obj = vehicle.get("object") or vehicle.get("obj")
            else:
                veh_obj = vehicle
            
            # Solo verificar si el vehículo no está ya destruido
            if veh_obj and hasattr(veh_obj, "status") and veh_obj.status != "destroyed":
                # Verificar si la celda está minada
                if mine_manager.isCellMined((new_row, new_col), tick):
                    # Vehículo explota: destruir y perder recursos
                    veh_obj.status = "destroyed"
                    veh_obj.collected_value = 0
                    # Limpiar el nodo donde estaba el vehículo
                    node.state = "empty"
                    node.content = {}
                    # print(f"¡Vehículo {getattr(veh_obj, 'id', 'unknown')} explotó en mina en posición ({new_row}, {new_col})!")
                    return True  # Retornamos True porque técnicamente se "colocó" (aunque explotó)

        return True

    def remove_vehicle(self, vehicle) -> bool:
        """
        Quita el vehículo del grafo (si está presente en la posición conocida).
        """
        # obtener posición conocida del vehículo
        if isinstance(vehicle, dict):
            pos = vehicle.get("position")
        else:
            pos = getattr(vehicle, "position", None)

        if not isinstance(pos, (list, tuple)) or len(pos) != 2:
            return False

        r, c = pos
        if 0 <= r < self.rows and 0 <= c < self.cols:
            node = self.get_node(r, c)
            if node and node.state == "vehicle":
                content = node.content
                match = False
                if isinstance(content, dict):
                    if content is vehicle:
                        match = True
                    else:
                        match = content.get("id") == (vehicle.get("id") if isinstance(vehicle, dict) else getattr(vehicle, "id", None))
                else:
                    if isinstance(content, dict) and content.get("_obj") is vehicle:
                        match = True
                    elif hasattr(content, "id"):
                        match = getattr(content, "id", None) == (vehicle.get("id") if isinstance(vehicle, dict) else getattr(vehicle, "id", None))
                    else:
                        match = content == vehicle

                if match:
                    self.set_node_state(r, c, "empty", {})
                    return True
        return False

    def generate_map(self):
        
        #Gestor de minas
        self.mine_manager = MineManager()

        #Cantidad de minas por tipo
        specific_mines = {
                MineType.O1: 2,
                MineType.O2: 2,
                MineType.T1: 2,
                MineType.T2: 2,
                MineType.G1: 2
            }
        
        #Generar minas aleatorias
        self.mine_manager.addRandomSet(self.rows, self.cols, specific_mines, margin=3)

        #Marcar nodos afectados por minas
        for mine in self.mine_manager.all(): 
            for r in range(self.rows):
                for c in range(self.cols):
                    if mine.contains((r,c), tick=0): #tick inicial
                        self.set_node_state(r,c, "mine", {"type": mine.type.name})
        
        #Obtener posiciones ocupadas por minas
        occupied_positions = set() #conjunto con elementos únicos 
        for mine in self.mine_manager.all():
            for r in range(self.rows):
                for c in range(self.cols):
                    if mine.contains((r,c), tick=0):
                        occupied_positions.add((r,c))

        #Generar recursos evitando minas
        resources = generate_resources(self.rows, self.cols, occupied_positions)
        
        # guardar referencia a la lista original de objetos recursos
        self.resources = resources
        
        #Marcar nodos con recursos
        for res in resources:
            r,c = res.position
            self.set_node_state(r,c, "resource", {
                "subtype": res.tipo,
                "points": res.puntos,
                "img": res.img_path
            })




