# Guía Práctica de Uso - Sistema de Persistencia

## 🚀 Inicio Rápido

### Uso Básico en el Juego

El sistema de persistencia está **completamente integrado** en `GameEngine` y funciona automáticamente. No necesitas hacer nada especial para usarlo.

```python
# rescue_simulator.py o tu script principal
from src.game_engine import GameEngine

# Crear motor del juego
engine = GameEngine()

# Iniciar juego (automáticamente registra simulación)
engine.init_game()
engine.start_game()

# El sistema automáticamente:
# - Guarda estados cada 5 ticks
# - Crea checkpoints cada 10 ticks
# - Registra todas las estadísticas al finalizar
```

## 💾 Guardado y Carga

### Guardado Manual Durante el Juego

```python
# Guardar estado actual con un nombre personalizado
engine.save_manual_state(
    name="partida_epica_momento_critico",
    description="Justo antes de la batalla final"
)
```

### Cargar un Guardado Manual

```python
# Listar guardados disponibles
saves = engine.persistence.list_manual_saves()
for save in saves:
    print(f"{save['name']}: {save['description']}")

# Cargar guardado específico
engine.load_manual_state("partida_epica_momento_critico_20251109_153000.pkl")
```

### Navegación por el Tiempo

El simulador permite avanzar y retroceder en el tiempo:

```python
# Avanzar un paso (ya implementado con los botones)
engine.step_forward()

# Retroceder un paso (ya implementado con los botones)
engine.step_backward()
```

## 📊 Exportar Estadísticas

### Exportar Simulación Actual a CSV

```python
# Después de que termine una simulación
if engine.state == "game_over":
    files = engine.export_statistics_csv()
    
    if files:
        print("Archivos CSV generados:")
        for key, filepath in files.items():
            print(f"  {key}: {filepath}")
```

### Exportar Todas las Simulaciones

```python
# Exportar historial completo
filepath = engine.persistence.export_all_simulations_csv(limit=50)
print(f"Historial exportado a: {filepath}")

# Exportar resumen estadístico
summary_file = engine.persistence.export_summary_csv()
print(f"Resumen exportado a: {summary_file}")
```

## 📈 Consultar Historial y Estadísticas

### Ver Historial de Simulaciones

```python
# Obtener últimas 10 simulaciones
history = engine.persistence.get_simulation_history(limit=10)

for sim in history:
    print(f"""
    Simulación: {sim['simulation_id']}
    Ganador: {sim['winner']}
    Puntajes: {sim['final_score_p1']} vs {sim['final_score_p2']}
    Ticks totales: {sim['total_ticks']}
    Duración: {sim['duration_seconds']:.2f} segundos
    """)
```

### Resumen Estadístico General

```python
summary = engine.persistence.get_statistics_summary()

print(f"""
📊 RESUMEN GENERAL
==================
Total de simulaciones: {summary['total_simulations']}
Simulaciones completadas: {summary['completed_simulations']}

Victorias:
{'-' * 40}
""")

for player, wins in summary['wins_by_player'].items():
    print(f"  {player}: {wins} victorias")

print(f"""
Promedios:
{'-' * 40}
  Duración: {summary['average_duration_seconds']:.2f} segundos
  Ticks: {summary['average_ticks']:.0f}
  Puntaje Jugador 1: {summary['average_score_p1']:.0f}
  Puntaje Jugador 2: {summary['average_score_p2']:.0f}
""")
```

## 🔄 Recuperar Simulación Interrumpida

Si el programa se cierra inesperadamente, puedes recuperar la última simulación:

```python
# Intentar recuperar última simulación
engine = GameEngine()
state = engine.persistence.resume_last_simulation()

if state:
    print("✅ Simulación recuperada exitosamente")
    # Puedes continuar desde donde quedó
else:
    print("ℹ️  No hay simulaciones para recuperar")
    # Iniciar nueva simulación
    engine.init_game()
```

## 🛠️ Administración del Sistema

### Ver Espacio Usado

```python
info = engine.persistence.get_storage_info()

print(f"""
💾 ALMACENAMIENTO
=================
Snapshots automáticos: {info['snapshots_formatted']}
Guardados manuales: {info['manual_saves_formatted']}
Checkpoints: {info['checkpoints_formatted']}
Total: {info['total_formatted']}
""")
```

### Limpiar Datos Antiguos

```python
# Limpiar simulaciones antiguas y liberar espacio
deleted = engine.persistence.cleanup_old_data(
    days_to_keep=30,      # Mantener últimos 30 días
    keep_snapshots=50     # Mantener últimos 50 snapshots
)

print(f"Eliminadas {deleted['simulations']} simulaciones antiguas")
```

## 📁 Estructura de Archivos Generados

Después de usar el sistema, encontrarás:

```
rescue-simulator/
├── config/
│   ├── saved_configs/
│   │   ├── map_*.json                    # Configuraciones de mapas
│   │   ├── strategy_*.json               # Configuraciones de estrategias
│   │   └── sim_*.json                    # Configuraciones de simulaciones
│   └── active_config.json                # Última configuración usada
│
├── saved_states/
│   ├── snapshots/
│   │   └── sim_*_tick_*.pkl             # Estados automáticos
│   ├── manual_saves/
│   │   └── nombre_timestamp.pkl          # Tus guardados manuales
│   └── checkpoints/
│       └── checkpoint_tick_*.pkl         # Checkpoints de recuperación
│
├── data/
│   └── simulation_history.db             # Base de datos con historial
│
└── exports/
    ├── simulations_*.csv                 # Listado de simulaciones
    ├── player_stats_*.csv                # Estadísticas de jugadores
    ├── vehicle_stats_*.csv               # Estadísticas de vehículos
    └── summary_stats_*.csv               # Resumen estadístico
```

## 🎯 Casos de Uso Comunes

### Caso 1: Debugging de Estrategia

```python
# 1. Guardar estado antes de probar cambio en estrategia
engine.save_manual_state("antes_cambio_estrategia", 
                         "Estado antes de modificar Strategy1")

# 2. Modificar estrategia y probar
# ... modificar código de estrategia ...

# 3. Ejecutar simulación
engine.init_game()
engine.start_game()

# 4. Si no funciona bien, volver al estado anterior
engine.load_manual_state("antes_cambio_estrategia_timestamp.pkl")
```

### Caso 2: Análisis Comparativo

```python
# Ejecutar múltiples simulaciones para análisis
for i in range(10):
    print(f"Ejecutando simulación {i+1}/10...")
    engine.init_game()
    engine.start_game()
    
    # Esperar a que termine (o hacer paso a paso)
    while engine.state != "game_over":
        engine.update()

# Exportar todas las estadísticas
engine.persistence.export_all_simulations_csv(limit=10)

# Analizar en Excel o Python
import pandas as pd
df = pd.read_csv('exports/simulations_*.csv')
print(df.describe())
```

### Caso 3: Demostración y Replay

```python
# Durante una partida interesante:

# Guardar momentos clave
engine.save_manual_state("inicio", "Comienzo de la partida")

# ... después de eventos importantes ...
engine.save_manual_state("batalla", "Batalla importante en el centro")

# ... al final ...
engine.save_manual_state("victoria", "Victoria del Jugador 1")

# Para demostrar después, cargar estos estados en orden
estados = ["inicio", "batalla", "victoria"]
for estado in estados:
    # Buscar archivo correspondiente
    saves = engine.persistence.list_manual_saves()
    archivo = next((s for s in saves if estado in s['name']), None)
    if archivo:
        engine.load_manual_state(archivo['filename'])
        # Mostrar estado...
```

### Caso 4: Análisis de Rendimiento de Vehículos

```python
# Después de varias simulaciones, analizar vehículos
from persistence import SimulationHistory

history = SimulationHistory()

# Obtener todas las simulaciones
sims = history.list_simulations(limit=100)

# Para cada simulación, obtener estadísticas de vehículos
all_vehicle_stats = []
for sim in sims:
    sim_data = history.get_simulation(sim['simulation_id'])
    all_vehicle_stats.extend(sim_data.get('vehicle_stats', []))

# Exportar a CSV para análisis
from persistence import CSVExporter
exporter = CSVExporter()
exporter.export_vehicle_performance(all_vehicle_stats)

# Ahora puedes analizar en Excel:
# - ¿Qué tipo de vehículo tiene mejor tasa de supervivencia?
# - ¿Qué vehículos recogen más recursos?
# - ¿Qué vehículos viajan más distancia?
```

## ⚙️ Configuración Avanzada

### Ajustar Frecuencia de Auto-guardado

```python
# Para simulaciones rápidas - guardar cada tick
engine.persistence.set_auto_save_config(enabled=True, interval=1)

# Para simulaciones largas - guardar cada 20 ticks
engine.persistence.set_auto_save_config(enabled=True, interval=20)

# Desactivar auto-guardado (solo checkpoints)
engine.persistence.set_auto_save_config(enabled=False)
```

### Acceso Directo a Componentes

Si necesitas control más fino:

```python
# Acceso directo a ConfigManager
config_mgr = engine.persistence.config_manager
config_mgr.save_map_config("mi_mapa", 100, 100, seed=999)

# Acceso directo a StateManager
state_mgr = engine.persistence.state_manager
snapshots = state_mgr.list_snapshots()

# Acceso directo a SimulationHistory
history = engine.persistence.history
summary = history.get_statistics_summary()

# Acceso directo a CSVExporter
exporter = engine.persistence.csv_exporter
exporter.export_simulations(simulations_list)
```

## 🐛 Solución de Problemas

### Problema: "No hay estados guardados"

**Solución:** Asegúrate de que la simulación haya ejecutado al menos algunos ticks. Los estados se guardan automáticamente cada 5 ticks.

```python
# Verificar si hay snapshots
snapshots = engine.persistence.list_snapshots()
print(f"Snapshots disponibles: {len(snapshots)}")
```

### Problema: El sistema ocupa mucho espacio

**Solución:** Ejecutar limpieza periódica

```python
# Limpiar datos antiguos
deleted = engine.persistence.cleanup_old_data(
    days_to_keep=7,       # Solo una semana
    keep_snapshots=20     # Solo últimos 20 snapshots
)
```

### Problema: Error al cargar estado

**Solución:** El estado puede estar corrupto o la estructura de clases cambió

```python
# Intentar cargar checkpoint más reciente
checkpoint = engine.persistence.get_latest_checkpoint()
if checkpoint:
    engine.load_state(checkpoint)
else:
    # Iniciar nueva simulación
    engine.init_game()
```

### Problema: Base de datos muy grande

**Solución:** Limpiar simulaciones antiguas

```python
# Eliminar simulaciones de más de 30 días
count = engine.persistence.history.cleanup_old_simulations(days_to_keep=30)
print(f"Eliminadas {count} simulaciones antiguas")
```

## 📚 Recursos Adicionales

- **Documentación Completa:** Ver `SISTEMA_PERSISTENCIA.md`
- **Script de Prueba:** Ejecutar `python test_persistence_system.py`
- **Código Fuente:** Revisar módulo `persistence/`

## 💡 Tips y Mejores Prácticas

1. **Guardados Manuales:** Usa nombres descriptivos que te ayuden a recordar el contexto
   ```python
   engine.save_manual_state("p1_victoria_estrategia_agresiva", 
                           "Jugador 1 ganó usando estrategia agresiva con motos")
   ```

2. **Exportación Regular:** Exporta estadísticas periódicamente para no perder análisis
   ```python
   # Al finalizar sesión de pruebas
   engine.persistence.export_all_simulations_csv()
   ```

3. **Limpieza Programada:** Configura limpieza automática en tu flujo de trabajo
   ```python
   # Al iniciar el programa
   if engine.persistence.get_storage_info()['total_bytes'] > 100_000_000:  # 100MB
       engine.persistence.cleanup_old_data(days_to_keep=15)
   ```

4. **Backup Importante:** Si tienes simulaciones importantes, haz backup manual
   ```bash
   # Copiar directorios importantes
   cp -r saved_states/ backup/
   cp data/simulation_history.db backup/
   ```

5. **Análisis Externo:** Usa pandas para análisis avanzado de CSVs
   ```python
   import pandas as pd
   
   # Cargar datos exportados
   df = pd.read_csv('exports/simulations_latest.csv')
   
   # Análisis
   print(df.groupby('winner').size())
   print(df[['final_score_p1', 'final_score_p2']].describe())
   ```

## 🎓 Ejemplos de Scripts Completos

### Script: Ejecutar y Analizar 10 Simulaciones

```python
from src.game_engine import GameEngine
import time

engine = GameEngine()

# Ejecutar 10 simulaciones
print("Ejecutando 10 simulaciones...")
for i in range(10):
    print(f"\nSimulación {i+1}/10")
    engine.init_game()
    engine.start_game()
    
    # Ejecutar hasta terminar
    while engine.state != "game_over" and engine.tick < 1000:
        engine.update()
    
    print(f"Ganador: {engine.game_over_info['winner']}")
    print(f"Puntajes: {engine.player1.score} vs {engine.player2.score}")
    
    time.sleep(0.5)  # Pausa breve

# Exportar todo
print("\nExportando resultados...")
engine.persistence.export_all_simulations_csv(limit=10)

# Mostrar resumen
summary = engine.persistence.get_statistics_summary()
print(f"\n📊 RESUMEN:")
print(f"Victorias: {summary['wins_by_player']}")
print(f"Puntaje promedio P1: {summary['average_score_p1']:.0f}")
print(f"Puntaje promedio P2: {summary['average_score_p2']:.0f}")
```

---

**¿Necesitas ayuda?** Revisa la documentación completa en `SISTEMA_PERSISTENCIA.md` o ejecuta el script de pruebas `test_persistence_system.py` para verificar que todo funciona correctamente.

