"""
Chatbot
=======
Chatbot de ayuda para backup.
"""

from typing import Dict


class Chatbot:
    def __init__(self):
        self.responses = {"help": "Usa el botón de pánico para backup de emergencia", "status": "Sistema operativo"}

    def respond(self, query: str) -> Dict:
        query_lower = query.lower()
        for key, response in self.responses.items():
            if key in query_lower:
                return {"response": response, "intent": key}
        return {"response": "No entiendo. Usa /help", "intent": "unknown"}


def get_chatbot():
    return Chatbot()