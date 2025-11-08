# Estrategia comentada anterior (mantener para referencia)
# ... código comentado anterior ...

import heapq
from typing import List, Tuple, Optional, Dict
from src.vehicle import Vehicle


class Strategy1:
    """
    Estrategia 1: Greedy
    - Motos: destruir camiones enemigos
    - Resto de vehículos: Greedy por valor (valor/distancia)
    """
    
    def __init__(self, map_width, map_height, map, enemy_player=None):
        self.map_width = map_width
        self.map_height = map_height
        self.map = map
        self.enemy_player = enemy_player
    
    def is_position_safe(self, row: int, col: int) -> bool:
        """Verifica si una posición está segura (no minada y dentro de límites)"""
        max_row = self.map.rows - 1 if hasattr(self.map, "rows") else (self.map_height - 1)
        max_col = self.map.cols - 1 if hasattr(self.map, "cols") else (self.map_width - 1)
        
        if not (0 <= row <= max_row and 0 <= col <= max_col):
            return False
        
        mine_manager = getattr(self.map, "mine_manager", None)
        tick = getattr(self.map, "current_tick", 0)
        
        if mine_manager:
            return not mine_manager.isCellMined((row, col), tick)
        
        return True
    
    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calcula la distancia Manhattan"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def find_enemy_trucks(self, player) -> List[Tuple[Tuple[int, int]]]:
        """
        Encuentra todos los camiones enemigos en el mapa.
        Retorna lista de posiciones (row, col) de camiones enemigos
        """
        enemy_trucks = []
        if not self.enemy_player:
            return enemy_trucks
        
        # Obtener IDs de vehículos del jugador actual
        current_player_ids = set()
        if hasattr(player, "vehicles"):
            vehicles = player.vehicles
            if isinstance(vehicles, dict):
                current_player_ids = set(vehicles.keys())
            else:
                current_player_ids = {getattr(v, "id", None) for v in vehicles if hasattr(v, "id")}
        
        # Buscar en el grafo vehículos enemigos que sean camiones
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
                    
                    # Si el vehículo no es del jugador actual y es un camión
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
    
    def find_best_resource_greedy(self, vehicle, resources: List) -> Optional[Tuple[object, Tuple[int, int]]]:
        """
        Encuentra el mejor recurso usando Greedy por valor.
        Score = valor / (distancia + 1)
        """
        if not resources:
            return None
        
        vehicle_pos = vehicle.position
        best_resource = None
        best_score = -1
        
        for resource in resources:
            # Obtener posición del recurso
            if hasattr(resource, "position"):
                res_pos = resource.position
            elif isinstance(resource, dict):
                res_pos = resource.get("position")
            else:
                continue
            
            if not res_pos or len(res_pos) != 2:
                continue
            
            # Convertir (x, y) a (row, col)
            res_x, res_y = res_pos[0], res_pos[1]
            res_row, res_col = res_y, res_x
            
            # Verificar que el recurso aún existe
            node = self.map.graph.get_node(res_row, res_col)
            if not node or node.state != "resource":
                continue
            
            # Obtener valor
            if hasattr(resource, "puntos"):
                value = resource.puntos
            elif isinstance(resource, dict):
                value = resource.get("puntos", resource.get("value", 1))
            else:
                value = 1
            
            # Obtener tipo
            if hasattr(resource, "tipo"):
                res_type = resource.tipo
            elif isinstance(resource, dict):
                res_type = resource.get("tipo", resource.get("subtype"))
            else:
                res_type = None
            
            # Verificar que el vehículo puede recoger este tipo
            if res_type and hasattr(vehicle, "can_pick") and not vehicle.can_pick(res_type):
                continue
            
            # Calcular distancia
            distance = self.manhattan_distance(vehicle_pos, (res_row, res_col))
            
            # Score: valor / (distancia + 1)
            score = value / (distance + 1)
            
            if score > best_score:
                best_score = score
                best_resource = (resource, (res_row, res_col))
        
        return best_resource
    
    def is_occupied_by_teammate(self, row: int, col: int, player, vehicle_id: str) -> bool:
        """Verifica si una posición está ocupada por un vehículo del mismo equipo"""
        if not player:
            return False
        
        node = self.map.graph.get_node(row, col)
        if not node or not node.content:
            return False
        
        # Verificar si hay un vehículo en esa posición
        if node.state == "vehicle" or node.state in ("base_p1", "base_p2"):
            vehicle_content = node.content
            existing_vehicle_id = None
            existing_vehicle_obj = None
            
            if isinstance(vehicle_content, dict):
                existing_vehicle_id = vehicle_content.get("id")
                existing_vehicle_obj = vehicle_content.get("object")
            else:
                existing_vehicle_id = getattr(vehicle_content, "id", None)
                existing_vehicle_obj = vehicle_content
            
            # Si es un vehículo diferente del mismo equipo
            if existing_vehicle_id and existing_vehicle_id != vehicle_id:
                # Verificar si pertenece al mismo equipo y no está destruido
                if existing_vehicle_obj:
                    status = getattr(existing_vehicle_obj, "status", None)
                    if status == "destroyed":
                        return False  # Vehículo destruido no cuenta como ocupado
                
                if hasattr(player, "vehicles"):
                    vehicles = player.vehicles
                    if isinstance(vehicles, dict):
                        return existing_vehicle_id in vehicles
                    else:
                        return any(getattr(v, "id", None) == existing_vehicle_id for v in vehicles if hasattr(v, "id"))
        
        return False
    
    def _get_random_safe_move(self, vehicle, player) -> Tuple[int, int]:
        """Obtiene un movimiento aleatorio seguro (evita minas y compañeros)"""
        row, col = vehicle.position
        vehicle_id = getattr(vehicle, "id", None)
        import random
        
        # Intentar todas las direcciones posibles en orden aleatorio
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        random.shuffle(directions)
        
        for dr, dc in directions:
            new_row = row + dr
            new_col = col + dc
            
            if self.is_position_safe(new_row, new_col) and not self.is_occupied_by_teammate(new_row, new_col, player, vehicle_id):
                return (new_row, new_col)
        
        # Si ninguna dirección es válida, quedarse (último recurso)
        return (row, col)
    
    def move_towards_target(self, vehicle, target_pos: Tuple[int, int], player=None) -> Tuple[int, int]:
        """
        Calcula el siguiente movimiento hacia el objetivo, evitando minas y vehículos del mismo equipo.
        """
        row, col = vehicle.position
        target_row, target_col = target_pos
        vehicle_id = getattr(vehicle, "id", None)
        
        # Calcular dirección ideal
        dr = 0 if target_row == row else (1 if target_row > row else -1)
        dc = 0 if target_col == col else (1 if target_col > col else -1)
        
        # Intentar movimiento directo
        new_row = row + dr
        new_col = col + dc
        
        if self.is_position_safe(new_row, new_col) and not self.is_occupied_by_teammate(new_row, new_col, player, vehicle_id):
            return (new_row, new_col)
        
        # Si está bloqueada, intentar alternativas
        alternatives = [
            (dr, 0),  # Solo fila
            (0, dc),  # Solo columna
            (-dr if dr != 0 else 0, dc),  # Fila opuesta
            (dr, -dc if dc != 0 else 0),  # Columna opuesta
            (1, 0), (-1, 0), (0, 1), (0, -1),  # Cualquier dirección válida
        ]
        
        for alt_dr, alt_dc in alternatives:
            alt_row = row + alt_dr
            alt_col = col + alt_dc
            if self.is_position_safe(alt_row, alt_col) and not self.is_occupied_by_teammate(alt_row, alt_col, player, vehicle_id):
                return (alt_row, alt_col)
        
        # Si ninguna es segura, quedarse (último recurso)
        return (row, col)
    
    def move_towards_base(self, vehicle, player) -> Tuple[int, int]:
        """Mueve hacia la posición específica de base del vehículo"""
        # Usar la posición específica de base del vehículo
        if hasattr(vehicle, "base_position") and vehicle.base_position:
            base_row, base_col = vehicle.base_position
        else:
            # Fallback: usar posición general de la base del jugador
            base_pos = player.base_position
            if isinstance(base_pos, tuple) and len(base_pos) == 2:
                base_row, base_col = base_pos
            elif hasattr(base_pos, "row") and hasattr(base_pos, "col"):
                base_row, base_col = base_pos.row, base_pos.col
            else:
                base_row, base_col = 0, 0
        
        return self.move_towards_target(vehicle, (base_row, base_col), player)
    
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
            
            # Si debe volver a la base
            if getattr(vehicle, "status", None) == "need_return":
                new_row, new_col = self.move_towards_base(vehicle, player)
                
                # Verificar si llegó a su posición específica de base
                if hasattr(vehicle, "base_position") and vehicle.base_position:
                    base_row, base_col = vehicle.base_position
                else:
                    # Fallback
                    base_pos = player.base_position
                    if isinstance(base_pos, tuple) and len(base_pos) == 2:
                        base_row, base_col = base_pos
                    elif hasattr(base_pos, "row") and hasattr(base_pos, "col"):
                        base_row, base_col = base_pos.row, base_pos.col
                    else:
                        base_row, base_col = 0, 0
                
                if new_row == base_row and new_col == base_col:
                    # Llegó a la base
                    collected = getattr(vehicle, "collected_value", 0)
                    if hasattr(player, "score"):
                        player.score += collected
                    else:
                        player.score = collected
                    vehicle.arrive_base()
            else:
                # Estrategia según tipo
                if vehicle_type == "moto":
                    # Motos: buscar camiones enemigos primero
                    closest_truck = None
                    if enemy_trucks:
                        # Encontrar el camión más cercano
                        min_distance = float('inf')
                        vehicle_pos = vehicle.position
                        
                        for truck_pos in enemy_trucks:
                            distance = self.manhattan_distance(vehicle_pos, truck_pos)
                            if distance < min_distance:
                                min_distance = distance
                                closest_truck = truck_pos
                    
                    # Si hay un camión válido, ir hacia él
                    if closest_truck:
                        new_row, new_col = self.move_towards_target(vehicle, closest_truck, player)
                        # Si no se movió (está en la misma posición), buscar recursos
                        if new_row == row and new_col == col:
                            best_resource = self.find_best_resource_greedy(vehicle, resources)
                            if best_resource:
                                _, res_pos = best_resource
                                new_row, new_col = self.move_towards_target(vehicle, res_pos, player)
                    else:
                        # No hay camiones válidos, usar Greedy para recursos
                        best_resource = self.find_best_resource_greedy(vehicle, resources)
                        if best_resource:
                            _, res_pos = best_resource
                            new_row, new_col = self.move_towards_target(vehicle, res_pos, player)
                        else:
                            # Si no hay recursos, moverse aleatoriamente
                            new_row, new_col = self._get_random_safe_move(vehicle, player)
                else:
                    # Resto: Greedy por valor
                    best_resource = self.find_best_resource_greedy(vehicle, resources)
                    if best_resource:
                        _, res_pos = best_resource
                        new_row, new_col = self.move_towards_target(vehicle, res_pos, player)
                        # Si no se movió, intentar movimiento aleatorio
                        if new_row == row and new_col == col:
                            new_row, new_col = self._get_random_safe_move(vehicle, player)
                    else:
                        # Si no hay recursos, moverse aleatoriamente
                        new_row, new_col = self._get_random_safe_move(vehicle, player)
            
            # Mover el vehículo
            placed = False
            try:
                tick = getattr(self.map, "current_tick", None)
                mine_manager = getattr(self.map, "mine_manager", None)
                
                if hasattr(self.map, "graph") and callable(getattr(self.map.graph, "place_vehicle", None)):
                    placed = self.map.graph.place_vehicle(vehicle, new_row, new_col, tick=tick, mine_manager=mine_manager, player1=player, player2=self.enemy_player)
                elif callable(getattr(self.map, "place_vehicle", None)):
                    placed = self.map.place_vehicle(vehicle, new_row, new_col, tick=tick, mine_manager=mine_manager, player1=player, player2=self.enemy_player)
            except Exception as e:
                placed = False
            
            # Si el movimiento falló o el vehículo no se movió, intentar alternativas
            if not placed or (new_row == row and new_col == col):
                # Si no se movió, obtener un movimiento alternativo seguro
                if new_row == row and new_col == col:
                    alt_row, alt_col = self._get_random_safe_move(vehicle, player)
                    if alt_row != row or alt_col != col:
                        new_row, new_col = alt_row, alt_col
                
                # Intentar moverse en direcciones alternativas
                alternatives = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
                found_alternative = False
                
                for dr, dc in alternatives:
                    alt_row = row + dr
                    alt_col = col + dc
                    
                    if self.is_position_safe(alt_row, alt_col) and not self.is_occupied_by_teammate(alt_row, alt_col, player, getattr(vehicle, "id", None)):
                        try:
                            if hasattr(self.map, "graph") and callable(getattr(self.map.graph, "place_vehicle", None)):
                                placed = self.map.graph.place_vehicle(vehicle, alt_row, alt_col, tick=tick, mine_manager=mine_manager, player1=player, player2=self.enemy_player)
                            elif callable(getattr(self.map, "place_vehicle", None)):
                                placed = self.map.place_vehicle(vehicle, alt_row, alt_col, tick=tick, mine_manager=mine_manager, player1=player, player2=self.enemy_player)
                            
                            if placed:
                                found_alternative = True
                                break
                        except Exception:
                            continue
                
                # Si aún no se pudo mover, actualizar posición directamente (fallback)
                if not found_alternative:
                    if hasattr(vehicle, "move_to"):
                        vehicle.move_to(new_row, new_col)
                    else:
                        vehicle.position = (new_row, new_col)
                        if hasattr(vehicle, "start_trip"):
                            vehicle.start_trip()
                        else:
                            if getattr(vehicle, "capacity", 0) <= 0:
                                vehicle.status = "need_return"
                            else:
                                vehicle.status = "moving"


# Alias para compatibilidad
BasicMoveStrategy = Strategy1
