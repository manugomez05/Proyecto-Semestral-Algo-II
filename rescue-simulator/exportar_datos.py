"""
Script para exportar datos de simulaciones a CSV
"""
import sqlite3
import csv
from pathlib import Path
from datetime import datetime

def main():
    # ✅ Usar ruta absoluta basada en la ubicación del script
    script_dir = Path(__file__).resolve().parent
    db_path = script_dir / "data" / "simulation_history.db"
    
    print("=" * 70)
    print("  EXPORTADOR DE DATOS A CSV - Rescue Simulator")
    print("=" * 70)
    print(f"\n🔍 Buscando BD en: {db_path}")
    
    if not db_path.exists():
        print(f"❌ No existe la base de datos en: {db_path}")
        print(f"\n💡 Verificando rutas alternativas...")
        
        # Intentar otras ubicaciones posibles
        alt_paths = [
            script_dir / "data" / "simulation_history.db",
            script_dir.parent / "rescue-simulator" / "data" / "simulation_history.db",
            Path("data/simulation_history.db"),
        ]
        
        for alt_path in alt_paths:
            if alt_path.exists():
                print(f"✅ Encontrada en: {alt_path}")
                db_path = alt_path
                break
        else:
            print("\n❌ No se encontró la base de datos en ninguna ubicación")
            return
    
    print(f"✅ Base de datos encontrada: {db_path}")
    print(f"📏 Tamaño: {db_path.stat().st_size / 1024:.2f} KB\n")
    
    # Crear directorio de exports si no existe
    exports_dir = script_dir / "exports"
    exports_dir.mkdir(exist_ok=True)
    
    try:
        exportar_datos_unificados(db_path, exports_dir)
    except Exception as e:
        print(f"\n❌ Error durante la exportación: {e}")
        import traceback
        traceback.print_exc()


def get_table_columns(cursor, table_name):
    """Obtiene las columnas reales de una tabla"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return columns


def exportar_datos_unificados(db_path: Path, exports_dir: Path):
    """Exporta TODOS los datos en UN SOLO archivo CSV unificado"""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 🔍 Verificar columnas disponibles
    print("🔍 Verificando esquema de la base de datos...")
    vehicle_cols = get_table_columns(cursor, 'vehicle_stats')
    print(f"   Columnas en vehicle_stats: {', '.join(vehicle_cols)}\n")
    
    # Verificar si existen las columnas opcionales
    has_collisions = 'collisions' in vehicle_cols
    has_mine_hits = 'mine_hits' in vehicle_cols
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = exports_dir / f"estadisticas_completas_{timestamp}.csv"
    
    print("=" * 70)
    print("📊 GENERANDO ARCHIVO CSV UNIFICADO")
    print("=" * 70)
    print()
    
    # 🔥 CONSULTA UNIFICADA adaptada al esquema real
    collisions_col = "vs.collisions" if has_collisions else "0"
    mine_hits_col = "vs.mine_hits" if has_mine_hits else "0"
    
    query = f"""
        SELECT 
            -- Información de la Simulación
            s.simulation_id,
            s.status as estado_simulacion,
            s.winner as ganador,
            s.total_ticks as ticks_totales,
            s.duration_seconds as duracion_segundos,
            ROUND(s.duration_seconds / 60.0, 2) as duracion_minutos,
            s.started_at as fecha_inicio,
            s.finished_at as fecha_fin,
            s.end_reason as razon_finalizacion,
            
            -- Información del Jugador
            ps.player_name as jugador,
            ps.final_score as puntaje_final,
            ps.resources_collected as recursos_recolectados,
            ps.vehicles_destroyed as vehiculos_destruidos,
            ps.vehicles_survived as vehiculos_sobrevivientes,
            ps.total_distance_traveled as distancia_total,
            ps.collisions as colisiones,
            ps.mine_hits as impactos_minas,
            
            -- Información del Vehículo
            vs.vehicle_id as id_vehiculo,
            vs.vehicle_type as tipo_vehiculo,
            vs.status as estado_vehiculo,
            vs.distance_traveled as distancia_vehiculo,
            vs.resources_collected as recursos_vehiculo,
            {collisions_col} as colisiones_vehiculo,
            {mine_hits_col} as impactos_minas_vehiculo,
            
            -- Métricas Calculadas
            CASE 
                WHEN s.winner = ps.player_name THEN 'Victoria'
                WHEN s.winner IS NULL THEN 'Empate'
                ELSE 'Derrota'
            END as resultado,
            
            ROUND(CAST(ps.resources_collected AS FLOAT) / NULLIF(s.total_ticks, 0), 4) as recursos_por_tick,
            ROUND(CAST(ps.total_distance_traveled AS FLOAT) / NULLIF(s.total_ticks, 0), 4) as distancia_por_tick,
            ROUND(CAST(vs.resources_collected AS FLOAT) / NULLIF(vs.distance_traveled, 0), 4) as eficiencia_vehiculo,
            
            -- Porcentajes
            ROUND(CAST(ps.vehicles_survived AS FLOAT) / NULLIF(ps.vehicles_destroyed + ps.vehicles_survived, 0) * 100, 2) as porcentaje_supervivencia,
            ROUND(CAST(ps.collisions AS FLOAT) / NULLIF(ps.total_distance_traveled, 0) * 100, 4) as tasa_colisiones,
            ROUND(CAST(ps.mine_hits AS FLOAT) / NULLIF(ps.total_distance_traveled, 0) * 100, 4) as tasa_impactos_minas
            
        FROM simulations s
        INNER JOIN player_stats ps ON s.simulation_id = ps.simulation_id
        LEFT JOIN vehicle_stats vs ON ps.simulation_id = vs.simulation_id 
                                    AND ps.player_name = vs.player_name
        ORDER BY s.started_at DESC, ps.player_name, vs.vehicle_id
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("⚠️  No hay datos para exportar")
        conn.close()
        return
    
    # Escribir CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in rows:
            writer.writerow(dict(row))
    
    conn.close()
    
    # Estadísticas del archivo generado
    total_rows = len(rows)
    simulaciones_unicas = len(set(row['simulation_id'] for row in rows))
    jugadores_unicos = len(set(row['jugador'] for row in rows))
    
    print("=" * 70)
    print("  ✅ EXPORTACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    print(f"\n📊 Estadísticas del archivo generado:")
    print(f"   • Total de registros: {total_rows}")
    print(f"   • Simulaciones únicas: {simulaciones_unicas}")
    print(f"   • Jugadores únicos: {jugadores_unicos}")
    print(f"   • Columnas: {len(fieldnames)}")
    print(f"\n📂 Archivo guardado en:")
    print(f"   {output_file}")
    print(f"\n📏 Tamaño del archivo: {output_file.stat().st_size / 1024:.2f} KB")
    print("\n📋 Columnas incluidas:")
    for i, col in enumerate(fieldnames, 1):
        print(f"   {i:2d}. {col}")
    
    if not has_collisions or not has_mine_hits:
        print("\n⚠️  Nota: Algunas columnas de vehículos no están disponibles:")
        if not has_collisions:
            print("   • collisions (se usó valor 0)")
        if not has_mine_hits:
            print("   • mine_hits (se usó valor 0)")
    
    print("=" * 70)


if __name__ == "__main__":
    main()