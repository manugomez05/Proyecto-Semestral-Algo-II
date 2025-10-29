import os
import shutil

# Define paths
base_path = "rescue_simulator"
config_path = os.path.join(base_path, "config")
strategies_path = os.path.join(config_path, "strategies")

# Create __init__.py files
os.makedirs(config_path, exist_ok=True)
os.makedirs(strategies_path, exist_ok=True)

with open(os.path.join(config_path, "__init__.py"), "w") as f:
    f.write("# Init file for config package\n")

with open(os.path.join(strategies_path, "__init__.py"), "w") as f:
    f.write("# Init file for strategies package\n")

# Move player1_strategies.py to config/strategies/
source_file = os.path.join(base_path, "player1_strategies.py")
destination_file = os.path.join(strategies_path, "player1_strategies.py")

if os.path.exists(source_file):
    shutil.move(source_file, destination_file)
    print("Archivo 'player1_strategies.py' movido a 'config/strategies/' y archivos __init__.py creados.")
else:
    print("No se encontró 'player1_strategies.py' en la carpeta raíz. Verifica la ubicación del archivo.")