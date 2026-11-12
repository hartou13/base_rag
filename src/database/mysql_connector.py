import os
from contextlib import asynccontextmanager

from databases import Database
from dotenv import load_dotenv
from sqlalchemy import inspect, select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import src.database.mysql_global as mysql_global

load_dotenv()
dbname = os.environ.get("MYSQL_DATABASE")
# dbhost = mysql_global.ip_address
dbhost = os.environ.get("MYSQL_HOST")
dbport = os.environ.get("MYSQL_PORT")
dbuser = os.environ.get("MYSQL_USER")
dbpassword = os.environ.get("MYSQL_PASSWORD")
# print(f"dbname: {dbname}, dbhost: {dbhost}, dbuser: {dbuser}, dbpassword: {dbpassword}")
DATABASE_URL = (
    f"mysql+aiomysql://{dbuser}:{dbpassword}@{dbhost}:{dbport}/{dbname}"
    # "?allow_public_key_retrieval=true"
)

Base = declarative_base()

# engine = create_engine(DATABASE_URL)
async_engine = create_async_engine(DATABASE_URL, echo=False)

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_db():
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# Create all tables in the database
async def init_db():
    # Backup
    backup = {}
    async with async_engine.begin() as conn:
        for table in Base.metadata.tables.values():
            try:
                result = await conn.execute(select(table))
                backup[table.name] = [dict(row) for row in result]
            except ProgrammingError as e:
                print(f"Erreur lors de la sélection de la table {table.name}: {e}")
                continue

    # Drop all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Restore
    async with async_engine.begin() as conn:
        for table_name, rows in backup.items():
            try:
                table = Base.metadata.tables[table_name]
                for row in rows:
                    await conn.execute(table.insert().values(**row))
            except ProgrammingError as e:
                print(f"Erreur lors de l'insertion dans la table {table_name}: {e}")
                continue


database = Database(DATABASE_URL)
