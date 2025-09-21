from sqlalchemy import Column, Integer, String
from app.db.database import Base


class Sale(Base):
    __tablename__ = "SalesBot2025"

    ID_מכירה = Column(Integer, primary_key=True, index=True)
    week = Column(String)
    name = Column(String, index=True)