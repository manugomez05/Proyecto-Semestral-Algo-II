# 🎮 Sistema de Persistencia - Rescue Simulator

## 🎯 Inicio Rápido

El sistema de persistencia está **completamente funcional y automático**. Solo necesitas ejecutar el juego normalmente:

```bash
python rescue_simulator.py
```

**El sistema automáticamente:**
- ✅ Guarda estados cada 5 ticks
- ✅ Crea checkpoints cada 10 ticks  
- ✅ Registra todas las estadísticas
- ✅ Permite recuperar simulaciones interrumpidas

## 📚 Documentación

| Archivo | Descripción |
|---------|-------------|
| [`SISTEMA_PERSISTENCIA.md`](SISTEMA_PERSISTENCIA.md) | 📖 Documentación técnica completa |
| [`GUIA_USO_PERSISTENCIA.md`](GUIA_USO_PERSISTENCIA.md) | 🎯 Guía práctica con ejemplos |
| [`RESUMEN_IMPLEMENTACION_PERSISTENCIA.md`](RESUMEN_IMPLEMENTACION_PERSISTENCIA.md) | ✅ Resumen de implementación |
| [`ejemplo_integracion_ui.py`](ejemplo_integracion_ui.py) | 🖼️ Ejemplo de integración con UI |
| [`test_persistence_system.py`](test_persistence_system.py) | 🧪 Script de pruebas |

## ✨ Características Principales

### 1. Guardado Automático
- Estados guardados cada 5 ticks
- Checkpoints de recuperación cada 10 ticks
- Sin intervención del usuario

### 2. Historial Completo
- Base de datos SQLite con todas las simulaciones
- Estadísticas detalladas por jugador y vehículo
- Consultas rápidas y eficientes

### 3. Recuperación de Simulaciones
- Reanudar simulaciones interrumpidas
- Navegación temporal (avanzar/retroceder)
- Sin pérdida de datos

### 4. Exportación a CSV
- Exportar estadísticas completas
- Compatible con Excel y pandas
- Múltiples formatos de análisis

## 🚀 Uso Básico

### En Código Python

```python
from src.game_engine import GameEngine

engine = GameEngine()

# Iniciar juego (todo automático)
engine.init_game()
engine.start_game()

# Funciones adicionales disponibles:
engine.save_manual_state("nombre", "descripción")
engine.load_manual_state("archivo.pkl")
engine.export_statistics_csv()

# Ver historial
history = engine.persistence.get_simulation_history()
summary = engine.persistence.get_statistics_summary()
```

### Desde Terminal

```bash
# Ejecutar pruebas del sistema
python test_persistence_system.py

# Ver archivos generados
ls saved_states/snapshots/    # Estados automáticos
ls saved_states/manual_saves/  # Guardados manuales
ls exports/                     # Archivos CSV
```

## 📊 Ejemplos Prácticos

### Recuperar Simulación Interrumpida

```python
engine = GameEngine()
state = engine.persistence.resume_last_simulation()

if state:
    print("✅ Simulación recuperada")
    # Continuar desde donde quedó
else:
    # Iniciar nueva simulación
    engine.init_game()
```

### Exportar Estadísticas

```python
# Después de terminar una simulación
if engine.state == "game_over":
    files = engine.export_statistics_csv()
    print("Archivos generados:", files)
```

### Ver Resumen de Rendimiento

```python
summary = engine.persistence.get_statistics_summary()

print(f"Total simulaciones: {summary['total_simulations']}")
print(f"Victorias: {summary['wins_by_player']}")
print(f"Puntaje promedio P1: {summary['average_score_p1']:.0f}")
print(f"Puntaje promedio P2: {summary['average_score_p2']:.0f}")
```

## 🗂️ Estructura de Archivos

```
rescue-simulator/
├── persistence/              # Sistema de persistencia
│   ├── config_manager.py    # Configuraciones (JSON)
│   ├── state_manager.py     # Estados (Pickle)
│   ├── simulation_history.py # Historial (SQLite)
│   ├── csv_exporter.py      # Exportación (CSV)
│   └── persistence_manager.py # Coordinador
│
├── config/saved_configs/    # Configuraciones guardadas
├── saved_states/            # Estados de simulación
│   ├── snapshots/          # Automáticos
│   ├── manual_saves/       # Manuales
│   └── checkpoints/        # Recuperación
├── data/
│   └── simulation_history.db # Base de datos
└── exports/                 # Archivos CSV
```

## 🔧 Configuración

### Ajustar Frecuencia de Auto-guardado

```python
# Guardar cada 10 ticks en lugar de 5
engine.persistence.set_auto_save_config(
    enabled=True,
    interval=10
)
```

### Limpiar Datos Antiguos

```python
# Limpiar simulaciones de más de 30 días
deleted = engine.persistence.cleanup_old_data(
    days_to_keep=30,
    keep_snapshots=50
)
```

## 🧪 Verificación

Para verificar que todo funciona correctamente:

```bash
python test_persistence_system.py
```

Debe mostrar:
```
✅ ConfigManager: OK
✅ StateManager: OK
✅ SimulationHistory: OK
✅ CSVExporter: OK
✅ PersistenceManager: OK
✅ Todos los tests completados exitosamente
```

## 📈 Análisis de Datos

### Con Python/Pandas

```python
import pandas as pd

# Cargar datos exportados
df = pd.read_csv('exports/simulations_latest.csv')

# Análisis
print(df.groupby('winner').size())
print(df[['final_score_p1', 'final_score_p2']].describe())

# Visualización
df.plot(x='total_ticks', y='duration_seconds')
```

### Con Excel

1. Ejecutar: `engine.persistence.export_all_simulations_csv()`
2. Abrir archivos en `exports/` con Excel
3. Crear tablas dinámicas y gráficos

## 🎓 Recursos de Aprendizaje

### Para Comenzar
1. ✅ Leer este README
2. 📖 Revisar [`GUIA_USO_PERSISTENCIA.md`](GUIA_USO_PERSISTENCIA.md)
3. 🧪 Ejecutar `test_persistence_system.py`

### Para Profundizar
1. 📖 Leer [`SISTEMA_PERSISTENCIA.md`](SISTEMA_PERSISTENCIA.md)
2. 🖼️ Ver [`ejemplo_integracion_ui.py`](ejemplo_integracion_ui.py)
3. 🔍 Explorar código en `persistence/`

## ⚠️ Notas Importantes

1. **Auto-guardado activo:** El sistema guarda automáticamente cada 5 ticks
2. **Espacio en disco:** Los estados ocupan espacio. Usar limpieza periódica
3. **Compatibilidad:** No modificar estructura de clases entre guardados
4. **Estrategias:** Se recrean al cargar (no se serializan)

## 🐛 Solución de Problemas

| Problema | Solución |
|----------|----------|
| "No hay estados guardados" | Ejecutar al menos algunos ticks de simulación |
| Mucho espacio usado | `engine.persistence.cleanup_old_data()` |
| Error al cargar estado | Usar checkpoint: `engine.persistence.get_latest_checkpoint()` |
| Base de datos grande | `engine.persistence.history.cleanup_old_simulations(days=7)` |

## 💻 Integración con UI

Ver [`ejemplo_integracion_ui.py`](ejemplo_integracion_ui.py) para ejemplos de:
- Botones de guardar/cargar
- Diálogos de selección
- Visualización de estadísticas
- Atajos de teclado

**Atajos sugeridos:**
- `Ctrl+S`: Guardado rápido
- `Ctrl+E`: Exportar estadísticas
- `Ctrl+H`: Ver historial
- `Ctrl+R`: Recuperar simulación

## 📞 Soporte

**Documentación completa:**
- 📖 [`SISTEMA_PERSISTENCIA.md`](SISTEMA_PERSISTENCIA.md) - Referencia técnica
- 🎯 [`GUIA_USO_PERSISTENCIA.md`](GUIA_USO_PERSISTENCIA.md) - Guía práctica
- ✅ [`RESUMEN_IMPLEMENTACION_PERSISTENCIA.md`](RESUMEN_IMPLEMENTACION_PERSISTENCIA.md) - Estado del proyecto

**Código de ejemplo:**
- 🖼️ [`ejemplo_integracion_ui.py`](ejemplo_integracion_ui.py)
- 🧪 [`test_persistence_system.py`](test_persistence_system.py)

## ✅ Estado del Proyecto

**Versión:** 1.0.0  
**Estado:** ✅ Completo y Funcional  
**Tests:** ✅ Todos pasando  
**Documentación:** ✅ Completa  

### Características Implementadas

- ✅ Configuraciones (JSON)
- ✅ Estados de simulación (Pickle)
- ✅ Historial completo (SQLite)
- ✅ Exportación (CSV)
- ✅ Recuperación automática
- ✅ Auto-guardado
- ✅ Navegación temporal
- ✅ Limpieza automática

---

**Implementado:** Noviembre 10, 2025  
**Autor:** Sistema de Persistencia v1.0  
**Licencia:** Mismo que Rescue Simulator

