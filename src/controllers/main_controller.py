# src/controllers/main_controller.py
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from src.utils.csv_manager import CsvManager

class MainController:
    def __init__(self, main_view):
        self.main_view = main_view
        self.csv_manager = CsvManager(
            self.main_view.companies_tab_instance,
            self.main_view.inventory_tab_instance,
            self.main_view.audit_log_tab_instance,
            self.main_view.invoice_history_tab_instance
        )
        # Optionally store reference to CreateInvoiceTab if present
        self.create_invoice_tab = getattr(self.main_view, 'create_invoice_tab_instance', None)

    def switch_page(self, name, button):
        if self.main_view.active_nav_button:
            self.main_view.active_nav_button.setChecked(False)
        button.setChecked(True)
        self.main_view.active_nav_button = button

        self.main_view.stacked_widget.setCurrentWidget(self.main_view.tabs_map[name])
        self.main_view.header_title.setText(name)
        self.main_view.header_subtitle.setText(f"Manage your {name.lower()}")

    def handle_import_csv(self):
        dialog = QFileDialog(self.main_view)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("CSV Files (*.csv)")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec():
            file_name = dialog.selectedFiles()[0]
            if "companies" in file_name.lower() or "products" in file_name.lower():
                import_type = "companies_and_products"
            elif "invoice" in file_name.lower():
                import_type = "invoices"
            else:
                QMessageBox.critical(self.main_view, "Import Error", "Could not determine import type from file name.")
                return

            success, message = self.csv_manager.handle_import_csv(file_name, import_type)
            if success:
                # Refresh company/product UI after import
                self.main_view.companies_tab_instance.load_companies()
                if self.create_invoice_tab:
                    self.create_invoice_tab.load_latest_data()
                QMessageBox.information(self.main_view, "Success", message)
            else:
                QMessageBox.critical(self.main_view, "Import Error", message)

    def handle_export_csv(self):
        dialog = QFileDialog(self.main_view)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setNameFilter("CSV Files (*.csv)")
        dialog.setDefaultSuffix("csv")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec():
            file_name = dialog.selectedFiles()[0]
            if "companies" in file_name.lower() or "products" in file_name.lower():
                export_type = "companies_and_products"
            elif "invoice" in file_name.lower():
                export_type = "invoices"
            else:
                # Default to companies and products if not specified
                export_type = "companies_and_products"

            success, message = self.csv_manager.handle_export_csv(file_name, export_type)
            if success:
                QMessageBox.information(self.main_view, "Success", message)
            else:
                QMessageBox.critical(self.main_view, "Export Error", message)
