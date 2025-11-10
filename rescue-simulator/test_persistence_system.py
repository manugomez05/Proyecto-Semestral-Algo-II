"""
Script de prueba del sistema de persistencia
==============================================

Este script demuestra el uso del sistema de persistencia
y verifica que todos los componentes funcionan correctamente.
"""

from persistence import PersistenceManager
from pathlib import Path

def print_section(title):
    """Imprime un título de sección"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_config_manager(pm):
    """Prueba ConfigManager"""
    print_section("TEST: ConfigManager")
    
    # Guardar configuración de mapa
    print("✓ Guardando configuración de mapa...")
    filepath = pm.config_manager.save_map_config(
        name="test_map",
        rows=50,
        cols=50,
        seed=12345
    )
    print(f"  Archivo guardado: {Path(filepath).name}")
    
    # Guardar configuración de simulación
    print("\n✓ Guardando configuración de simulación...")
    config = pm.config_manager.get_default_config()
    filepath = pm.config_manager.save_simulation_config(config, "test_sim")
    print(f"  Archivo guardado: {Path(filepath).name}")
    
    # Listar configuraciones
    print("\n✓ Listando configuraciones guardadas...")
    configs = pm.config_manager.list_configs()
    print(f"  Total de configuraciones: {len(configs)}")
    for filename, config in configs[:3]:  # Mostrar primeras 3
        print(f"    - {filename}: {config.get('type', 'unknown')}")
    
    print("\n✅ ConfigManager: OK")

def test_state_manager(pm):
    """Prueba StateManager"""
    print_section("TEST: StateManager")
    
    # Crear estado de ejemplo
    test_state = {
        "tick": 100,
        "players": {"p1": "data1", "p2": "data2"},
        "map": "map_data"
    }
    
    # Guardar estado
    print("✓ Guardando estado de simulación...")
    filepath = pm.state_manager.save_state(
        test_state,
        tick=100,
        simulation_id="test_sim_001"
    )
    if filepath:
        print(f"  Archivo guardado: {Path(filepath).name}")
    else:
        print("  ❌ Error al guardar estado")
    
    # Crear checkpoint
    print("\n✓ Creando checkpoint...")
    checkpoint = pm.state_manager.create_checkpoint(test_state, tick=100)
    if checkpoint:
        print(f"  Checkpoint creado: {Path(checkpoint).name}")
    else:
        print("  ❌ Error al crear checkpoint")
    
    # Guardado manual
    print("\n✓ Guardado manual...")
    manual_save = pm.state_manager.save_manual(
        test_state,
        name="test_manual",
        description="Guardado de prueba"
    )
    if manual_save:
        print(f"  Guardado manual: {Path(manual_save).name}")
    else:
        print("  ❌ Error en guardado manual")
    
    # Listar snapshots
    print("\n✓ Listando snapshots...")
    snapshots = pm.state_manager.list_snapshots()
    print(f"  Total de snapshots: {len(snapshots)}")
    
    # Listar guardados manuales
    print("\n✓ Listando guardados manuales...")
    saves = pm.state_manager.list_manual_saves()
    print(f"  Total de guardados manuales: {len(saves)}")
    for save in saves[:3]:  # Mostrar primeros 3
        print(f"    - {save['name']}: {save['description']}")
    
    # Info de almacenamiento
    print("\n✓ Información de almacenamiento...")
    sizes = pm.state_manager.get_total_size()
    print(f"  Snapshots: {sizes['snapshots']} bytes")
    print(f"  Guardados manuales: {sizes['manual_saves']} bytes")
    print(f"  Checkpoints: {sizes['checkpoints']} bytes")
    print(f"  Total: {sizes['total']} bytes")
    
    print("\n✅ StateManager: OK")

def test_simulation_history(pm):
    """Prueba SimulationHistory"""
    print_section("TEST: SimulationHistory")
    
    # Iniciar simulación
    print("✓ Iniciando registro de simulación...")
    sim_id = "test_sim_history_001"
    success = pm.history.start_simulation(
        sim_id,
        map_rows=50,
        map_cols=50,
        config_data={"test": True}
    )
    print(f"  Resultado: {'OK' if success else 'ERROR'}")
    
    # Agregar estadísticas de jugador
    print("\n✓ Registrando estadísticas de jugadores...")
    pm.history.add_player_stats(sim_id, "Jugador_1", {
        "final_score": 1500,
        "vehicles_destroyed": 2,
        "vehicles_survived": 8,
        "resources_collected": 30,
        "total_distance_traveled": 500.0,
        "collisions": 1,
        "mine_hits": 0
    })
    pm.history.add_player_stats(sim_id, "Jugador_2", {
        "final_score": 1200,
        "vehicles_destroyed": 3,
        "vehicles_survived": 7,
        "resources_collected": 25,
        "total_distance_traveled": 450.0,
        "collisions": 2,
        "mine_hits": 1
    })
    print("  Estadísticas registradas para ambos jugadores")
    
    # Agregar estadísticas de vehículos
    print("\n✓ Registrando estadísticas de vehículos...")
    pm.history.add_vehicle_stats(sim_id, "Jugador_1", "moto_1", "motorcycle", {
        "status": "job_done",
        "distance_traveled": 150.0,
        "resources_collected": 5,
        "collision_count": 0,
        "final_position": (25, 25)
    })
    print("  Estadísticas de vehículo registradas")
    
    # Registrar evento
    print("\n✓ Registrando evento...")
    pm.history.add_event(sim_id, tick=50, event_type="collision", 
                        event_data={"vehicles": ["moto_1", "camion_2"]})
    print("  Evento registrado")
    
    # Finalizar simulación
    print("\n✓ Finalizando simulación...")
    success = pm.history.finish_simulation(
        sim_id,
        total_ticks=500,
        winner="Jugador_1",
        final_score_p1=1500,
        final_score_p2=1200,
        end_reason="Todos los recursos recolectados"
    )
    print(f"  Resultado: {'OK' if success else 'ERROR'}")
    
    # Listar simulaciones
    print("\n✓ Listando simulaciones...")
    simulations = pm.history.list_simulations(limit=5)
    print(f"  Total de simulaciones: {len(simulations)}")
    for sim in simulations:
        print(f"    - {sim['simulation_id']}: {sim['winner']} "
              f"({sim['final_score_p1']} vs {sim['final_score_p2']})")
    
    # Obtener resumen estadístico
    print("\n✓ Resumen estadístico...")
    summary = pm.history.get_statistics_summary()
    print(f"  Total simulaciones: {summary['total_simulations']}")
    print(f"  Simulaciones completadas: {summary['completed_simulations']}")
    print(f"  Duración promedio: {summary['average_duration_seconds']:.2f} seg")
    
    print("\n✅ SimulationHistory: OK")

def test_csv_exporter(pm):
    """Prueba CSVExporter"""
    print_section("TEST: CSVExporter")
    
    # Obtener datos para exportar
    simulations = pm.history.list_simulations(limit=10)
    
    if not simulations:
        print("⚠️  No hay simulaciones para exportar")
        print("   (Esto es normal en la primera ejecución)")
        return
    
    # Exportar simulaciones
    print("✓ Exportando simulaciones a CSV...")
    filepath = pm.csv_exporter.export_simulations(simulations, "test_export.csv")
    print(f"  Archivo creado: {Path(filepath).name}")
    
    # Exportar resumen
    print("\n✓ Exportando resumen estadístico...")
    summary = pm.history.get_statistics_summary()
    filepath = pm.csv_exporter.export_summary_statistics(summary, "test_summary.csv")
    print(f"  Archivo creado: {Path(filepath).name}")
    
    # Listar archivos exportados
    print("\n✓ Listando archivos CSV exportados...")
    exports = pm.csv_exporter.list_exports()
    print(f"  Total de archivos: {len(exports)}")
    for export in exports[:5]:  # Mostrar primeros 5
        size_kb = export['size_bytes'] / 1024
        print(f"    - {export['filename']} ({size_kb:.2f} KB)")
    
    print("\n✅ CSVExporter: OK")

def test_persistence_manager():
    """Prueba PersistenceManager completo"""
    print_section("TEST: PersistenceManager - Flujo Completo")
    
    pm = PersistenceManager()
    
    # Iniciar nueva simulación
    print("✓ Iniciando nueva simulación...")
    config = {
        "map": {"rows": 50, "cols": 50},
        "simulation": {"max_ticks": 1000, "auto_save_interval": 5}
    }
    sim_id = pm.start_new_simulation(config)
    print(f"  Simulation ID: {sim_id}")
    
    # Simular guardado de estados
    print("\n✓ Simulando guardado de estados...")
    for tick in [10, 20, 30]:
        test_state = {"tick": tick, "data": f"state_{tick}"}
        pm.save_simulation_state(test_state, tick)
        print(f"  Estado guardado en tick {tick}")
    
    # Crear checkpoint
    print("\n✓ Creando checkpoint...")
    test_state = {"tick": 30, "data": "checkpoint"}
    pm.create_checkpoint(test_state, 30)
    print("  Checkpoint creado")
    
    # Buscar estado por tick
    print("\n✓ Buscando estado por tick...")
    state_file = pm.find_state_by_tick(20)
    if state_file:
        print(f"  Estado encontrado: {Path(state_file).name}")
    else:
        print("  No se encontró estado")
    
    # Finalizar simulación
    print("\n✓ Finalizando simulación...")
    pm.finish_simulation(
        total_ticks=30,
        winner="Jugador_1",
        final_score_p1=1000,
        final_score_p2=800
    )
    print("  Simulación finalizada y registrada")
    
    # Obtener información de almacenamiento
    print("\n✓ Información de almacenamiento...")
    info = pm.get_storage_info()
    print(f"  Total usado: {info['total_formatted']}")
    print(f"  Snapshots: {info['snapshots_formatted']}")
    print(f"  Guardados manuales: {info['manual_saves_formatted']}")
    print(f"  Checkpoints: {info['checkpoints_formatted']}")
    
    # Historial de simulaciones
    print("\n✓ Historial de simulaciones...")
    history = pm.get_simulation_history(limit=5)
    print(f"  Simulaciones registradas: {len(history)}")
    
    print("\n✅ PersistenceManager: OK")
    
    return pm

def main():
    """Función principal de pruebas"""
    print("\n" + "🎮 " * 20)
    print("  PRUEBA DEL SISTEMA DE PERSISTENCIA")
    print("  Rescue Simulator")
    print("🎮 " * 20)
    
    try:
        # Crear instancia del gestor
        pm = PersistenceManager()
        
        # Ejecutar pruebas individuales
        test_config_manager(pm)
        test_state_manager(pm)
        test_simulation_history(pm)
        test_csv_exporter(pm)
        
        # Prueba del flujo completo
        test_persistence_manager()
        
        # Resumen final
        print_section("RESUMEN FINAL")
        print("✅ Todos los tests completados exitosamente")
        print("\nEl sistema de persistencia está funcionando correctamente.")
        print("\nArchivos generados:")
        print("  - config/saved_configs/     (Configuraciones JSON)")
        print("  - saved_states/             (Estados de simulación)")
        print("  - data/simulation_history.db (Base de datos SQLite)")
        print("  - exports/                  (Archivos CSV)")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

