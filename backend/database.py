"""
Database configuration for the Healing Agent.
Uses SQLite with SQLAlchemy for persistent storage.
Swap DATABASE_URL to PostgreSQL for production scaling.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database path — use env var or default to local data directory
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DB_DIR, exist_ok=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(DB_DIR, 'healing_agent.db')}"
)

# For SQLite, need check_same_thread=False for FastAPI's async usage
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set True for SQL debug logging
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Create all tables if they don't exist."""
    from models import Run, Fix, TimelineEvent  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print(f"[DB] Database initialized at: {DATABASE_URL}")


def get_db():
    """FastAPI dependency — yields a DB session, auto-closes on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
