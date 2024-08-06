"""
Database session management..
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.conf.config import settings
from src.conf.logger import logger

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo_pool=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Create a new database session.

    Yields:
        Session: Database session.
    """
    db = SessionLocal()

    try:
        yield db
    except Exception as e:
        logger.exception(e)
        db.rollback()
    finally:
        db.close()
