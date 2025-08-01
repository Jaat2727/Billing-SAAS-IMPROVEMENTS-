# src/models/audit_log.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from src.utils.database import Base

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    action = Column(String)       # e.g., 'CREATE', 'UPDATE', 'DELETE', 'IMPORT'
    entity_type = Column(String)  # e.g., 'Company', 'Product', 'Inventory', 'System'
    entity_id = Column(Integer, nullable=True)
    details = Column(String)      # e.g., "Company 'ABC Corp' created."