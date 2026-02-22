from sqlalchemy import Column, String, Float, Boolean
from database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(String, primary_key=True)

    name = Column(String)
    weight = Column(Float, default=0)

    # For attachments
    ergonomics_modifier = Column(Float, default=0)

    # For weapons only
    is_weapon = Column(Boolean, default=False)
    base_ergonomics = Column(Float, default=0)
