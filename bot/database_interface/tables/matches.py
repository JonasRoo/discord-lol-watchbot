from bot.database_interface import bot_declarative_base

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship


class Match(bot_declarative_base):
    """
    Represents a LoL match played by a registered user
    """

    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    played_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="matches")
    map = Column(String)
    champion = Column(String)
    summoner_one = Column(String)
    summoner_two = Column(String)

    def has_almost_same_info(self, other: "Match") -> bool:
        return (
            (self.map == other.map)
            and (self.champion == other.champion)
            and (self.summoner_one == other.summoner_one)
            and (self.summoner_two == other.summoner_two)
        )
