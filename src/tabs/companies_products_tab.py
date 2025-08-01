from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget,
                             QPushButton, QFrame, QStackedWidget, QTableWidget, QHeaderView,
                             QCheckBox, QLineEdit, QAbstractItemView)
from PyQt6.QtCore import Qt
from src.utils.theme import DARK_THEME
from src.controllers.companies_products_controller import CompaniesProductsController
from src.utils.ui_manager import UIManager

from src.tabs.base_tab import BaseTab

class CompaniesProductsTab(BaseTab):
    def load_companies(self):
        """Reload the companies list from the database and update the UI."""
        self.controller.load_companies()
    def __init__(self):
        super().__init__()
        self.ui_manager = UIManager(None, self)
        self.controller = CompaniesProductsController(self)
        self.init_ui()
        self.controller.load_companies()
        self.apply_styles()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(1)

        # Left Panel for Companies
        left_panel = QFrame()
        left_panel.setObjectName("left-panel")
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(400)
        left_layout.setContentsMargins(0,0,0,0)

        self.company_header = self.create_panel_header("Registered Companies", self.controller.show_add_company_dialog, self.controller.handle_bulk_delete_companies, vertical=True)
        left_layout.addWidget(self.company_header)

        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_frame.setObjectName("search-frame")
        self.company_search_input = QLineEdit()
        self.company_search_input.setPlaceholderText("Search companies...")
        self.company_search_input.textChanged.connect(self.filter_companies)
        search_layout.addWidget(self.company_search_input)
        left_layout.addWidget(search_frame)

        self.company_list = QListWidget()
        self.company_list.itemSelectionChanged.connect(self.on_company_selection_changed)
        self.company_list.itemClicked.connect(self.controller.on_company_selected)
        left_layout.addWidget(self.company_list)

        # Right Panel for Products
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0,0,0,0)
        self.product_stack = QStackedWidget()

        # Placeholder
        placeholder_widget = QWidget()
        placeholder_layout = QVBoxLayout(placeholder_widget)
        placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label = QLabel("Select a company to manage its details and products.")
        placeholder_label.setObjectName("placeholder-label")
        placeholder_layout.addWidget(placeholder_label)

        # Product View
        product_view_widget = QWidget()
        product_view_layout = QVBoxLayout(product_view_widget)
        self.product_header = self.create_panel_header("Products", self.controller.show_add_product_dialog, self.controller.handle_bulk_delete_products, vertical=False)
        self.company_detail_title = self.product_header.findChild(QLabel)

        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(["", "Product Name", "Price", ""])
        self.product_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.product_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        product_view_layout.addWidget(self.product_header)
        product_view_layout.addWidget(self.product_table, 1)

        self.product_stack.addWidget(placeholder_widget)
        self.product_stack.addWidget(product_view_widget)
        right_layout.addWidget(self.product_stack)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)

    def create_panel_header(self, title_text, add_callback, delete_callback, vertical=False):
        header = QFrame()
        header.setObjectName("panel-header")
        if vertical:
            layout = QVBoxLayout(header)
            layout.setContentsMargins(15, 8, 15, 8)
            layout.setSpacing(6)
            title = QLabel(title_text)
            title.setStyleSheet("font-size: 18px; font-weight: 600; color: #fff;")
            layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
            add_btn = QPushButton("+ Add Company")
            add_btn.setObjectName("add-button")
            add_btn.setToolTip("Add a new company")
            add_btn.clicked.connect(add_callback)
            add_btn.setStyleSheet("font-size: 15px; font-weight: 500; padding: 8px 0; border-radius: 6px; background: #1976d2; color: #fff; min-width: 160px;")
            layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignLeft)
            delete_btn = QPushButton("Delete Selected")
            delete_btn.setObjectName("destructive-button")
            delete_btn.setEnabled(False)
            delete_btn.clicked.connect(delete_callback)
            delete_btn.setStyleSheet("font-size: 15px; font-weight: 500; padding: 8px 0; border-radius: 6px; border: 1px solid #d32f2f; color: #d32f2f; background: transparent; min-width: 160px;")
            layout.addWidget(delete_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        else:
            layout = QHBoxLayout(header)
            layout.setContentsMargins(15, 8, 15, 8)
            layout.setSpacing(12)
            title = QLabel(title_text)
            title.setStyleSheet("font-size: 18px; font-weight: 600; color: #fff;")
            layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            layout.addStretch()
            add_btn = QPushButton("+ Add Product")
            add_btn.setObjectName("add-button")
            add_btn.setToolTip("Add a new product")
            add_btn.clicked.connect(add_callback)
            add_btn.setStyleSheet("font-size: 15px; font-weight: 500; padding: 8px 24px; border-radius: 6px; background: #1976d2; color: #fff; min-width: 180px;")
            layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            delete_btn = QPushButton("Delete Selected")
            delete_btn.setObjectName("destructive-button")
            delete_btn.setEnabled(False)
            delete_btn.clicked.connect(delete_callback)
            delete_btn.setStyleSheet("font-size: 15px; font-weight: 500; padding: 8px 24px; border-radius: 6px; border: 1px solid #d32f2f; color: #d32f2f; background: transparent; min-width: 180px;")
            layout.addWidget(delete_btn, alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        header.setProperty("delete_button", delete_btn)
        return header

    def filter_companies(self):
        search_text = self.company_search_input.text().lower()
        for i in range(self.company_list.count()):
            item = self.company_list.item(i)
            widget = self.company_list.itemWidget(item)
            item.setHidden(search_text not in widget.label.text().lower())

    def on_company_selection_changed(self):
        for i in range(self.company_list.count()):
            item = self.company_list.item(i)
            widget = self.company_list.itemWidget(item)
            widget.setProperty("selected", item.isSelected())
            widget.style().polish(widget)

    def get_checked_company_ids(self):
        checked_ids = []
        for i in range(self.company_list.count()):
            item = self.company_list.item(i)
            widget = self.company_list.itemWidget(item)
            checkbox = widget.property("checkbox")
            if checkbox and checkbox.isChecked():
                checked_ids.append(item.data(Qt.ItemDataRole.UserRole))
        return checked_ids

    def get_checked_product_ids(self):
        checked_ids = []
        for i in range(self.product_table.rowCount()):
            widget = self.product_table.cellWidget(i, 0)
            checkbox = widget.property("checkbox")
            if checkbox and checkbox.isChecked():
                checked_ids.append(widget.property("product_id"))
        return checked_ids

    def update_delete_button_state(self):
        # Company delete button
        company_delete_btn = self.company_header.property("delete_button")
        company_delete_btn.setEnabled(len(self.get_checked_company_ids()) > 0)

        # Product delete button
        product_delete_btn = self.product_header.property("delete_button")
        product_delete_btn.setEnabled(len(self.get_checked_product_ids()) > 0)

    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{ font-family: Roboto; }}
            QFrame#left-panel, QFrame#right-panel {{ background-color: {DARK_THEME['bg_surface']}; }}
            QFrame#panel-header {{
                border-bottom: 1px solid {DARK_THEME['border_main']};
                padding: 10px 15px;
            }}
            #panel-header QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {DARK_THEME['text_primary']};
            }}
            QFrame#search-frame {{ padding: 10px; }}
            QLineEdit {{
                background-color: {DARK_THEME['bg_input']};
                color: {DARK_THEME['text_primary']};
                border: 1px solid {DARK_THEME['border_main']};
                border-radius: 6px;
                padding: 8px;
            }}
            QListWidget {{ border: none; }}
            QListWidget::item {{ border-bottom: 1px solid {DARK_THEME['border_main']}; }}
            QWidget[selected=true] {{ background-color: {DARK_THEME['bg_hover']}; }}

            #placeholder-label {{
                color: {DARK_THEME['text_secondary']};
                font-size: 16px;
            }}

            #add-button, #menu-button {{
                background-color: transparent;
                color: {DARK_THEME['text_secondary']};
                border: none;
                font-size: 20px;
                font-weight: bold;
                max-width: 30px;
                border-radius: 6px;
            }}
            #add-button:hover, #menu-button:hover {{ color: {DARK_THEME['accent_primary']}; }}

            #destructive-button {{
                background-color: transparent;
                color: {DARK_THEME['accent_danger']};
                border: 1px solid {DARK_THEME['accent_danger']};
                padding: 5px 10px;
                border-radius: 6px;
                font-weight: 600;
            }}
            #destructive-button:hover {{
                background-color: {DARK_THEME['accent_danger_hover']};
                color: {DARK_THEME['text_on_accent']};
                border-color: {DARK_THEME['accent_danger_hover']};
            }}
            #destructive-button:disabled {{
                color: {DARK_THEME['text_secondary']};
                border-color: {DARK_THEME['text_secondary']};
                background-color: transparent;
            }}

            QTableWidget {{
                background-color: transparent;
                gridline-color: {DARK_THEME['border_main']};
                border: none;
            }}
            QHeaderView::section {{
                background-color: {DARK_THEME['bg_sidebar']};
                color: {DARK_THEME['text_secondary']};
                padding: 10px;
                border: none;
                font-weight: 600;
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {DARK_THEME['border_main']};
                color: {DARK_THEME['text_primary']};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {DARK_THEME['border_main']};
            }}
            QCheckBox::indicator:hover {{ border-color: {DARK_THEME['accent_primary']}; }}
            QCheckBox::indicator:checked {{
                background-color: {DARK_THEME['accent_primary']};
                border-color: {DARK_THEME['accent_primary']};
            }}
        """)
