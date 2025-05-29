import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
#inrender
DATABASE_URL = "postgresql://maintenance_db_f0k5_user:PkOy1CqZlB9uKpFQigKVhIv04uzOcozr@dpg-d0s12eh5pdvs7393ervg-a/maintenance_db_f0k5"
#DB_PATH = os.path.abspath("./data/test.db")
#DATABASE_URL = "postgresql://postgres:Post123@localhost:5431/katebalbalawi"

# إذا أردت جعل الاتصال ديناميكي (من env):
# DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# فقط أزل connect_args عند استخدام Postgres أو أي قاعدة غير SQLite
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
print(f"Database connected at: {DATABASE_URL}")