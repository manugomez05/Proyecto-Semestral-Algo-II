"""
Script para visualizar el contenido de la base de datos de simulaciones
=======================================================================

Este script permite ver fácilmente:
- Todas las simulaciones registradas
- Estadísticas de jugadores
- Estadísticas de vehículos
- Resumen estadístico

Uso: python ver_bd.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def format_datetime(iso_string):
    """Formatea una fecha ISO a formato legible"""
    if not iso_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_string

def format_duration(seconds):
    """Formatea duración en segundos a formato legible"""
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{seconds:.2f} seg"
    elif seconds < 3600:
        return f"{seconds/60:.2f} min"
    else:
        return f"{seconds/3600:.2f} horas"

def main():
    db_path = Path("data/simulation_history.db")
    
    if not db_path.exists():
        print("❌ La base de datos no existe aún")
        print("   Ejecuta el simulador primero para generar datos.")
        return
    
    print("=" * 70)
    print("  VISUALIZADOR DE BASE DE DATOS - Rescue Simulator")
    print("=" * 70)
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Ver todas las tablas
    print("\n📊 TABLAS DISPONIBLES:")
    print("-" * 70)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        # Contar registros en cada tabla
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  ✓ {table[0]:<25} ({count} registros)")
    
    # Ver simulaciones
    print("\n🎮 SIMULACIONES REGISTRADAS:")
    print("-" * 70)
    cursor.execute("""
        SELECT * FROM simulations 
        ORDER BY started_at DESC 
        LIMIT 20
    """)
    sims = cursor.fetchall()
    
    if sims:
        for i, sim in enumerate(sims, 1):
            status_icon = "✅" if sim['status'] == 'completed' else "⏳"
            winner = sim['winner'] if sim['winner'] else 'En curso'
            score_p1 = sim['final_score_p1'] if sim['final_score_p1'] is not None else 0
            score_p2 = sim['final_score_p2'] if sim['final_score_p2'] is not None else 0
            ticks = sim['total_ticks'] if sim['total_ticks'] is not None else 0
            duration = format_duration(sim['duration_seconds'] if 'duration_seconds' in sim.keys() else None)
            
            print(f"\n{status_icon} Simulación #{i}: {sim['simulation_id']}")
            print(f"   Estado: {sim['status']}")
            print(f"   Ganador: {winner}")
            print(f"   Puntajes: {score_p1} vs {score_p2}")
            print(f"   Ticks totales: {ticks}")
            print(f"   Duración: {duration}")
            print(f"   Inicio: {format_datetime(sim['started_at'])}")
            if sim['finished_at']:
                print(f"   Fin: {format_datetime(sim['finished_at'])}")
            if sim['end_reason']:
                print(f"   Razón: {sim['end_reason']}")
    else:
        print("  No hay simulaciones registradas aún")
        print("  Ejecuta el simulador y completa una partida para ver datos aquí.")
    
    # Ver estadísticas de jugadores
    print("\n\n👥 ESTADÍSTICAS DE JUGADORES:")
    print("-" * 70)
    cursor.execute("""
        SELECT * FROM player_stats 
        ORDER BY simulation_id DESC, player_name
        LIMIT 20
    """)
    stats = cursor.fetchall()
    
    if stats:
        for stat in stats:
            print(f"\n  Jugador: {stat['player_name']}")
            print(f"    Simulación: {stat['simulation_id']}")
            print(f"    Puntaje final: {stat['final_score']}")
            print(f"    Recursos recolectados: {stat['resources_collected']}")
            print(f"    Vehículos destruidos: {stat['vehicles_destroyed']}")
            print(f"    Vehículos sobrevivientes: {stat['vehicles_survived']}")
            print(f"    Distancia total: {stat['total_distance_traveled']:.2f}")
            print(f"    Colisiones: {stat['collisions']}")
            print(f"    Impactos de minas: {stat['mine_hits']}")
    else:
        print("  No hay estadísticas de jugadores aún")
    
    # Ver estadísticas de vehículos
    print("\n\n🚗 ESTADÍSTICAS DE VEHÍCULOS:")
    print("-" * 70)
    cursor.execute("""
        SELECT * FROM vehicle_stats 
        ORDER BY simulation_id DESC
        LIMIT 15
    """)
    vehicles = cursor.fetchall()
    
    if vehicles:
        for veh in vehicles:
            print(f"\n  Vehículo: {veh['vehicle_id']} ({veh['vehicle_type']})")
            print(f"    Jugador: {veh['player_name']}")
            print(f"    Simulación: {veh['simulation_id']}")
            print(f"    Estado final: {veh['status']}")
            print(f"    Distancia recorrida: {veh['distance_traveled']:.2f}")
            print(f"    Recursos recolectados: {veh['resources_collected']}")
            print(f"    Colisiones: {veh['collision_count']}")
    else:
        print("  No hay estadísticas de vehículos aún")
    
    # Resumen estadístico
    print("\n\n📈 RESUMEN ESTADÍSTICO:")
    print("-" * 70)
    
    # Total de simulaciones
    cursor.execute("SELECT COUNT(*) FROM simulations")
    total = cursor.fetchone()[0]
    
    # Simulaciones completadas
    cursor.execute("SELECT COUNT(*) FROM simulations WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    
    # Victorias por jugador
    cursor.execute("""
        SELECT winner, COUNT(*) as wins 
        FROM simulations 
        WHERE status = 'completed' AND winner IS NOT NULL
        GROUP BY winner
        ORDER BY wins DESC
    """)
    wins = cursor.fetchall()
    
    # Duración promedio
    cursor.execute("""
        SELECT AVG(duration_seconds) as avg_duration,
               AVG(total_ticks) as avg_ticks,
               AVG(final_score_p1) as avg_p1,
               AVG(final_score_p2) as avg_p2
        FROM simulations 
        WHERE status = 'completed'
    """)
    avg = cursor.fetchone()
    
    print(f"  Total de simulaciones: {total}")
    print(f"  Simulaciones completadas: {completed}")
    
    if wins:
        print(f"\n  Victorias por jugador:")
        for win in wins:
            print(f"    {win['winner']}: {win['wins']} victorias")
    
    if avg and avg['avg_duration'] is not None:
        print(f"\n  Promedios (simulaciones completadas):")
        print(f"    Duración: {format_duration(avg['avg_duration'])}")
        avg_ticks = avg['avg_ticks'] if avg['avg_ticks'] is not None else 0
        avg_p1 = avg['avg_p1'] if avg['avg_p1'] is not None else 0
        avg_p2 = avg['avg_p2'] if avg['avg_p2'] is not None else 0
        print(f"    Ticks: {avg_ticks:.0f}")
        print(f"    Puntaje Jugador 1: {avg_p1:.0f}")
        print(f"    Puntaje Jugador 2: {avg_p2:.0f}")
    
    # Estadísticas de jugadores agregadas
    cursor.execute("""
        SELECT 
            player_name,
            COUNT(*) as games,
            AVG(final_score) as avg_score,
            SUM(resources_collected) as total_resources,
            AVG(total_distance_traveled) as avg_distance
        FROM player_stats
        GROUP BY player_name
    """)
    player_summary = cursor.fetchall()
    
    if player_summary:
        print(f"\n  Estadísticas agregadas por jugador:")
        for ps in player_summary:
            print(f"\n    {ps['player_name']}:")
            print(f"      Partidas: {ps['games']}")
            print(f"      Puntaje promedio: {ps['avg_score']:.0f}")
            print(f"      Recursos totales: {ps['total_resources']}")
            print(f"      Distancia promedio: {ps['avg_distance']:.2f}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("  Fin del reporte")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

