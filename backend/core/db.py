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
    try:
        # In a real app, use Alembic. For this prototype, metadata create_all is fine.
        Base.metadata.create_all(bind=engine)
        print("✅ Veritabanı başarıyla bağlandı.")
    except Exception as e:
        print(f"⚠️ Veritabanı bağlantı hatası (Atlanıyor...): {e}")
        print("ℹ️ Uygulama JSON tabanlı yerel veri ile çalışmaya devam edecek.")
