# src/tabs/audit_log_tab.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QHBoxLayout, QLabel, QAbstractItemView, QPushButton)
from src.utils.database import SessionLocal
from src.models import AuditLog
from src.utils.theme import DARK_THEME

from src.tabs.base_tab import BaseTab

class AuditLogTab(BaseTab):
    def __init__(self):
        super().__init__()
        self.db_session = self.get_db_session()
        self.init_ui()
        self.load_logs()
        self.apply_styles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Application Action History"))
        header_layout.addStretch()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("secondary-button")
        refresh_btn.clicked.connect(self.load_logs)
        header_layout.addWidget(refresh_btn)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["Timestamp", "Action", "Entity", "Details"])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.log_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.log_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.log_table.cellDoubleClicked.connect(self.show_details_dialog)

        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.log_table, 1)

    def load_logs(self):
        self.log_table.setRowCount(0)
        self.logs = self.db_session.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
        for log in self.logs:
            row = self.log_table.rowCount()
            self.log_table.insertRow(row)
            self.log_table.setItem(row, 0, QTableWidgetItem(log.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
            self.log_table.setItem(row, 1, QTableWidgetItem(log.action))
            entity_str = f"{log.entity_type} (ID: {log.entity_id})" if log.entity_id else log.entity_type
            self.log_table.setItem(row, 2, QTableWidgetItem(entity_str))
            details_item = QTableWidgetItem(log.details)
            self.log_table.setItem(row, 3, details_item)

    def show_details_dialog(self, row, col):
        # Only show dialog for Details column or STOCK_ADJUST/PRODUCT/INVENTORY actions
        log = self.logs[row]
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
        from src.models import Product, Inventory, CustomerCompany
        session = self.db_session
        details = log.details
        dialog = QDialog(self)
        dialog.setWindowTitle("Audit Log Details")
        layout = QVBoxLayout(dialog)
        # Main info
        layout.addWidget(QLabel(f"<b>Timestamp:</b> {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"))
        layout.addWidget(QLabel(f"<b>Action:</b> {log.action}"))
        layout.addWidget(QLabel(f"<b>Entity:</b> {log.entity_type} (ID: {log.entity_id})"))
        # If inventory/product, show more info
        if log.entity_type in ("Inventory", "Product") and log.entity_id:
            if log.entity_type == "Inventory":
                inv = session.query(Inventory).filter_by(id=log.entity_id).first()
                if inv:
                    prod = session.query(Product).filter_by(id=inv.product_id).first()
                    if prod:
                        layout.addWidget(QLabel(f"<b>Product:</b> {prod.name} (ID: {prod.id})"))
                        layout.addWidget(QLabel(f"<b>Price:</b> ₹{prod.price:,.2f}"))
                        if prod.company_id:
                            company = session.query(CustomerCompany).filter_by(id=prod.company_id).first()
                            if company:
                                layout.addWidget(QLabel(f"<b>Company:</b> {company.name} (ID: {company.id})"))
                                layout.addWidget(QLabel(f"<b>GSTIN:</b> {company.gstin or ''}"))
                                layout.addWidget(QLabel(f"<b>State:</b> {company.state or ''} ({company.state_code or ''})"))
                        layout.addWidget(QLabel(f"<b>Stock Quantity:</b> {inv.stock_quantity}"))
                        layout.addWidget(QLabel(f"<b>Low Stock Threshold:</b> {inv.low_stock_threshold}"))
            elif log.entity_type == "Product":
                prod = session.query(Product).filter_by(id=log.entity_id).first()
                if prod:
                    layout.addWidget(QLabel(f"<b>Product:</b> {prod.name} (ID: {prod.id})"))
                    layout.addWidget(QLabel(f"<b>Price:</b> ₹{prod.price:,.2f}"))
                    if prod.company_id:
                        company = session.query(CustomerCompany).filter_by(id=prod.company_id).first()
                        if company:
                            layout.addWidget(QLabel(f"<b>Company:</b> {company.name} (ID: {company.id})"))
                            layout.addWidget(QLabel(f"<b>GSTIN:</b> {company.gstin or ''}"))
                            layout.addWidget(QLabel(f"<b>State:</b> {company.state or ''} ({company.state_code or ''})"))
        # Always show details
        layout.addWidget(QLabel(f"<b>Details:</b> {details}"))
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        dialog.exec()

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
                border-bottom: 1px solid {DARK_THEME['border_main']};
                font-weight: 600;
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {DARK_THEME['border_main']};
                color: {DARK_THEME['text_primary']};
            }}
            QPushButton#secondary-button {{
                background-color: transparent;
                color: {DARK_THEME['text_secondary']};
                border: 1px solid {DARK_THEME['border_main']};
                padding: 5px 10px;
                border-radius: 6px;
            }}
            QPushButton#secondary-button:hover {{
                border-color: {DARK_THEME['accent_primary']};
                color: {DARK_THEME['accent_primary']};
            }}
        """)
