import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


async def test_connection():
    try:
        pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        print("✅ Успешное подключение к базе данных!")
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT version();")
            print("📊 Версия PostgreSQL:", result)
            result = await conn.fetch("SELECT * FROM participants LIMIT 1;")
            print("📊 Пример данных из таблицы participants:", result)
    except Exception as e:
        print("❌ Ошибка подключения к БД:", e)

if __name__ == "__main__":
    asyncio.run(test_connection())