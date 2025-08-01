# src/tabs/settings_tab.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QGridLayout, QFrame, QMessageBox)
from PyQt6.QtCore import Qt
from src.utils.theme import DARK_THEME
from src.utils.database import SessionLocal
from src.models.user import UserSettings
from src.utils.helpers import log_action
import re
from src.tabs.base_tab import BaseTab

class SettingsTab(BaseTab):
    def __init__(self):
        super().__init__()
        self.db_session = self.get_db_session()
        self.init_ui()
        self.load_settings()
        self.apply_styles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Grid Layout for Cards ---
        grid_layout = QGridLayout()
        grid_layout.setSpacing(30)

        # --- Company Profile Card ---
        company_card = self.create_card("Company Profile", "This information will appear on your invoices.")
        company_form_layout = QGridLayout()
        self.company_name_input = QLineEdit()
        self.gstin_input = QLineEdit()
        self.pan_input = QLineEdit()
        self.address_input = QLineEdit()
        company_form_layout.addWidget(QLabel("Legal Company Name"), 0, 0)
        company_form_layout.addWidget(self.company_name_input, 0, 1)
        company_form_layout.addWidget(QLabel("GSTIN"), 1, 0)
        company_form_layout.addWidget(self.gstin_input, 1, 1)
        company_form_layout.addWidget(QLabel("PAN Number"), 2, 0)
        company_form_layout.addWidget(self.pan_input, 2, 1)
        company_form_layout.addWidget(QLabel("Company Address"), 3, 0)
        company_form_layout.addWidget(self.address_input, 3, 1)
        company_card.layout().addLayout(company_form_layout)
        grid_layout.addWidget(company_card, 0, 0)

        # --- Contact & Payment Card ---
        contact_card = self.create_card("Contact & Payment Details", "Contact and UPI details for your clients.")
        contact_form_layout = QGridLayout()
        self.mobile_input = QLineEdit()
        self.email_input = QLineEdit()
        self.upi_id_input = QLineEdit()
        contact_form_layout.addWidget(QLabel("Mobile Number"), 0, 0)
        contact_form_layout.addWidget(self.mobile_input, 0, 1)
        contact_form_layout.addWidget(QLabel("Email Address"), 1, 0)
        contact_form_layout.addWidget(self.email_input, 1, 1)
        contact_form_layout.addWidget(QLabel("UPI ID (for payments)"), 2, 0)
        contact_form_layout.addWidget(self.upi_id_input, 2, 1)
        contact_card.layout().addLayout(contact_form_layout)
        grid_layout.addWidget(contact_card, 0, 1)

        # --- Invoice Customization Card ---
        invoice_card = self.create_card("Invoice Customization", "Add a custom message to your invoices.")
        invoice_form_layout = QGridLayout()
        self.tagline_input = QLineEdit()
        self.tagline_input.setPlaceholderText("e.g., Thank you for your business!")
        invoice_form_layout.addWidget(QLabel("Invoice Tagline / Footer Note"), 0, 0)
        invoice_form_layout.addWidget(self.tagline_input, 0, 1)
        invoice_card.layout().addLayout(invoice_form_layout)
        grid_layout.addWidget(invoice_card, 1, 0, 1, 2)

        main_layout.addLayout(grid_layout)
        main_layout.addStretch()

        # --- Save Button ---
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_button = QPushButton("Save All Changes")
        self.save_button.setObjectName("primary-button")
        self.save_button.setFixedSize(180, 44)
        self.save_button.clicked.connect(self.save_settings)
        save_layout.addWidget(self.save_button)
        main_layout.addLayout(save_layout)

    def create_card(self, title_text, subtitle_text):
        card = QFrame(self)
        card.setObjectName("content-card")
        layout = QVBoxLayout(card)
        layout.setSpacing(20)
        
        title = QLabel(title_text)
        title.setObjectName("card-title")
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("card-subtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        return card

    def load_settings(self):
        settings = self.db_session.query(UserSettings).first()
        if not settings:
            # Create default settings if none exist
            settings = UserSettings()
            self.db_session.add(settings)
            self.db_session.commit()
            
        # Safely get attributes with fallback to empty string
        def get_safe_attr(obj, attr):
            return getattr(obj, attr, "") or ""
            
        self.company_name_input.setText(get_safe_attr(settings, "company_name"))
        self.gstin_input.setText(get_safe_attr(settings, "gstin"))
        self.pan_input.setText(get_safe_attr(settings, "pan_number"))
        self.address_input.setText(get_safe_attr(settings, "address"))
        self.mobile_input.setText(get_safe_attr(settings, "mobile_number"))
        self.email_input.setText(get_safe_attr(settings, "email"))
        self.upi_id_input.setText(get_safe_attr(settings, "upi_id"))
        self.tagline_input.setText(get_safe_attr(settings, "tagline"))

    def save_settings(self):
        gstin = self.gstin_input.text()
        pan = self.pan_input.text()

        if gstin and not re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$", gstin):
            QMessageBox.critical(self, "Error", "Invalid GSTIN format.")
            return

        if pan and not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", pan):
            QMessageBox.critical(self, "Error", "Invalid PAN format.")
            return

        settings = self.db_session.query(UserSettings).first()
        if settings:
            details = "Updated company settings."
            settings.company_name = self.company_name_input.text()
            settings.gstin = gstin
            settings.pan_number = pan
            settings.address = self.address_input.text()
            settings.mobile_number = self.mobile_input.text()
            settings.email = self.email_input.text()
            settings.upi_id = self.upi_id_input.text()
            settings.tagline = self.tagline_input.text()
            
            log_action(self.db_session, "UPDATE", "Settings", settings.id, details)
            self.db_session.commit()
            
            msg_box = QMessageBox(self)
            msg_box.setText("Settings have been saved successfully.")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Success")
            msg_box.setStyleSheet(f"""
                QMessageBox {{ background-color: {DARK_THEME['bg_surface']}; }}
                QLabel {{ color: {DARK_THEME['text_primary']}; }}
                QPushButton {{
                    background-color: {DARK_THEME['accent_primary']};
                    color: {DARK_THEME['text_on_accent']};
                    padding: 8px 16px;
                    border-radius: 4px;
                    border: none;
                }}
            """)
            msg_box.exec()

    def apply_styles(self):
        self.setStyleSheet(f"""
            SettingsTab {{ font-family: Roboto; }}
            QFrame#content-card {{
                background-color: {DARK_THEME['bg_surface']};
                border: 1px solid {DARK_THEME['border_main']};
                border-radius: 8px;
                padding: 20px;
            }}
            QLabel#card-title {{
                font-size: 18px;
                font-weight: 600;
                color: {DARK_THEME['text_primary']};
                padding-bottom: 5px;
            }}
            QLabel#card-subtitle {{
                font-size: 13px;
                color: {DARK_THEME['text_secondary']};
                padding-bottom: 10px;
            }}
            QLineEdit {{
                background-color: {DARK_THEME['bg_input']};
                color: {DARK_THEME['text_primary']};
                border: 1px solid {DARK_THEME['border_main']};
                border-radius: 6px;
                padding: 8px;
            }}
            QPushButton#primary-button {{
                background-color: {DARK_THEME['accent_primary']};
                color: {DARK_THEME['text_on_accent']};
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: 600;
            }}
            QPushButton#primary-button:hover {{
                background-color: {DARK_THEME['accent_hover']};
            }}
        """)