# src/controllers/companies_products_controller.py
from PyQt6.QtWidgets import QMessageBox, QListWidgetItem, QPushButton
from PyQt6.QtCore import Qt
from src.utils.database import SessionLocal
from src.models import CustomerCompany, Product, Inventory
from src.utils.dialogs import CompanyDialog, ProductDialog
from src.utils.helpers import log_action

class CompaniesProductsController:
    def __init__(self, view):
        self.view = view
        self.db_session = SessionLocal()
        self.selected_company = None

    def load_companies(self):
        current_selection = self.view.company_list.currentItem()
        current_id = current_selection.data(Qt.ItemDataRole.UserRole) if current_selection else None
        self.view.company_list.clear()
        companies = self.db_session.query(CustomerCompany).order_by(CustomerCompany.name).all()
        for company in companies:
            item_widget = self.view.ui_manager.create_list_item_widget(
                company.name, company, self.show_edit_company_dialog, self.handle_delete_company
            )
            list_item = QListWidgetItem(self.view.company_list)
            list_item.setSizeHint(item_widget.sizeHint())
            list_item.setData(Qt.ItemDataRole.UserRole, company.id)
            self.view.company_list.addItem(list_item)
            self.view.company_list.setItemWidget(list_item, item_widget)
            if company.id == current_id:
                self.view.company_list.setCurrentItem(list_item)
        self.view.update_delete_button_state()

    def on_company_selected(self, item):
        company_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_company = self.db_session.query(CustomerCompany).get(company_id)
        if self.selected_company:
            self.view.company_detail_title.setText(f"Products for: {self.selected_company.name}")
            self.load_products_for_company()
            self.view.product_stack.setCurrentIndex(1)
            self.view.product_header.findChild(QPushButton, "add-button").setEnabled(True)
        self.view.update_delete_button_state()

    def load_products_for_company(self):
        self.view.product_table.setRowCount(0)
        if not self.selected_company:
            return
        for product in sorted(self.selected_company.products, key=lambda p: p.name):
            row_pos = self.view.product_table.rowCount()
            self.view.product_table.insertRow(row_pos)
            self.view.ui_manager.create_product_table_row(
                row_pos, product, self.show_edit_product_dialog, self.handle_delete_product
            )
        self.view.update_delete_button_state()

    def show_add_company_dialog(self):
        dialog = CompanyDialog(parent=self.view)
        if dialog.exec():
            data = dialog.get_data()
            if data['name']:
                new_company = CustomerCompany(**data)
                self.db_session.add(new_company)
                self.db_session.flush()
                log_action(self.db_session, "CREATE", "Company", new_company.id, f"Company '{new_company.name}' created.")
                self.db_session.commit()
                self.load_companies()

    def show_edit_company_dialog(self, company):
        dialog = CompanyDialog(company=company, parent=self.view)
        if dialog.exec():
            data = dialog.get_data()
            details = f"Updated company '{company.name}'."
            for key, value in data.items():
                setattr(company, key, value)
            log_action(self.db_session, "UPDATE", "Company", company.id, details)
            self.db_session.commit()
            self.load_companies()

    def handle_delete_company(self, company):
        product_count = len(company.products)
        title = "Confirm Deletion"
        text = f"Are you sure you want to delete '{company.name}'? This action cannot be undone."
        if product_count > 0:
            text = f"Are you sure you want to delete '{company.name}'?\n\nThis will also permanently delete its {product_count} associated products. This action cannot be undone."

        msg_box = QMessageBox(self.view)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        yes_btn = msg_box.addButton("Yes", QMessageBox.ButtonRole.YesRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        yes_btn.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 6px 18px; border-radius: 5px;")
        msg_box.exec()
        if msg_box.clickedButton() == yes_btn:
            details = f"Company '{company.name}' and its {product_count} products deleted."
            log_action(self.db_session, "DELETE", "Company", company.id, details)
            self.db_session.delete(company)
            self.db_session.commit()
            self.load_companies()
            self.view.product_stack.setCurrentIndex(0)

    def handle_bulk_delete_companies(self):
        company_ids_to_delete = self.view.get_checked_company_ids()
        if not company_ids_to_delete: return

        product_count = sum(len(self.db_session.get(CustomerCompany, cid).products) for cid in company_ids_to_delete)
        title = "Confirm Bulk Deletion"
        text = f"Are you sure you want to delete these {len(company_ids_to_delete)} companies?"
        if product_count > 0:
            text += f"\n\nThis will also permanently delete a total of {product_count} associated products. This action cannot be undone."

        msg_box = QMessageBox(self.view)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        yes_btn = msg_box.addButton("Yes", QMessageBox.ButtonRole.YesRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        yes_btn.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 6px 18px; border-radius: 5px;")
        msg_box.exec()
        if msg_box.clickedButton() == yes_btn:
            for cid in company_ids_to_delete:
                company = self.db_session.get(CustomerCompany, cid)
                details = f"Company '{company.name}' and its products deleted in bulk."
                log_action(self.db_session, "DELETE", "Company", cid, details)
                self.db_session.delete(company)
            self.db_session.commit()
            self.load_companies()
            if self.selected_company and self.selected_company.id in company_ids_to_delete:
                self.view.product_stack.setCurrentIndex(0)

    def show_add_product_dialog(self):
        if not self.selected_company: return
        dialog = ProductDialog(parent=self.view)
        if dialog.exec():
            data = dialog.get_data()
            if data['name']:
                new_product = Product(name=data['name'], price=data['price'], company_id=self.selected_company.id)
                new_inventory = Inventory(stock_quantity=0, product=new_product)
                self.db_session.add(new_product)
                self.db_session.add(new_inventory)
                self.db_session.flush()
                log_action(self.db_session, "CREATE", "Product", new_product.id, f"Product '{new_product.name}' created for company '{self.selected_company.name}'.")
                self.db_session.commit()
                self.load_products_for_company()

    def show_edit_product_dialog(self, product):
        dialog = ProductDialog(product=product, parent=self.view)
        if dialog.exec():
            data = dialog.get_data()
            product.name = data['name']
            product.price = data['price']
            log_action(self.db_session, "UPDATE", "Product", product.id, f"Product '{product.name}' updated.")
            self.db_session.commit()
            self.load_products_for_company()

    def handle_delete_product(self, product):
        reply = QMessageBox.question(self.view, "Confirm Deletion", f"Are you sure you want to delete '{product.name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            log_action(self.db_session, "DELETE", "Product", product.id, f"Product '{product.name}' deleted.")
            self.db_session.delete(product)
            self.db_session.commit()
            self.load_products_for_company()

    def handle_bulk_delete_products(self):
        product_ids_to_delete = self.view.get_checked_product_ids()
        if not product_ids_to_delete: return
        reply = QMessageBox.question(self.view, "Confirm Deletion", f"Are you sure you want to delete these {len(product_ids_to_delete)} products?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for pid in product_ids_to_delete:
                product = self.db_session.get(Product, pid)
                log_action(self.db_session, "DELETE", "Product", pid, f"Product '{product.name}' deleted in bulk.")
                self.db_session.delete(product)
            self.db_session.commit()
            self.load_products_for_company()
