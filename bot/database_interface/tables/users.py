from bot.database_interface import bot_declarative_base

import os
import enum
from sqlalchemy import Column, Integer, String, BigInteger, Enum, UniqueConstraint


class Server(enum.Enum):
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


class User(bot_declarative_base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger)
    league_name = Column(String)
    server_name = Column(Enum(Server))
    opgg_link = Column(String)

    __table_args__ = (
        UniqueConstraint("league_name", "server_name", name="unique_account_uc"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, discord_name=<@!{self.discord_id}>, league_name={self.league_name}, server={self.server_name})>"