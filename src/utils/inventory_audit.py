# src/utils/inventory_audit.py
from src.models import Inventory, InventoryHistory, Product
from sqlalchemy.orm import Session

def validate_inventory_integrity(db: Session):
    errors = []
    products = db.query(Product).all()
    for product in products:
        if not product.inventory:
            continue
        history = db.query(InventoryHistory).filter_by(product_id=product.id).order_by(InventoryHistory.timestamp).all()
        stock_calc = 0
        for h in history:
            stock_calc += h.change_quantity
            if h.new_stock != stock_calc:
                errors.append(f"Stock mismatch for product {product.name} at history {h.id}: expected {stock_calc}, got {h.new_stock}")
            if h.new_stock < 0:
                errors.append(f"Negative stock for product {product.name} at history {h.id}")
        if product.inventory.stock_quantity != stock_calc:
            errors.append(f"Current stock mismatch for product {product.name}: expected {stock_calc}, got {product.inventory.stock_quantity}")
    return errors

def find_orphaned_history(db: Session):
    orphans = []
    histories = db.query(InventoryHistory).all()
    for h in histories:
        if not db.query(Product).filter_by(id=h.product_id).first():
            orphans.append(h.id)
    return orphans
