"""
El mapa contiene un total de 60 elementos distribuidos aleatoriamente:
● 10 Personas (50 puntos cada una)
● 50 Mercancías distribuidas en cuatro tipos:
○ Ropa: 5 puntos por unidad
○ Alimentos: 10 puntos por unidad
○ Medicamentos: 20 puntos por unidad
○ Armamentos: 50 puntos por unidad
"""

"""
clase Resources
    tipo, persona, ropa, alimentos, medicamentos
    img, url del sprite
    puntaje por unidad


funcion GenerateResources():
    accede a una posicion random del grafo y coloca los resources correspondientes (10 personas, 50 mercancias de tipo random)


"""

import random
from pathlib import Path

class Resource:
    def __init__(self, tipo, puntos, img_path, position):
        self.tipo = tipo
        self.puntos = puntos
        self.img_path = img_path
        self.position = position  # (x, y)
    

    #Metodo especial de python que define como se muestra un objeto cuando se imprime por pantalla o en consola
    def __repr__(self):
        return f"<Resource tipo={self.tipo}, img_path={self.img_path}, puntos={self.puntos}, pos={self.position}>"



def get_random_free_position(map_width, map_height, used_positions, mine_manager=None, tick=0):
    """Devuelve una coordenada libre en el mapa, evitando minas."""
    max_attempts = 1000  # Evitar bucle infinito
    attempts = 0
    
    while attempts < max_attempts:
        x = random.randint(0, map_width - 1)
        y = random.randint(0, map_height - 1)
        
        # Verificar que no esté ocupada y que esté segura de minas
        if (x, y) not in used_positions:
            if mine_manager is None or is_position_safe_from_mines(x, y, mine_manager, tick):
                used_positions.add((x, y))
                return (x, y)
            else:
                print(f"DEBUG: Posición ({x}, {y}) no es segura por minas")
        attempts += 1
    
    # Si no se encuentra posición segura, usar la primera disponible
    for x in range(map_width):
        for y in range(map_height):
            if (x, y) not in used_positions:
                used_positions.add((x, y))
                return (x, y)
    
    # Fallback: posición aleatoria
    x = random.randint(0, map_width - 1)
    y = random.randint(0, map_height - 1)
    used_positions.add((x, y))
    return (x, y)


def is_position_safe_from_mines(x, y, mine_manager, tick=0):
    """Verifica si una posición está segura de todas las minas"""
    from src.mines import Cell
    cell = (y, x)  # Convertir a formato (row, col)
    return not mine_manager.isCellMined(cell, tick)

def generate_resources(map_width, map_height, occupied_positions=set(), mine_manager=None, tick=0):
    """
    Genera los 60 recursos (10 personas, 50 mercancías) en posiciones aleatorias.
    Evita colocar recursos en posiciones ya ocupadas (minas, bases, etc.)
    y dentro del radio de las minas.
    """
    resources = []
    used_positions = set(occupied_positions)

    

    # 📁 Ruta base del archivo actual (src/visualization.py)
    base_path = Path(__file__).resolve().parent

    # 📁 Ruta absoluta a la carpeta assets (un nivel arriba de src)
    assets_path = base_path.parent / 'assets'



    # Tipos y puntajes
    persons = [("people", 50, str(assets_path / 'person.png'))] * 10 #crea una lista de tuplas y la repite 10 veces

    #goods == mercancias 
    goods = [
        ("cargo", 5, str(assets_path / 'cloth.png')),
        ("cargo", 10, str(assets_path / 'food.png')),
        ("cargo", 20, str(assets_path / 'meds.png')),
        ("cargo", 50, str(assets_path / 'recurso.png')),
    ]

    # Generar personas
    for tipo, puntos, img in persons:
        pos = get_random_free_position(map_width, map_height, used_positions, mine_manager, tick)
        resources.append(Resource(tipo, puntos, img, pos))

    # Generar mercancías (50 en total)
    for _ in range(50): #_ convencion que indica que la variable no se usa en el bucle
        tipo, puntos, img = random.choice(goods)
        pos = get_random_free_position(map_width, map_height, used_positions, mine_manager, tick)
        resources.append(Resource(tipo, puntos, img, pos))

    return resources #lista con todos los recursos distribuidos y sus posiciones en el grafo

## en MapManager.py
### resources = generate_resources(map_width=50, map_height=50, occupied_positions=bases + minas)