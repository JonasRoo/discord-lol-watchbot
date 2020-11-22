import os
import enum
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, BigInteger, Enum, UniqueConstraint

# create database connection
db_path = os.environ.get("LOL_WATCHBOT_DB_ABSPATH")
engine = create_engine(f"sqlite:///{db_path}")

# declare the base (declarative mapping)
Base = declarative_base()


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

    __table_args__ = (
        UniqueConstraint("league_name", "server_name", name="unique_account_ac"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, discord_name={self.discord_name}, league_name={self.league_name}, server={self.server_name})>"


# create a session, and bind it to the engine
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

# create all the tables
Base.metadata.create_all(engine)


# creating an instance, and saving to database
new_user = User(
    discord_name=170571097253740544, league_name="JeanSuper", server_name="euw"
)
session.add(new_user)
new_user = User(
    discord_name=170571097253740544, league_name="Fortniter", server_name="euw"
)
session.add(new_user)
session.commit()

our_user = session.query(User).filter_by(league_name="Fortniter").first()
print(our_user)

session.close()