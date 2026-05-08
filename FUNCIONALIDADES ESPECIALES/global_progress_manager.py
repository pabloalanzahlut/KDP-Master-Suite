# --- INICIO FUNCIONALIDAD US-008: GLOBAL PROGRESS BAR MANAGER ---
import threading
from typing import Callable, List

class GlobalProgressManager:
    """
    Singleton que centraliza el estado de progreso de todas las 
    operaciones del sistema (Thread-safe). US-008.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GlobalProgressManager, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        self.current_percent = 0.0
        self.current_label = "Idle"
        self.subscribers: List[Callable[[float, str], None]] = []

    def subscribe(self, callback: Callable[[float, str], None]):
        """Añade una función de callback para actualizar la UI (Observer Pattern)."""
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def update_progress(self, percent: float, message: str = ""):
        """
        Actualiza el estado global y notifica a los suscriptores.
        :param percent: Valor flotante de 0.0 a 100.0
        :param message: Mensaje descriptivo del estado actual.
        """
        self.current_percent = max(0.0, min(100.0, percent))
        if message:
            self.current_label = message
        
        for callback in self.subscribers:
            try:
                # Se asume que el callback maneja la integración con el main thread de la UI
                callback(self.current_percent, self.current_label)
            except Exception as e:
                print(f"[ERROR UI UPDATE] Error al notificar suscriptor: {e}")

    def reset(self):
        """Reinicia el estado del manager."""
        self.update_progress(0.0, "Ready")

# --- FIN FUNCIONALIDAD US-008 ---