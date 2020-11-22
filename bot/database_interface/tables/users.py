import os
import enum
from sqlalchemy import Column, Integer, String, BigInteger, Enum, UniqueConstraint


class Server(enum.Enum):
    br = "BR1"
    eune = "EUN1"
    euw = "EUW1"
    jp = "JP1"
    kr = "KR"
    la1 = "LA1"
    la2 = "LA2"
    na = "NA1"
    oce = "OC1"
    ru = "RU"
    tr = "TR1"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    discord_name = Column(BigInteger)
    league_name = Column(String)
    server_name = Column(Enum(Server))
    opgg_link = Column(String)

    __table_args__ = (
        UniqueConstraint("league_name", "server_name", name="unique_account_ac"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, discord_name={self.discord_name}, league_name={self.league_name}, server={self.server_name})>"