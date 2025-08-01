from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox, QDateEdit, QGridLayout)
from PyQt6.QtCore import QDate, Qt


from src.models.inventory import Inventory

from src.utils.database import SessionLocal
from src.models import CustomerCompany, Product, Invoice, InvoiceItem, UserSettings, InventoryHistory
from src.utils.theme import DARK_THEME
from src.utils.pdf_service import PdfService
from src.utils.invoice_number_service import InvoiceNumberService

from src.tabs.base_tab import BaseTab

class CreateInvoiceTab(BaseTab):
    def load_latest_data(self, select_last=False):
        """Refresh the company and product dropdowns with the latest data from the database."""
        self.refresh_company_dropdown(select_last=select_last)
        # Also refresh products for the selected company
        self.on_company_selected(self.company_combo.currentIndex())

    def safe_float(self, value):
        try:
            num = float(value)
            if not (num == num and num != float('inf') and num != float('-inf')):
                return 0.0
            return num
        except Exception:
            return 0.0

    def safe_int(self, value):
        try:
            num = int(float(value))
            return num
        except Exception:
            return 0
    def __init__(self):
        super().__init__()
        self.db_session = self.get_db_session()
        self.invoice_number_service = InvoiceNumberService()
        self.init_ui()
        self.apply_styles()
        self.load_initial_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(28)

        # --- Modern Card for Customer & Invoice Details ---
        details_card = QFrame()
        details_card.setObjectName("details-card")
        details_layout = QGridLayout(details_card)
        details_layout.setHorizontalSpacing(32)
        details_layout.setVerticalSpacing(16)

        # Customer
        company_label = QLabel("Customer Company")
        company_label.setObjectName("form-label")
        self.company_combo = QComboBox()
        self.company_combo.setObjectName("company-combo")
        self.company_combo.currentIndexChanged.connect(self.on_company_selected)
        details_layout.addWidget(company_label, 0, 0)
        details_layout.addWidget(self.company_combo, 0, 1)

        # Invoice Date
        date_label = QLabel("Invoice Date")
        date_label.setObjectName("form-label")
        self.invoice_date_edit = QDateEdit(QDate.currentDate())
        self.invoice_date_edit.setCalendarPopup(True)
        details_layout.addWidget(date_label, 1, 0)
        details_layout.addWidget(self.invoice_date_edit, 1, 1)

        # Vehicle Number
        vehicle_label = QLabel("Vehicle Number")
        vehicle_label.setObjectName("form-label")
        self.vehicle_no_input = QLineEdit()
        details_layout.addWidget(vehicle_label, 2, 0)
        details_layout.addWidget(self.vehicle_no_input, 2, 1)

        # GST Type (Intra/Inter State)
        gst_type_label = QLabel("GST Type")
        gst_type_label.setObjectName("form-label")
        self.gst_type_combo = QComboBox()
        self.gst_type_combo.addItem("Intra-State (CGST/SGST)", "intra")
        self.gst_type_combo.addItem("Inter-State (IGST)", "inter")
        details_layout.addWidget(gst_type_label, 3, 0)
        details_layout.addWidget(self.gst_type_combo, 3, 1)

        main_layout.addWidget(details_card)

        # --- Add Products Section ---
        add_product_card = QFrame()
        add_product_card.setObjectName("add-product-card")
        add_product_layout = QHBoxLayout(add_product_card)
        add_product_layout.setSpacing(16)
        from PyQt6.QtWidgets import QCompleter
        self.product_combo = QComboBox()
        self.product_combo.setObjectName("product-combo")
        self.product_combo.setEditable(True)
        self.product_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.product_combo.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.quantity_input = QLineEdit("1")
        self.quantity_input.setObjectName("quantity-input")
        add_product_btn = QPushButton("+ Add Product")
        add_product_btn.setObjectName("add-product-btn")
        add_product_btn.clicked.connect(self.add_product_to_table)
        add_product_layout.addWidget(self.product_combo, 3)
        add_product_layout.addWidget(self.quantity_input, 1)
        add_product_layout.addWidget(add_product_btn, 1)
        main_layout.addWidget(add_product_card)

        # --- Items Table ---
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["Product Name", "Price", "Quantity", "Total", ""])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.items_table.setObjectName("items-table")
        main_layout.addWidget(self.items_table)

        # --- Bottom Section: Total & Generate PDF ---
        bottom_card = QFrame()
        bottom_card.setObjectName("bottom-card")
        bottom_layout = QHBoxLayout(bottom_card)
        self.total_label = QLabel("Total Amount: ₹0.00")
        self.total_label.setObjectName("total-label")
        generate_pdf_btn = QPushButton("Generate & Save Invoice PDF")
        generate_pdf_btn.setObjectName("primary-button")
        generate_pdf_btn.clicked.connect(self.generate_invoice_pdf)
        bottom_layout.addWidget(self.total_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(generate_pdf_btn)
        main_layout.addWidget(bottom_card)


    def load_initial_data(self):
        self.refresh_company_dropdown()
        # No need to load states for GST, handled by GST type combo

    def refresh_company_dropdown(self, select_last=False):
        self.company_combo.blockSignals(True)
        self.company_combo.clear()
        companies = self.db_session.query(CustomerCompany).all()
        for company in companies:
            self.company_combo.addItem(company.name, company.id)
        self.company_combo.blockSignals(False)
        if select_last and companies:
            self.company_combo.setCurrentIndex(len(companies) - 1)

    def on_company_selected(self, index):
        company_id = self.company_combo.itemData(index)
        self.product_combo.clear()
        if company_id:
            products = (
                self.db_session.query(Product)
                .filter(Product.company_id == company_id)
                .outerjoin(Product.inventory)
                .all()
            )
            for i, product in enumerate(products):
                stock = product.inventory.stock_quantity if product.inventory else 0
                label = f"{product.name} (In Stock: {stock})" if stock > 0 else f"{product.name} (Out of Stock)"
                self.product_combo.addItem(label, product.id)
                # Use a subtle pastel color for out-of-stock, and set text color for readability
                if stock == 0:
                    from PyQt6.QtGui import QColor
                    from PyQt6.QtCore import Qt
                    # Light pastel orange background, dark gray text
                    self.product_combo.setItemData(i, QColor(255, 230, 210), Qt.ItemDataRole.BackgroundRole)
                    self.product_combo.setItemData(i, QColor(60, 60, 60), Qt.ItemDataRole.ForegroundRole)

    def add_product_to_table(self):
        product_id = self.product_combo.itemData(self.product_combo.currentIndex())
        if not product_id:
            return

        product = self.db_session.query(Product).get(product_id)
        quantity = self.safe_int(self.quantity_input.text())
        stock = product.inventory.stock_quantity if product.inventory else 0
        if quantity > stock:
            QMessageBox.critical(self, "Insufficient Stock", f"Cannot add {quantity} units of {product.name}. Only {stock} in stock.")
            return
        # Check for duplicate product in table
        for row in range(self.items_table.rowCount()):
            existing_name = self.items_table.item(row, 0).text()
            if existing_name == product.name:
                # Ask user if they want to add to previous quantity
                reply = QMessageBox.question(self, "Duplicate Product", f"'{product.name}' is already in the invoice.\nDo you want to add this quantity to the previous one?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
                if reply == QMessageBox.StandardButton.Yes:
                    prev_qty = self.safe_int(self.items_table.item(row, 2).text())
                    new_qty = prev_qty + quantity
                    if new_qty > stock:
                        QMessageBox.critical(self, "Insufficient Stock", f"Cannot add {new_qty} units of {product.name}. Only {stock} in stock.")
                        return
                    self.items_table.setItem(row, 2, QTableWidgetItem(str(new_qty)))
                    total_price = product.price * new_qty
                    self.items_table.setItem(row, 3, QTableWidgetItem(f"₹{total_price:,.2f}"))
                    self.update_total()
                # If No, do nothing
                return

        row_position = self.items_table.rowCount()
        self.items_table.insertRow(row_position)
        self.items_table.setItem(row_position, 0, QTableWidgetItem(product.name))
        self.items_table.setItem(row_position, 1, QTableWidgetItem(f"₹{product.price:,.2f}"))
        self.items_table.setItem(row_position, 2, QTableWidgetItem(str(quantity)))
        self.items_table.setItem(row_position, 3, QTableWidgetItem(f"₹{product.price * quantity:,.2f}"))
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.items_table.removeRow(row_position))
        self.items_table.setCellWidget(row_position, 4, remove_btn)
        self.update_total()

    def update_total(self):
        total = 0
        for row in range(self.items_table.rowCount()):
            value = self.items_table.item(row, 3)
            if value is None:
                continue
            text = value.text().replace("₹", "").replace(",", "")
            num = self.safe_float(text)
            total += num
        self.total_label.setText(f"Total Amount: ₹{total:,.2f}")

    def generate_invoice_pdf(self):
        import os
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        settings = self.db_session.query(UserSettings).first()
        if not settings:
            QMessageBox.critical(self, "Error", "Please configure your company settings first.")
            return

        customer_id = self.company_combo.itemData(self.company_combo.currentIndex())
        if not customer_id:
            QMessageBox.critical(self, "Error", "Please select a customer.")
            return

        customer = self.db_session.query(CustomerCompany).get(customer_id)

        items = []
        for row in range(self.items_table.rowCount()):
            try:
                product_name = self.items_table.item(row, 0).text()
                quantity_text = self.items_table.item(row, 2).text()
                price_text = self.items_table.item(row, 1).text().replace("₹", "").replace(",", "")
                quantity = self.safe_int(quantity_text)
                price_per_unit = self.safe_float(price_text)
                items.append({
                    "product_name": product_name,
                    "quantity": quantity,
                    "price_per_unit": price_per_unit
                })
            except Exception:
                continue

        if not items:
            QMessageBox.critical(self, "Error", "Please add at least one item to the invoice.")
            return

        total_amount = sum(item['quantity'] * item['price_per_unit'] for item in items)

        invoice_data = {
            "customer_id": customer_id,
            "vehicle_number": self.vehicle_no_input.text(),
            "date": self.invoice_date_edit.date().toPyDate(),
            "total_amount": total_amount,
            "items": items,
            "customer": {
                "name": customer.name,
                "address": customer.address,
                "gstin": customer.gstin,
                "state_code": customer.state_code
            }
        }

        invoice = self.save_invoice(invoice_data)
        if invoice is None:
            # Error already shown in save_invoice (e.g. insufficient stock)
            return
        invoice_data['invoice_number'] = invoice.invoice_number

        pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../pdf'))
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        file_name = f"invoice_{invoice.invoice_number}.pdf"
        file_path = os.path.join(pdf_dir, file_name)

        if os.path.exists(file_path):
            msg = QMessageBox(self)
            msg.setWindowTitle("PDF Exists")
            msg.setText(f"A PDF for this invoice already exists. What would you like to do?")
            open_btn = msg.addButton("Open PDF", QMessageBox.ButtonRole.AcceptRole)
            overwrite_btn = msg.addButton("Overwrite PDF", QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            msg.setIcon(QMessageBox.Icon.Question)
            msg.exec()
            if msg.clickedButton() == open_btn:
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                return
            elif msg.clickedButton() == cancel_btn:
                return
            # else: overwrite

        pdf_service = PdfService(settings)
        pdf_service.generate_invoice(invoice_data, file_path=file_path)
        msg = QMessageBox(self)
        msg.setWindowTitle("PDF Saved")
        msg.setText(f"Invoice PDF generated and saved as {file_path}\n\nWould you like to open the PDF folder?")
        open_btn = msg.addButton("Open Folder", QMessageBox.ButtonRole.AcceptRole)
        close_btn = msg.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
        if msg.clickedButton() == open_btn:
            QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_dir))

    def save_invoice(self, invoice_data):
        invoice_number = self.invoice_number_service.get_next_invoice_number()
        new_invoice = Invoice(
            invoice_number=invoice_number,
            customer_id=invoice_data['customer_id'],
            vehicle_number=invoice_data['vehicle_number'],
            date=invoice_data['date'],
            total_amount=invoice_data['total_amount']
        )
        self.db_session.add(new_invoice)
        self.db_session.flush()

        user_id = None  # TODO: Replace with actual user ID if available
        for item in invoice_data['items']:
            product = self.db_session.query(Product).filter(Product.name == item['product_name']).first()
            if product:
                if product.inventory.stock_quantity < item['quantity']:
                    QMessageBox.critical(self, "Error", f"Insufficient stock for {product.name}.")
                    return None
                product.inventory.stock_quantity -= item['quantity']
                history_entry = InventoryHistory(
                    product_id=product.id,
                    change_quantity=-item['quantity'],
                    new_stock=product.inventory.stock_quantity,
                    reason=f"Invoice {invoice_number}",
                    user_id=user_id
                )
                self.db_session.add(history_entry)

            new_item = InvoiceItem(
                invoice_id=new_invoice.id,
                product_name=item['product_name'],
                quantity=item['quantity'],
                price_per_unit=item['price_per_unit']
            )
            self.db_session.add(new_item)

        self.db_session.commit()
        return new_invoice

    def apply_styles(self):
        self.setStyleSheet(f"""
            QFrame#details-card, QFrame#add-product-card, QFrame#bottom-card {{
                background-color: {DARK_THEME['bg_surface']};
                border-radius: 14px;
                padding: 24px 32px;
                margin-bottom: 12px;
            }}
            QLabel, QDateEdit {{ color: {DARK_THEME['text_primary']}; }}
            QLabel#form-label {{ font-size: 15px; font-weight: 500; color: {DARK_THEME['text_secondary']}; }}
            QComboBox, QLineEdit {{
                background-color: {DARK_THEME['bg_input']};
                color: {DARK_THEME['text_primary']};
                border: 1px solid {DARK_THEME['border_main']};
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 15px;
            }}
            QComboBox#company-combo, QComboBox#product-combo {{ min-width: 320px; }}
            QComboBox#product-combo QAbstractItemView {{
                min-width: 340px;
                font-size: 18px;
                padding: 8px 16px;
            }}
            QComboBox#product-combo QAbstractItemView::item {{
                min-height: 36px;
                font-size: 18px;
                padding: 8px 16px;
                
            }}
            QLineEdit#quantity-input {{ max-width: 80px; }}
            QPushButton#add-product-btn {{
                background-color: {DARK_THEME['accent_primary']};
                color: {DARK_THEME['text_on_accent']};
                border: none;
                padding: 10px 18px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 15px;
            }}
            QTableWidget#items-table {{
                background-color: {DARK_THEME['bg_surface']};
                gridline-color: {DARK_THEME['border_main']};
                border: 1px solid {DARK_THEME['border_main']};
                font-size: 15px;
            }}
            QHeaderView::section {{
                background-color: {DARK_THEME['bg_sidebar']};
                color: {DARK_THEME['text_secondary']};
                padding: 10px;
                border: none;
                font-size: 15px;
            }}
            QLabel#total-label {{
                font-size: 20px;
                font-weight: 700;
                color: {DARK_THEME['text_primary']};
            }}
            QPushButton#primary-button {{
                background-color: {DARK_THEME['accent_primary']};
                color: {DARK_THEME['text_on_accent']};
                border: none;
                padding: 12px 28px;
                border-radius: 8px;
                font-weight: 700;
                font-size: 16px;
            }}
        """)
