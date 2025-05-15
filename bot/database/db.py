import asyncio
import asyncpg
from typing import Optional, List, Dict
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


async def create_pool():
    """Создаёт и возвращает пул соединений с БД с повторными попытками."""
    for attempt in range(3):
        try:
            pool = await asyncpg.create_pool(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            print("✅ Подключение к БД успешно")
            return pool
        except Exception as e:
            print(f"❌ Ошибка подключения к БД (попытка {attempt + 1}):", e)
            await asyncio.sleep(3)
    raise ConnectionError("Не удалось подключиться к базе данных после нескольких попыток.")


async def create_table(pool):
    """Создаёт таблицу участников, если её нет."""
    async with pool.acquire() as connection:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id SERIAL PRIMARY KEY,
                telegram_user_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                phone_number VARCHAR(20),
                registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reminder_sent BOOLEAN DEFAULT FALSE
            )
        """)
        print("✅ Таблица 'participants' готова.")
        logging.info("✅ Таблица 'participants' готова.")


async def add_participant(pool, user_id: int, username: Optional[str], phone: str):
    """Добавляет нового пользователя в базу."""
    async with pool.acquire() as connection:
        await connection.execute("""
            INSERT INTO participants (telegram_user_id, username, phone_number)
            VALUES ($1, $2, $3)
            ON CONFLICT (telegram_user_id) DO NOTHING
        """, user_id, username, phone)


async def get_all_participants(pool):
    """Возвращает список всех зарегистрированных участников."""
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT telegram_user_id FROM participants")
        return [row['telegram_user_id'] for row in rows]


async def get_unnotified_participants(pool):
    """Возвращает список пользователей, которым ещё не отправлено напоминание."""
    async with pool.acquire() as connection:
        rows = await connection.fetch("""
            SELECT telegram_user_id FROM participants
            WHERE reminder_sent = FALSE
        """)
        return [row['telegram_user_id'] for row in rows]


async def mark_reminder_sent(pool, user_id: int):
    """Помечает, что пользователь получил напоминание."""
    async with pool.acquire() as connection:
        await connection.execute("""
            UPDATE participants SET reminder_sent = TRUE
            WHERE telegram_user_id = $1
        """, user_id)


async def get_all_participants_data(pool):
    async with pool.acquire() as connection:
        rows = await connection.fetch("""
            SELECT telegram_user_id, username, phone_number, registration_time, reminder_sent
            FROM participants
            ORDER BY registration_time DESC
        """)
        return [dict(row) for row in rows]
        print(await get_all_participants_data(pool))


async def get_participant_by_id(pool, user_id: int):
    """Получает данные пользователя по его Telegram ID."""
    async with pool.acquire() as connection:
        row = await connection.fetchrow("""
            SELECT * FROM participants
            WHERE telegram_user_id = $1
        """, user_id)
        return dict(row) if row else None

