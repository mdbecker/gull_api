import json
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Boolean
import sqlalchemy.orm
from sqlalchemy.exc import SQLAlchemyError

Base = sqlalchemy.orm.declarative_base()

class APIRequestLog(Base):
    __tablename__ = "api_request_log"

    id = Column(Integer, primary_key=True)
    request = Column(String)
    response = Column(String)
    error_occurred = Column(Boolean)
    error_details = Column(String)

def load_db_config(filename="db_config.json"):
    try:
        with open(filename) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"db_uri": "sqlite:////app/data/database.db"}

def get_engine():
    db_config = load_db_config()
    return create_engine(db_config.get("db_uri", "sqlite:///:memory:"))

def get_session_maker(engine=None):
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(bind=engine)
    return sqlalchemy.orm.sessionmaker(bind=engine)

class SessionManager:
    def __init__(self, log, session_maker=None):
        if session_maker is None:
            session_maker = get_session_maker()
        self.session = session_maker()
        self.log = log

    def __enter__(self):
        self.session.add(self.log)
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                # An exception occurred, but commit the log record before propagating the exception.
                self.session.commit()
            else:
                # If no exception occurred, commit the session.
                self.session.commit()
        except SQLAlchemyError:
            # If an exception occurred during commit, roll back the session.
            self.session.rollback()
            raise
        finally:
            self.session.close()

        # Return False to propagate the exception, if one occurred.
        return False