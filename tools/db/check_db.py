# -*- coding: utf-8 -*-
"""Script para verificar estructura y datos de la DB del dashboard."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "channel_monitor.db")

def check_database():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Base de datos no encontrada: {DB_PATH}")
        return
    
    print(f"[INFO] Base de datos: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Estructura de channels
    cursor.execute("PRAGMA table_info(channels)")
    print("\n[INFO] Estructura de tabla 'channels':")
    for col in cursor.fetchall():
        print(f"  - {col[1]} ({col[2]})")
    
    # Estructura de videos
    cursor.execute("PRAGMA table_info(videos)")
    print("\n[INFO] Estructura de tabla 'videos':")
    for col in cursor.fetchall():
        print(f"  - {col[1]} ({col[2]})")
    
    # Contar canales y videos
    cursor.execute("SELECT COUNT(*) FROM channels")
    print(f"\n[INFO] Canales monitoreados: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM videos")
    print(f"[INFO] Videos en la DB: {cursor.fetchone()[0]}")
    
    # Videos por canal (top 10)
    print("\n[INFO] Videos por canal (top 10):")
    cursor.execute("""
        SELECT c.channel_name, COUNT(v.id) as video_count 
        FROM channels c 
        LEFT JOIN videos v ON c.channel_id = v.channel_id 
        GROUP BY c.channel_id 
        ORDER BY video_count DESC 
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]} videos")
    
    # Videos más recientes (sin fecha nula)
    print("\n[INFO] Videos más recientes (con fecha):")
    cursor.execute("""
        SELECT v.title, v.channel_id, c.channel_name, v.published_at 
        FROM videos v 
        JOIN channels c ON v.channel_id = c.channel_id 
        WHERE v.published_at IS NOT NULL 
        ORDER BY v.published_at DESC 
        LIMIT 15
    """)
    for row in cursor.fetchall():
        print(f"  - {row[3]}: {row[0][:40]}... ({row[2]})")
    
    # Verificar si hay datos de fechas
    cursor.execute("SELECT COUNT(*) FROM videos WHERE published_at IS NULL")
    null_dates = cursor.fetchone()[0]
    print(f"\n[INFO] Videos sin fecha: {null_dates}")
    
    cursor.execute("SELECT COUNT(*) FROM videos WHERE published_at IS NOT NULL")
    with_dates = cursor.fetchone()[0]
    print(f"[INFO] Videos con fecha: {with_dates}")
    
    conn.close()
    print("\n[OK] Verificacion completada")

if __name__ == "__main__":
    check_database()