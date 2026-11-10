import os
from databases import Database
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import src.database.mysql_global as mysql_global

load_dotenv()
dbname = os.environ.get("MYSQL_DATABASE_SHARED")
dbhost = mysql_global.ip_address
dbuser = os.environ.get("MYSQL_USER_SHARED")
dbpassword = os.environ.get("MYSQL_PASSWORD_SHARED")
DATABASE_URL = (
    f"mysql+aiomysql://{dbuser}:{dbpassword}@{dbhost}/{dbname}"
    "?allow_public_key_retrieval=true"
)

Base_shared = declarative_base()

# engine = create_engine(DATABASE_URL)
async_engine_shared = create_async_engine(DATABASE_URL, echo=False)

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async_session_shared = sessionmaker(async_engine_shared, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def get_db():
    session = async_session_shared()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

database = Database(DATABASE_URL)
