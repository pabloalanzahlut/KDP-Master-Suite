"""
Módulo de Singleton Global para acceso de emergencia en atexit.
Proporciona una referencia global a la instancia de la aplicación.
"""

CURRENT_APP_INSTANCE = None


def get_current_app():
    """Retorna la instancia actual de la aplicación."""
    return CURRENT_APP_INSTANCE


def set_current_app(instance):
    """Establece la instancia actual de la aplicación."""
    global CURRENT_APP_INSTANCE
    CURRENT_APP_INSTANCE = instance