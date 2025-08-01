# src/models/product.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.utils.database import Base

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    company_id = Column(Integer, ForeignKey('customer_companies.id'))
    
    company = relationship("CustomerCompany", back_populates="products")
    # --- DEFINITIVE FIX: Establishes the one-to-one link to its inventory record ---
    inventory = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")