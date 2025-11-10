"""
Script para limpiar/reiniciar las simulaciones guardadas
==========================================================

Este script elimina TODAS las simulaciones de la base de datos
y limpia los estados guardados, dejando el sistema como nuevo.

Uso: python limpiar_bd.py
"""

from pathlib import Path
import sqlite3
from persistence import PersistenceManager

def main():
    """Función principal"""
    
    print("=" * 70)
    print("  LIMPIEZA Y REINICIO DEL SISTEMA DE PERSISTENCIA")
    print("=" * 70)
    
    # Verificar que existe la base de datos
    db_path = Path("data/simulation_history.db")
    if not db_path.exists():
        print("\nℹ️  La base de datos no existe aún")
        print("   No hay nada que limpiar.")
        return
    
    # Mostrar estadísticas antes
    print("\n📊 ESTADO ACTUAL:")
    pm = PersistenceManager()
    
    try:
        summary = pm.get_statistics_summary()
        print(f"  Simulaciones totales: {summary.get('total_simulations', 0)}")
        print(f"  Simulaciones completadas: {summary.get('completed_simulations', 0)}")
        
        storage_info = pm.get_storage_info()
        print(f"  Espacio usado: {storage_info['total_formatted']}")
    except Exception as e:
        print(f"  ⚠️  Error al leer estadísticas: {e}")
    
    # Confirmación
    print("\n" + "=" * 70)
    print("  ⚠️  ADVERTENCIA")
    print("=" * 70)
    print("\nEsto eliminará:")
    print("  ✓ Todas las simulaciones de la base de datos")
    print("  ✓ Todos los estados guardados (snapshots, checkpoints)")
    print("  ✓ Todos los guardados manuales")
    print("\nNO se eliminarán:")
    print("  ✓ Configuraciones guardadas (config/saved_configs/)")
    print("  ✓ Archivos CSV exportados (exports/)")
    
    print("\n" + "-" * 70)
    confirmacion = input("¿Continuar? Escribe 'SI' (en mayúsculas) para confirmar: ").strip()
    
    if confirmacion.upper() != 'SI':
        print("\n❌ Operación cancelada")
        return
    
    try:
        print("\n🗑️  Iniciando limpieza...")
        print("-" * 70)
        
        # 1. Eliminar todas las simulaciones de la base de datos
        print("\n1️⃣  Eliminando simulaciones de la base de datos...")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Contar antes
        cursor.execute("SELECT COUNT(*) FROM simulations")
        total_sims = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM player_stats")
        total_stats = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vehicle_stats")
        total_vehicles = cursor.fetchone()[0]
        
        # Eliminar en orden (respetando integridad referencial)
        cursor.execute("DELETE FROM vehicle_stats")
        cursor.execute("DELETE FROM simulation_events")
        cursor.execute("DELETE FROM player_stats")
        cursor.execute("DELETE FROM simulations")
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Eliminadas {total_sims} simulaciones")
        print(f"   ✅ Eliminadas {total_stats} estadísticas de jugadores")
        print(f"   ✅ Eliminadas {total_vehicles} estadísticas de vehículos")
        
        # 2. Limpiar estados guardados
        print("\n2️⃣  Eliminando estados guardados...")
        
        # Obtener información antes
        info_before = pm.get_storage_info()
        snapshots_before = info_before['snapshots_bytes']
        manual_before = info_before['manual_saves_bytes']
        checkpoints_before = info_before['checkpoints_bytes']
        
        # Limpiar estados
        pm.state_manager.clear_all_states(confirm=True)
        
        print(f"   ✅ Snapshots eliminados ({info_before['snapshots_formatted']})")
        print(f"   ✅ Guardados manuales eliminados ({info_before['manual_saves_formatted']})")
        print(f"   ✅ Checkpoints eliminados ({info_before['checkpoints_formatted']})")
        
        # 3. Verificar resultado
        print("\n3️⃣  Verificando resultado...")
        
        # Verificar base de datos
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM simulations")
        remaining = cursor.fetchone()[0]
        conn.close()
        
        if remaining == 0:
            print("   ✅ Base de datos limpiada correctamente")
        else:
            print(f"   ⚠️  Quedan {remaining} simulaciones (puede ser normal)")
        
        # Verificar estados
        info_after = pm.get_storage_info()
        if info_after['total_bytes'] == 0:
            print("   ✅ Estados guardados eliminados correctamente")
        else:
            print(f"   ⚠️  Quedan {info_after['total_formatted']} de estados")
        
        print("\n" + "=" * 70)
        print("  ✅ LIMPIEZA COMPLETA EXITOSA")
        print("=" * 70)
        print("\nEl sistema está ahora como nuevo.")
        print("Puedes ejecutar el simulador para comenzar a registrar nuevas simulaciones.")
        print("\n💡 Tip: Usa 'python ver_bd.py' para verificar que todo está limpio.")
        
    except Exception as e:
        print(f"\n❌ Error durante la limpieza: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  La limpieza puede haber quedado incompleta.")
        print("   Verifica manualmente la base de datos si es necesario.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

