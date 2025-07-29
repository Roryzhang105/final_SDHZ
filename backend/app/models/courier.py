from sqlalchemy import Column, String, Boolean, Text

from .base import BaseModel


class Courier(BaseModel):
    __tablename__ = "couriers"
    
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(20), nullable=False, unique=True)
    website = Column(String(255))
    tracking_url = Column(String(255))
    is_active = Column(Boolean, default=True)
    description = Column(Text)