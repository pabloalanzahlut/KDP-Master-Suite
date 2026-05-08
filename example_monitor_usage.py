"""
Ejemplo de Uso del Monitor de Canales
======================================
Este script demuestra cómo usar el sistema de monitoreo de canales
de forma programática.
"""

import sys
import time
from pathlib import Path

# Añadir el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent))

from db_manager import DatabaseManager
from channel_monitor_service import ChannelMonitorService


def print_separator():
    """Imprime un separador visual."""
    print("\n" + "="*70 + "\n")


def example_basic_usage():
    """Ejemplo básico de uso del monitor."""
    print("🔵 EJEMPLO 1: Uso Básico del Monitor")
    print_separator()
    
    # Inicializar servicios
    db = DatabaseManager()
    monitor = ChannelMonitorService(db_manager=db)
    
    # Configurar callbacks para ver logs
    def log_callback(message, level):
        prefix = {
            'info': '✓',
            'warning': '⚠',
            'error': '✗'
        }.get(level, 'ℹ')
        print(f"{prefix} {message}")
    
    monitor.set_callbacks(on_log=log_callback)
    
    # Añadir un canal de ejemplo
    print("Añadiendo canal de ejemplo...")
    channel_id = monitor.add_channel(
        "https://www.youtube.com/@TED",
        "TED Talks"
    )
    
    if channel_id:
        print(f"Canal añadido con ID: {channel_id}")
    
    # Listar canales
    print("\nCanales registrados:")
    channels = monitor.get_all_channels()
    for ch in channels:
        print(f"  - {ch['channel_name']} (ID: {ch['id']})")
    
    print_separator()


def example_check_videos():
    """Ejemplo de verificación de nuevos videos."""
    print("🔵 EJEMPLO 2: Verificar Nuevos Videos")
    print_separator()
    
    db = DatabaseManager()
    monitor = ChannelMonitorService(db_manager=db)
    
    # Configurar callback para nuevos videos
    def new_video_callback(video):
        print(f"📹 Nuevo video detectado: {video['title']}")
    
    monitor.set_callbacks(on_new_video=new_video_callback)
    
    # Verificar nuevos videos
    print("Verificando nuevos videos en canales...")
    new_count = monitor.check_for_new_videos()
    
    print(f"\nTotal de videos nuevos detectados: {new_count}")
    
    print_separator()


def example_process_videos():
    """Ejemplo de procesamiento de videos pendientes."""
    print("🔵 EJEMPLO 3: Procesar Videos Pendientes")
    print_separator()
    
    db = DatabaseManager()
    monitor = ChannelMonitorService(db_manager=db)
    
    # Configurar callback para videos procesados
    def processing_complete_callback(video):
        print(f"✅ Video procesado: {video['title']}")
    
    monitor.set_callbacks(on_processing_complete=processing_complete_callback)
    
    # Procesar videos pendientes (máximo 5)
    print("Procesando videos pendientes...")
    processed = monitor.process_pending_videos(max_videos=5)
    
    print(f"\nTotal de videos procesados: {processed}")
    
    print_separator()


def example_statistics():
    """Ejemplo de obtención de estadísticas."""
    print("🔵 EJEMPLO 4: Estadísticas del Sistema")
    print_separator()
    
    db = DatabaseManager()
    monitor = ChannelMonitorService(db_manager=db)
    
    stats = monitor.get_statistics()
    
    print("📊 Estadísticas:")
    print(f"  Canales activos: {stats.get('active_channels', 0)}")
    print(f"  Total de videos: {stats.get('total_videos', 0)}")
    print(f"  Videos pendientes: {stats.get('pending', 0)}")
    print(f"  Videos procesando: {stats.get('processing', 0)}")
    print(f"  Videos completados: {stats.get('completed', 0)}")
    print(f"  Videos fallidos: {stats.get('failed', 0)}")
    
    print_separator()


def example_automatic_monitoring():
    """Ejemplo de monitoreo automático."""
    print("🔵 EJEMPLO 5: Monitoreo Automático")
    print_separator()
    
    db = DatabaseManager()
    monitor = ChannelMonitorService(
        db_manager=db,
        interval_minutes=1,  # Verificar cada 1 minuto para el ejemplo
        max_videos_per_check=5
    )
    
    # Configurar callbacks
    def log_callback(message, level):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    monitor.set_callbacks(on_log=log_callback)
    
    # Iniciar monitoreo
    print("Iniciando monitoreo automático...")
    print("(Presiona Ctrl+C para detener)\n")
    
    monitor.start_monitoring()
    
    try:
        # Mantener el script corriendo
        while monitor.is_monitoring():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nDeteniendo monitoreo...")
        monitor.stop_monitoring()
        print("Monitor detenido.")
    
    print_separator()


def example_database_operations():
    """Ejemplo de operaciones directas con la base de datos."""
    print("🔵 EJEMPLO 6: Operaciones de Base de Datos")
    print_separator()
    
    db = DatabaseManager()
    
    # Añadir un canal
    print("Añadiendo canal...")
    channel_id = db.add_channel(
        "https://www.youtube.com/@example",
        "Canal de Ejemplo",
        "UC123456789"
    )
    print(f"Canal añadido con ID: {channel_id}")
    
    # Añadir un video
    print("\nAñadiendo video...")
    video_id = db.add_video(
        channel_id=channel_id,
        video_id="abc123xyz",
        video_url="https://youtube.com/watch?v=abc123xyz",
        title="Video de Ejemplo",
        published_at="2026-01-24"
    )
    print(f"Video añadido con ID: {video_id}")
    
    # Actualizar estado del video
    print("\nActualizando estado del video...")
    db.update_video_status(video_id, 'completed')
    print("Estado actualizado a 'completed'")
    
    # Obtener videos del canal
    print("\nVideos del canal:")
    videos = db.get_videos_by_channel(channel_id)
    for video in videos:
        print(f"  - {video['title']} [{video['status']}]")
    
    # Limpiar (eliminar canal de ejemplo)
    print("\nLimpiando datos de ejemplo...")
    db.remove_channel(channel_id)
    print("Canal eliminado.")
    
    print_separator()


def main():
    """Función principal que ejecuta todos los ejemplos."""
    print("\n" + "="*70)
    print("  EJEMPLOS DE USO - MONITOR DE CANALES YOUTUBE")
    print("="*70 + "\n")
    
    print("Selecciona un ejemplo para ejecutar:")
    print("1. Uso básico del monitor")
    print("2. Verificar nuevos videos")
    print("3. Procesar videos pendientes")
    print("4. Ver estadísticas")
    print("5. Monitoreo automático (Ctrl+C para detener)")
    print("6. Operaciones de base de datos")
    print("0. Ejecutar todos los ejemplos (excepto #5)")
    
    choice = input("\nOpción: ").strip()
    
    examples = {
        '1': example_basic_usage,
        '2': example_check_videos,
        '3': example_process_videos,
        '4': example_statistics,
        '5': example_automatic_monitoring,
        '6': example_database_operations,
    }
    
    if choice == '0':
        # Ejecutar todos excepto el monitoreo automático
        for key in ['1', '2', '3', '4', '6']:
            examples[key]()
    elif choice in examples:
        examples[choice]()
    else:
        print("Opción no válida.")


if __name__ == "__main__":
    main()
