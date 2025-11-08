"""
Módulo: map_manager
-------------------------------------------------
Administra el mapa general del simulador, coordinando el grafo 
de nodos, los recursos, las minas y las bases.

Responsabilidades:
- Crear y mantener el grafo del mapa (`MapGraph`).
- Distribuir aleatoriamente los recursos (personas y mercancías).
- Colocar las minas y bases en posiciones válidas.
- Proveer acceso a nodos, recursos, minas y bases para otros módulos.
"""



import random
from src.map_graph import MapGraph
from src.resources import generate_resources
from src.mines_manager import MineManager
from src.mines import MineType

class MapManager:
    """
    Clase encargada de administrar el mapa del simulador:
    - Grafo de nodos
    - Recursos (personas, mercancías)
    - Minas y bases
    """

    def __init__(self, rows=50, cols=50):
        self.rows = rows
        self.cols = cols
        self.graph = MapGraph(rows, cols)
        self.resources = []
        self.mine_manager = MineManager()  # Usar el MineManager
        self.bases = []
        self.current_tick = 0  # Tick actual para verificación de minas
        
    def __getstate__(self):
        """Método especial para pickle - asegura que el objeto puede ser serializado"""
        return self.__dict__.copy()

    def __setstate__(self, state):
        """Método especial para pickle - restaura el objeto al ser deserializado"""
        self.__dict__.update(state)

    # --------------------------------------------------
    # GENERACIÓN DE ELEMENTOS
    # --------------------------------------------------

    def generate_random_map(self):
        """Distribuye recursos y minas aleatoriamente en el mapa."""
        # Generar bases primero
        self.generate_bases()
        
        # Obtener posiciones de las bases para excluirlas
        base_positions = self.get_base_positions_set()
        
        # Generar minas usando MineManager (excluyendo bases)
        self.generate_mines_with_manager(base_positions)
        
        # Generar recursos evitando las minas y las bases (usar tick=0 para generación inicial)
        # Convertir base_positions de (row, col) a (x, y) para generate_resources
        occupied_for_resources = {(col, row) for row, col in base_positions}
        self.resources = generate_resources(self.cols, self.rows, occupied_positions=occupied_for_resources, mine_manager=self.mine_manager, tick=0)
        for res in self.resources:
            x, y = res.position
            self.graph.set_node_state(y, x, "resource", res)

    def generate_mines_with_manager(self, excluded_positions=None):
        """
        Genera minas usando el MineManager con diferentes tipos.
        Excluye las posiciones proporcionadas (típicamente las bases).
        
        Args:
            excluded_positions: Set de tuplas (row, col) que deben ser excluidas
        """
        if excluded_positions is None:
            excluded_positions = set()
        
        # Especificación de minas: tipo -> cantidad
        mine_spec = {
            MineType.O1: 2,  # 2 minas circulares grandes
            MineType.O2: 3,   # 3 minas circulares pequeñas
            MineType.T1: 2,   # 2 bandas horizontales
            MineType.T2: 2,   # 2 bandas verticales
            MineType.G1: 1    # 1 mina dinámica
        }
        
        # Generar todas las minas, excluyendo las posiciones de las bases
        for mine_type, count in mine_spec.items():
            for _ in range(count):
                self._add_mine_excluding_positions(mine_type, excluded_positions)
    
    def _add_mine_excluding_positions(self, mine_type, excluded_positions, max_attempts=200):
        """
        Intenta agregar una mina del tipo especificado, excluyendo las posiciones dadas.
        
        Args:
            mine_type: Tipo de mina a crear
            excluded_positions: Set de tuplas (row, col) a excluir
            max_attempts: Número máximo de intentos
        """
        from src.mines import MINE_PARAMS
        
        params = MINE_PARAMS[mine_type]
        radius = params.get("radius", 0)
        half_width = params.get("half_width", 0)
        margin = 2
        
        # Calcular rangos seguros según el tipo de mina
        if mine_type in (MineType.O1, MineType.O2, MineType.G1):  # Círculos
            min_row = radius + margin
            max_row = self.rows - 1 - (radius + margin)
            min_col = radius + margin
            max_col = self.cols - 1 - (radius + margin)
        elif mine_type == MineType.T1:  # Banda horizontal
            min_row = half_width + margin
            max_row = self.rows - 1 - (half_width + margin)
            min_col = 0 + margin
            max_col = self.cols - 1 - margin
        elif mine_type == MineType.T2:  # Banda vertical
            min_row = 0 + margin
            max_row = self.rows - 1 - margin
            min_col = half_width + margin
            max_col = self.cols - 1 - (half_width + margin)
        else:
            min_row = margin
            max_row = self.rows - 1 - margin
            min_col = margin
            max_col = self.cols - 1 - margin
        
        # Asegurar rangos válidos
        min_row = max(0, min_row)
        min_col = max(0, min_col)
        max_row = max(min_row, max_row)
        max_col = max(min_col, max_col)
        
        # Intentar encontrar una posición válida
        for attempt in range(max_attempts):
            row = random.randint(min_row, max_row)
            col = random.randint(min_col, max_col)
            
            # Verificar que la posición central no esté excluida
            if (row, col) in excluded_positions:
                continue
            
            # Verificar que ninguna celda afectada por la mina esté en las bases
            # Para círculos, verificar todas las celdas en el radio
            if mine_type in (MineType.O1, MineType.O2, MineType.G1):  # Círculos
                safe = True
                for dr in range(-radius, radius + 1):
                    for dc in range(-radius, radius + 1):
                        if dr*dr + dc*dc <= radius*radius:
                            check_row, check_col = row + dr, col + dc
                            if (check_row, check_col) in excluded_positions:
                                safe = False
                                break
                    if not safe:
                        break
                if not safe:
                    continue
            elif mine_type == MineType.T1:  # Banda horizontal
                safe = True
                for r in range(row - half_width, row + half_width + 1):
                    if (r, col) in excluded_positions:
                        safe = False
                        break
                if not safe:
                    continue
            elif mine_type == MineType.T2:  # Banda vertical
                safe = True
                for c in range(col - half_width, col + half_width + 1):
                    if (row, c) in excluded_positions:
                        safe = False
                        break
                if not safe:
                    continue
            
            # Si llegamos aquí, la posición es segura de las bases
            # Ahora verificar que no se superponga con otras minas existentes
            from src.mines import Mine
            temp_mine = Mine(
                id=0,  # ID temporal
                type=mine_type,
                center=(row, col),
                radius=radius,
                half_width=half_width,
                period=params.get("period", 0),
                static=params.get("static", True),
                active=True,
                next_activation=params.get("period", 0)
            )
            
            # Verificar superposición con minas existentes
            if self.mine_manager._would_overlap_any(temp_mine):
                continue
            
            # Si no hay superposición, agregar la mina
            try:
                mine = self.mine_manager.addMine(mine_type, (row, col))
                return mine
            except Exception as e:
                continue
        
        # Si no se encontró posición válida después de max_attempts, lanzar error
        raise RuntimeError(f"No se pudo encontrar una posición válida para la mina {mine_type} después de {max_attempts} intentos (excluyendo bases)")

    def generate_mines(self, count, occupied_positions):
        """Genera minas aleatoriamente en el mapa."""
        for _ in range(count):
            while True:
                x = random.randint(0, self.cols - 1)
                y = random.randint(0, self.rows - 1)
                if (x, y) not in occupied_positions:
                    occupied_positions.add((x, y))
                    self.graph.set_node_state(y, x, "mine", {"tipo": "mina"})
                    self.mines.append((x, y))
                    break

    def get_base_positions_set(self):
        """
        Calcula y devuelve un conjunto con todas las posiciones (row, col) que pertenecen a las bases.
        Las bases son de 20x2, centradas verticalmente en ambos lados del mapa.
        """
        base_positions = set()
        base_width = 2  # Ancho de la base (2 columnas)
        base_height = 20  # Alto de la base (20 filas)
        
        # Calcular posición vertical centrada
        start_row = (self.rows - base_height) // 2
        end_row = start_row + base_height
        
        # Base izquierda: columnas 0 y 1
        for row in range(start_row, end_row):
            for col in range(base_width):
                base_positions.add((row, col))
        
        # Base derecha: columnas cols-2 y cols-1
        for row in range(start_row, end_row):
            for col in range(self.cols - base_width, self.cols):
                base_positions.add((row, col))
        
        return base_positions

    def generate_bases(self):
        """
        Genera las bases de 20x2 en ambos lados del mapa, centradas verticalmente.
        Marca los nodos como bases en el grafo.
        """
        base_positions = self.get_base_positions_set()
        
        # Marcar todos los nodos de las bases en el grafo
        for row, col in base_positions:
            node = self.graph.get_node(row, col)
            if node:
                # Determinar si es base izquierda o derecha
                if col < 2:
                    node.state = "base_p1"
                else:
                    node.state = "base_p2"
        
        # Guardar posiciones para referencia (punto central de cada base)
        base_height = 20
        start_row = (self.rows - base_height) // 2
        center_row = start_row + base_height // 2
        
        self.base_positions = {
            "player1": self.graph.get_node(center_row, 0),  # Centro de base izquierda
            "player2": self.graph.get_node(center_row, self.cols - 1)  # Centro de base derecha
        }
        
        return self.base_positions

    # --------------------------------------------------
    # FUNCIONES DE CONSULTA
    # --------------------------------------------------

    def get_node(self, row, col):
        """Devuelve un nodo del grafo."""
        return self.graph.get_node(row, col)

    def get_resources(self):
        """Devuelve la lista de recursos activos en el mapa."""
        return [r for r in self.resources if r]

    def get_mines(self):
        """Devuelve todas las minas."""
        return self.mine_manager.all()

    def get_bases(self):
        """Devuelve las bases de los jugadores."""
        return self.bases

    def all_resources(self):
        """
        Wrapper que devuelve la lista de recursos desde el grafo interno.
        """
        if hasattr(self, "graph") and callable(getattr(self.graph, "all_resources", None)):
            return self.graph.all_resources()
        if hasattr(self, "map_graph") and callable(getattr(self.map_graph, "all_resources", None)):
            return self.map_graph.all_resources()
        # fallback: si MapManager guarda resources directamente
        if hasattr(self, "resources"):
            try:
                return list(self.resources)
            except Exception:
                return []
        return []

    # --------------------------------------------------
    # FUNCIONES DE MODIFICACIÓN
    # --------------------------------------------------

    def clear_map(self):
        """Limpia el mapa para reiniciar la simulación."""
        self.graph = MapGraph(self.rows, self.cols)
        self.resources.clear()
        self.mine_manager = MineManager()  # Reiniciar el MineManager
        self.bases.clear()
        self.current_tick = 0  # Reiniciar el tick