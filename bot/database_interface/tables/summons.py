from bot.database_interface import bot_declarative_base
from bot.database_interface.tables.users import User
from bot.database_interface.tables.felonies import Felony

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship


class Summon(bot_declarative_base):
    """
    Represents an entry of a registered user committing a felony.
    """

    __tablename__ = "summons"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="summons")
    felony_id = Column(Integer, ForeignKey("felonies.id"))
    felony = relationship("Felony", back_populates="summons")
    points = Column(Integer)
    date_added = Column(DateTime, default=datetime.utcnow)

    # __table_args__ = (UniqueConstraint("champion", "is_active", name="only_one_active_champ_uc"),)
