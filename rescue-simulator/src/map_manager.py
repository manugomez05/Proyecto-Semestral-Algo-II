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
        occupied = set()

        # Generar bases primero
        self.generate_bases()
        
        # Generar minas usando MineManager
        self.generate_mines_with_manager()
        
        # Generar recursos evitando las minas (usar tick=0 para generación inicial)
        self.resources = generate_resources(self.cols, self.rows, occupied_positions=occupied, mine_manager=self.mine_manager, tick=0)
        for res in self.resources:
            x, y = res.position
            self.graph.set_node_state(y, x, "resource", res)

    def generate_mines_with_manager(self):
        """Genera minas usando el MineManager con diferentes tipos"""
        # Especificación de minas: tipo -> cantidad
        mine_spec = {
            MineType.O1: 2,  # 2 minas circulares grandes
            MineType.O2: 3,   # 3 minas circulares pequeñas
            MineType.T1: 2,   # 2 bandas horizontales
            MineType.T2: 2,   # 2 bandas verticales
            MineType.G1: 1    # 1 mina dinámica
        }
        
        # Generar todas las minas
        self.mine_manager.addRandomSet(
            rows=self.rows, 
            cols=self.cols, 
            spec=mine_spec, 
            margin=2,  # Margen de seguridad
            map_graph=self.graph
        )

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

    def generate_bases(self):
        """Ubica las bases de los dos jugadores en extremos opuestos."""
        """

        Implementacion vieja

        base1 = self.graph.get_node(0, 0)
        base2 = self.graph.get_node(self.rows - 1, self.cols - 1)
        base1.state = "base_p1"
        base2.state = "base_p2"
        self.bases = [base1, base2]
        """

        """
        Genera las posiciones iniciales de las bases de ambos jugadores.
        """
        self.base_positions = {
            "player1": self.graph.get_node(0, 0),
            "player2": self.graph.get_node(self.rows - 1, self.cols - 1)
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