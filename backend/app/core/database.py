from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Neon's free tier suspends the database when idle and drops open connections.
# pool_pre_ping checks each pooled connection before use, so a stale one is
# replaced instead of failing the request with an unhandled 500.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()
