from sqlalchemy import Column, Integer, String
from app.db.database import Base


class Client(Base):
    __tablename__ = "ClientsBot2025"

    ID_לקוח = Column(Integer, primary_key=True, index=True)
    lname = Column(String, index=True)  # Last name
    fname = Column(String, index=True)  # First name  
    wname = Column(String)              # Wife name
    city = Column(String, index=True)