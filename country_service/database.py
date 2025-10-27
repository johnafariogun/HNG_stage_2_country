from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    db = os.getenv("MYSQL_DB", "country_cache")
    DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"

print(f"this is the database url {DATABASE_URL}")

# echo can be set via env if desired
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db(Base):
    # Create all tables (safe to call repeatedly)
    Base.metadata.create_all(bind=engine)
