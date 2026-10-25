"""Database engine; SQLite is for local preview, PostgreSQL for a durable deployment."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from models import Base

URL = os.environ.get("DATABASE_URL", "sqlite:///./company_os.db")
if URL.startswith("postgres://"):
    URL = URL.replace("postgres://", "postgresql+psycopg://", 1)
elif URL.startswith("postgresql://"):
    URL = URL.replace("postgresql://", "postgresql+psycopg://", 1)

ENV = os.environ.get("APP_ENV", "production" if os.environ.get("VERCEL_ENV") in ("production","preview") else "development").lower()
if ENV == "production" and URL.startswith("sqlite"):
    raise RuntimeError("Production must use persistent PostgreSQL. Set DATABASE_URL.")
engine = create_engine(URL, pool_pre_ping=True, connect_args={"check_same_thread": False} if URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_database() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    with SessionLocal() as session:
        yield session
