from sqlalchemy import Column, Integer, String, DateTime, Float
from app.db.database import Base


class Order(Base):
    __tablename__ = "OrdersBot2025"

    # Creating a composite primary key since there's no single ID field
    ID_מכירה = Column(Integer, primary_key=True)
    ID_לקוח = Column(Integer, primary_key=True)
    ID_פריט = Column(Integer, primary_key=True)
    תאריך = Column(String)  # Store as string since source is string format
    סכום = Column(Float)