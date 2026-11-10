from app.models.models import AuditLog

def audit(db, actor_id, action, entity, entity_id=None, details=None):
    db.add(AuditLog(actor_id=actor_id, action=action, entity=entity, entity_id=entity_id, details=details or {}))
