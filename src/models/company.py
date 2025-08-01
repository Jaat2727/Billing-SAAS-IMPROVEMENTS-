from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.utils.database import Base

class CustomerCompany(Base):
    __tablename__ = 'customer_companies'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    gstin = Column(String)
    state = Column(String)
    state_code = Column(String)
    address = Column(String)
    # The relationship back to the products is RESTORED.
    products = relationship("Product", back_populates="company", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer")