from bot.database_interface import bot_declarative_base

from datetime import datetime
from sqlalchemy import Column, Boolean, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.orm import column_property, relationship


class Felony(bot_declarative_base):
    """
    Represents a LoL match played by a registered user
    """

    __tablename__ = "felonies"

    id = Column(Integer, primary_key=True)
    champion = Column(String)
    points = Column(Integer, default=1)
    date_added = Column(DateTime, default=datetime.utcnow)
    date_closed = Column(DateTime)
    is_active = Column(Boolean, default=True)
    summons = relationship("Summon", back_populates="felony", cascade="all,delete")

    # __table_args__ = (UniqueConstraint("champion", "is_active", name="only_one_active_champ_uc"),)
