from sqlalchemy import Column, Integer, String
from app.db.database import Base


class TranslationDictionaryModel(Base):
    """
    טבלת מילון התרגום כפי שמוגדר באיפיון:
    מיפוי בין מונחים עסקיים למונחי מסד נתונים
    """
    __tablename__ = "translation_dictionary"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, nullable=False, index=True)  # מזהה לקוח
    user_term = Column(String, nullable=False, index=True)   # מונח משתמש: "לקוחות"
    db_table = Column(String, nullable=False)                # טבלה במסד: "ClientsBot2025"
    db_field = Column(String, nullable=False)                # שדה במסד: "ID_לקוח"
    default_agg = Column(String)                             # פונקציית ברירת מחדל (COUNT/SUM)
    date_field = Column(String)                              # שדה תאריך לצורך פילטרים