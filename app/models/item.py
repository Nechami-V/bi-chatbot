from sqlalchemy import Column, Integer, String
from app.db.database import Base


class Item(Base):
    __tablename__ = "ItemsBot2025"

    ID_פריט = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    pgrp = Column(Integer)