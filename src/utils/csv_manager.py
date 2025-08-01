# src/utils/csv_manager.py
import csv
import os
import re
from .database import SessionLocal
from .helpers import log_action
from src.models import CustomerCompany, Product, Inventory

from src.models import Invoice, InvoiceItem

class CsvManager:
    def __init__(self, companies_tab, inventory_tab, audit_log_tab, invoice_history_tab):
        self.companies_tab = companies_tab
        self.inventory_tab = inventory_tab
        self.audit_log_tab = audit_log_tab
        self.invoice_history_tab = invoice_history_tab

    def handle_import_csv(self, file_name, import_type):
        if import_type == "companies_and_products":
            return self.import_companies_and_products(file_name)
        elif import_type == "invoices":
            return self.import_invoices(file_name)

    def handle_export_csv(self, file_name, export_type):
        if export_type == "companies_and_products":
            return self.export_companies_and_products(file_name)
        elif export_type == "invoices":
            return self.export_invoices(file_name)

    def import_companies_and_products(self, file_name):
        try:
            with SessionLocal() as db_session:
                companies_cache = {c.name: c for c in db_session.query(CustomerCompany).all()}

                with open(file_name, mode='r', encoding='utf-8-sig') as infile:
                    reader = csv.DictReader(infile)
                    for row in reader:
                        company_name = row.get('CompanyName', '').strip()
                        if not company_name:
                            continue

                        company = companies_cache.get(company_name)
                        if not company:
                            state_raw = row.get('State', '').strip()
                            state_name, state_code = self._parse_state(state_raw)

                            company = CustomerCompany(
                                name=company_name, address=row.get('Address', '').strip(),
                                state=state_name, state_code=state_code,
                                gstin=row.get('GSTIN', '').strip()
                            )
                            db_session.add(company)
                            db_session.flush()
                            companies_cache[company_name] = company

                        product_name = row.get('ProductName', '').strip()
                        if product_name:
                            price_str = row.get('Price', '0').strip()
                            price = float(price_str) if price_str else 0.0
                            new_product = Product(name=product_name, price=price, company_id=company.id)
                            new_inventory = Inventory(stock_quantity=0, product=new_product)
                            db_session.add(new_product)
                            db_session.add(new_inventory)

                log_action(db_session, "IMPORT", "System", None, f"Imported data from CSV file: {os.path.basename(file_name)}.")
                db_session.commit()

            self.companies_tab.load_companies()
            self.inventory_tab.load_inventory_data()
            self.audit_log_tab.load_logs()
            return True, "Data imported successfully!"
        except Exception as e:
            return False, f"An error occurred during import:\n{e}"

    def export_companies_and_products(self, file_name):
        try:
            with SessionLocal() as db_session:
                companies = db_session.query(CustomerCompany).order_by(CustomerCompany.name).all()
                with open(file_name, mode='w', newline='', encoding='utf-8') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(['CompanyName', 'CompanyID', 'Address', 'State', 'GSTIN', 'ProductID', 'ProductName', 'Price'])

                    for company in companies:
                        state_formatted = f"{company.state} (Code: {company.state_code})"
                        if not company.products:
                            writer.writerow([company.name, company.id, company.address, state_formatted, company.gstin, '', '', ''])
                        else:
                            for product in sorted(company.products, key=lambda p: p.name):
                                writer.writerow([company.name, company.id, company.address, state_formatted, company.gstin, product.id, product.name, product.price])

                log_action(db_session, "EXPORT", "System", None, f"Exported data to CSV file: {os.path.basename(file_name)}.")
                db_session.commit()

            self.audit_log_tab.load_logs()
            return True, "Data exported successfully!"
        except Exception as e:
            return False, f"An error occurred during export:\n{e}"

    def import_invoices(self, file_name):
        try:
            with SessionLocal() as db_session:
                with open(file_name, mode='r', encoding='utf-8-sig') as infile:
                    reader = csv.DictReader(infile)
                    for row in reader:
                        # This is a simplified import process. A real-world application
                        # would need more robust error handling and data validation.
                        customer = db_session.query(CustomerCompany).filter(CustomerCompany.name == row['CustomerName']).first()
                        if customer:
                            invoice = Invoice(
                                invoice_number=row['InvoiceNumber'],
                                customer_id=customer.id,
                                vehicle_number=row['VehicleNumber'],
                                date=row['Date'],
                                total_amount=row['TotalAmount']
                            )
                            db_session.add(invoice)
                            db_session.flush()

                            # Assuming items are in a separate file or a more complex format
                            # For simplicity, we are not importing items here.

                log_action(db_session, "IMPORT", "System", None, f"Imported invoices from CSV file: {os.path.basename(file_name)}.")
                db_session.commit()

            self.invoice_history_tab.load_invoices()
            self.audit_log_tab.load_logs()
            return True, "Invoices imported successfully!"
        except Exception as e:
            return False, f"An error occurred during invoice import:\n{e}"

    def export_invoices(self, file_name):
        try:
            with SessionLocal() as db_session:
                invoices = db_session.query(Invoice).order_by(Invoice.date.desc()).all()
                with open(file_name, mode='w', newline='', encoding='utf-8') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(['InvoiceNumber', 'CustomerName', 'Date', 'VehicleNumber', 'TotalAmount'])

                    for invoice in invoices:
                        writer.writerow([
                            invoice.invoice_number,
                            invoice.customer.name,
                            invoice.date,
                            invoice.vehicle_number,
                            invoice.total_amount
                        ])

                log_action(db_session, "EXPORT", "System", None, f"Exported invoices to CSV file: {os.path.basename(file_name)}.")
                db_session.commit()

            self.audit_log_tab.load_logs()
            return True, "Invoices exported successfully!"
        except Exception as e:
            return False, f"An error occurred during invoice export:\n{e}"

    def _parse_state(self, state_raw):
        match = re.search(r"(.+?)\s*\(Code:\s*(\d+)\)", state_raw)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return state_raw, ""
