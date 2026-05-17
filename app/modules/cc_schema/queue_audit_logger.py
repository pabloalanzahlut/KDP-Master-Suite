"""
Queue Audit Logger - Módulo 47
===============================
Sistema de registro de auditoría para operaciones de vaciado de cola.

¿Para qué sirve esto?
====================
Imagina que trabajas en un banco (gestión de dinero).
Cada vez que alguien hace una transacción, el banco NO solo guarda
el resultado, sino que guarda QUIÉN lo hizo, CUÁNDO, y QUÉ cambió.

Esto se llama "log de auditoría" y sirve para:
- Detectar fraudes
- Resolver disputas
- Cumplir regulaciones
- Investigar problemas

Este módulo hace LO MISMO para tu cola de videos:
- Cada vez que vacías la cola, quedan registrados:
  * Cuántos videos borraste
  * Cuál fue la estrategia usada
  * Cuándo lo hiciste
  * (Opcional) Quién lo hizo

Caso de uso real:
================
Tu jefe pregunta: "¿Qué borraste la semana pasada?"
Sin auditoría: "No me acuerdo"
Con auditoría: "El martes borré 47 videos, 12 fallidos, estrategia: oldest_50"

O más importante:
"Viste que borramos ese video importante?"
"Déjame ver el log... sí, el 15 de mayo a las 3pm, estrategia: all"
"¿Quién lo hizo? El usuario 'admin' desde la IP 192.168.1.5"

Aquí está la respuesta exacta.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading

logger = logging.getLogger(__name__)


class QueueAuditLogger:
    """
    Gestor de logs de auditoría para operaciones de cola.
    
    Implementa registro inmutable de todas las operaciones de vaciado.
    """

    _lock = threading.Lock()

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Inicializa el logger de auditoría.
        
        Args:
            data_dir: Directorio donde se guardan los logs.
        """
        if data_dir is None:
            import sys
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
            else:
                base_dir = Path(__file__).parent.parent.parent.parent
            data_dir = base_dir / "data"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.audit_file = self.data_dir / "queue_audit.jsonl"
        
        logger.info(f"QueueAuditLogger inicializado: {self.audit_file}")

    def log_clear_action(
        self,
        cleared_count: int,
        protected_count: int,
        strategy: str,
        snapshot_path: Optional[str] = None,
        export_path: Optional[str] = None,
        reason: str = "",
        user: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Registra una operación de vaciado.
        
        Args:
            cleared_count: Número de items borrados.
            protected_count: Número de items protegidos.
            strategy: Estrategia usada (all, failed_only, etc.).
            snapshot_path: Ruta del snapshot creado.
            export_path: Ruta del CSV exportado.
            reason: Razón del vaciado (opcional).
            user: Usuario que ejecutó la acción.
            metadata: Metadatos adicionales.

        Returns:
            True si se registró correctamente.
        """
        with self._lock:
            try:
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "action": "queue_clear",
                    "cleared_count": cleared_count,
                    "protected_count": protected_count,
                    "strategy": strategy,
                    "snapshot_path": snapshot_path,
                    "export_path": export_path,
                    "reason": reason,
                    "user": user,
                    "metadata": metadata or {}
                }
                
                with open(self.audit_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                
                logger.info(f"Audit: cleared={cleared_count}, protected={protected_count}, strategy={strategy}")
                return True

            except Exception as e:
                logger.error(f"Error registrando auditoría: {e}")
                return False

    def log_restore_action(
        self,
        restored_count: int,
        snapshot_id: str,
        user: str = "system"
    ) -> bool:
        """
        Registra una restauración desde snapshot.
        
        Args:
            restored_count: Número de items restaurados.
            snapshot_id: ID del snapshot usado.
            user: Usuario que ejecutó la acción.

        Returns:
            True si se registró correctamente.
        """
        with self._lock:
            try:
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "action": "queue_restore",
                    "restored_count": restored_count,
                    "snapshot_id": snapshot_id,
                    "user": user
                }
                
                with open(self.audit_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                
                logger.info(f"Audit: restored={restored_count}, snapshot={snapshot_id}")
                return True

            except Exception as e:
                logger.error(f"Error registrando restauración: {e}")
                return False

    def log_protect_action(
        self,
        items_protected: List[str],
        user: str = "system"
    ) -> bool:
        """
        Registra protección de items.
        
        Args:
            items_protected: Lista de URLs protegidas.
            user: Usuario que ejecutó la acción.

        Returns:
            True si se registró correctamente.
        """
        with self._lock:
            try:
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "action": "items_protected",
                    "count": len(items_protected),
                    "items": items_protected,
                    "user": user
                }
                
                with open(self.audit_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                
                logger.info(f"Audit: protected={len(items_protected)} items")
                return True

            except Exception as e:
                logger.error(f"Error registrando protección: {e}")
                return False

    def get_history(
        self,
        limit: int = 50,
        action_filter: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de operaciones.
        
        Args:
            limit: Máximo de entradas a retornar.
            action_filter: Filtrar por tipo de acción.
            since: Filtrar desde fecha específica.

        Returns:
            Lista de entradas del historial.
        """
        entries = []
        
        if not self.audit_file.exists():
            return entries
        
        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        if action_filter and entry.get("action") != action_filter:
                            continue
                        
                        if since:
                            entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                            if entry_time < since:
                                continue
                        
                        entries.append(entry)
                        
                        if len(entries) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
            
            return entries[-limit:] if len(entries) > limit else entries

        except Exception as e:
            logger.error(f"Error leyendo historial: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas globales de auditoría.
        
        Returns:
            Diccionario con estadísticas.
        """
        if not self.audit_file.exists():
            return {
                "total_actions": 0,
                "total_cleared": 0,
                "total_restored": 0
            }
        
        stats = {
            "total_actions": 0,
            "total_cleared": 0,
            "total_protected": 0,
            "total_restored": 0,
            "by_strategy": {}
        }
        
        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        action = entry.get("action")
                        
                        stats["total_actions"] += 1
                        
                        if action == "queue_clear":
                            stats["total_cleared"] += entry.get("cleared_count", 0)
                            stats["total_protected"] += entry.get("protected_count", 0)
                            
                            strategy = entry.get("strategy", "unknown")
                            stats["by_strategy"][strategy] = stats["by_strategy"].get(strategy, 0) + 1
                        
                        elif action == "queue_restore":
                            stats["total_restored"] += entry.get("restored_count", 0)
                    
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Error calculando estadísticas: {e}")
        
        return stats

    def export_to_csv(self, output_path: Optional[Path] = None) -> str:
        """
        Exporta el historial a CSV.
        
        Args:
            output_path: Ruta de salida. Si es None, usa nombre automático.

        Returns:
            Ruta del archivo exportado.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.data_dir / f"audit_export_{timestamp}.csv"
        
        history = self.get_history(limit=10000)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("timestamp,action,count,strategy,user,reason\n")
                
                for entry in history:
                    timestamp = entry.get("timestamp", "")
                    action = entry.get("action", "")
                    count = entry.get("cleared_count", entry.get("restored_count", entry.get("count", 0)))
                    strategy = entry.get("strategy", "")
                    user = entry.get("user", "")
                    reason = entry.get("reason", "")
                    
                    f.write(f'"{timestamp}","{action}",{count},"{strategy}","{user}","{reason}"\n')
            
            logger.info(f"Auditoría exportada a: {output_path}")
            return str(output_path)
        
        except Exception as e:
            logger.error(f"Error exportando auditoría: {e}")
            return ""


def create_audit_logger(data_dir: Optional[Path] = None) -> QueueAuditLogger:
    """Factory function."""
    return QueueAuditLogger(data_dir=data_dir)