from bot.database_interface import bot_declarative_base

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import column_property


class Felony(bot_declarative_base):
    """
    Represents a LoL match played by a registered user
    """

    __tablename__ = "felonies"

    id = Column(Integer, primary_key=True)
    champion = Column(String)
    date_added = Column(DateTime)
    date_closed = Column(DateTime)
    is_active = column_property(date_closed is not None)