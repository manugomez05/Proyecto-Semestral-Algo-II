import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.map_graph import MapGraph
def test_map_creation():
    map_graph = MapGraph(10, 15)
    assert len(map_graph.grid) == 10  # 10 filas
    assert all(len(row) == 15 for row in map_graph.grid)  # 15 columnas por fila
    print("✅ test_map_creation passed")

def test_get_node():
    map_graph = MapGraph(5, 5)
    node = map_graph.get_node(2, 3)
    assert node.row == 2
    assert node.col == 3
    assert node.state == "empty"
    print("✅ test_get_node passed")

def test_set_node_state():
    map_graph = MapGraph(5, 5)
    map_graph.set_node_state(1, 1, "mine", {"subtype": "O1", "radius": 10})
    node = map_graph.get_node(1, 1)
    assert node.is_mine()
    assert node.content["subtype"] == "O1"
    assert node.content["radius"] == 10
    print("✅ test_set_node_state passed")

def test_neighbors_connection():
    map_graph = MapGraph(3, 3)
    node = map_graph.get_node(1, 1)
    positions = [n.get_position() for n in node.neighbors]
    expected = [(0, 1), (2, 1), (1, 0), (1, 2)]
    assert all(pos in positions for pos in expected)
    print("✅ test_neighbors_connection passed")

def test_has_person_resource():
    map_graph = MapGraph(3, 3)
    map_graph.set_node_state(0, 0, "resource", {"subtype": "person", "value": 50})
    node = map_graph.get_node(0, 0)
    assert node.has_person()
    print("✅ test_has_person_resource passed")

def test_has_person_vehicle():
    map_graph = MapGraph(3, 3)
    map_graph.set_node_state(0, 1, "vehicle", {
        "vehicle_type": "jeep",
        "cargo": ["person", "alimentos"]
    })
    node = map_graph.get_node(0, 1)
    assert node.has_person()
    print("✅ test_has_person_vehicle passed")

if __name__ == "__main__":
    test_map_creation()
    test_get_node()
    test_set_node_state()
    test_neighbors_connection()
    test_has_person_resource()
    test_has_person_vehicle()