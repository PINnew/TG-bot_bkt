import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os

from bot.handlers import user
from bot.utils.scheduler import start_scheduler
from bot.database.db import create_pool, create_table
from bot.middlewares.admin_middleware import AdminOnlyMiddleware

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))


async def main():
    pool = await create_pool()
    await create_table(pool)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Передаем пул и временное хранилище
    dp.pool = pool
    bot.dp = dp
    bot.db_state = {}

    # Добавляем middleware только для админских команд
    dp.message.middleware(AdminOnlyMiddleware(admin_ids=ADMIN_IDS))

    # Подключаем обработчики
    dp.include_router(user.router)

    # Запуск планировщика
    asyncio.create_task(start_scheduler(bot))

    print("✅ Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())