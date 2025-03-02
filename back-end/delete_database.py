"""
delete_database.py

An async-compatible script to delete all tables from the database.
This is useful for cleaning up the database during development or testing.

Steps:
1. Drop all tables from the database.
2. Optionally, delete the database itself (if needed).
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlmodel import SQLModel
from dotenv import load_dotenv
import os

# ------------------------------------------------------------------------------
#  Load environment variables
# ------------------------------------------------------------------------------
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
ASYNC_DATABASE_URL = (
    f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}?charset=utf8mb4"
)


# ------------------------------------------------------------------------------
# Function to drop all tables
# ------------------------------------------------------------------------------
async def drop_tables(async_engine: AsyncEngine) -> None:
    """
    Drops all tables from the database using SQLModel metadata.

    Args:
        async_engine (AsyncEngine): The asynchronous engine to use.
    """
    print("Dropping all tables from the database...")
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    print("All tables dropped successfully.")


# ------------------------------------------------------------------------------
# Optional Function to Delete Database
# ------------------------------------------------------------------------------
async def delete_database() -> None:
    """
    Optionally deletes the entire database from the server.
    """
    from sqlalchemy import create_engine, text

    BASE_SYNC_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}"

    engine = create_engine(BASE_SYNC_URL, echo=False, future=True)
    with engine.connect() as connection:
        connection.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME}"))
        print(f"Database '{DB_NAME}' deleted successfully.")


# ------------------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------------------
async def main_async(delete_db: bool = False) -> None:
    """
    Orchestrates the database deletion process:
    - Drop all tables
    - Optionally delete the database itself

    Args:
        delete_db (bool): Whether to delete the entire database.
    """
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL, echo=False, future=True)

    try:
        await drop_tables(async_engine)
        if delete_db:
            await delete_database()
    finally:
        await async_engine.dispose()


# ------------------------------------------------------------------------------
# Script Execution
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Starting database deletion...")
    delete_db_flag = (
        input("Do you want to delete the entire database? (yes/no): ").strip().lower()
        == "yes"
    )
    asyncio.run(main_async(delete_db_flag))
    print("Database cleanup completed successfully.")
