from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QHBoxLayout, QComboBox, QMessageBox, QLabel)
from src.utils.database import SessionLocal
from src.models import Invoice, UserSettings
from src.utils.theme import DARK_THEME
from src.utils.pdf_service import PdfService

from src.tabs.base_tab import BaseTab

class InvoiceHistoryTab(BaseTab):
    def __init__(self):
        super().__init__()
        self.db_session = self.get_db_session()
        self.init_ui()
        self.load_invoices()
        self.apply_styles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Top controls: navigation, sorting, and refresh
        controls_layout = QHBoxLayout()
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Newest First", "Oldest First", "Paid", "Pending", "Overdue"])
        self.sort_combo.currentIndexChanged.connect(self.load_invoices)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.handle_refresh)
        # Navigation buttons
        nav_prev_btn = QPushButton("← Prev")
        nav_next_btn = QPushButton("Next →")
        nav_prev_btn.clicked.connect(self.goto_prev_page)
        nav_next_btn.clicked.connect(self.goto_next_page)
        controls_layout.addWidget(nav_prev_btn)
        controls_layout.addWidget(nav_next_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(QLabel("Sort by:"))
        controls_layout.addWidget(self.sort_combo)
        controls_layout.addWidget(refresh_btn)
        main_layout.addLayout(controls_layout)

        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(6)
        self.invoice_table.setHorizontalHeaderLabels(["Invoice #", "Company", "Date", "Total", "Status", "Actions"])
        self.invoice_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.invoice_table.setColumnWidth(5, 240)  # Double the default width for Actions
        self.invoice_table.setSortingEnabled(True)
        self.invoice_table.horizontalHeader().sectionClicked.connect(self.handle_header_sort)
        main_layout.addWidget(self.invoice_table)

        # For navigation (pagination)
        self.current_page = 0
        self.page_size = 20

    def load_invoices(self):
        self.invoice_table.setRowCount(0)
        sort_option = self.sort_combo.currentText() if hasattr(self, 'sort_combo') else "Newest First"
        query = self.db_session.query(Invoice)
        if sort_option == "Newest First":
            query = query.order_by(Invoice.date.desc())
        elif sort_option == "Oldest First":
            query = query.order_by(Invoice.date.asc())
        elif sort_option == "Paid":
            query = query.filter(Invoice.payment_status == "Paid").order_by(Invoice.date.desc())
        elif sort_option == "Pending":
            query = query.filter(Invoice.payment_status == "Pending").order_by(Invoice.date.desc())
        elif sort_option == "Overdue":
            query = query.filter(Invoice.payment_status == "Overdue").order_by(Invoice.date.desc())
        invoices = query.all()

        # Pagination
        start = self.current_page * self.page_size
        end = start + self.page_size
        paged_invoices = invoices[start:end]

        for inv in paged_invoices:
            row = self.invoice_table.rowCount()
            self.invoice_table.insertRow(row)
            self.invoice_table.setItem(row, 0, QTableWidgetItem(inv.invoice_number))
            self.invoice_table.setItem(row, 1, QTableWidgetItem(inv.customer.name))
            self.invoice_table.setItem(row, 2, QTableWidgetItem(inv.date.strftime("%Y-%m-%d")))
            self.invoice_table.setItem(row, 3, QTableWidgetItem(f"₹{inv.total_amount:,.2f}"))

            # Status with improved color plate
            status_combo = QComboBox()
            status_combo.addItems(["Pending", "Paid", "Overdue"])
            status_combo.setCurrentText(inv.payment_status)
            color_map = {
                "Paid": "background-color: #43a047; color: #fff; border: 2px solid #388e3c; font-weight: bold;",
                "Pending": "background-color: #fbc02d; color: #222; border: 2px solid #fbc02d; font-weight: bold;",
                "Overdue": "background-color: #e53935; color: #fff; border: 2px solid #b71c1c; font-weight: bold;"
            }
            status_style = color_map.get(inv.payment_status, color_map["Pending"])
            status_combo.setStyleSheet(f"QComboBox {{{status_style} border-radius: 6px; padding: 6px 12px;}}")
            self.invoice_table.setCellWidget(row, 4, status_combo)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            download_btn = QPushButton("Download PDF")
            download_btn.clicked.connect(lambda chk, inv=inv: self.redownload_invoice(inv))
            share_btn = QPushButton("Share")
            share_btn.clicked.connect(lambda chk, inv=inv: self.share_invoice(inv))
            actions_layout.addWidget(download_btn)
            actions_layout.addWidget(share_btn)
            actions_layout.setContentsMargins(0,0,0,0)
            self.invoice_table.setCellWidget(row, 5, actions_widget)
            # Make the row double thick for better visibility
            self.invoice_table.setRowHeight(row, 60)

    def handle_refresh(self):
        # Fully reloads the table and updates all colors/styles
        self.db_session.close()
        self.db_session = self.get_db_session()
        self.load_invoices()

    def handle_header_sort(self, logicalIndex):
        # Sorts by column when header is clicked
        self.invoice_table.sortItems(logicalIndex, order=self.invoice_table.horizontalHeader().sortIndicatorOrder())

    def goto_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_invoices()

    def goto_next_page(self):
        # Only go to next page if there are more invoices
        sort_option = self.sort_combo.currentText() if hasattr(self, 'sort_combo') else "Newest First"
        query = self.db_session.query(Invoice)
        if sort_option == "Newest First":
            query = query.order_by(Invoice.date.desc())
        elif sort_option == "Oldest First":
            query = query.order_by(Invoice.date.asc())
        elif sort_option == "Paid":
            query = query.filter(Invoice.payment_status == "Paid").order_by(Invoice.date.desc())
        elif sort_option == "Pending":
            query = query.filter(Invoice.payment_status == "Pending").order_by(Invoice.date.desc())
        elif sort_option == "Overdue":
            query = query.filter(Invoice.payment_status == "Overdue").order_by(Invoice.date.desc())
        invoices = query.all()
        max_page = (len(invoices) - 1) // self.page_size
        if self.current_page < max_page:
            self.current_page += 1
            self.load_invoices()

    def redownload_invoice(self, invoice):
        import os
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        settings = self.db_session.query(UserSettings).first()
        if not settings:
            QMessageBox.critical(self, "Error", "Please configure your company settings first.")
            return

        items = []
        for item in invoice.items:
            items.append({
                "product_name": item.product_name,
                "quantity": item.quantity,
                "price_per_unit": item.price_per_unit
            })

        invoice_data = {
            "invoice_number": invoice.invoice_number,
            "date": invoice.date.strftime("%Y-%m-%d"),
            "vehicle_number": invoice.vehicle_number,
            "customer": {
                "name": invoice.customer.name,
                "address": invoice.customer.address,
                "gstin": invoice.customer.gstin,
                "state_code": invoice.customer.state_code
            },
            "items": items
        }

        pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../pdf'))
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        file_name = f"invoice_{invoice.invoice_number}.pdf"
        file_path = os.path.join(pdf_dir, file_name)

        if os.path.exists(file_path):
            msg = QMessageBox(self)
            msg.setWindowTitle("PDF Exists")
            msg.setText(f"A PDF for this invoice already exists. What would you like to do?")
            open_btn = msg.addButton("Open Folder", QMessageBox.ButtonRole.AcceptRole)
            overwrite_btn = msg.addButton("Overwrite PDF", QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            msg.setIcon(QMessageBox.Icon.Question)
            msg.exec()
            if msg.clickedButton() == open_btn:
                QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_dir))
                return
            elif msg.clickedButton() == cancel_btn:
                return
            # else: overwrite

        # Generate and save PDF in pdf/ folder
        pdf_service = PdfService(settings)
        # Patch PdfService to allow custom path
        if hasattr(pdf_service, 'generate_invoice'):
            try:
                pdf_service.generate_invoice(invoice_data, file_path=file_path)
            except TypeError:
                # fallback for old signature
                generated = pdf_service.generate_invoice(invoice_data)
                # Move to pdf_dir if not already there
                if os.path.abspath(generated) != os.path.abspath(file_path):
                    import shutil
                    shutil.move(generated, file_path)
        else:
            QMessageBox.critical(self, "Error", "PDF generation service is not available.")
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("PDF Saved")
        msg.setText(f"Invoice PDF saved as {file_path}\n\nWhat would you like to do?")
        open_folder_btn = msg.addButton("Open Folder", QMessageBox.ButtonRole.AcceptRole)
        open_pdf_btn = msg.addButton("Open PDF", QMessageBox.ButtonRole.ActionRole)
        close_btn = msg.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
        if msg.clickedButton() == open_folder_btn:
            QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_dir))
        elif msg.clickedButton() == open_pdf_btn:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def share_invoice(self, invoice):
        import os
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        settings = self.db_session.query(UserSettings).first()
        if not settings:
            QMessageBox.critical(self, "Error", "Please configure your company settings first.")
            return

        items = []
        for item in invoice.items:
            items.append({
                "product_name": item.product_name,
                "quantity": item.quantity,
                "price_per_unit": item.price_per_unit
            })

        invoice_data = {
            "invoice_number": invoice.invoice_number,
            "date": invoice.date.strftime("%Y-%m-%d"),
            "vehicle_number": invoice.vehicle_number,
            "customer": {
                "name": invoice.customer.name,
                "address": invoice.customer.address,
                "gstin": invoice.customer.gstin,
                "state_code": invoice.customer.state_code
            },
            "items": items
        }

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


    def apply_styles(self):
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {DARK_THEME['bg_surface']};
                gridline-color: {DARK_THEME['border_main']};
                border: 1px solid {DARK_THEME['border_main']};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {DARK_THEME['bg_sidebar']};
                color: {DARK_THEME['text_secondary']};
                padding: 10px;
                border: none;
            }}
            QTableWidget::item {{
                padding: 10px;
                color: {DARK_THEME['text_primary']};
            }}
        """)
