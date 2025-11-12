# Sistema de Persistencia - Rescue Simulator

## 📋 Descripción General

El sistema de persistencia del Rescue Simulator proporciona un conjunto completo de herramientas para guardar, cargar y analizar simulaciones. Está diseñado para ser eficiente, robusto y fácil de usar.

## 🏗️ Arquitectura

El sistema está compuesto por 5 módulos principales:

```
persistence/
├── __init__.py                  # Módulo principal
├── config_manager.py            # Gestión de configuraciones (JSON)
├── state_manager.py             # Gestión de estados (Pickle)
├── simulation_history.py        # Historial de simulaciones (SQLite)
├── csv_exporter.py              # Exportación a CSV
└── persistence_manager.py       # Coordinador principal
```

### 1. **ConfigManager** - Gestión de Configuraciones

Guarda y carga configuraciones en formato JSON para facilitar lectura y edición manual.

**Características:**
- ✅ Configuraciones de mapas
- ✅ Configuraciones de estrategias
- ✅ Parámetros de simulación
- ✅ Validación automática
- ✅ Importar/Exportar configuraciones

**Ubicación de archivos:** `config/saved_configs/`

**Ejemplo de uso:**
```python
from persistence import ConfigManager

config_mgr = ConfigManager()

# Guardar configuración de mapa
config_mgr.save_map_config(
    name="mapa_grande",
    rows=100,
    cols=100,
    seed=12345
)

# Listar configuraciones
configs = config_mgr.list_configs(config_type="map")

# Cargar configuración
config = config_mgr.load_config("config/saved_configs/mapa_grande.json")
```

### 2. **StateManager** - Gestión de Estados

Guarda estados completos del juego usando Pickle para serialización eficiente.

**Características:**
- ✅ Snapshots automáticos durante simulación
- ✅ Guardados manuales con nombre
- ✅ Checkpoints para recuperación automática
- ✅ Búsqueda por tick
- ✅ Limpieza automática de estados antiguos

**Ubicación de archivos:**
- Snapshots: `saved_states/snapshots/`
- Guardados manuales: `saved_states/manual_saves/`
- Checkpoints: `saved_states/checkpoints/`

**Ejemplo de uso:**
```python
from persistence import StateManager

state_mgr = StateManager()

# Guardar estado
state_mgr.save_state(state_data, tick=100, simulation_id="sim_001")

# Buscar estado por tick
state_file = state_mgr.find_state_by_tick(95)

# Cargar estado
state = state_mgr.load_state(state_file)

# Guardado manual
state_mgr.save_manual(state_data, name="antes_batalla", description="Estado previo a batalla importante")

# Listar guardados manuales
saves = state_mgr.list_manual_saves()
```

### 3. **SimulationHistory** - Historial de Simulaciones

Almacena historial completo en base de datos SQLite para consultas y análisis.

**Características:**
- ✅ Registro completo de simulaciones
- ✅ Estadísticas por jugador
- ✅ Estadísticas por vehículo
- ✅ Registro de eventos
- ✅ Consultas eficientes con SQL
- ✅ Resúmenes estadísticos

**Ubicación:** `data/simulation_history.db`

**Estructura de tablas:**
- `simulations` - Datos principales de simulaciones
- `player_stats` - Estadísticas de jugadores
- `vehicle_stats` - Estadísticas de vehículos
- `simulation_events` - Eventos durante simulación

**Ejemplo de uso:**
```python
from persistence import SimulationHistory

history = SimulationHistory()

# Iniciar registro de simulación
history.start_simulation("sim_001", map_rows=50, map_cols=50)

# Registrar estadísticas de jugador
history.add_player_stats("sim_001", "Jugador_1", {
    "final_score": 1500,
    "vehicles_destroyed": 2,
    "resources_collected": 30
})

# Finalizar simulación
history.finish_simulation("sim_001", total_ticks=500, 
                         winner="Jugador_1", 
                         final_score_p1=1500, 
                         final_score_p2=1200)

# Obtener resumen estadístico
summary = history.get_statistics_summary()

# Listar últimas simulaciones
sims = history.list_simulations(limit=10)
```

### 4. **CSVExporter** - Exportación a CSV

Exporta datos a formato CSV para análisis en hojas de cálculo o herramientas externas.

**Características:**
- ✅ Exportación de simulaciones
- ✅ Exportación de estadísticas de jugadores
- ✅ Exportación de estadísticas de vehículos
- ✅ Exportación de eventos
- ✅ Comparaciones entre simulaciones
- ✅ Análisis de rendimiento

**Ubicación:** `exports/`

**Ejemplo de uso:**
```python
from persistence import CSVExporter

exporter = CSVExporter()

# Exportar todas las simulaciones
exporter.export_simulations(simulations_list)

# Exportar simulación completa (múltiples archivos)
files = exporter.export_complete_simulation(simulation_data)

# Exportar comparación entre simulaciones
exporter.export_comparison(simulations_list)

# Exportar análisis de rendimiento de vehículos
exporter.export_vehicle_performance(vehicle_stats)
```

### 5. **PersistenceManager** - Coordinador Principal

Proporciona interfaz unificada que coordina todos los componentes.

**Características:**
- ✅ Interfaz simplificada
- ✅ Auto-guardado configurable
- ✅ Gestión automática de ciclo de simulación
- ✅ Recuperación de simulaciones interrumpidas
- ✅ Limpieza automática de datos antiguos

**Ejemplo de uso completo:**
```python
from persistence import PersistenceManager

# Inicializar gestor
pm = PersistenceManager()

# Iniciar nueva simulación
sim_id = pm.start_new_simulation({
    "map": {"rows": 50, "cols": 50},
    "simulation": {"max_ticks": 10000}
})

# Durante la simulación - guardar estado cada N ticks
if pm.should_auto_save(current_tick):
    pm.save_simulation_state(game_state, current_tick)

# Al finalizar - registrar estadísticas
pm.finish_simulation(
    total_ticks=500,
    winner="Jugador_1",
    final_score_p1=1500,
    final_score_p2=1200
)

# Registrar estadísticas de jugadores
pm.record_player_stats("Jugador_1", player_stats)

# Exportar a CSV
files = pm.export_current_simulation_csv()

# Obtener información de almacenamiento
storage_info = pm.get_storage_info()
print(f"Espacio usado: {storage_info['total_formatted']}")
```

## 🎮 Integración con GameEngine

El sistema está completamente integrado con `GameEngine`. Las siguientes funciones están disponibles:

### Funciones Automáticas

- **Auto-guardado**: Cada 5 ticks se guarda automáticamente el estado
- **Checkpoints**: Cada 10 ticks se crea un checkpoint de recuperación
- **Registro de estadísticas**: Al finalizar el juego se registran automáticamente todas las estadísticas

### Funciones Disponibles

```python
# En GameEngine

# Iniciar juego (automáticamente registra simulación)
engine.init_game()

# Guardar estado manualmente
engine.save_manual_state("nombre_guardado", "descripción")

# Cargar guardado manual
engine.load_manual_state("filename.pkl")

# Exportar estadísticas a CSV (después de terminar simulación)
files = engine.export_statistics_csv()

# Acceder directamente al sistema de persistencia
engine.persistence.get_simulation_history()
engine.persistence.get_storage_info()
```

## 📊 Estructura de Datos

### Configuración de Simulación

```json
{
  "map": {
    "rows": 50,
    "cols": 50,
    "seed": null
  },
  "simulation": {
    "max_ticks": 10000,
    "auto_save_interval": 5,
    "enable_debug": true
  },
  "players": {
    "player1": {
      "name": "Jugador_1",
      "strategy": "Strategy1"
    },
    "player2": {
      "name": "Jugador_2",
      "strategy": "Strategy2"
    }
  },
  "mines": {
    "O1": 2,
    "O2": 3,
    "T1": 2,
    "T2": 2,
    "G1": 1
  }
}
```

### Estado Guardado

```python
{
    "saved_at": "2024-01-15T10:30:00",
    "tick": 250,
    "simulation_id": "sim_20240115_103000_abc123",
    "state": {
        "state": "running",
        "tick": 250,
        "start_time": 1705315800.0,
        "elapsed_time": 25.5,
        "player1": <Player object>,
        "player2": <Player object>,
        "map": <MapManager object>,
        "debug_events": [...],
        "game_over_info": None
    }
}
```

## 🔧 Configuración

### Auto-guardado

```python
# Configurar intervalo de auto-guardado
engine.persistence.set_auto_save_config(
    enabled=True,
    interval=10  # Guardar cada 10 ticks
)
```

### Limpieza de Datos Antiguos

```python
# Limpiar simulaciones más antiguas que 30 días
# y mantener solo los últimos 50 snapshots
deleted = engine.persistence.cleanup_old_data(
    days_to_keep=30,
    keep_snapshots=50
)

print(f"Eliminadas {deleted['simulations']} simulaciones antiguas")
```

## 📈 Análisis y Reportes

### Obtener Resumen Estadístico

```python
summary = engine.persistence.get_statistics_summary()

print(f"Total simulaciones: {summary['total_simulations']}")
print(f"Simulaciones completadas: {summary['completed_simulations']}")
print(f"Victorias por jugador: {summary['wins_by_player']}")
print(f"Duración promedio: {summary['average_duration_seconds']} seg")
print(f"Puntaje promedio P1: {summary['average_score_p1']}")
print(f"Puntaje promedio P2: {summary['average_score_p2']}")
```

### Listar Historial

```python
# Obtener últimas 20 simulaciones
history = engine.persistence.get_simulation_history(limit=20)

for sim in history:
    print(f"{sim['simulation_id']}: {sim['winner']} - "
          f"P1: {sim['final_score_p1']} vs P2: {sim['final_score_p2']}")
```

### Exportar para Análisis Externo

```python
# Exportar todo a CSV
engine.persistence.export_all_simulations_csv(limit=100)
engine.persistence.export_summary_csv()

# Los archivos se guardan en la carpeta exports/
```

## 🔄 Recuperación de Simulaciones

### Reanudar Última Simulación Interrumpida

```python
# Intentar reanudar última simulación
state = engine.persistence.resume_last_simulation()

if state:
    print("Simulación recuperada correctamente")
    # El estado se carga automáticamente
else:
    print("No hay simulaciones para recuperar")
```

### Cargar Estado Específico

```python
# Buscar y cargar estado de un tick específico
state_file = engine.persistence.find_state_by_tick(250)
if state_file:
    engine.load_state(state_file)
```

## 📁 Organización de Archivos

```
rescue-simulator/
├── config/
│   ├── saved_configs/              # Configuraciones JSON
│   │   ├── map_*.json
│   │   ├── strategy_*.json
│   │   └── sim_*.json
│   └── active_config.json         # Configuración activa
│
├── saved_states/
│   ├── snapshots/                 # Snapshots automáticos
│   │   └── sim_*_tick_*.pkl
│   ├── manual_saves/              # Guardados manuales
│   │   └── nombre_timestamp.pkl
│   └── checkpoints/               # Checkpoints de recuperación
│       └── checkpoint_tick_*.pkl
│
├── data/
│   └── simulation_history.db      # Base de datos SQLite
│
└── exports/                       # Archivos CSV exportados
    ├── simulations_*.csv
    ├── player_stats_*.csv
    ├── vehicle_stats_*.csv
    └── summary_stats_*.csv
```

## ⚡ Optimización y Rendimiento

### Configuración Recomendada

```python
# Para simulaciones largas
pm.set_auto_save_config(
    enabled=True,
    interval=10  # Guardar cada 10 ticks (menos frecuente)
)

# Para simulaciones cortas o debugging
pm.set_auto_save_config(
    enabled=True,
    interval=1  # Guardar cada tick (más granular)
)
```

### Gestión de Espacio

```python
# Ver espacio usado
info = pm.get_storage_info()
print(f"Total: {info['total_formatted']}")
print(f"Snapshots: {info['snapshots_formatted']}")
print(f"Guardados manuales: {info['manual_saves_formatted']}")
print(f"Checkpoints: {info['checkpoints_formatted']}")

# Limpiar si es necesario
if info['total_bytes'] > 1_000_000_000:  # Si supera 1GB
    pm.cleanup_old_data(days_to_keep=7, keep_snapshots=20)
```

## 🛠️ Mantenimiento

### Limpieza Periódica

Se recomienda ejecutar limpieza periódica para mantener el sistema eficiente:

```python
# Limpiar cada cierto tiempo
deleted = pm.cleanup_old_data(
    days_to_keep=30,      # Mantener simulaciones de último mes
    keep_snapshots=50     # Mantener últimos 50 snapshots
)
```

### Backup y Restauración

Para hacer backup completo, copiar las siguientes carpetas:

```bash
# Backup
cp -r saved_states/ backup/saved_states_2024_01_15/
cp -r data/ backup/data_2024_01_15/
cp -r config/saved_configs/ backup/configs_2024_01_15/

# Restaurar
cp -r backup/saved_states_2024_01_15/ saved_states/
cp -r backup/data_2024_01_15/ data/
cp -r backup/configs_2024_01_15/ config/saved_configs/
```

## 🔍 Debugging

### Ver Snapshots Disponibles

```python
snapshots = pm.list_snapshots()
for snap in snapshots:
    print(f"Tick: {snap['tick']}, "
          f"Fecha: {snap['saved_at']}, "
          f"Tamaño: {snap['size_bytes']} bytes")
```

### Ver Guardados Manuales

```python
saves = pm.list_manual_saves()
for save in saves:
    print(f"Nombre: {save['name']}, "
          f"Descripción: {save['description']}, "
          f"Fecha: {save['saved_at']}")
```

## 📝 Notas Importantes

1. **Serialización**: Las estrategias (Strategy1, Strategy2) no se serializan debido a referencias circulares. Se recrean al cargar un estado.

2. **Compatibilidad**: Los estados guardados son compatibles entre sesiones del mismo proyecto. No modificar la estructura de clases entre guardados.

3. **Rendimiento**: El auto-guardado puede afectar ligeramente el rendimiento. Ajustar el intervalo según necesidad.

4. **Espacio**: Los estados guardados pueden ocupar espacio considerable. Usar limpieza periódica.

5. **Base de Datos**: El archivo SQLite puede crecer. Se recomienda limpieza periódica de simulaciones antiguas.

## 🎯 Casos de Uso

### Caso 1: Análisis de Estrategias

```python
# Ejecutar múltiples simulaciones
for i in range(10):
    engine.init_game()
    engine.start_game()
    # ... esperar fin de simulación

# Exportar todas las estadísticas
pm.export_all_simulations_csv(limit=10)

# Analizar en Excel/Python usando los CSV generados
```

### Caso 2: Debugging de Comportamiento

```python
# Guardar estado antes de comportamiento problemático
engine.save_manual_state("antes_error", "Estado antes del bug")

# Continuar simulación...
# Si ocurre problema, cargar estado guardado
engine.load_manual_state("antes_error_timestamp.pkl")
```

### Caso 3: Demostración y Replay

```python
# Durante partida interesante, guardar estados clave
engine.save_manual_state("inicio_batalla", "Inicio de batalla épica")
# ... más tarde ...
engine.save_manual_state("final_batalla", "Final de batalla épica")

# Luego, recargar para demostración
engine.load_manual_state("inicio_batalla_timestamp.pkl")
```

## 🔗 Referencias

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Python Pickle Module](https://docs.python.org/3/library/pickle.html)
- [CSV Format Specification](https://tools.ietf.org/html/rfc4180)

---

**Versión del Sistema**: 1.0.0
**Última Actualización**: Noviembre 2025

