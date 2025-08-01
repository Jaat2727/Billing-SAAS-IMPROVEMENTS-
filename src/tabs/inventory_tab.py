# src/tabs/inventory_tab.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
                             QHeaderView, QPushButton, QFrame, QLabel, QAbstractItemView)
from PyQt6.QtCore import Qt
from src.utils.database import SessionLocal
from src.models import CustomerCompany, Product, Inventory, InventoryHistory
from src.utils.dialogs import StockAdjustmentDialog
from src.utils.theme import DARK_THEME
from sqlalchemy.orm import joinedload
from src.utils.helpers import log_action
from src.utils.ui_manager import UIManager

from src.tabs.base_tab import BaseTab

class InventoryTab(BaseTab):
    def __init__(self):
        super().__init__()
        self.db_session = self.get_db_session()
        self.ui_manager = UIManager(self.db_session, self)
        self.init_ui()
        self.load_inventory_data()
        self.apply_styles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        stats_frame = QFrame()
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(20)
        self.total_products_card = self.ui_manager.create_stat_card("Total Products", "0")
        self.low_stock_card = self.ui_manager.create_stat_card("Low Stock Items", "0")
        self.out_of_stock_card = self.ui_manager.create_stat_card("Out of Stock", "0")
        stats_layout.addWidget(self.total_products_card)
        stats_layout.addWidget(self.low_stock_card)
        stats_layout.addWidget(self.out_of_stock_card)
        stats_layout.addStretch()

        controls_frame = QFrame()
        controls_frame.setObjectName("panel-header")
        controls_layout = QHBoxLayout(controls_frame)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search product or company...")
        self.search_input.textChanged.connect(self.load_inventory_data)
        self.stock_filter_combo = QComboBox()
        self.stock_filter_combo.addItems(["All Stock", "Low Stock", "Out of Stock"])
        self.stock_filter_combo.currentIndexChanged.connect(self.load_inventory_data)
        add_product_btn = QPushButton("Add Product")
        add_product_btn.setObjectName("primary-button")
        # add_product_btn.clicked.connect(self.show_add_product_dialog)  # Implement as needed
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("secondary-button")
        refresh_btn.clicked.connect(self.load_inventory_data)
        # Pagination and sync toggle
        self.nav_prev_btn = QPushButton("← Prev")
        self.nav_next_btn = QPushButton("Next →")
        self.nav_prev_btn.clicked.connect(self.goto_prev_page)
        self.nav_next_btn.clicked.connect(self.goto_next_page)
        controls_layout.addWidget(self.nav_prev_btn)
        controls_layout.addWidget(self.nav_next_btn)
        controls_layout.addWidget(QLabel("Search:"))
        controls_layout.addWidget(self.search_input, 1)
        controls_layout.addWidget(QLabel("Filter by:"))
        controls_layout.addWidget(self.stock_filter_combo)
        controls_layout.addWidget(add_product_btn)
        controls_layout.addWidget(refresh_btn)

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(7)
        self.inventory_table.setHorizontalHeaderLabels(["S.No.", "Product Name", "Company", "Current Stock", "Price", "Stock Change History", "Actions"])
        self.inventory_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.inventory_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.inventory_table.setColumnWidth(0, 50)
        self.inventory_table.setColumnWidth(5, 260)  # Wider History column
        self.inventory_table.setColumnWidth(6, 220)  # Actions
        self.inventory_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.inventory_table.setSortingEnabled(True)
        self.inventory_table.horizontalHeader().sectionClicked.connect(self.handle_header_sort)

        main_layout.addWidget(stats_frame)
        main_layout.addWidget(controls_frame)
        main_layout.addWidget(self.inventory_table, 1)

        # For navigation (pagination)
        self.current_page = 0
        self.page_size = 20

    def load_inventory_data(self):
        search_text = self.search_input.text().lower()
        stock_filter = self.stock_filter_combo.currentText()

        query = self.db_session.query(Product).join(Product.company).options(
            joinedload(Product.company),
            joinedload(Product.inventory)
        )

        if search_text:
            query = query.filter(Product.name.ilike(f"%{search_text}%") | CustomerCompany.name.ilike(f"%{search_text}%"))

        all_products_for_stats = self.db_session.query(Product).all()

        if stock_filter == "Low Stock":
            product_ids = [p.id for p in all_products_for_stats if p.inventory and p.inventory.stock_quantity <= p.inventory.low_stock_threshold and p.inventory.stock_quantity > 0]
            query = query.filter(Product.id.in_(product_ids))
        elif stock_filter == "Out of Stock":
            product_ids = [p.id for p in all_products_for_stats if p.inventory and p.inventory.stock_quantity == 0]
            query = query.filter(Product.id.in_(product_ids))

        products = query.order_by(Product.name).all()

        # Pagination
        self.all_products = products
        start = self.current_page * self.page_size
        end = start + self.page_size
        paged_products = products[start:end]

        self.inventory_table.setRowCount(0)
        low_stock_count = 0
        out_of_stock_count = 0

        for p in all_products_for_stats:
            stock = p.inventory.stock_quantity if p.inventory else 0
            low_thresh = p.inventory.low_stock_threshold if p.inventory else 10
            if stock <= low_thresh and stock > 0: low_stock_count += 1
            if stock == 0: out_of_stock_count += 1

        self.total_products_card.findChild(QLabel, "stat-value").setText(str(len(all_products_for_stats)))
        self.low_stock_card.findChild(QLabel, "stat-value").setText(str(low_stock_count))
        self.out_of_stock_card.findChild(QLabel, "stat-value").setText(str(out_of_stock_count))

        for i, product in enumerate(paged_products):
            row = self.inventory_table.rowCount()
            self.inventory_table.insertRow(row)

            s_no_item = QTableWidgetItem(str(start + i + 1))
            s_no_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.inventory_table.setItem(row, 0, s_no_item)

            self.inventory_table.setItem(row, 1, QTableWidgetItem(product.name))
            self.inventory_table.setItem(row, 2, QTableWidgetItem(product.company.name))
            stock_value = product.inventory.stock_quantity if product.inventory else 0
            stock_item = QTableWidgetItem(str(stock_value))
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Color indicator for low/out-of-stock
            if product.inventory:
                if stock_value == 0:
                    stock_item.setBackground(Qt.GlobalColor.red)
                elif stock_value <= product.inventory.low_stock_threshold:
                    stock_item.setBackground(Qt.GlobalColor.yellow)
                else:
                    stock_item.setBackground(Qt.GlobalColor.green)
            self.inventory_table.setItem(row, 3, stock_item)
            price_item = QTableWidgetItem(f"₹{product.price:,.2f}")
            self.inventory_table.setItem(row, 4, price_item)
            # --- History button, centered and full label ---
            history_widget = QWidget()
            history_layout = QHBoxLayout(history_widget)
            history_layout.setContentsMargins(0, 0, 0, 0)
            history_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            history_btn = QPushButton("View Stock Change History")
            history_btn.setObjectName("secondary-button")
            history_btn.setMinimumWidth(160)
            history_btn.clicked.connect(lambda chk, p=product: self.show_history_modal(p))
            history_layout.addWidget(history_btn)
            self.inventory_table.setCellWidget(row, 5, history_widget)
            # --- Improved Actions button ---
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the button
            adjust_btn = QPushButton("Adjust Stock")
            adjust_btn.setObjectName("primary-button")
            adjust_btn.setStyleSheet(f"background-color: {DARK_THEME['accent_primary']}; color: {DARK_THEME['text_on_accent']}; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 600; font-size: 14px;")
            adjust_btn.setMinimumWidth(120)
            adjust_btn.clicked.connect(lambda chk, p=product: self.show_adjust_stock_dialog(p))
            action_layout.addWidget(adjust_btn)
            self.inventory_table.setCellWidget(row, 6, action_widget)
            # Make the row double thick for better visibility
            self.inventory_table.setRowHeight(row, 60)

    def handle_header_sort(self, logicalIndex):
        self.inventory_table.sortItems(logicalIndex, order=self.inventory_table.horizontalHeader().sortIndicatorOrder())

    def goto_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_inventory_data()

    def goto_next_page(self):
        max_page = (len(self.all_products) - 1) // self.page_size
        if self.current_page < max_page:
            self.current_page += 1
            self.load_inventory_data()

    def show_history_modal(self, product):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox
        from src.models import InventoryHistory
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Stock Change History - {product.name}")
        dialog.resize(1200, 700)  # Triple the size for better viewing
        layout = QVBoxLayout(dialog)
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Date", "Action", "Quantity", "Source", "Notes"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        histories = self.db_session.query(InventoryHistory).filter_by(product_id=product.id).order_by(InventoryHistory.timestamp.desc()).all()
        table.setRowCount(len(histories))
        for i, h in enumerate(histories):
            table.setItem(i, 0, QTableWidgetItem(h.timestamp.strftime("%Y-%m-%d %H:%M")))
            action = "Added" if h.change_quantity > 0 else "Deducted"
            table.setItem(i, 1, QTableWidgetItem(action))
            table.setItem(i, 2, QTableWidgetItem(str(abs(h.change_quantity))))
            source = h.reason if h.reason else "Manual"
            table.setItem(i, 3, QTableWidgetItem(source))
            table.setItem(i, 4, QTableWidgetItem(h.reason or ""))
        layout.addWidget(table)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        dialog.exec()

    def show_adjust_stock_dialog(self, product):
        current_stock = product.inventory.stock_quantity if product.inventory else 0
        dialog = StockAdjustmentDialog(product.name, current_stock, self)
        if dialog.exec():
            data = dialog.get_data()
            adjustment = data['adjustment']
            if adjustment != 0:
                if not product.inventory:
                    product.inventory = Inventory(stock_quantity=0, product=product)
                    self.db_session.add(product.inventory)

                old_stock = product.inventory.stock_quantity
                product.inventory.stock_quantity += adjustment
                new_stock = product.inventory.stock_quantity
                user_id = None  # TODO: Replace with actual user ID if available
                details = f"Stock for '{product.name}' changed by {adjustment}. Old: {old_stock}, New: {new_stock}."
                history_entry = InventoryHistory(
                    product_id=product.id,
                    change_quantity=adjustment,
                    new_stock=new_stock,
                    reason=data['reason'],
                    user_id=user_id
                )
                self.db_session.add(history_entry)

                log_action(self.db_session, "STOCK_ADJUST", "Inventory", product.id, details)
                self.db_session.commit()
                self.load_inventory_data()

    def apply_styles(self):
        self.setStyleSheet(f"""
            QFrame#stat-card {{ background-color: {DARK_THEME['bg_surface']}; border: 1px solid {DARK_THEME['border_main']}; border-radius: 8px; padding: 15px; }}
            QLabel#stat-title {{ color: {DARK_THEME['text_secondary']}; font-size: 13px; font-weight: 500; }}
            QLabel#stat-value {{ color: {DARK_THEME['text_primary']}; font-size: 24px; font-weight: 600; }}
            QFrame#panel-header {{ border-bottom: 1px solid {DARK_THEME['border_main']}; padding: 10px; }}
            QTableWidget {{ background-color: transparent; gridline-color: {DARK_THEME['border_main']}; border: none; }}
            QHeaderView::section {{ background-color: {DARK_THEME['bg_sidebar']}; color: {DARK_THEME['text_secondary']}; padding: 10px; border: none; font-weight: 600; }}
            QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {DARK_THEME['border_main']}; color: {DARK_THEME['text_primary']}; }}
            QPushButton#secondary-button {{ background-color: transparent; color: {DARK_THEME['text_secondary']}; border: 1px solid {DARK_THEME['border_main']}; padding: 5px 10px; border-radius: 6px; }}
            QPushButton#secondary-button:hover {{ border-color: {DARK_THEME['accent_primary']}; color: {DARK_THEME['accent_primary']}; }}
        """)