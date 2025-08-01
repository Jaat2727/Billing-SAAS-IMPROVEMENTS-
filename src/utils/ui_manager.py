# src/utils/ui_manager.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QPushButton, QMenu, QTableWidgetItem, QFrame)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

class UIManager:
    def __init__(self, db_session, parent):
        self.db_session = db_session
        self.parent = parent

    def create_stat_card(self, title, value):
        card = QFrame()
        card.setObjectName("stat-card")
        layout = QVBoxLayout(card)
        title_label = QLabel(title)
        title_label.setObjectName("stat-title")
        value_label = QLabel(value)
        value_label.setObjectName("stat-value")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return card

    def create_list_item_widget(self, text, entity, edit_callback, delete_callback):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 10, 15, 10)

        checkbox = QCheckBox()
        checkbox.stateChanged.connect(self.parent.update_delete_button_state)

        label = QLabel(text)

        menu_btn = QPushButton("⋮")
        menu_btn.setObjectName("menu-button")

        menu = QMenu(self.parent)
        edit_action = QAction("Edit", menu)
        delete_action = QAction("Delete", menu)

        edit_action.triggered.connect(lambda chk, e=entity: edit_callback(e))
        delete_action.triggered.connect(lambda chk, e=entity: delete_callback(e))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu_btn.setMenu(menu)

        layout.addWidget(checkbox)
        layout.addWidget(label, 1)
        layout.addWidget(menu_btn)

        widget.setProperty("checkbox", checkbox)
        # Make the row double thick for better visibility
        widget.setMinimumHeight(48)
        return widget

    def create_product_table_row(self, row_pos, product, edit_callback, delete_callback):
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(self.parent.update_delete_button_state)
        checkbox_layout.addWidget(checkbox)
        checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        checkbox_widget.setProperty("product_id", product.id)
        checkbox_widget.setProperty("checkbox", checkbox)
        self.parent.product_table.setCellWidget(row_pos, 0, checkbox_widget)

        self.parent.product_table.setItem(row_pos, 1, QTableWidgetItem(product.name))
        self.parent.product_table.setItem(row_pos, 2, QTableWidgetItem(f"₹{product.price:,.2f}"))

        actions_btn = QPushButton("⋮")
        actions_btn.setObjectName("menu-button")
        menu = QMenu(self.parent)
        edit_action = QAction("Edit", menu)
        edit_action.triggered.connect(lambda chk, p=product: edit_callback(p))
        delete_action = QAction("Delete", menu)
        delete_action.triggered.connect(lambda chk, p=product: delete_callback(p))
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        actions_btn.setMenu(menu)
        self.parent.product_table.setCellWidget(row_pos, 3, actions_btn)
        # Make the row double thick for better visibility
        self.parent.product_table.setRowHeight(row_pos, 48)
