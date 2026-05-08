from pathlib import Path
from typing import Dict, List, Optional
from app.core.audit_logger import AuditLogger
from app.core.compliance_checker import ComplianceChecker

class KBDistributor:
    """
    Orquestador Elite de Distribución de Conocimiento.
    Implementa la Regla de Oro: Master KB (100%) + Especializados (Condicional).
    """
    def __init__(self, base_dir: Path, integrator, webhook=None, git=None):
        self.base_dir = base_dir
        self.integrator = integrator  # Instancia de KnowledgeIntegrator
        self.audit = AuditLogger(base_dir)
        self.compliance = ComplianceChecker()
        
        # Integraciones opcionales (Fase 4)
        self.webhook = webhook
        self.git = git
        
        self.master_file = base_dir / "knowledge" / "manuals" / "MASTER_KB_CONSOLIDADO.txt"
        self.threshold = 0.75
        
        # Asegurar que existe el directorio del master
        self.master_file.parent.mkdir(parents=True, exist_ok=True)

    def process_and_distribute(self, text: str, source: str, metadata: Optional[dict] = None) -> Dict:
        """Ejecuta el flujo de distribución corporativa."""
        if metadata is None:
            metadata = {}
        
        # 1. Pre-filtro de Cumplimiento
        comp_result = self.compliance.scan_text(text)
        if not comp_result["safe"]:
            self.audit.log_event(
                "REJECTED_BY_COMPLIANCE", 
                source, 
                [], 
                "BLOCKED", 
                metadata=comp_result
            )
            return {
                "status": "blocked", 
                "flags": comp_result.get("flags", []),
                "targets": []
            }

        # 2. Forzar escritura en MASTER_KB_CONSOLIDADO.txt (100%)
        master_success = self._write_to_master(text, source, metadata)
        if not master_success:
            return {
                "status": "error",
                "message": "Failed to write to MASTER_KB",
                "targets": []
            }
        
        distributed_to = ["MASTER_KB_CONSOLIDADO.txt"]

        # 3. Clasificación Temática e Inferencia de Confianza
        classification = self.integrator._classify_block(text)
        category, key = classification
        
        # Obtener confianza (puede venir del clasificador o ser calculada)
        confidence = self._get_confidence(text, category, key)
        
        # 4. Routing Condicional (Fase 1)
        if confidence >= self.threshold and key != "MASTER":
            target_file = self.integrator.files.get(key)
            if target_file:
                success = self.integrator._append_to_file(
                    target_file, 
                    text, 
                    source, 
                    category, 
                    lock_key=key, 
                    metadata=metadata
                )
                if success: 
                    distributed_to.append(target_file.name)
                    
                    # FASE 4: Disparar Sincronización Externa
                    if self.webhook or self.git:
                        self._trigger_external_sync(
                            source, category, text, confidence, metadata
                        )

        # 5. Review Queue (Fase 2 - Hook)
        if confidence < self.threshold:
            self._add_to_review_queue(text, source, category, confidence, metadata)
            status = "PENDING_REVIEW"
        else:
            status = "SUCCESS"

        # 6. Auditoría
        self.audit.log_event(
            "DISTRIBUTE", 
            source, 
            distributed_to, 
            status, 
            confidence
        )
        
        return {
            "status": status, 
            "targets": distributed_to,
            "confidence": confidence,
            "category": category
        }

    def _write_to_master(self, text: str, source: str, metadata: dict) -> bool:
        """Escritura obligatoria en la fuente de verdad."""
        try:
            success = self.integrator._append_to_file(
                self.master_file, 
                text, 
                source, 
                "General Consolidado", 
                lock_key="MASTER", 
                metadata=metadata
            )
            return success
        except Exception as e:
            self.audit.log_event(
                "MASTER_WRITE_ERROR", 
                source, 
                [], 
                "ERROR", 
                metadata={"error": str(e)}
            )
            return False

    def _get_confidence(self, text: str, category: str, key: str) -> float:
        """
        Calcula o recupera el nivel de confianza de la clasificación.
        
        Puede usar:
        - Score del clasificador ML
        - Análisis de keywords
        - Longitud y estructura del texto
        - Modelo Ollama para validación
        """
        # Implementación básica - ajustar según necesidades
        confidence = 0.85  # Default
        
        # Ajustes heurísticos
        if len(text.strip()) < 50:
            confidence *= 0.7  # Textos muy cortos = menor confianza
        
        if key == "MASTER":
            confidence = 1.0  # Máxima confianza para contenido general
        
        # TODO: Integrar con clasificador ML o Ollama
        # confidence = self.integrator.get_classification_confidence(text)
        
        return confidence

    def _trigger_external_sync(
        self, 
        source: str, 
        category: str, 
        content: str, 
        confidence: float, 
        metadata: dict
    ):
        """Dispara sincronización con sistemas externos (webhooks, git, etc)."""
        sync_data = {
            "source": source, 
            "category": category, 
            "content": content, 
            "confidence": confidence, 
            "metadata": metadata
        }
        
        # Webhook dispatch
        if self.webhook:
            try:
                self.webhook.dispatch(sync_data)
            except Exception as e:
                self.audit.log_event(
                    "WEBHOOK_ERROR", 
                    source, 
                    [], 
                    "ERROR", 
                    metadata={"error": str(e)}
                )
        
        # Git auto-commit
        if self.git:
            try:
                self.git.auto_commit(source)
            except Exception as e:
                self.audit.log_event(
                    "GIT_ERROR", 
                    source, 
                    [], 
                    "ERROR", 
                    metadata={"error": str(e)}
                )

    def _add_to_review_queue(
        self, 
        text: str, 
        source: str, 
        category: str, 
        confidence: float,
        metadata: dict
    ):
        """Persistencia para la pestaña de Revisión Humana (Fase 2)."""
        # TODO: Implementar persistencia en SQLite
        # Estructura sugerida:
        # CREATE TABLE review_queue (
        #     id INTEGER PRIMARY KEY,
        #     text TEXT NOT NULL,
        #     source TEXT NOT NULL,
        #     category TEXT,
        #     confidence REAL,
        #     metadata TEXT,  -- JSON
        #     status TEXT DEFAULT 'pending',
        #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        # )
        
        try:
            # Placeholder para la implementación de BD
            review_entry = {
                "text": text,
                "source": source,
                "category": category,
                "confidence": confidence,
                "metadata": metadata,
                "status": "pending"
            }
            
            # self.db.insert_review_queue(review_entry)
            
            self.audit.log_event(
                "ADDED_TO_REVIEW_QUEUE", 
                source, 
                [], 
                "QUEUED",
                confidence
            )
        except Exception as e:
            self.audit.log_event(
                "REVIEW_QUEUE_ERROR", 
                source, 
                [], 
                "ERROR", 
                metadata={"error": str(e)}
            )

    def get_pending_reviews(self, limit: int = 50) -> List[Dict]:
        """Recupera items pendientes de revisión humana."""
        # TODO: Implementar consulta a BD
        # return self.db.get_pending_reviews(limit)
        return []

    def approve_review(self, review_id: int, target_category: str) -> bool:
        """Aprueba un item de revisión y lo distribuye al KB especializado."""
        # TODO: Implementar
        # 1. Obtener el review de BD
        # 2. Escribir en el KB especializado
        # 3. Actualizar status a 'approved'
        # 4. Auditar acción
        pass

    def reject_review(self, review_id: int, reason: str) -> bool:
        """Rechaza un item de revisión."""
        # TODO: Implementar
        # 1. Actualizar status a 'rejected'
        # 2. Guardar motivo de rechazo
        # 3. Auditar acción
        pass