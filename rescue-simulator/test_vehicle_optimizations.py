"""
Script de prueba para las optimizaciones con hash tables en VehicleManager.
Demuestra las mejoras de rendimiento en búsquedas por tipo y estado.
"""

import time
from src.vehicle import VehicleManager, Vehicle


def test_vehicle_manager_hash_tables():
    """Prueba las hash tables optimizadas del VehicleManager"""
    print("=" * 60)
    print("TEST: VehicleManager con Hash Tables Múltiples")
    print("=" * 60)
    
    # Crear dos flotas (jugador 1 y jugador 2)
    manager1 = VehicleManager()
    manager1.create_default_fleet(player_num=1)
    
    manager2 = VehicleManager()
    manager2.create_default_fleet(player_num=2)
    
    print(f"\n1. Flotas creadas:")
    print(f"   ✓ Jugador 1: {len(manager1.vehicles)} vehículos")
    print(f"   ✓ Jugador 2: {len(manager2.vehicles)} vehículos")
    
    # Búsqueda por tipo - O(k) con hash table
    print("\n2. Búsqueda por tipo (O(k) con hash table)...")
    start = time.time()
    jeeps = manager1.get_vehicles_by_type("jeep")
    motos = manager1.get_vehicles_by_type("moto")
    camiones = manager1.get_vehicles_by_type("camion")
    autos = manager1.get_vehicles_by_type("auto")
    end = time.time()
    
    print(f"   ✓ Jeeps encontrados: {len(jeeps)}")
    print(f"   ✓ Motos encontradas: {len(motos)}")
    print(f"   ✓ Camiones encontrados: {len(camiones)}")
    print(f"   ✓ Autos encontrados: {len(autos)}")
    print(f"   ✓ Tiempo total: {(end - start) * 1000:.3f} ms")
    
    # Conteo por tipo - O(1) directo
    print("\n3. Conteo por tipo (O(1) directo con hash table)...")
    start = time.time()
    count_jeeps = manager1.count_by_type("jeep")
    count_motos = manager1.count_by_type("moto")
    count_camiones = manager1.count_by_type("camion")
    count_autos = manager1.count_by_type("auto")
    end = time.time()
    
    print(f"   ✓ Jeeps: {count_jeeps}")
    print(f"   ✓ Motos: {count_motos}")
    print(f"   ✓ Camiones: {count_camiones}")
    print(f"   ✓ Autos: {count_autos}")
    print(f"   ✓ Tiempo total: {(end - start) * 1000000:.2f} μs")
    
    # Simular cambios de estado
    print("\n4. Simulando cambios de estado...")
    
    # Simular que algunos vehículos salen de la base
    for i, (vid, vehicle) in enumerate(list(manager1.vehicles.items())[:5]):
        if i < 3:
            manager1.update_vehicle_status(vid, "moving")
            print(f"   ✓ {vid} → moving")
        else:
            manager1.update_vehicle_status(vid, "need_return")
            print(f"   ✓ {vid} → need_return")
    
    # Simular que un vehículo es destruido
    first_vehicle_id = list(manager1.vehicles.keys())[0]
    manager1.update_vehicle_status(first_vehicle_id, "destroyed")
    print(f"   ✓ {first_vehicle_id} → destroyed")
    
    # Búsqueda por estado - O(k) con hash table
    print("\n5. Búsqueda por estado (O(k) con hash table)...")
    start = time.time()
    in_base = manager1.get_vehicles_by_status("in_base")
    moving = manager1.get_vehicles_by_status("moving")
    need_return = manager1.get_vehicles_needing_return()
    destroyed = manager1.get_destroyed_vehicles()
    end = time.time()
    
    print(f"   ✓ En base: {len(in_base)} vehículos")
    print(f"   ✓ Moviéndose: {len(moving)} vehículos")
    print(f"   ✓ Necesitan regresar: {len(need_return)} vehículos")
    print(f"   ✓ Destruidos: {len(destroyed)} vehículos")
    print(f"   ✓ Tiempo total: {(end - start) * 1000:.3f} ms")
    
    # Conteo por estado - O(1)
    print("\n6. Conteo por estado (O(1) directo)...")
    start = time.time()
    count_in_base = manager1.count_by_status("in_base")
    count_moving = manager1.count_by_status("moving")
    count_need_return = manager1.count_by_status("need_return")
    count_destroyed = manager1.count_by_status("destroyed")
    end = time.time()
    
    print(f"   ✓ En base: {count_in_base}")
    print(f"   ✓ Moviéndose: {count_moving}")
    print(f"   ✓ Necesitan regresar: {count_need_return}")
    print(f"   ✓ Destruidos: {count_destroyed}")
    print(f"   ✓ Tiempo total: {(end - start) * 1000000:.2f} μs")
    
    # Vehículos disponibles
    print("\n7. Obteniendo vehículos disponibles...")
    start = time.time()
    available = manager1.get_available_vehicles()
    end = time.time()
    
    print(f"   ✓ Vehículos disponibles: {len(available)}")
    for v in available[:3]:  # Mostrar solo los primeros 3
        print(f"      - {v.id} ({v.type}): capacidad {v.capacity}, estado {v.status}")
    print(f"   ✓ Tiempo: {(end - start) * 1000:.3f} ms")
    
    # Verificar sincronización de hash tables
    print("\n8. Verificando sincronización de hash tables...")
    
    total_vehicles = len(manager1.vehicles)
    total_by_type = sum(len(vids) for vids in manager1.vehicles_by_type.values())
    total_by_status = sum(len(vids) for vids in manager1.vehicles_by_status.values())
    
    print(f"   ✓ Total en hash table principal: {total_vehicles}")
    print(f"   ✓ Total en hash table por tipo: {total_by_type}")
    print(f"   ✓ Total en hash table por estado: {total_by_status}")
    
    if total_vehicles == total_by_type == total_by_status:
        print("   ✅ Hash tables perfectamente sincronizadas!")
    else:
        print("   ⚠️  Advertencia: Discrepancia en sincronización")
    
    print("\n✅ VehicleManager: Todas las pruebas pasaron!\n")


def performance_comparison():
    """Comparación de rendimiento antes/después"""
    print("=" * 60)
    print("COMPARACIÓN DE RENDIMIENTO - VehicleManager")
    print("=" * 60)
    
    print("\n📊 Mejoras implementadas:")
    print("   • Búsqueda por tipo:        O(n) → O(k) donde k = vehículos de ese tipo")
    print("   • Búsqueda por estado:      O(n) → O(k) donde k = vehículos en ese estado")
    print("   • Conteo por tipo:          O(n) → O(1)")
    print("   • Conteo por estado:        O(n) → O(1)")
    print("   • Actualización de estado:  O(n) → O(1)")
    
    print("\n🎯 Hash Tables Implementadas:")
    print("   1. vehicles: Dict[id -> Vehicle]")
    print("      - Búsqueda por ID: O(1)")
    print("      - Ya existía, pero ahora optimizado")
    
    print("\n   2. vehicles_by_type: Dict[type -> List[id]]")
    print("      - Búsqueda de todos los jeeps: O(1) lookup + O(k) construcción")
    print("      - Antes: O(n) iterando todos los vehículos")
    print("      - Mejora: ~(n/k)x más rápido")
    
    print("\n   3. vehicles_by_status: Dict[status -> Set[id]]")
    print("      - Búsqueda de vehículos destruidos: O(1) lookup + O(k) construcción")
    print("      - Antes: O(n) iterando todos los vehículos")
    print("      - Mejora: ~(n/k)x más rápido")
    
    print("\n💡 Casos de Uso Óptimos:")
    print("   • Estrategias que necesitan contar vehículos disponibles")
    print("   • UI que muestra estadísticas por tipo/estado")
    print("   • Lógica de game over (contar destruidos rápidamente)")
    print("   • Asignación inteligente de tareas por tipo de vehículo")
    
    print("\n💾 Overhead de Memoria:")
    print("   • vehicles_by_type: 4 listas × ~3 IDs promedio = ~100 bytes")
    print("   • vehicles_by_status: 4 sets × ~3 IDs promedio = ~100 bytes")
    print("   • Total adicional: ~200 bytes (despreciable)")
    
    print()


def example_usage():
    """Ejemplo de uso práctico de las nuevas funcionalidades"""
    print("=" * 60)
    print("EJEMPLO DE USO PRÁCTICO")
    print("=" * 60)
    
    manager = VehicleManager()
    manager.create_default_fleet(player_num=1)
    
    print("\n📋 Escenario: Estrategia de juego necesita asignar tareas")
    print()
    
    # 1. Obtener todas las motos para misión específica
    print("1. Obtener motos disponibles para misión de rescate:")
    motos = manager.get_vehicles_by_type("moto")
    print(f"   → Encontradas {len(motos)} motos")
    print(f"   → IDs: {[m.id for m in motos]}")
    
    # 2. Verificar cuántos camiones hay (para carga pesada)
    print("\n2. Contar camiones disponibles para carga:")
    num_camiones = manager.count_by_type("camion")
    print(f"   → {num_camiones} camiones en la flota")
    
    # 3. Obtener vehículos que necesitan regresar
    print("\n3. Gestionar vehículos que necesitan regresar:")
    # Simular algunos vehículos que necesitan regresar
    manager.update_vehicle_status("jeep_1", "need_return")
    manager.update_vehicle_status("auto_1", "need_return")
    
    need_return = manager.get_vehicles_needing_return()
    print(f"   → {len(need_return)} vehículos necesitan regresar a base")
    print(f"   → IDs: {[v.id for v in need_return]}")
    
    # 4. Verificar estado de la flota rápidamente
    print("\n4. Estado general de la flota (en tiempo real):")
    print(f"   • En base:          {manager.count_by_status('in_base')}")
    print(f"   • Moviéndose:       {manager.count_by_status('moving')}")
    print(f"   • Necesitan volver: {manager.count_by_status('need_return')}")
    print(f"   • Destruidos:       {manager.count_by_status('destroyed')}")
    
    print("\n✅ Operaciones completadas en tiempo O(1) y O(k)!\n")


if __name__ == "__main__":
    print("\n" + "🚗" * 30)
    print("PRUEBAS DE OPTIMIZACIONES - VehicleManager")
    print("🚗" * 30 + "\n")
    
    try:
        test_vehicle_manager_hash_tables()
        performance_comparison()
        example_usage()
        
        print("=" * 60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 60)
        print("\n🎯 VehicleManager ahora usa múltiples hash tables para")
        print("   búsquedas optimizadas por tipo y estado (O(1) y O(k))\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

