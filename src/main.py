import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.database import Base, engine, SessionLocal
from src.main_window import SaaSBillingApp
from src.models import UserSettings # We only need one for the default check

def initialize_database():
    """Creates the database and all tables."""
    # The 'Base' object now knows about all models thanks to the imports in src/models/__init__.py
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    if db.query(UserSettings).count() == 0:
        default_settings = UserSettings(id=1, company_name="Your Company Name")
        db.add(default_settings)
        db.commit()
    db.close()

def main():
    try:
        initialize_database()
        app = QApplication(sys.argv)

        resource_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources')
        QFontDatabase.addApplicationFont(os.path.join(resource_path, "Roboto-Regular.ttf"))
        QFontDatabase.addApplicationFont(os.path.join(resource_path, "Roboto-Medium.ttf"))

        window = SaaSBillingApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()