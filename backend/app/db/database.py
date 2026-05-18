from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Set it in .env or as an environment variable."
    )

engine = create_engine(
    DATABASE_URL,
    pool_size=5,           # persistent connections
    max_overflow=10,       # burst connections above pool_size
    pool_recycle=300,      # recycle connections after 5 min (prevents stale connections)
    pool_pre_ping=True,    # test connection liveness before use
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
