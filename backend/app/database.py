import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

_encryption_available = False
_using_encryption = False


def _create_engine():
    global _encryption_available, _using_encryption

    db_url = settings.database_url
    connect_args = {"check_same_thread": False}

    if settings.db_encryption_key:
        try:
            # SQLAlchemy's sqlite+pysqlcipher dialect imports this module.
            import pysqlcipher3.dbapi2  # noqa: F401

            db_url = db_url.replace("sqlite:///", "sqlite+pysqlcipher:///")
            _encryption_available = True
            _using_encryption = True
            logger.info("Database encryption enabled (SQLCipher)")
        except ImportError:
            logger.warning(
                "db_encryption_key is set but sqlcipher3/pysqlcipher3 not installed. "
                "Database will NOT be encrypted. Install: brew install sqlcipher && pip install pysqlcipher3"
            )

    eng = create_engine(db_url, connect_args=connect_args)

    if settings.db_encryption_key and _using_encryption:

        @event.listens_for(eng, "connect")
        def set_cipher_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute(f"PRAGMA key='{settings.db_encryption_key}'")
            cursor.close()

    return eng


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_encrypted() -> bool:
    return _using_encryption
