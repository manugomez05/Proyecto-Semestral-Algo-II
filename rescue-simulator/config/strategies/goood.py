"""
Estrategia del Equipo 1: BFS (Breadth-First Search)
- Recolectores: BFS hacia recursos de mayor valor (priorizar mayor valor, en empate el más cercano según BFS)
- Motos: Atacar camiones enemigos con BFS, si no hay camiones, recoger recursos con BFS
"""

from collections import deque
from typing import List, Tuple, Optional, Set, Dict


class Strategy1:
    """
    Estrategia 1: BFS
    - Motos: destruir camiones enemigos usando BFS
    - Resto de vehículos: BFS hacia recursos de mayor valor
    """
    
    def __init__(self, map_width, map_height, map, enemy_player=None):
        self.map_width = map_width
        self.map_height = map_height
        self.map = map
        self.enemy_player = enemy_player
        # Almacenar objetivos asignados a cada vehículo para evitar conflictos
        self.vehicle_targets: Dict[str, Tuple[int, int]] = {}
    
    def get_current_tick(self) -> int:
        """Obtiene el tick actual del mapa"""
        return getattr(self.map, "current_tick", 0)
    
    def get_mine_manager(self):
        """Obtiene el gestor de minas"""
        return getattr(self.map, "mine_manager", None)
    
    def is_position_safe(self, row: int, col: int, allow_risk: bool = False) -> bool:
        """
        Verifica si una posición está segura (no minada y dentro de límites)
        allow_risk: actualmente sin uso, reservado para futuras mejoras
        """
        if not (0 <= row < self.map.rows and 0 <= col < self.map.cols):
            return False
        
        mine_manager = self.get_mine_manager()
        tick = self.get_current_tick()
        
        if mine_manager:
            return not mine_manager.isCellMined((row, col), tick)
        
        return True
    
    def is_occupied_by_teammate(self, row: int, col: int, player, vehicle_id: str, planned_moves: Dict[str, Tuple[int, int]] = None) -> bool:
        """
        Verifica si una posición está ocupada por un vehículo del mismo equipo.
        Considera también los movimientos planificados de otros vehículos en este turno.
        SOLO bloquea si es el siguiente movimiento inmediato, no para BFS de largo alcance.
        """
        # Para BFS de planificación, solo verificar movimientos planificados del turno actual
        if planned_moves:
            for other_id, other_pos in planned_moves.items():
                if other_id != vehicle_id and other_pos == (row, col):
                    return True
        
        return False
    
    def bfs_path(self, start: Tuple[int, int], target: Tuple[int, int], player, vehicle_id: str, planned_moves: Dict[str, Tuple[int, int]] = None, max_iterations: int = 10000) -> Optional[List[Tuple[int, int]]]:
        """
        BFS para encontrar el camino más corto.
        Trata minas como bloqueadas y evita posiciones ocupadas por compañeros de equipo.
        """
        if start == target:
            return [start]
        
        queue = deque([(start, [start])])
        visited = {start}
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        iterations = 0
        
        while queue and iterations < max_iterations:
            iterations += 1
            current_pos, path = queue.popleft()
            
            if current_pos == target:
                return path
            
            row, col = current_pos
            
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                
                if not (0 <= new_row < self.map.rows and 0 <= new_col < self.map.cols):
                    continue
                
                neighbor = (new_row, new_col)
                
                if neighbor in visited:
                    continue
                
                # Verificar si la posición es segura (no minada)
                if not self.is_position_safe(new_row, new_col):
                    continue
                
                # Solo evitar compañeros si es un movimiento planificado (no bloquear BFS por vehículos en el mapa)
                # Esto permite que BFS encuentre rutas que requieren que otros vehículos se muevan
                if planned_moves and neighbor != target:
                    if self.is_occupied_by_teammate(new_row, new_col, player, vehicle_id, planned_moves):
                        continue
                
                # No permitir entrar en la base enemiga
                node = self.map.graph.get_node(new_row, new_col)
                if node:
                    # Determinar qué base es del jugador actual
                    if hasattr(player, "name"):
                        player_base = "base_p1" if "1" in player.name else "base_p2"
                        enemy_base = "base_p2" if player_base == "base_p1" else "base_p1"
                        # No permitir entrar en base enemiga (excepto si es el objetivo)
                        if node.state == enemy_base and neighbor != target:
                            continue
                
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
        
        # Si alcanza el máximo, es probable que haya un problema
        # pero no imprimir para no saturar la consola
        
        return None
    
    def bfs_distance(self, start: Tuple[int, int], target: Tuple[int, int], player, vehicle_id: str, planned_moves: Dict[str, Tuple[int, int]] = None) -> int:
        """
        Calcula la distancia en pasos usando BFS entre dos posiciones.
        Retorna -1 si no hay camino.
        """
        path = self.bfs_path(start, target, player, vehicle_id, planned_moves)
        if path:
            return len(path) - 1  # -1 porque el path incluye la posición inicial
        return -1
    
    def find_enemy_trucks(self, player) -> List[Tuple[int, int]]:
        """Encuentra todos los camiones enemigos en el mapa que no estén destruidos"""
        enemy_trucks = []
        if not self.enemy_player:
            return enemy_trucks
        
        current_player_ids = set(player.vehicles.keys()) if hasattr(player, "vehicles") else set()
        
        for row in range(self.map.rows):
            for col in range(self.map.cols):
                node = self.map.graph.get_node(row, col)
                if node and (node.state == "vehicle" or node.state in ("base_p1", "base_p2")) and node.content:
                    vehicle_content = node.content
                    vehicle_id = None
                    vehicle_obj = None
                    
                    if isinstance(vehicle_content, dict):
                        vehicle_id = vehicle_content.get("id")
                        vehicle_obj = vehicle_content.get("object")
                    else:
                        vehicle_id = getattr(vehicle_content, "id", None)
                        vehicle_obj = vehicle_content
                    
                    if vehicle_id and vehicle_id not in current_player_ids:
                        if vehicle_obj:
                            vehicle_type = getattr(vehicle_obj, "type", None)
                            status = getattr(vehicle_obj, "status", None)
                        else:
                            vehicle_type = vehicle_content.get("type") if isinstance(vehicle_content, dict) else None
                            status = vehicle_content.get("status") if isinstance(vehicle_content, dict) else None
                        
                        if vehicle_type == "camion" and status != "destroyed":
                            enemy_trucks.append((row, col))
        
        return enemy_trucks
    
    def find_best_resource(self, vehicle, resources: List, player, vehicle_id: str, planned_moves: Dict[str, Tuple[int, int]] = None, assigned_targets: Set[Tuple[int, int]] = None) -> Optional[Tuple[object, Tuple[int, int]]]:
        """
        Encuentra el mejor recurso: mayor valor, en empate el más cercano según BFS.
        Solo considera recursos que el vehículo puede recoger.
        Evita recursos ya asignados a otros vehículos.
        Busca en TODO el mapa sin restricciones de distancia.
        """
        if not resources:
            return None
        
        if assigned_targets is None:
            assigned_targets = set()
        
        vehicle_pos = vehicle.position
        best_resource = None
        best_pos = None
        best_value = -1
        best_distance = float('inf')
        
        # Contar recursos válidos para debug
        valid_count = 0
        checked_count = 0
        
        for resource in resources:
            checked_count += 1
            # Obtener posición del recurso
            res_pos = None
            if hasattr(resource, "position"):
                res_pos = resource.position
            elif isinstance(resource, dict):
                res_pos = resource.get("position")
            
            if not res_pos or len(res_pos) != 2:
                continue
            
            # Convertir de (x, y) a (row, col)
            res_x, res_y = res_pos[0], res_pos[1]
            res_row, res_col = res_y, res_x
            
            # Verificar que el nodo existe y tiene un recurso
            node = self.map.graph.get_node(res_row, res_col)
            if not node or node.state != "resource":
                continue
            
            # Evitar recursos ya asignados a otros vehículos
            if (res_row, res_col) in assigned_targets:
                continue
            
            # Obtener valor del recurso
            if hasattr(resource, "puntos"):
                value = resource.puntos
            elif isinstance(resource, dict):
                value = resource.get("puntos", resource.get("value", 1))
            else:
                value = 1
            
            # Obtener tipo del recurso
            if hasattr(resource, "tipo"):
                res_type = resource.tipo
            elif isinstance(resource, dict):
                res_type = resource.get("tipo", resource.get("subtype"))
            else:
                res_type = None
            
            # Verificar si el vehículo puede recoger este tipo de recurso
            if res_type and hasattr(vehicle, "can_pick") and not vehicle.can_pick(res_type):
                continue
            
            # Calcular distancia usando BFS
            distance = self.bfs_distance(vehicle_pos, (res_row, res_col), player, vehicle_id, planned_moves)
            
            # Si no hay camino, ignorar este recurso
            if distance < 0:
                continue
            
            valid_count += 1
            
            # Priorizar mayor valor, en empate menor distancia
            if value > best_value or (value == best_value and distance < best_distance):
                best_value = value
                best_distance = distance
                best_resource = resource
                best_pos = (res_row, res_col)
        
        # Debug: mostrar información de búsqueda solo si no encuentra nada
        if checked_count > 0 and valid_count == 0:
            import random
            if random.random() < 0.1:  # Solo cuando no encuentra recursos accesibles
                # Encontrar el recurso más cercano solo por distancia Manhattan para comparar
                closest_dist = float('inf')
                for resource in resources:
                    if hasattr(resource, "position"):
                        res_pos = resource.position
                    elif isinstance(resource, dict):
                        res_pos = resource.get("position")
                    else:
                        continue
                    if res_pos and len(res_pos) == 2:
                        res_x, res_y = res_pos[0], res_pos[1]
                        res_row, res_col = res_y, res_x
                        dist = abs(vehicle_pos[0] - res_row) + abs(vehicle_pos[1] - res_col)
                        if dist < closest_dist:
                            closest_dist = dist
                print(f"[WARN {vehicle_id} @ {vehicle_pos}] {checked_count} recursos, 0 accesibles BFS, más cercano Manhattan: {closest_dist}")
        
        if best_resource and best_pos:
            return (best_resource, best_pos)
        
        return None
    
    def find_closest_enemy_truck(self, vehicle, enemy_trucks: List[Tuple[int, int]], player, vehicle_id: str, planned_moves: Dict[str, Tuple[int, int]] = None, assigned_targets: Set[Tuple[int, int]] = None) -> Optional[Tuple[int, int]]:
        """
        Encuentra el camión enemigo más cercano usando BFS.
        Evita camiones ya asignados a otros vehículos.
        """
        if not enemy_trucks:
            return None
        
        if assigned_targets is None:
            assigned_targets = set()
        
        vehicle_pos = vehicle.position
        closest_truck = None
        min_distance = float('inf')
        
        for truck_pos in enemy_trucks:
            # Evitar camiones ya asignados
            if truck_pos in assigned_targets:
                continue
            
            distance = self.bfs_distance(vehicle_pos, truck_pos, player, vehicle_id, planned_moves)
            if distance >= 0 and distance < min_distance:
                min_distance = distance
                closest_truck = truck_pos
        
        return closest_truck
    
    def get_next_move(self, vehicle, target_pos: Tuple[int, int], player, vehicle_id: str, planned_moves: Dict[str, Tuple[int, int]] = None) -> Tuple[int, int]:
        """
        Obtiene el siguiente movimiento hacia el objetivo usando BFS.
        Retorna la posición actual si no hay movimiento posible.
        Detecta deadlocks cuando dos vehículos se bloquean mutuamente.
        """
        vehicle_pos = vehicle.position
        
        if vehicle_pos == target_pos:
            return vehicle_pos
        
        path = self.bfs_path(vehicle_pos, target_pos, player, vehicle_id, planned_moves)
        
        if path and len(path) > 1:
            next_pos = path[1]
            # Verificar una vez más que el siguiente movimiento es válido
            if not self.is_occupied_by_teammate(next_pos[0], next_pos[1], player, vehicle_id, planned_moves):
                return next_pos
            else:
                # Si el siguiente paso está bloqueado por un compañero, intentar esperar o movimiento alternativo
                # para evitar deadlocks
                pass
        
        # Si no hay path válido, intentar movimiento directo
        row, col = vehicle_pos
        target_row, target_col = target_pos
        
        dr = 0 if target_row == row else (1 if target_row > row else -1)
        dc = 0 if target_col == col else (1 if target_col > col else -1)
        
        new_row = row + dr
        new_col = col + dc
        
        if (self.is_position_safe(new_row, new_col) and 
            not self.is_occupied_by_teammate(new_row, new_col, player, vehicle_id, planned_moves)):
            return (new_row, new_col)
        
        # Intentar alternativas en orden de preferencia
        for alt_dr, alt_dc in [(dr, 0), (0, dc), (1, 0), (-1, 0), (0, 1), (0, -1)]:
            alt_row = row + alt_dr
            alt_col = col + alt_dc
            if (self.is_position_safe(alt_row, alt_col) and 
                not self.is_occupied_by_teammate(alt_row, alt_col, player, vehicle_id, planned_moves)):
                return (alt_row, alt_col)
        
        # Si no hay movimiento posible, quedarse en la posición actual
        return (row, col)
    
    def get_safe_move_away(self, vehicle, player, vehicle_id: str, planned_moves: Dict[str, Tuple[int, int]] = None) -> Tuple[int, int]:
        """
        Obtiene un movimiento seguro exploratorio cuando no hay objetivos.
        Intenta moverse hacia el centro del mapa o explorar áreas no visitadas.
        """
        row, col = vehicle.position
        import random
        
        # Calcular dirección hacia el centro del mapa
        center_row = self.map.rows // 2
        center_col = self.map.cols // 2
        
        # Dirección preferida hacia el centro
        preferred_directions = []
        if row < center_row:
            preferred_directions.append((1, 0))  # Sur
        elif row > center_row:
            preferred_directions.append((-1, 0))  # Norte
        
        if col < center_col:
            preferred_directions.append((0, 1))  # Este
        elif col > center_col:
            preferred_directions.append((0, -1))  # Oeste
        
        # Todas las direcciones posibles
        all_directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        # Intentar primero direcciones preferidas
        random.shuffle(preferred_directions)
        for dr, dc in preferred_directions:
            new_row = row + dr
            new_col = col + dc
            
            if (self.is_position_safe(new_row, new_col) and 
                not self.is_occupied_by_teammate(new_row, new_col, player, vehicle_id, planned_moves)):
                return (new_row, new_col)
        
        # Si no funcionó, intentar cualquier dirección
        random.shuffle(all_directions)
        for dr, dc in all_directions:
            new_row = row + dr
            new_col = col + dc
            
            if (self.is_position_safe(new_row, new_col) and 
                not self.is_occupied_by_teammate(new_row, new_col, player, vehicle_id, planned_moves)):
                return (new_row, new_col)
        
        return (row, col)
    
    def move_towards_base(self, vehicle, player, vehicle_id: str, planned_moves: Dict[str, Tuple[int, int]] = None) -> Tuple[int, int]:
        """Mueve hacia la base del vehículo usando BFS"""
        if hasattr(vehicle, "base_position") and vehicle.base_position:
            base_row, base_col = vehicle.base_position
        else:
            base_pos = player.base_position
            if isinstance(base_pos, tuple) and len(base_pos) == 2:
                base_row, base_col = base_pos
            elif hasattr(base_pos, "row") and hasattr(base_pos, "col"):
                base_row, base_col = base_pos.row, base_pos.col
            else:
                base_row, base_col = 0, 0
        
        return self.get_next_move(vehicle, (base_row, base_col), player, vehicle_id, planned_moves)
    
    def is_at_base(self, vehicle, player) -> bool:
        """Verifica si el vehículo está en su base"""
        vehicle_pos = vehicle.position
        
        if hasattr(vehicle, "base_position") and vehicle.base_position:
            base_row, base_col = vehicle.base_position
            return vehicle_pos == (base_row, base_col)
        else:
            base_pos = player.base_position
            if isinstance(base_pos, tuple) and len(base_pos) == 2:
                base_row, base_col = base_pos
            elif hasattr(base_pos, "row") and hasattr(base_pos, "col"):
                base_row, base_col = base_pos.row, base_pos.col
            else:
                return False
            
            return vehicle_pos == (base_row, base_col)
    
    def update(self, player):
        """
        Actualiza las posiciones de todos los vehículos.
        Lee todos los recursos del mapa en cada ejecución.
        """
        if not hasattr(player, "vehicles") or not player.vehicles:
            return
        
        vehicles = player.vehicles
        
        # Leer todos los recursos del mapa en cada ejecución
        # Escanear el mapa directamente para asegurar que solo se consideran recursos que realmente existen
        resources = []
        for row in range(self.map.rows):
            for col in range(self.map.cols):
                node = self.map.graph.get_node(row, col)
                if node and node.state == "resource" and node.content:
                    # Reconstruir objeto de recurso desde el nodo
                    content = node.content
                    if hasattr(content, 'position'):
                        resources.append(content)
                    elif isinstance(content, dict):
                        # Asegurar que tenga posición
                        if 'position' not in content:
                            content['position'] = (col, row)  # (x, y)
                        resources.append(content)
        
        # Debug ocasional: mostrar cantidad de minas
        import random
        if random.random() < 0.01:  # 1% de las veces
            mine_manager = self.get_mine_manager()
            if mine_manager:
                total_mines = len(mine_manager.all())
                print(f"[INFO] Recursos restantes: {len(resources)}, Minas totales: {total_mines}")
        
        # Encontrar camiones enemigos
        enemy_trucks = self.find_enemy_trucks(player)
        
        # Planificar movimientos de todos los vehículos primero para evitar colisiones
        planned_moves: Dict[str, Tuple[int, int]] = {}
        vehicle_targets: Dict[str, Optional[Tuple[int, int]]] = {}
        assigned_targets: Set[Tuple[int, int]] = set()  # Objetivos ya asignados
        
        # Primera pasada: determinar objetivos de cada vehículo
        for vehicle_id, vehicle in vehicles.items():
            if getattr(vehicle, "status", None) == "destroyed":
                continue
            
            vehicle_type = getattr(vehicle, "type", None)
            vehicle_status = getattr(vehicle, "status", None)
            
            target_pos = None
            
            # Si debe volver a la base
            if vehicle_status == "need_return":
                if hasattr(vehicle, "base_position") and vehicle.base_position:
                    base_row, base_col = vehicle.base_position
                else:
                    base_pos = player.base_position
                    if isinstance(base_pos, tuple) and len(base_pos) == 2:
                        base_row, base_col = base_pos
                    elif hasattr(base_pos, "row") and hasattr(base_pos, "col"):
                        base_row, base_col = base_pos.row, base_pos.col
                    else:
                        base_row, base_col = 0, 0
                target_pos = (base_row, base_col)
            
            # Si está en la base, mantener estado in_base hasta que se mueva
            # No cambiar automáticamente a "moving" aquí, se cambiará cuando realmente se mueva
            
            # Si no está en need_return, buscar objetivos (incluir in_base después de entregar)
            if vehicle_status != "need_return" and target_pos is None:
                if vehicle_type == "moto":
                    # Motos: buscar camiones enemigos primero
                    if enemy_trucks:
                        closest_truck = self.find_closest_enemy_truck(vehicle, enemy_trucks, player, vehicle_id, planned_moves, assigned_targets)
                        if closest_truck:
                            target_pos = closest_truck
                            assigned_targets.add(closest_truck)
                    
                    # Si no hay camiones o no se encontró uno, buscar recursos
                    if target_pos is None:
                        best_resource = self.find_best_resource(vehicle, resources, player, vehicle_id, planned_moves, assigned_targets)
                        if best_resource:
                            _, res_pos = best_resource
                            target_pos = res_pos
                            assigned_targets.add(res_pos)
                else:
                    # Recolectores: buscar recursos de mayor valor
                    best_resource = self.find_best_resource(vehicle, resources, player, vehicle_id, planned_moves, assigned_targets)
                    if best_resource:
                        _, res_pos = best_resource
                        target_pos = res_pos
                        assigned_targets.add(res_pos)
            
            vehicle_targets[vehicle_id] = target_pos
        
        # Segunda pasada: calcular movimientos considerando los objetivos de todos
        for vehicle_id, vehicle in vehicles.items():
            if getattr(vehicle, "status", None) == "destroyed":
                continue
            
            target_pos = vehicle_targets.get(vehicle_id)
            vehicle_status = getattr(vehicle, "status", None)
            
            # Si el vehículo está en la base SIN objetivo, verificar si es porque no hay recursos
            if vehicle_status == "in_base" and target_pos is None:
                # Si no hay recursos disponibles, cambiar estado a "job_done"
                if len(resources) == 0:
                    vehicle.status = "job_done"
                planned_moves[vehicle_id] = vehicle.position
                continue
            
            # Si está en la base PERO tiene objetivo, cambiar a "moving" para que salga
            if vehicle_status == "in_base" and target_pos is not None:
                vehicle.status = "moving"
            
            if target_pos:
                next_move = self.get_next_move(vehicle, target_pos, player, vehicle_id, planned_moves)
            else:
                # Si no hay objetivo, moverse explorando hacia el centro del mapa
                next_move = self.get_safe_move_away(vehicle, player, vehicle_id, planned_moves)
            
            planned_moves[vehicle_id] = next_move
        
        # Tercera pasada: ejecutar movimientos y manejar llegada a base
        for vehicle_id, vehicle in vehicles.items():
            if getattr(vehicle, "status", None) == "destroyed":
                continue
            
            new_row, new_col = planned_moves.get(vehicle_id, vehicle.position)
            current_pos = vehicle.position
            
            # Si debe volver a la base y llegó
            if getattr(vehicle, "status", None) == "need_return":
                # Verificar si está en su posición de base específica
                if hasattr(vehicle, "base_position") and vehicle.base_position:
                    base_row, base_col = vehicle.base_position
                    # Solo entregar si está exactamente en su posición de base
                    if current_pos == (base_row, base_col) or (new_row, new_col) == (base_row, base_col):
                        # Llegó a la base: entregar recursos y resetear
                        collected = getattr(vehicle, "collected_value", 0)
                        if hasattr(player, "score"):
                            player.score += collected
                        vehicle.arrive_base()
                        # NO mover este turno, quedarse en la base
                        planned_moves[vehicle_id] = (base_row, base_col)
                        continue
            
            # Si el vehículo está en la base y se va a mover, cambiar estado a "moving"
            if getattr(vehicle, "status", None) == "in_base" and (new_row, new_col) != current_pos:
                vehicle.status = "moving"
            
            # Solo mover si el vehículo no está destruido y la posición cambió
            if getattr(vehicle, "status", None) != "destroyed" and (new_row, new_col) != current_pos:
                try:
                    tick = self.get_current_tick()
                    mine_manager = self.get_mine_manager()
                    
                    if hasattr(self.map, "graph") and callable(getattr(self.map.graph, "place_vehicle", None)):
                        result = self.map.graph.place_vehicle(
                            vehicle, new_row, new_col, 
                            tick=tick, 
                            mine_manager=mine_manager, 
                            player1=player, 
                            player2=self.enemy_player
                        )
                except Exception as e:
                    print(f"[ERROR {vehicle_id}] Error al mover: {e}")
                    pass
