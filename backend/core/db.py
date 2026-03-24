from sqlalchemy import create_all
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings
from models.database import Base

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # In a real app, use Alembic. For this prototype, metadata create_all is fine.
    Base.metadata.create_all(bind=engine)
