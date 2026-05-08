import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any

class AnalyticsService:
    def __init__(self, monitor_db_path: str, knowledge_db_path: str):
        """
        [US-035] Unified Analytics Access.
        """
        self.monitor_db = monitor_db_path
        self.knowledge_db = knowledge_db_path

    def get_posting_frequency(self, days: int = 30) -> Dict[str, int]:
        """Calculates videos per day in the last N days."""
        query = """
            SELECT pub_date, COUNT(*) as count
            FROM videos
            WHERE pub_date >= ?
            GROUP BY pub_date
            ORDER BY pub_date ASC
        """
        since = (datetime.now() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self.monitor_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (since,))
            return {row['pub_date']: row['count'] for row in cursor.fetchall()}

    def get_niche_trends(self) -> List[Dict[str, Any]]:
        """Analyzes category distribution to identify trending niches."""
        query = """
            SELECT category, COUNT(*) as count
            FROM knowledge_entries
            GROUP BY category
            ORDER BY count DESC
        """
        with sqlite3.connect(self.knowledge_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    # --- [US-035] Advanced Niche Efficiency Analytics ---
    def get_channel_efficiency(self) -> List[Dict[str, Any]]:
        """
        Calculates processing efficiency per channel.
        Fundamental for identifying high-yield niches.
        """
        query = """
            SELECT c.channel_name, 
                   COUNT(v.id) as total_detected,
                   SUM(CASE WHEN v.status = 'completed' THEN 1 ELSE 0 END) as processed_ok
            FROM channels c
            LEFT JOIN videos v ON c.id = v.channel_id
            GROUP BY c.id
        """
        with sqlite3.connect(self.monitor_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def get_posting_velocity(self) -> float:
        """Returns average videos per week across all monitored channels."""
        with sqlite3.connect(self.monitor_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM videos WHERE published_at >= date('now', '-7 days')")
            return cursor.fetchone()[0] / 1.0
    # --- END [US-035] ---