from sqlalchemy import Column, Integer, String, DateTime, Float
from app.db.database import Base


class Order(Base):
    __tablename__ = "OrdersBot2025"

    # Creating a composite primary key since there's no single ID field
    ID_sale = Column(Integer, primary_key=True)
    ID_customer = Column(Integer, primary_key=True)
    ID_item = Column(Integer, primary_key=True)
    date = Column(String)  # Store as string since source is string format
    amount = Column(Float)