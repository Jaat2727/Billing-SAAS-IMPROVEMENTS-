# src/models/inventory.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.utils.database import Base

class Inventory(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True, index=True)
    # --- DEFINITIVE FIX: Links to a product by its ID, not its name ---
    product_id = Column(Integer, ForeignKey('products.id'), unique=True, nullable=False)
    stock_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=10)
    
    # --- DEFINITIVE FIX: Relationship back to the Product model ---
    product = relationship("Product", back_populates="inventory")

class InventoryHistory(Base):
    __tablename__ = 'inventory_history'
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    change_quantity = Column(Integer)
    new_stock = Column(Integer)  # Track resulting stock after change
    reason = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, nullable=True)  # Optionally track user