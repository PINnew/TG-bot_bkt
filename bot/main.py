import asyncio
from typing import Any

import dp
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os

from bot.handlers import user
from bot.utils.scheduler import start_scheduler
from bot.database.db import create_pool, create_table

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


bot: Any = Bot(token=BOT_TOKEN)
bot.dp = dp
bot.db_state = {}


async def main():
    # Подключение к БД
    pool = await create_pool()
    await create_table(pool)

    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Передача пула и диспетчера в бота для доступа из других модулей
    bot.dp = dp  # <-- важно: сохраняем диспетчер в боте
    dp.pool = pool  # <-- передаём пул в диспетчер

    # Временное хранилище для сбора данных пользователя
    bot.db_state = {}

    # Подключаем обработчики
    dp.include_router(user.router)

    # Запуск планировщика напоминаний
    asyncio.create_task(start_scheduler(bot))

    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())