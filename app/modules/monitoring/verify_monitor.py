# -*- coding: utf-8 -*-
"""
Verificacion del sistema de monitoreo de canales.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "channel_monitor.db")

def main():
    print("="*60)
    print("VERIFICACION DEL SISTEMA DE MONITOREO")
    print("="*60)
    
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] DB no encontrada: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Canales con prioridad alta (4-5)
    print("\n[INFO] Canales de alta prioridad (4-5):")
    c.execute("SELECT id, channel_name, priority, last_checked FROM channels WHERE priority >= 4 ORDER BY priority DESC")
    high_priority = c.fetchall()
    for ch in high_priority:
        print(f"  ID {ch[0]}: {ch[1]} (prioridad: {ch[2]}, ultimo check: {ch[3]})")
    
    # 2. Canales nunca checkeados o con check muy antiguo
    print("\n[INFO] Canales sin checkear o muy antiguos:")
    c.execute("""
        SELECT id, channel_name, last_checked, active 
        FROM channels 
        WHERE last_checked IS NULL 
           OR last_checked < datetime('now', '-2 days')
        ORDER BY last_checked
    """)
    stale = c.fetchall()
    for ch in stale:
        print(f"  ID {ch[0]}: {ch[1]} (ultimo: {ch[2]}, activo: {ch[3]})")
    
    # 3. Videos por dia (ultimos 30 dias)
    print("\n[INFO] Videos por dia (ultimos 30 dias):")
    c.execute("""
        SELECT DATE(discovered_at) as dia, COUNT(*) as count
        FROM videos
        WHERE discovered_at >= datetime('now', '-30 days')
        GROUP BY DATE(discovered_at)
        ORDER BY dia DESC
    """)
    por_dia = c.fetchall()
    for dia, count in por_dia:
        print(f"  {dia}: {count} videos")
    
    # 4. Verificar estructura de la DB
    print("\n[INFO] Verificando estructura...")
    c.execute("PRAGMA table_info(channels)")
    print("  Columnas de channels:", [col[1] for col in c.fetchall()])
    
    c.execute("PRAGMA table_info(videos)")
    print("  Columnas de videos:", [col[1] for col in c.fetchall()])
    
    conn.close()
    print("\n[OK] Verificacion completada")

if __name__ == "__main__":
    main()