"""
P3-22 (avanzado): Aprendizaje Avanzado de Preferencias
Sistema avanzado de aprendizaje de preferencias del usuario.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class AdvancedPreferences:
    """Sistema avanzado de preferencias."""

    def __init__(self, storage_path: str = "data/advanced_preferences.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._preferences: Dict = {}
        self._interaction_history: List[Dict] = []
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding='utf-8'))
                self._preferences = data.get('preferences', {})
                self._interaction_history = data.get('history', [])
            except:
                pass

    def _save(self):
        data = {
            'preferences': self._preferences,
            'history': self._interaction_history
        }
        self.storage_path.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def learn_from_interaction(
        self,
        video_id: str,
        action: str,
        metadata: Dict = None
    ):
        """Aprende de una interacción del usuario."""
        entry = {
            'video_id': video_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self._interaction_history.append(entry)

        if action in ['download', 'bookmark']:
            self._preferences.setdefault('positive', defaultdict(int))
            for kw in metadata.get('keywords', []):
                self._preferences['positive'][kw] += 1

        elif action in ['skip', 'ignore']:
            self._preferences.setdefault('negative', defaultdict(int))
            for kw in metadata.get('keywords', []):
                self._preferences['negative'][kw] += 1

        self._clean_old_history()
        self._save()

    def _clean_old_history(self, days: int = 90):
        """Limpia historial antiguo."""
        cutoff = datetime.now() - timedelta(days=days)
        self._interaction_history = [
            h for h in self._interaction_history
            if datetime.fromisoformat(h['timestamp']) > cutoff
        ]

    def get_recommended_actions(self) -> List[str]:
        """Obtiene acciones recomendadas basadas en aprendizaje."""
        positive = self._preferences.get('positive', {})

        if not positive:
            return ['continue', 'explore']

        top_keywords = sorted(positive.items(), key=lambda x: x[1], reverse=True)[:3]

        if any('tutorial' in kw for kw, _ in top_keywords):
            return ['prioritize_tutorials', 'suggest_related']
        elif any('review' in kw for kw, _ in top_keywords):
            return ['prioritize_reviews', 'track_updates']

        return ['continue', 'explore', 'diversify']

    def get_topic_weights(self) -> Dict[str, float]:
        """Obtiene pesos de topics aprendidos."""
        positive = self._preferences.get('positive', {})
        negative = self._preferences.get('negative', {})

        all_topics = set(positive.keys()) | set(negative.keys())

        weights = {}
        for topic in all_topics:
            pos = positive.get(topic, 0)
            neg = negative.get(topic, 0)
            weights[topic] = (pos - neg) / max(pos + neg, 1)

        return weights


def get_advanced_preferences() -> AdvancedPreferences:
    return AdvancedPreferences()