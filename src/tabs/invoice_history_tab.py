import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QHBoxLayout, QComboBox, QMessageBox, QLabel, QDialog, QDialogButtonBox)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from src.utils.database import SessionLocal
from src.models import Invoice, UserSettings
from src.utils.theme import DARK_THEME
from src.utils.pdf_service import PdfService

from src.tabs.base_tab import BaseTab

class EditInvoiceDialog(QDialog):
    def __init__(self, current_status, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Invoice Status")

        self.layout = QVBoxLayout(self)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Paid", "Pending", "Overdue"])
        self.status_combo.setCurrentText(current_status)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(QLabel("Select new status:"))
        self.layout.addWidget(self.status_combo)
        self.layout.addWidget(self.buttons)

    def get_status(self):
        return self.status_combo.currentText()

class InvoiceHistoryTab(BaseTab):
    def __init__(self):
        super().__init__()
        self.db_session = self.get_db_session()
        self.resource_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'resources')
        self.init_ui()
        self.load_invoices()
        self.apply_styles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # Top controls: filtering, and refresh
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        self.filter_combo = QComboBox()
        self.filter_combo.setObjectName("filter-combo")
        self.filter_combo.addItems(["All", "Paid", "Pending", "Overdue"])
        self.filter_combo.currentIndexChanged.connect(self.load_invoices)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("header-button")
        refresh_btn.clicked.connect(self.handle_refresh)

        controls_layout.addWidget(QLabel("Filter by:"))
        controls_layout.addWidget(self.filter_combo)
        controls_layout.addStretch()
        controls_layout.addWidget(refresh_btn)
        main_layout.addLayout(controls_layout)

        self.invoice_table = QTableWidget()
        self.invoice_table.setObjectName("invoice-table")
        self.invoice_table.setColumnCount(6)
        self.invoice_table.setHorizontalHeaderLabels(["Invoice #", "Company", "Date", "Total", "Status", "Actions"])
        self.invoice_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.invoice_table.setColumnWidth(5, 160)
        self.invoice_table.setSortingEnabled(True)
        self.invoice_table.horizontalHeader().sectionClicked.connect(self.handle_header_sort)
        self.invoice_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.invoice_table)

        # Pagination controls
        pagination_layout = QHBoxLayout()
        pagination_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nav_prev_btn = QPushButton("← Prev")
        self.nav_next_btn = QPushButton("Next →")
        self.nav_prev_btn.setObjectName("pagination-button")
        self.nav_next_btn.setObjectName("pagination-button")
        self.nav_prev_btn.clicked.connect(self.goto_prev_page)
        self.nav_next_btn.clicked.connect(self.goto_next_page)
        self.page_label = QLabel("Page 1")
        self.page_label.setObjectName("page-label")
        pagination_layout.addWidget(self.nav_prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.nav_next_btn)
        main_layout.addLayout(pagination_layout)

        # For navigation (pagination)
        self.current_page = 0
        self.page_size = 15

    def _build_invoice_query(self):
        filter_option = self.filter_combo.currentText()
        query = self.db_session.query(Invoice)

        if filter_option in ["Paid", "Pending", "Overdue"]:
            query = query.filter(Invoice.payment_status == filter_option)

        # Default sort order
        query = query.order_by(Invoice.date.desc())

        return query

    def load_invoices(self):
        self.invoice_table.setRowCount(0)
        query = self._build_invoice_query()

        total_invoices = query.count()
        self.total_pages = (total_invoices + self.page_size - 1) // self.page_size

        # Pagination
        offset = self.current_page * self.page_size
        paged_invoices = query.offset(offset).limit(self.page_size).all()

        for inv in paged_invoices:
            row = self.invoice_table.rowCount()
            self.invoice_table.insertRow(row)

            self.invoice_table.setItem(row, 0, QTableWidgetItem(inv.invoice_number))
            self.invoice_table.setItem(row, 1, QTableWidgetItem(inv.customer.name))
            self.invoice_table.setItem(row, 2, QTableWidgetItem(inv.date.strftime("%b %d, %Y")))
            self.invoice_table.setItem(row, 3, QTableWidgetItem(f"₹{inv.total_amount:,.2f}"))

            # Status Indicator
            status_widget = self.create_status_widget(inv.payment_status)
            self.invoice_table.setCellWidget(row, 4, status_widget)

            # Action Buttons
            actions_widget = self.create_action_buttons(inv)
            self.invoice_table.setCellWidget(row, 5, actions_widget)

            self.invoice_table.setRowHeight(row, 48)

        self.update_pagination_controls()

    def create_status_widget(self, status):
        if status is None:
            status = "Pending"
        status_label = QLabel(status)
        status_label.setObjectName("status-label")
        status_label.setProperty("status", status.lower())
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return status_label

    def create_action_buttons(self, invoice):
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0,0,0,0)
        actions_layout.setSpacing(10)
        actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        download_btn = QPushButton("↓")
        download_btn.setObjectName("action-button")
        download_btn.setToolTip("Download PDF")
        download_btn.clicked.connect(lambda chk, inv=invoice: self.redownload_invoice(inv))

        share_btn = QPushButton("✉")
        share_btn.setObjectName("action-button")
        share_btn.setToolTip("Share Invoice")
        share_btn.clicked.connect(lambda chk, inv=invoice: self.share_invoice(inv))

        edit_btn = QPushButton("✎")
        edit_btn.setObjectName("action-button")
        edit_btn.setToolTip("Edit Status")
        edit_btn.clicked.connect(lambda chk, inv=invoice: self.edit_invoice(inv))

        actions_layout.addWidget(download_btn)
        actions_layout.addWidget(share_btn)
        actions_layout.addWidget(edit_btn)
        return actions_widget

    def edit_invoice(self, invoice):
        dialog = EditInvoiceDialog(invoice.payment_status or "Pending", self)
        if dialog.exec():
            new_status = dialog.get_status()
            invoice.payment_status = new_status
            self.db_session.commit()
            self.load_invoices()


    def handle_refresh(self):
        self.current_page = 0
        self.load_invoices()

    def handle_header_sort(self, logicalIndex):
        self.invoice_table.sortItems(logicalIndex, order=self.invoice_table.horizontalHeader().sortIndicatorOrder())

    def update_pagination_controls(self):
        self.page_label.setText(f"Page {self.current_page + 1} of {self.total_pages}")
        self.nav_prev_btn.setEnabled(self.current_page > 0)
        self.nav_next_btn.setEnabled(self.current_page < self.total_pages - 1)

    def goto_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_invoices()

    def goto_next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_invoices()

    def _get_invoice_data(self, invoice):
        return {
            "invoice_number": invoice.invoice_number,
            "date": invoice.date.strftime("%Y-%m-%d"),
            "vehicle_number": invoice.vehicle_number,
            "payment_status": invoice.payment_status,
            "customer": {
                "name": invoice.customer.name,
                "address": invoice.customer.address,
                "gstin": invoice.customer.gstin,
                "state_code": invoice.customer.state_code
            },
            "items": [{
                "product_name": item.product_name,
                "quantity": item.quantity,
                "price_per_unit": item.price_per_unit
            } for item in invoice.items]
        }

    def _handle_pdf_generation(self, invoice, action='download'):
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        settings = self.db_session.query(UserSettings).first()
        if not settings:
            QMessageBox.critical(self, "Error", "Please configure your company settings first.")
            return

        invoice_data = self._get_invoice_data(invoice)

        pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../pdf'))
        os.makedirs(pdf_dir, exist_ok=True)
        file_name = f"invoice_{invoice.invoice_number}.pdf"
        file_path = os.path.join(pdf_dir, file_name)

        should_generate = True
        if os.path.exists(file_path):
            msg = QMessageBox(self)
            msg.setWindowTitle("PDF Exists")
            msg.setText("A PDF for this invoice already exists. What would you like to do?")
            open_btn_text = "Open PDF" if action == 'share' else "Open Folder"
            open_btn = msg.addButton(open_btn_text, QMessageBox.ButtonRole.AcceptRole)
            overwrite_btn = msg.addButton("Overwrite PDF", QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            msg.setIcon(QMessageBox.Icon.Question)
            msg.exec()

            if msg.clickedButton() == open_btn:
                url = QUrl.fromLocalFile(file_path if action == 'share' else pdf_dir)
                QDesktopServices.openUrl(url)
                should_generate = False
            elif msg.clickedButton() == cancel_btn:
                should_generate = False

        if not should_generate:
            return

        pdf_service = PdfService(settings)
        pdf_service.generate_invoice(invoice_data, file_path=file_path)

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

    def redownload_invoice(self, invoice):
        self._handle_pdf_generation(invoice, action='download')

    def share_invoice(self, invoice):
        self._handle_pdf_generation(invoice, action='share')


    def apply_styles(self):
        self.setStyleSheet(f"""
            #invoice-table {{
                background-color: {DARK_THEME['bg_surface']};
                gridline-color: {DARK_THEME['border_main']};
                border: 1px solid {DARK_THEME['border_main']};
                border-radius: 8px;
                alternate-background-color: {DARK_THEME['bg_sidebar']};
            }}
            #invoice-table QHeaderView::section {{
                background-color: {DARK_THEME['bg_sidebar']};
                color: {DARK_THEME['text_secondary']};
                padding: 12px;
                border: none;
                font-weight: 600;
            }}
            #invoice-table::item {{
                padding: 10px;
                color: {DARK_THEME['text_primary']};
                border-bottom: 1px solid {DARK_THEME['border_main']};
            }}
            #invoice-table::item:selected {{
                background-color: {DARK_THEME['accent_primary']};
                color: {DARK_THEME['text_on_accent']};
            }}
            #status-label {{
                color: #000;
                font-weight: 600;
                padding: 5px 10px;
                border-radius: 5px;
            }}
            #status-label[status="paid"] {{
                background-color: #4CAF50; /* Green */
            }}
            #status-label[status="pending"] {{
                background-color: #FFC107; /* Amber */
            }}
            #status-label[status="overdue"] {{
                background-color: #F44336; /* Red */
            }}
            #action-button {{
                background-color: transparent;
                border: none;
                color: {DARK_THEME['text_secondary']};
                font-size: 18px;
                padding: 5px;
            }}
            #action-button:hover {{
                color: {DARK_THEME['accent_primary']};
            }}
            #pagination-button {{
                background-color: {DARK_THEME['bg_surface']};
                color: {DARK_THEME['text_secondary']};
                border: 1px solid {DARK_THEME['border_main']};
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: 600;
            }}
            #pagination-button:hover {{
                border-color: {DARK_THEME['accent_primary']};
                color: {DARK_THEME['accent_primary']};
            }}
            #pagination-button:disabled {{
                color: #555;
                border-color: #444;
            }}
            #page-label {{
                color: {DARK_THEME['text_secondary']};
                font-weight: 600;
                padding: 0 10px;
            }}
            #sort-combo {{
                min-width: 150px;
            }}
        """)
