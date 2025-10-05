from sqlalchemy import Column, Integer, String
from app.db.database import Base


class TranslationDictionaryModel(Base):
    """
The translation dictionary table as defined in the specification:
Mapping between business terms and database terms
    """
    __tablename__ = "translation_dictionary"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, nullable=False, index=True)  # Client identifier
    user_term = Column(String, nullable=False, index=True)   # User term: "customers"
    db_table = Column(String, nullable=False)                # Database table: "ClientsBot2025"
    db_field = Column(String, nullable=False)                # Database field: "ID_Customer"
    default_agg = Column(String)                             # Default aggregation function (COUNT/SUM)
    date_field = Column(String)                              # Date field for filtering