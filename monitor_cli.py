"""
KDP_MASTER - Monitor CLI
========================
Herramienta de línea de comandos para gestionar el monitoreo de canales.
"""

import sys
import argparse
from pathlib import Path
from colorama import init, Fore, Style
from tabulate import tabulate

# Añadir el directorio padre al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from app.database.db_manager import DatabaseManager
from app.services.monitor_service import ChannelMonitorService

# Inicializar colorama
init(autoreset=True)


def print_banner():
    """Imprime el banner de la aplicación."""
    print(f"{Fore.MAGENTA}")
    print("=" * 60)
    print("   KDP MASTER - MONITOR DE CANALES YOUTUBE")
    print("=" * 60)
    print(f"{Style.RESET_ALL}\n")


def cmd_add(args):
    """Añade un nuevo canal al monitoreo."""
    db = DatabaseManager()
    monitor = ChannelMonitorService(db_manager=db)
    
    channel_id = monitor.add_channel(args.url, args.name)
    
    if channel_id:
        print(f"{Fore.GREEN}✓ Canal añadido exitosamente: {args.name}{Style.RESET_ALL}")
        print(f"  ID: {channel_id}")
        print(f"  URL: {args.url}")
    else:
        print(f"{Fore.YELLOW}⚠ El canal ya existe o hubo un error.{Style.RESET_ALL}")


def cmd_list(args):
    """Lista todos los canales monitoreados."""
    db = DatabaseManager()
    channels = db.get_all_channels(active_only=False)
    
    if not channels:
        print(f"{Fore.YELLOW}No hay canales registrados.{Style.RESET_ALL}")
        return
    
    # Preparar datos para la tabla
    table_data = []
    for ch in channels:
        status = f"{Fore.GREEN}✓ Activo{Style.RESET_ALL}" if ch['active'] else f"{Fore.RED}✗ Inactivo{Style.RESET_ALL}"
        last_checked = ch['last_checked'] or "Nunca"
        
        table_data.append([
            ch['id'],
            ch['channel_name'],
            status,
            last_checked
        ])
    
    headers = ["ID", "Nombre", "Estado", "Última Verificación"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\n{Fore.CYAN}Total: {len(channels)} canales{Style.RESET_ALL}")


def cmd_remove(args):
    """Elimina un canal del monitoreo."""
    db = DatabaseManager()
    monitor = ChannelMonitorService(db_manager=db)
    
    success = monitor.remove_channel(args.id)
    
    if success:
        print(f"{Fore.GREEN}✓ Canal eliminado exitosamente (ID: {args.id}){Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ Error eliminando canal o canal no encontrado.{Style.RESET_ALL}")


def cmd_toggle(args):
    """Activa o desactiva un canal."""
    db = DatabaseManager()
    
    success = db.toggle_channel_active(args.id, args.active)
    
    if success:
        status = "activado" if args.active else "desactivado"
        print(f"{Fore.GREEN}✓ Canal {status} exitosamente (ID: {args.id}){Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ Error cambiando estado del canal.{Style.RESET_ALL}")


def cmd_check(args):
    """Verifica nuevos videos en los canales."""
    db = DatabaseManager()
    monitor = ChannelMonitorService(db_manager=db)
    
    print(f"{Fore.CYAN}Verificando nuevos videos...{Style.RESET_ALL}\n")
    
    new_count = monitor.check_for_new_videos()
    
    print(f"\n{Fore.GREEN}✓ Verificación completada.{Style.RESET_ALL}")
    print(f"  Videos nuevos detectados: {new_count}")


def cmd_process(args):
    """Procesa videos pendientes."""
    db = DatabaseManager()
    monitor = ChannelMonitorService(db_manager=db)
    
    max_videos = args.max if args.max else None
    
    print(f"{Fore.CYAN}Procesando videos pendientes...{Style.RESET_ALL}\n")
    
    processed = monitor.process_pending_videos(max_videos=max_videos)
    
    print(f"\n{Fore.GREEN}✓ Procesamiento completado.{Style.RESET_ALL}")
    print(f"  Videos procesados: {processed}")


def cmd_stats(args):
    """Muestra estadísticas del sistema."""
    db = DatabaseManager()
    stats = db.get_statistics()
    
    print(f"{Fore.CYAN}📊 ESTADÍSTICAS DEL SISTEMA{Style.RESET_ALL}\n")
    
    data = [
        ["Canales activos", stats.get('active_channels', 0)],
        ["Total de videos", stats.get('total_videos', 0)],
        ["Videos pendientes", f"{Fore.YELLOW}{stats.get('pending', 0)}{Style.RESET_ALL}"],
        ["Videos procesando", f"{Fore.BLUE}{stats.get('processing', 0)}{Style.RESET_ALL}"],
        ["Videos completados", f"{Fore.GREEN}{stats.get('completed', 0)}{Style.RESET_ALL}"],
        ["Videos fallidos", f"{Fore.RED}{stats.get('failed', 0)}{Style.RESET_ALL}"],
    ]
    
    print(tabulate(data, tablefmt="simple"))


def cmd_videos(args):
    """Lista videos de un canal específico."""
    db = DatabaseManager()
    videos = db.get_videos_by_channel(args.channel_id)
    
    if not videos:
        print(f"{Fore.YELLOW}No hay videos registrados para este canal.{Style.RESET_ALL}")
        return
    
    # Preparar datos para la tabla
    table_data = []
    for video in videos:
        status_colors = {
            'pending': Fore.YELLOW,
            'processing': Fore.BLUE,
            'completed': Fore.GREEN,
            'failed': Fore.RED
        }
        
        status = video.get('status', 'unknown')
        color = status_colors.get(status, Fore.WHITE)
        status_display = f"{color}{status}{Style.RESET_ALL}"
        
        title = video['title'][:50] + "..." if video['title'] and len(video['title']) > 50 else video['title']
        
        table_data.append([
            video['id'],
            title,
            status_display,
            video.get('discovered_at', 'N/A')[:10]
        ])
    
    headers = ["ID", "Título", "Estado", "Descubierto"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\n{Fore.CYAN}Total: {len(videos)} videos{Style.RESET_ALL}")


def main():
    """Función principal del CLI."""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="Gestión de monitoreo de canales de YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando: add
    parser_add = subparsers.add_parser('add', help='Añadir un nuevo canal')
    parser_add.add_argument('url', help='URL del canal de YouTube')
    parser_add.add_argument('name', help='Nombre descriptivo del canal')
    parser_add.set_defaults(func=cmd_add)
    
    # Comando: list
    parser_list = subparsers.add_parser('list', help='Listar todos los canales')
    parser_list.set_defaults(func=cmd_list)
    
    # Comando: remove
    parser_remove = subparsers.add_parser('remove', help='Eliminar un canal')
    parser_remove.add_argument('id', type=int, help='ID del canal a eliminar')
    parser_remove.set_defaults(func=cmd_remove)
    
    # Comando: toggle
    parser_toggle = subparsers.add_parser('toggle', help='Activar/desactivar un canal')
    parser_toggle.add_argument('id', type=int, help='ID del canal')
    parser_toggle.add_argument('--active', type=bool, default=True, help='True para activar, False para desactivar')
    parser_toggle.set_defaults(func=cmd_toggle)
    
    # Comando: check
    parser_check = subparsers.add_parser('check', help='Verificar nuevos videos')
    parser_check.set_defaults(func=cmd_check)
    
    # Comando: process
    parser_process = subparsers.add_parser('process', help='Procesar videos pendientes')
    parser_process.add_argument('--max', type=int, help='Número máximo de videos a procesar')
    parser_process.set_defaults(func=cmd_process)
    
    # Comando: stats
    parser_stats = subparsers.add_parser('stats', help='Mostrar estadísticas')
    parser_stats.set_defaults(func=cmd_stats)
    
    # Comando: videos
    parser_videos = subparsers.add_parser('videos', help='Listar videos de un canal')
    parser_videos.add_argument('channel_id', type=int, help='ID del canal')
    parser_videos.set_defaults(func=cmd_videos)
    
    # Parsear argumentos
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Ejecutar comando
    try:
        args.func(args)
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
