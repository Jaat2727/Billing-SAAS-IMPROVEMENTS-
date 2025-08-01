from sqlalchemy import Column, Integer, String
# CORRECT: Imports 'Base' from the central utils file.
from src.utils.database import Base

class UserSettings(Base):
    __tablename__ = 'user_settings'
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String)
    gstin = Column(String)
    pan_number = Column(String)
    address = Column(String)  # Added address column
    state = Column(String)    # Added for GST
    state_code = Column(String)  # Added for GST
    mobile_number = Column(String)
    email = Column(String)
    upi_id = Column(String)
    tagline = Column(String)
    logo_filepath = Column(String)
    chosen_template = Column(String, default='Modern')