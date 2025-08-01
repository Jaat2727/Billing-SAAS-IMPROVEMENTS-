from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from src.utils.database import Base

class Invoice(Base):
    __tablename__ = 'invoices'
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('customer_companies.id'))
    vehicle_number = Column(String)
    date = Column(Date, nullable=False)
    total_amount = Column(Float)
    payment_status = Column(String)
    
    # SQLAlchemy can now find 'CustomerCompany' correctly
    customer = relationship("CustomerCompany", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceItem(Base):
    __tablename__ = 'invoice_items'
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    product_name = Column(String)
    quantity = Column(Integer)
    price_per_unit = Column(Float)
    invoice = relationship("Invoice", back_populates="items")

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    payment_date = Column(Date)
    amount_paid = Column(Float)
    payment_method = Column(String)
    invoice = relationship("Invoice", back_populates="payments")