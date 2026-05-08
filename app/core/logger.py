import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

_app_loggers_initialized = False

def setup_app_logging(base_dir, max_bytes=10*1024*1024, backup_count=5):
    """
    Configura el sistema de logs para la aplicación.
    
    Args:
        base_dir: Directorio base para almacenar logs
        max_bytes: Tamaño máximo por archivo de log (default: 10MB)
        backup_count: Número de archivos de backup a mantener (default: 5)
    
    Returns:
        Tuple (logger, audit_logger)
    """
    global _app_loggers_initialized
    if _app_loggers_initialized:
        return logging.getLogger("KDP_MASTER"), logging.getLogger("AUDIT")
    
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"app_{timestamp}.log")
    audit_file = os.path.join(log_dir, f"audit_{timestamp}.log")

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    audit_formatter = logging.Formatter('%(asctime)s - [AUDIT] - %(message)s')

    # Logger Principal
    logger = logging.getLogger("KDP_MASTER")
    logger.setLevel(logging.DEBUG)
    
    # Prevenir duplicación de handlers
    logger.handlers.clear()
    logger.propagate = False
    
    # File handler con rotación
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Logger de Auditoría
    audit_logger = logging.getLogger("AUDIT")
    audit_logger.setLevel(logging.INFO)
    
    # Prevenir duplicación de handlers
    audit_logger.handlers.clear()
    audit_logger.propagate = False
    
    # File handler con rotación
    audit_handler = RotatingFileHandler(
        audit_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    audit_handler.setFormatter(audit_formatter)
    audit_logger.addHandler(audit_handler)
    
    # Console handler para audit
    audit_console = logging.StreamHandler()
    audit_console.setLevel(logging.WARNING)
    audit_console.setFormatter(audit_formatter)
    audit_logger.addHandler(audit_console)

    _app_loggers_initialized = True
    return logger, audit_logger
