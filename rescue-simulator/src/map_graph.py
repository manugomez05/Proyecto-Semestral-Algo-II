from src.node import Node
from mines_manager import MineManager
from mines import MineType
from resources import generate_resources

class MapGraph:
    def __init__(self,rows,cols):
        self.rows = rows
        self.cols = cols
        self.grid = [] #matriz de nodos

        self.generate_nodes()
        self.connect_neighbors()

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
        
        #Marcar nodos con recursos
        for res in resources:
            r,c = res.position
            self.set_node_state(r,c, "resource", {
                "subtype": res.tipo,
                "points": res.puntos,
                "img": res.img_path
            })
