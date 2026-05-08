# -*- coding: utf-8 -*-
"""
Monitoreo independiente de canales KDP.
Este script puede ejecutarse en background para verificar canales sin necesidad de la GUI.
Uso: python monitor_background.py
"""
import sys
import os
import sqlite3
import time
import logging
from datetime import datetime

# Añadir path del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "monitor_bg.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar servicios necesarios
try:
    from app.database.db_manager import DatabaseManager
    from app.services.monitor_service import ChannelMonitorService
    logger.info("Servicios importados correctamente")
except ImportError as e:
    logger.error(f"Error importando servicios: {e}")
    sys.exit(1)

class BackgroundMonitor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_manager = None
        self.monitor_service = None
        self.running = False
        
    def initialize(self):
        """Inicializa los servicios."""
        logger.info("Inicializando monitor de fondo...")
        
        data_dir = os.path.dirname(self.db_path)
        db_manager = DatabaseManager(db_path=self.db_path)
        
        # Importar el servicio de monitoreo
        from app.services.monitor_service import ChannelMonitorService
        
        # Crear el servicio (con interval_minutes reducido para más frecuencia)
        self.monitor_service = ChannelMonitorService(
            db_manager=db_manager,
            interval_minutes=30  # Check cada 30 minutos
        )
        
        logger.info("Monitor de fondo inicializado")
        
    def run_single_cycle(self):
        """Ejecuta un ciclo de verificación."""
        logger.info("="*40)
        logger.info(f"CICLO DE MONITOREO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*40)
        
        new_count = 0
        
        try:
            # Obtener todos los canales activos
            channels = self.monitor_service.db.get_all_channels(active_only=True)
            logger.info(f"Canales a verificar: {len(channels)}")
            
            # Verificar cada canal manualmente (sin el metodo paralelo que tiene el bug)
            for channel in channels:
                try:
                    channel_id = channel.get('id')
                    channel_name = channel.get('channel_name', 'Unknown')
                    channel_url = channel.get('channel_url', '')
                    
                    logger.info(f"Verificando canal: {channel_name}")
                    
                    # Verificar nuevos videos para este canal
                    result = self.monitor_service.check_for_new_videos(channel_id)
                    if result > 0:
                        logger.info(f"  -> {result} videos nuevos en {channel_name}")
                        new_count += result
                        
                except Exception as e:
                    logger.error(f"Error verificando canal {channel.get('name', 'unknown')}: {e}")
            
            logger.info(f"Total videos nuevos encontrados: {new_count}")
            
            # Procesar videos pendientes
            if new_count > 0:
                logger.info("Procesando videos pendientes...")
                try:
                    self.monitor_service.process_pending_videos()
                except Exception as e:
                    logger.error(f"Error procesando videos: {e}")
            
            # Mostrar estadísticas
            stats = self.monitor_service.get_statistics()
            logger.info(f"Estadisticas: {stats}")
            
            return new_count
            
        except Exception as e:
            logger.error(f"Error en ciclo de monitoreo: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def run_continuous(self, interval_minutes: int = 30, max_cycles: int = None):
        """Ejecuta el monitoreo continuamente."""
        self.running = True
        cycles = 0
        
        logger.info(f"Iniciando monitoreo continuo (intervalo: {interval_minutes} min)")
        
        while self.running:
            cycles += 1
            self.run_single_cycle()
            
            if max_cycles and cycles >= max_cycles:
                logger.info(f"Maximo de ciclos alcanzado: {max_cycles}")
                break
            
            # Esperar siguiente ciclo
            logger.info(f"Esperando {interval_minutes} minutos...")
            time.sleep(interval_minutes * 60)
        
        logger.info("Monitoreo de fondo terminado")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitoreo de canales KDP en background')
    parser.add_argument('--interval', type=int, default=30, help='Intervalo en minutos')
    parser.add_argument('--cycles', type=int, default=None, help='Numero maximo de ciclos')
    parser.add_argument('--once', action='store_true', help='Ejecutar solo un ciclo')
    args = parser.parse_args()
    
    # Ruta de la DB
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "data", "channel_monitor.db")
    
    if not os.path.exists(db_path):
        logger.error(f"Base de datos no encontrada: {db_path}")
        sys.exit(1)
    
    monitor = BackgroundMonitor(db_path)
    monitor.initialize()
    
    if args.once:
        logger.info("Modo: Un solo ciclo")
        monitor.run_single_cycle()
    else:
        logger.info(f"Modo: Continuo ({args.interval} min intervalo)")
        monitor.run_continuous(interval_minutes=args.interval, max_cycles=args.cycles)

if __name__ == "__main__":
    main()