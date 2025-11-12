"""
Script simple para reiniciar todas las simulaciones
====================================================

Este script elimina TODAS las simulaciones de la base de datos
y limpia los estados guardados, dejando el sistema como nuevo.

Uso: python reiniciar_simulaciones.py
"""

from pathlib import Path
import sqlite3
from persistence import PersistenceManager

def find_database():
    """Busca la base de datos en múltiples ubicaciones posibles"""
    script_dir = Path(__file__).resolve().parent
    possible_paths = [
        script_dir / "data" / "simulation_history.db",  # Si se ejecuta desde rescue-simulator/
        script_dir.parent / "rescue-simulator" / "data" / "simulation_history.db",  # Si se ejecuta desde el proyecto raíz
        Path("data/simulation_history.db"),  # Ruta relativa actual
        Path("rescue-simulator/data/simulation_history.db"),  # Desde proyecto raíz
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None

def reiniciar_todo():
    """Reinicia completamente el sistema de persistencia"""
    
    print("=" * 60)
    print("  REINICIO COMPLETO DEL SISTEMA DE PERSISTENCIA")
    print("=" * 60)
    
    # Buscar la base de datos en múltiples ubicaciones
    db_path = find_database()
    if db_path is None:
        print("\nℹ️  La base de datos no existe aún")
        print("   No hay nada que reiniciar.")
        return True
    
    print(f"\n📁 Base de datos encontrada: {db_path}")
    
    # Mostrar estadísticas antes
    print("\n📊 ESTADO ACTUAL:")
    pm = PersistenceManager()
    summary = pm.get_statistics_summary()
    print(f"  Simulaciones: {summary.get('total_simulations', 0)}")
    
    storage_info = pm.get_storage_info()
    print(f"  Espacio usado: {storage_info['total_formatted']}")
    
    # Confirmación
    print("\n⚠️  ADVERTENCIA:")
    print("   Esto eliminará:")
    print("   - Todas las simulaciones de la base de datos")
    print("   - Todos los estados guardados (snapshots, checkpoints)")
    print("   - Todos los guardados manuales")
    print("\n   NO se eliminarán:")
    print("   - Configuraciones guardadas")
    print("   - Archivos CSV exportados")
    
    confirmacion = input("\n¿Continuar? Escribe 'SI' para confirmar: ").strip().upper()
    
    if confirmacion != 'SI':
        print("\n❌ Operación cancelada")
        return False
    
    try:
        print("\n🗑️  Eliminando simulaciones...")
        
        # Eliminar todas las simulaciones de la base de datos
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Contar antes
        cursor.execute("SELECT COUNT(*) FROM simulations")
        total_before = cursor.fetchone()[0]
        
        # Eliminar en orden (respetando integridad referencial)
        cursor.execute("DELETE FROM vehicle_stats")
        cursor.execute("DELETE FROM simulation_events")
        cursor.execute("DELETE FROM player_stats")
        cursor.execute("DELETE FROM simulations")
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Eliminadas {total_before} simulaciones")
        
        print("\n🗑️  Eliminando estados guardados...")
        
        # Limpiar estados
        pm.state_manager.clear_all_states(confirm=True)
        
        print("   ✅ Estados guardados eliminados")
        
        print("\n" + "=" * 60)
        print("  ✅ REINICIO COMPLETO EXITOSO")
        print("=" * 60)
        print("\nEl sistema está ahora como nuevo.")
        print("Puedes ejecutar el simulador para comenzar a registrar nuevas simulaciones.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante el reinicio: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        reiniciar_todo()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

