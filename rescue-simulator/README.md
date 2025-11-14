
Link video demostracion: https://drive.google.com/file/d/15Vh5eDWQKqqQJeTC5wUWyyZO3-i5yoe4/view?usp=drive_link

# Rescue Simulator - Guía de Instalación y Uso (Rama principal-Reestructuracion)

## Prerequisitos

1. Python 3.8 o superior instalado
2. Windows 10/11
3. Terminal/CMD o PowerShell

## Instalación

1. Abrir terminal en la carpeta del proyecto: `rescue-simulator/`

2. Crear entorno virtual:
   ```
   python -m venv venv
   ```

3. Activar entorno virtual:
   - CMD: `venv\Scripts\activate`
   - PowerShell: `venv\Scripts\Activate.ps1`

4. Instalar dependencias:
   ```
   pip install pygame
   ```

## Configuración

El archivo de configuración se encuentra en: `config/active_config.json`

Configuración mínima (ya incluida):
- Tamaño del mapa: 50x50 celdas
- Se genera automáticamente al iniciar

## Ejecución

1. Desde la carpeta `rescue-simulator/`, ejecutar:
   ```
   python rescue_simulator.py
   ```

2. Controles de la interfaz:
   - **INIT**: Inicializa nueva partida
   - **PLAY**: Inicia/pausa la simulación
   - **FORWARD**: Avanza un paso (tick)
   - **STOP**: Detiene la simulación
   - **X**: Cierra la aplicación

## Comandos Útiles

**Ver historial de partidas:**
```
python ver_bd.py
```

**Limpiar base de datos:**
```
python limpiar_bd.py
```

## Archivos Importantes

- `rescue_simulator.py` - Punto de entrada principal
- `config/active_config.json` - Configuración activa
- `data/simulation_history.db` - Base de datos de partidas
- `config/strategies/` - Estrategias de los jugadores
- `src/game_engine.py` - Motor del juego
- `src/visualization.py` - Interfaz gráfica

## Notas

- La base de datos se crea automáticamente en `data/simulation_history.db`
- Las partidas se registran automáticamente al finalizar
- Para desactivar el entorno virtual: `deactivate`

