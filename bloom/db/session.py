"""Database engine and session factory (synchronous)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from bloom.core.config import get_settings

_settings = get_settings()

engine = create_engine(str(_settings.SQLALCHEMY_DATABASE_URI), pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
