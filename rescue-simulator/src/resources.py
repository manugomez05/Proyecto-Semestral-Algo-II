"""
El mapa contiene un total de 60 elementos distribuidos aleatoriamente:
● 10 Personas (50 puntos cada una)
● 50 Mercancías distribuidas en cuatro tipos:
○ Ropa: 5 puntos por unidad
○ Alimentos: 10 puntos por unidad
○ Medicamentos: 20 puntos por unidad
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

class Resource:
    def __init__(self, tipo, puntos, img_path, position):
        self.tipo = tipo
        self.puntos = puntos
        self.img_path = img_path
        self.position = position  # (x, y)
    

    #Metodo especial de python que define como se muestra un objeto cuando se imprime por pantalla o en consola
    def __repr__(self):
        return f"<Resource tipo={self.tipo}, img_path={self.img_path}, puntos={self.puntos}, pos={self.position}>"



def get_random_free_position(map_width, map_height, used_positions):
    """Devuelve una coordenada libre en el mapa."""
    while True:
        x = random.randint(0, map_width - 1)
        y = random.randint(0, map_height - 1)
        if (x, y) not in used_positions:
            used_positions.add((x, y))
            return (x, y)


def generate_resources(map_width, map_height, occupied_positions=set()):
    """
    Genera los 60 recursos (10 personas, 50 mercancías) en posiciones aleatorias.
    Evita colocar recursos en posiciones ya ocupadas (minas, bases, etc.)
    """
    resources = []
    used_positions = set(occupied_positions)

    # Tipos y puntajes
    persons = [("persona", 50, "prueba/assets/person.png")] * 10 #crea una lista de tuplas y la repite 10 veces

    #goods == mercancias 
    goods = [
        ("ropa", 5, "prueba/assets/cloth.png"),
        ("alimentos", 10, "prueba/assets/food.png"),
        ("medicamentos", 20, "prueba/assets/meds.png"),
        ("armamentos", 50, "prueba/assets/recurso.png"),
    ]

    # Generar personas
    for tipo, puntos, img in persons:
        pos = get_random_free_position(map_width, map_height, used_positions)
        resources.append(Resource(tipo, puntos, img, pos))

    # Generar mercancías (50 en total)
    for _ in range(50): #_ convencion que indica que la variable no se usa en el bucle
        tipo, puntos, img = random.choice(goods)
        pos = get_random_free_position(map_width, map_height, used_positions)
        resources.append(Resource(tipo, puntos, img, pos))

    return resources #lista con todos los recursos distribuidos y sus posiciones en el grafo

## en MapManager.py
### resources = generate_resources(map_width=50, map_height=50, occupied_positions=bases + minas)