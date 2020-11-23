import os
from contextlib import contextmanager

from sqlalchemy import create_engine
import sqlalchemy.orm
from sqlalchemy.ext.declarative import declarative_base

# Declarative base that is being used by all our DB interfaces
bot_declarative_base = declarative_base()


class SessionCreator:
    """
    Singleton class to initiate a DB session only when upon instantiation;
    otherwise, refers to an on-going session.
    """

    _session_creator = None

    @property
    def session_creator(self) -> sqlalchemy.orm.session.Session:
        """Yields the sqlalchemy session created by our factory.

        Returns:
            sqlalchemy.orm.session.Session: sqlalchemy session
        """
        if not self._session_creator:
            self._initialize_database_interface()
        return self._session_creator

    def _initialize_database_interface(self):
        """
        Initializes our DB interface through sqlalchemy
        """
        # create DB engine
        # connection string abstraced into environment to make DB agnostic
        engine = create_engine(os.environ.get("LOL_WATCHBOT_DB_CONNECTION_STRING"))

        # create all required tables from the "tables" module
        bot_declarative_base.metadata.create_all(bind=engine)

        # Initial creation of the SessionMaker
        self._session_creator = sqlalchemy.orm.sessionmaker(bind=engine)


# Singleton instantiation
session_creator = SessionCreator()


@contextmanager
def session_scope():
    """
    Provides a transactional scope for DB operations.
    """
    # call the session_creator property to get the current DB session
    session = session_creator.session_creator()

    try:
        yield session
        # try to commit changes created in context
        session.commit()
    except Exception as e:
        # base exception sucks, but chosen in favor of not blocking the DB at runtime
        # roll back the changes, then propagate the exception
        session.rollback()
        raise e
    finally:
        # close session when exitting context
        session.close()