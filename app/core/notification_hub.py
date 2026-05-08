# -*- coding: utf-8 -*-
"""
[US-036/040] Notification Hub
Sistema centralizado de notificaciones Push y Webhooks (Slack/Discord).
"""
import requests
import logging
from datetime import datetime

class NotificationHub:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url
        self.history = []

    def notify(self, title: str, message: str, level: str = "info", send_webhook: bool = False):
        """
        [US-036] Envía una notificación Toast y la registra en el historial.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        notification = {
            "timestamp": timestamp,
            "title": title,
            "message": message,
            "level": level
        }
        self.history.append(notification)
        
        # Lógica para mostrar Toast en UI aquí...
        print(f"[{level.upper()}] {title}: {message}")

        if send_webhook and self.webhook_url:
            self._dispatch_webhook(title, message)

    def _dispatch_webhook(self, title: str, message: str):
        """
        [US-040] Integración con Webhooks externos.
        """
        payload = {
            "text": f"🚀 *KDP Master Suite Alert*\n*Title:* {title}\n*Message:* {message}"
        }
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to send webhook: {e}")

    def get_searchable_history(self, query: str = ""):
        """
        [US-036] Retorna el historial filtrado.
        """
        if not query: return self.history
        return [n for n in self.history if query.lower() in n['message'].lower() or query.lower() in n['title'].lower()]