"""
KDP_MASTER - Auto Decision Engine
=================================
Motor de reglas automáticas para decisiones de duplicados.
Persiste en SQLite para funcionar en .exe
"""

import logging
from typing import List, Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class DecisionAction(Enum):
    """Acciones disponibles para duplicados."""
    OMIT_NEW = "omit_new"
    PROCESS_BOTH = "process_both"
    GROUP = "group"
    IGNORE_ALWAYS = "ignore_always"
    SHOW_DIALOG = "show_dialog"


class AutoDecisionRule:
    """Modelo de regla de decisión automática."""

    def __init__(self, duplicate_type: str, min_confidence: float = 0.0,
                 action: str = "show_dialog", enabled: bool = True, rule_id: int = None):
        self.id = rule_id
        self.duplicate_type = duplicate_type
        self.min_confidence = min_confidence
        self.action = action
        self.enabled = enabled
        self.created_at = None
        self.updated_at = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'duplicate_type': self.duplicate_type,
            'min_confidence': self.min_confidence,
            'action': self.action,
            'enabled': self.enabled
        }


class AutoDecisionEngine:
    """
    Motor de reglas automáticas para duplicados.

    TABLA: auto_decision_rules
    --------------------------
    - id: INTEGER PRIMARY KEY
    - duplicate_type: TEXT (EXACT_CONTENT, REPOST, etc.)
    - min_confidence: REAL (0.0-1.0, opcional)
    - action: TEXT (omit_new, process_both, group, ignore_always, show_dialog)
    - enabled: BOOLEAN DEFAULT 1
    - created_at: TIMESTAMP
    - updated_at: TIMESTAMP

    REGLAS POR DEFECTO (se crean en migrate):
    ------------------------------------------
    | duplicate_type     | min_confidence | action      |
    |--------------------|----------------|-------------|
    | EXACT_CONTENT      | 0.0            | omit_new    |
    | REPOST             | 0.90           | omit_new    |
    | REPOST             | 0.80           | show_dialog |
    | SIMILAR_DURATION   | 0.0            | show_dialog |
    | SIMILAR_TAGS       | 0.0            | process_both|
    | SEMANTIC_SIMILAR   | 0.0            | show_dialog |
    """

    DEFAULT_RULES = [
        {'duplicate_type': 'EXACT_CONTENT', 'min_confidence': 0.0, 'action': 'omit_new'},
        {'duplicate_type': 'REPOST', 'min_confidence': 0.90, 'action': 'omit_new'},
        {'duplicate_type': 'REPOST', 'min_confidence': 0.80, 'action': 'show_dialog'},
        {'duplicate_type': 'SIMILAR_DURATION', 'min_confidence': 0.0, 'action': 'show_dialog'},
        {'duplicate_type': 'SIMILAR_TAGS', 'min_confidence': 0.0, 'action': 'process_both'},
        {'duplicate_type': 'SEMANTIC_SIMILAR', 'min_confidence': 0.0, 'action': 'show_dialog'},
    ]

    def __init__(self, db_manager):
        """
        Args:
            db_manager: Instancia de DatabaseManager
        """
        self.db = db_manager
        self._rules_cache: List[AutoDecisionRule] = []
        self._ensure_migration()
        self._load_rules()

    def _ensure_migration(self):
        """Crea tabla si no existe + inserta reglas por defecto."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auto_decision_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    duplicate_type TEXT NOT NULL,
                    min_confidence REAL DEFAULT 0.0,
                    action TEXT NOT NULL DEFAULT 'show_dialog',
                    enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(duplicate_type, min_confidence)
                )
            """)

            for rule in self.DEFAULT_RULES:
                cursor.execute("""
                    INSERT OR IGNORE INTO auto_decision_rules
                    (duplicate_type, min_confidence, action)
                    VALUES (?, ?, ?)
                """, (rule['duplicate_type'], rule['min_confidence'], rule['action']))

            conn.commit()
            logger.info("AutoDecisionEngine migration completed")
        except Exception as e:
            logger.error(f"Error en migración AutoDecisionEngine: {e}")

    def _load_rules(self):
        """Carga reglas desde SQLite a cache."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, duplicate_type, min_confidence, action, enabled
                FROM auto_decision_rules
                ORDER BY min_confidence DESC
            """)

            self._rules_cache = []
            for row in cursor.fetchall():
                rule = AutoDecisionRule(
                    rule_id=row[0],
                    duplicate_type=row[1],
                    min_confidence=row[2],
                    action=row[3],
                    enabled=bool(row[4])
                )
                self._rules_cache.append(rule)

            logger.info(f"AutoDecisionEngine: {len(self._rules_cache)} reglas cargadas")
        except Exception as e:
            logger.error(f"Error cargando reglas: {e}")
            self._rules_cache = []

    def check_rule(self, duplicate_info: Dict) -> Tuple[str, bool]:
        """
        Verifica si hay regla automática para el duplicado.

        Args:
            duplicate_info: Diccionario con:
                - type: tipo de duplicado (EXACT_CONTENT, REPOST, etc.)
                - confidence: nivel de confianza (0.0-1.0)

        Returns:
            Tupla (action, is_auto)
            - action: acción a tomar
            - is_auto: True si se aplica automáticamente, False si mostrar diálogo
        """
        dup_type = duplicate_info.get('type', duplicate_info.get('duplicate_type', ''))
        confidence = duplicate_info.get('confidence', duplicate_info.get('level', 0.0))

        dup_type = dup_type.upper() if dup_type else ''

        for rule in self._rules_cache:
            if not rule.enabled:
                continue

            if rule.duplicate_type == dup_type:
                if confidence >= rule.min_confidence:
                    if rule.action == 'show_dialog':
                        return ('show_dialog', False)
                    return (rule.action, True)

        return ('show_dialog', False)

    def add_rule(self, duplicate_type: str, min_confidence: float = 0.0,
                 action: str = 'show_dialog') -> bool:
        """Añade nueva regla."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO auto_decision_rules
                (duplicate_type, min_confidence, action, enabled, updated_at)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            """, (duplicate_type.upper(), min_confidence, action))
            conn.commit()
            self._load_rules()
            logger.info(f"Regla añadida: {duplicate_type} → {action}")
            return True
        except Exception as e:
            logger.error(f"Error añadiendo regla: {e}")
            return False

    def remove_rule(self, rule_id: int) -> bool:
        """Elimina regla por ID."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM auto_decision_rules WHERE id = ?", (rule_id,))
            conn.commit()
            self._load_rules()
            return True
        except Exception as e:
            logger.error(f"Error eliminando regla: {e}")
            return False

    def toggle_rule(self, rule_id: int, enabled: bool) -> bool:
        """Activa/desactiva regla."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE auto_decision_rules
                SET enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (1 if enabled else 0, rule_id))
            conn.commit()
            self._load_rules()
            return True
        except Exception as e:
            logger.error(f"Error toggling regla: {e}")
            return False

    def get_rules(self) -> List[Dict]:
        """Retorna todas las reglas."""
        return [r.to_dict() for r in self._rules_cache]

    def reset_to_defaults(self) -> bool:
        """Resetea todas las reglas a valores por defecto."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM auto_decision_rules")

            for rule in self.DEFAULT_RULES:
                cursor.execute("""
                    INSERT INTO auto_decision_rules
                    (duplicate_type, min_confidence, action)
                    VALUES (?, ?, ?)
                """, (rule['duplicate_type'], rule['min_confidence'], rule['action']))

            conn.commit()
            self._load_rules()
            return True
        except Exception as e:
            logger.error(f"Error reseteando reglas: {e}")
            return False
