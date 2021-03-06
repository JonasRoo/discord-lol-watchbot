from bot.database_interface import bot_declarative_base
from bot.database_interface.tables.matches import Match

from typing import List
import os
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    BigInteger,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship


class Server(enum.Enum):
    """
    Enum of all the available LoL servers
    and their corresponding opgg routing values
    """

    br = "br"
    eune = "eune"
    euw = "euw"
    jp = "jp"
    kr = "kr"
    lan = "lan"
    las = "las"
    na = "na"
    oce = "oce"
    ru = "ru"
    tr = "tr"

    @classmethod
    def list(cls) -> List[str]:
        """
        Lists all possible Enum values of this class

        Returns:
            List[str]: A list of possible values
        """
        return list(map(lambda s: s.value, cls))


class User(bot_declarative_base):
    """
    Represents a linked LoL account for a specific discord user
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger)
    league_name = Column(String)
    server_name = Column(Enum(Server))
    opgg_link = Column(String)
    is_punished = Column(Boolean, default=False)
    matches = relationship("Match", back_populates="user", cascade="all,delete")
    summons = relationship("Summon", back_populates="user", cascade="all,delete")

    # account names on a server are unique
    __table_args__ = (UniqueConstraint("league_name", "server_name", name="unique_account_uc"),)

    def __repr__(self):
        return f"<User(id={self.id}, discord_name=<@!{self.discord_id}>, league_name={self.league_name}, server={self.server_name})>"