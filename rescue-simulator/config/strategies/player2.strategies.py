"""
Estrategia del Equipo 2: Dijkstra
- Recolectores: Dijkstra hacia recursos de mayor valor, evitando minas (costo muy alto)
- Motos: Atacar camiones enemigos con Dijkstra, si no hay camiones, recoger recursos con Dijkstra
"""

import heapq
from typing import List, Tuple, Optional
from src.vehicle import Vehicle


class Strategy2:
    """
    Estrategia 2: Dijkstra
    - Motos: destruir camiones enemigos usando Dijkstra
    - Resto de vehículos: Dijkstra hacia recursos de mayor valor, evitando minas
    """
    
    def __init__(self, map_width, map_height, map, enemy_player=None):
        self.map_width = map_width
        self.map_height = map_height
        self.map = map
        self.enemy_player = enemy_player
        self.MINE_COST = 10000
    
    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calcula la distancia Manhattan"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def is_position_safe(self, row: int, col: int) -> bool:
        """Verifica si una posición está segura (no minada y dentro de límites)"""
        if not (0 <= row < self.map.rows and 0 <= col < self.map.cols):
            return False
        
        mine_manager = getattr(self.map, "mine_manager", None)
        tick = getattr(self.map, "current_tick", 0)
        
        if mine_manager:
            return not mine_manager.isCellMined((row, col), tick)
        
        return True
    
    def get_cell_cost(self, row: int, col: int) -> float:
        """Obtiene el costo de moverse a una celda. Las minas tienen costo muy alto"""
        if not self.is_position_safe(row, col):
            return self.MINE_COST
        return 1.0
    
    def dijkstra_shortest_path(self, start: Tuple[int, int], target: Tuple[int, int], player, vehicle_id: str) -> Optional[List[Tuple[int, int]]]:
        """Dijkstra para encontrar el camino de menor costo"""
        pq = [(0, start)]
        distances = {start: 0}
        previous = {start: None}
        visited = set()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        while pq:
            current_cost, current_pos = heapq.heappop(pq)
            
            if current_pos in visited:
                continue
            
            visited.add(current_pos)
            
            if current_pos == target:
                path = []
                node = target
                while node is not None:
                    path.append(node)
                    node = previous.get(node)
                path.reverse()
                return path
            
            row, col = current_pos
            
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                
                if not (0 <= new_row < self.map.rows and 0 <= new_col < self.map.cols):
                    continue
                
                neighbor = (new_row, new_col)
                
                if neighbor in visited:
                    continue
                
                if self.is_occupied_by_teammate(new_row, new_col, player, vehicle_id):
                    continue
                
                cell_cost = self.get_cell_cost(new_row, new_col)
                new_cost = current_cost + cell_cost
                
                if neighbor not in distances or new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    previous[neighbor] = current_pos
                    heapq.heappush(pq, (new_cost, neighbor))
        
        return None
    
    def find_enemy_trucks(self, player) -> List[Tuple[int, int]]:
        """Encuentra todos los camiones enemigos en el mapa"""
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
    
    def find_best_resource(self, vehicle, resources: List, player) -> Optional[Tuple[object, Tuple[int, int]]]:
        """Encuentra el mejor recurso: mayor valor, en empate menor costo"""
        if not resources:
            return None
        
        vehicle_pos = vehicle.position
        vehicle_id = getattr(vehicle, "id", None)
        best_resource = None
        best_pos = None
        best_value = -1
        best_cost = float('inf')
        
        for resource in resources:
            if hasattr(resource, "position"):
                res_pos = resource.position
            elif isinstance(resource, dict):
                res_pos = resource.get("position")
            else:
                continue
            
            if not res_pos or len(res_pos) != 2:
                continue
            
            res_x, res_y = res_pos[0], res_pos[1]
            res_row, res_col = res_y, res_x
            
            node = self.map.graph.get_node(res_row, res_col)
            if not node or node.state != "resource":
                continue
            
            if hasattr(resource, "puntos"):
                value = resource.puntos
            elif isinstance(resource, dict):
                value = resource.get("puntos", resource.get("value", 1))
            else:
                value = 1
            
            if hasattr(resource, "tipo"):
                res_type = resource.tipo
            elif isinstance(resource, dict):
                res_type = resource.get("tipo", resource.get("subtype"))
            else:
                res_type = None
            
            if res_type and hasattr(vehicle, "can_pick") and not vehicle.can_pick(res_type):
                continue
            
            # Calcular camino usando Dijkstra
            path = self.dijkstra_shortest_path(vehicle_pos, (res_row, res_col), player, vehicle_id)
            
            if path:
                total_cost = 0
                for i in range(len(path) - 1):
                    r, c = path[i + 1]
                    total_cost += self.get_cell_cost(r, c)
                
                if value > best_value or (value == best_value and total_cost < best_cost):
                    best_value = value
                    best_cost = total_cost
                    best_resource = resource
                    best_pos = (res_row, res_col)
        
        if best_resource and best_pos:
            return (best_resource, best_pos)
        
        return None
    
    def is_occupied_by_teammate(self, row: int, col: int, player, vehicle_id: str) -> bool:
        """Verifica si una posición está ocupada por un vehículo del mismo equipo"""
        node = self.map.graph.get_node(row, col)
        if not node or not node.content:
            return False
        
        if node.state == "vehicle" or node.state in ("base_p1", "base_p2"):
            vehicle_content = node.content
            existing_vehicle_id = None
            
            if isinstance(vehicle_content, dict):
                existing_vehicle_id = vehicle_content.get("id")
            else:
                existing_vehicle_id = getattr(vehicle_content, "id", None)
            
            if existing_vehicle_id and existing_vehicle_id != vehicle_id:
                if hasattr(player, "vehicles") and existing_vehicle_id in player.vehicles:
                    existing_vehicle_obj = vehicle_content.get("object") if isinstance(vehicle_content, dict) else vehicle_content
                    if existing_vehicle_obj and getattr(existing_vehicle_obj, "status", None) != "destroyed":
                        return True
        
        return False
    
    def get_next_move(self, vehicle, target_pos: Tuple[int, int], player) -> Tuple[int, int]:
        """Obtiene el siguiente movimiento hacia el objetivo usando Dijkstra"""
        vehicle_pos = vehicle.position
        vehicle_id = getattr(vehicle, "id", None)
        
        path = self.dijkstra_shortest_path(vehicle_pos, target_pos, player, vehicle_id)
        
        if path and len(path) > 1:
            next_pos = path[1]
            if not self.is_occupied_by_teammate(next_pos[0], next_pos[1], player, vehicle_id):
                return next_pos
        
        # Si no hay path, intentar movimiento directo
        row, col = vehicle_pos
        target_row, target_col = target_pos
        
        dr = 0 if target_row == row else (1 if target_row > row else -1)
        dc = 0 if target_col == col else (1 if target_col > col else -1)
        
        new_row = row + dr
        new_col = col + dc
        
        if self.is_position_safe(new_row, new_col) and not self.is_occupied_by_teammate(new_row, new_col, player, vehicle_id):
            return (new_row, new_col)
        
        # Intentar alternativas
        for alt_dr, alt_dc in [(dr, 0), (0, dc), (1, 0), (-1, 0), (0, 1), (0, -1)]:
            alt_row = row + alt_dr
            alt_col = col + alt_dc
            if self.is_position_safe(alt_row, alt_col) and not self.is_occupied_by_teammate(alt_row, alt_col, player, vehicle_id):
                return (alt_row, alt_col)
        
        return (row, col)
    
    def get_random_safe_move(self, vehicle, player) -> Tuple[int, int]:
        """Obtiene un movimiento aleatorio seguro"""
        row, col = vehicle.position
        vehicle_id = getattr(vehicle, "id", None)
        import random
        
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(directions)
        
        for dr, dc in directions:
            new_row = row + dr
            new_col = col + dc
            
            if self.is_position_safe(new_row, new_col) and not self.is_occupied_by_teammate(new_row, new_col, player, vehicle_id):
                return (new_row, new_col)
        
        return (row, col)
    
    def move_towards_base(self, vehicle, player) -> Tuple[int, int]:
        """Mueve hacia la base del vehículo"""
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
        
        return self.get_next_move(vehicle, (base_row, base_col), player)
    
    def update(self, player):
        """Actualiza las posiciones de todos los vehículos"""
        if not hasattr(player, "vehicles") or not player.vehicles:
            return
        
        vehicles = player.vehicles
        resources = self.map.all_resources()
        enemy_trucks = self.find_enemy_trucks(player)
        
        for vehicle_id, vehicle in vehicles.items():
            if getattr(vehicle, "status", None) == "destroyed":
                continue
            
            vehicle_type = getattr(vehicle, "type", None)
            row, col = vehicle.position
            new_row, new_col = row, col
            
            # Si debe volver a la base
            if getattr(vehicle, "status", None) == "need_return":
                new_row, new_col = self.move_towards_base(vehicle, player)
                
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
                
                if new_row == base_row and new_col == base_col:
                    collected = getattr(vehicle, "collected_value", 0)
                    if hasattr(player, "score"):
                        player.score += collected
                    vehicle.arrive_base()
                    vehicle.status = "moving"
            
            # Si está en la base, salir
            if getattr(vehicle, "status", None) == "in_base":
                vehicle.status = "moving"
            
            # Si no está en need_return, buscar objetivos
            if getattr(vehicle, "status", None) != "need_return":
                if vehicle_type == "moto":
                    # Motos: buscar camiones enemigos primero
                    if enemy_trucks:
                        # Encontrar el más cercano
                        closest_truck = None
                        min_cost = float('inf')
                        for truck_pos in enemy_trucks:
                            path = self.dijkstra_shortest_path(vehicle.position, truck_pos, player, getattr(vehicle, "id", None))
                            if path:
                                total_cost = 0
                                for i in range(len(path) - 1):
                                    r, c = path[i + 1]
                                    total_cost += self.get_cell_cost(r, c)
                                if total_cost < min_cost:
                                    min_cost = total_cost
                                    closest_truck = truck_pos
                        
                        if closest_truck:
                            new_row, new_col = self.get_next_move(vehicle, closest_truck, player)
                    
                    # Si no hay camiones o no se movió, buscar recursos
                    if new_row == row and new_col == col:
                        best_resource = self.find_best_resource(vehicle, resources, player)
                        if best_resource:
                            _, res_pos = best_resource
                            new_row, new_col = self.get_next_move(vehicle, res_pos, player)
                        else:
                            # Si no hay recursos, moverse aleatoriamente
                            new_row, new_col = self.get_random_safe_move(vehicle, player)
                else:
                    # Resto: buscar recursos
                    best_resource = self.find_best_resource(vehicle, resources, player)
                    if best_resource:
                        _, res_pos = best_resource
                        new_row, new_col = self.get_next_move(vehicle, res_pos, player)
                    else:
                        # Si no hay recursos, moverse aleatoriamente
                        new_row, new_col = self.get_random_safe_move(vehicle, player)
            
            # Mover el vehículo
            try:
                tick = getattr(self.map, "current_tick", None)
                mine_manager = getattr(self.map, "mine_manager", None)
                
                if hasattr(self.map, "graph") and callable(getattr(self.map.graph, "place_vehicle", None)):
                    self.map.graph.place_vehicle(vehicle, new_row, new_col, tick=tick, mine_manager=mine_manager, player1=self.enemy_player, player2=player)
            except Exception:
                pass
