# src/tabs/base_tab.py
from PyQt6.QtWidgets import QWidget

class BaseTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def get_db_session(self):
        # This is a placeholder. In a real application, you would
        # get the database session from a central location.
        from src.utils.database import SessionLocal
        return SessionLocal()
