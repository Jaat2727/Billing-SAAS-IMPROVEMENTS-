# src/utils/helpers.py
from src.models import AuditLog

def log_action(db_session, action, entity_type, entity_id, details):
    """A centralized function to create an audit log entry. Note: does not commit."""
    log_entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details
    )
    db_session.add(log_entry)