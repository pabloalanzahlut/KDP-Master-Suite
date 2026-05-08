import time
import queue
import threading
import logging
import sys
from typing import Callable, Optional

logger = logging.getLogger("kdp.notifications")

class NotificationRouter:
    _instance = None
    
    def __init__(self, app_instance, settings: dict = None):
        self.app = app_instance
        self.settings = settings or getattr(app_instance, 'settings', {}) or {}
        self.notif_settings = self.settings.get("notifications", {})
        self.cooldown_seconds = self.notif_settings.get("cooldown_minutes", 5) * 60
        self.cooldowns = {}
        self._lock = threading.Lock()
        self._queue = queue.Queue(maxsize=50)
        self._running = True
        self.native_notifier = self._init_native()
        self.internal_notifier = self._init_internal()
        
        self._root = getattr(app_instance, 'root', app_instance)
        
        self._start_worker()
        
        NotificationRouter._instance = self
    
    def _start_worker(self):
        def worker():
            while self._running:
                try:
                    msg = self._queue.get(timeout=1)
                    if msg is None:
                        break
                    self._dispatch(msg)
                    self._queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.warning(f"Worker error: {e}")
        
        thread = threading.Thread(target=worker, daemon=True, name="NotifWorker")
        thread.start()
    
    def shutdown(self):
        self._running = False
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass

    def _init_native(self):
        # ==================== MÓDULO 2: winotify init con manejo robusto ====================
        if sys.platform != "win32":
            logger.info(f"ℹ️ Plataforma '{sys.platform}' detectada. Notificaciones nativas Windows (winotify) desactivadas.")
            return None
        
        try:
            import winotify
            notifier = winotify.Winotify(app_id="KDP Master")
            return notifier
        except ImportError:
            logger.warning("⚠️ Librería 'winotify' no encontrada. Solo toasts internos disponibles.")
            return None
        except AttributeError as e:
            logger.warning(f"⚠️ winotify API incompatibile: {e}. Usando fallback interno.")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando winotify: {e}. Usando fallback interno.")
            return None
        # ==================== FIN MÓDULO 2 ====================

    def _init_internal(self):
        try:
            from app.ui.components.notifications import ToastNotification
            return ToastNotification
        except Exception:
            return None

    def _schedule_after(self, delay_ms, callback):
        """Programa un callback de forma segura usando after()."""
        try:
            if hasattr(self, '_root') and self._root:
                self._root.after(delay_ms, callback)
            elif hasattr(self.app, 'after'):
                self.app.after(delay_ms, callback)
        except Exception:
            pass

    def notify(self, title: str, message: str, type: str = "info", 
             event_type: str = None, action: Callable = None, channel_id: str = None):
        if not self.notif_settings.get("enabled", True):
            return
        
        if event_type is None:
            event_type = type
        
        if self._should_cooldown(event_type, channel_id):
            return

        msg = {
            "title": title,
            "message": message,
            "type": type,
            "action": action,
            "event_type": event_type,
            "channel_id": channel_id
        }
        
        try:
            self._queue.put_nowait(msg)
        except queue.Full:
            logger.debug("Cola de notificaciones llena")

    def _should_cooldown(self, event_type: str, channel_id: str = None) -> bool:
        key = f"{event_type}:{channel_id}" if channel_id else event_type
        with self._lock:
            last_time = self.cooldowns.get(key, 0)
            if (time.time() - last_time) < self.cooldown_seconds:
                return True
            self.cooldowns[key] = time.time()
            self._cleanup_expired()
        return False

    def _update_cooldown(self, event_type: str, msg_type: str = None, channel_id: str = None):
        key = f"{event_type}:{channel_id}" if channel_id else event_type
        with self._lock:
            self.cooldowns[key] = time.time()

    def _cleanup_expired(self, max_age_multiplier: float = 2.5):
        now = time.time()
        threshold = self.cooldown_seconds * max_age_multiplier
        expired = [k for k, v in self.cooldowns.items() if now - v > threshold]
        for k in expired:
            del self.cooldowns[k]

    def _dispatch(self, msg):
        title = msg.get("title", "")
        message = msg.get("message", "")
        msg_type = msg.get("type", "info")
        action = msg.get("action")
        event_type = msg.get("event_type", msg_type)
        channel_id = msg.get("channel_id")
        
        try:
            if self.internal_notifier and self.notif_settings.get("enable_internal", True):
                self._schedule_after(100, lambda: self._show_internal_notification(title, message, msg_type, action))

            if self.native_notifier and self.notif_settings.get("enable_native", False):
                self._schedule_after(100, lambda: self._show_native_notification(title, message, msg_type, action))
            
            self._update_cooldown(event_type, msg_type, channel_id)
        except Exception as e:
            logger.warning(f"Dispatch error: {e}")

    def _show_internal_notification(self, title: str, message: str, type: str, action: Callable):
        try:
            if self.internal_notifier:
                self.internal_notifier.show(
                    self.app,
                    f"[{type.upper()}] {title}\n{message}",
                    type=type,
                    duration=5000
                )
            if action and self.app:
                if hasattr(self.app, 'after'):
                    self.app.after(2000, action)
        except Exception as e:
            self._log(f"Error notificación interna: {str(e)}", "error")

    def _show_native_notification(self, title: str, message: str, type: str, action: Callable):
        # ==================== MÓDULO 2: winotify con manejo de errores mejorado ====================
        try:
            if not self.native_notifier:
                logger.debug("Native notifier no disponible, saltando notificación")
                return
            
            import winotify
            toast = winotify.Toast(title, message)
            toast.add_actions([winotify.Action("Abrir App", lambda: self._handle_native_click(action))])
            toast.show()
        except ImportError:
            logger.warning("⚠️ winotify no disponible en tiempo de ejecución")
        except AttributeError:
            logger.warning("⚠️ winotify API incompatibile, usando fallback")
        except Exception as e:
            logger.warning(f"⚠️ Error notificación nativa: {str(e)}, usando fallback interno")
        # ==================== FIN MÓDULO 2 ====================

    def _handle_native_click(self, action: Callable):
        try:
            if action and self.app:
                if hasattr(self.app, 'after'):
                    self.app.after(0, action)
        except Exception as e:
            self._log(f"Error acción notificación: {str(e)}", "error")

    def _log(self, message: str, level: str):
        if self.app:
            if hasattr(self.app, 'log_monitor_activity'):
                try:
                    self.app.root.after(0, lambda: self.app.log_monitor_activity(message))
                except:
                    pass
            elif hasattr(self.app, 'log'):
                try:
                    self.app.root.after(0, lambda: self.app.log(message))
                except:
                    pass
