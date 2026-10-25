"""Database engine; SQLite is for local preview, PostgreSQL for a durable deployment."""
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool
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
options = {"pool_pre_ping": True}
if URL.startswith("sqlite"):
    options["connect_args"] = {"check_same_thread": False}
elif URL.startswith("postgresql+psycopg://"):
    # Vercel functions should release connections after every request rather than
    # retaining a pool across frozen serverless instances.
    if os.environ.get("VERCEL_ENV") in ("preview", "production"):
        options["poolclass"] = NullPool
    # Supabase transaction pooler (port 6543) rejects prepared statements.
    if make_url(URL).port == 6543:
        options["connect_args"] = {"prepare_threshold": None}
engine = create_engine(URL, **options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_database() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    with SessionLocal() as session:
        yield session
