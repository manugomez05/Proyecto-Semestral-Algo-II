"""
Módulo: node
En el simulador, cada celda de la cuadrícula va a ser un nodo. Cada nodo representa una posición en el mapa y puede tener:
-------------------------------------------------
Define la clase `Node`, que representa una celda individual 
del grafo del mapa.

Cada nodo almacena información sobre su posición, estado 
y contenido (recurso, mina, base, etc).

"""
class Node:
    def __init__(self, row, col, state="empty", content=None):
        self.row = row
        self.col = col
        self.state = state
        self.content = content if content else {}
        self.neighbors = []
    def add_neighbor(self, neighbor_node):
        """
        Añade un nodo vecino a la lista de vecinos.
        """
        self.neighbors.append(neighbor_node)
    def is_empty(self):
        """
        Verifica si el nodo está vacío.
        """
        return self.state == "empty"
    def is_mine(self):
        """
        Verifica si el nodo contiene una mina.
        """
        return self.state == "mine"
    def is_resource(self):
        """
        Verifica si el nodo contiene un recurso.
        """
        return self.state == "resource"
    def is_vehicle(self):
        """
        Verifica si el nodo contiene un vehículo.
        """
        return self.state == "vehicle"
    def has_person(self):
        """
        Verifica si el contenido del nodo incluye una persona.
        """
        if self.state == "resource":
            return self.content.get("subtype") == "person"
        elif self.state == "vehicle":
            return "person" in self.content.get("cargo", [])
        return False
    
    def get_position(self):
        """
        Devuelve la posición del nodo como tupla (row, col).
        """
        return (self.row, self.col)
    def __str__(self):
        """
        Representación en texto del nodo para depuración.
        """
        return f"Node({self.row}, {self.col}) - State: {self.state} - Content: {self.content}"