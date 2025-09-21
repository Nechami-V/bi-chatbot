from sqlalchemy import Column, Integer, String, Date
from app.db.database import Base


class Customer(Base):
    __tablename__ = "customer"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    city = Column(String, index=True)
    created_at = Column(Date)
