import asyncio
from datetime import datetime, timedelta
from aiogram import Bot

from bot.database.db import get_unnotified_participants, mark_reminder_sent

REMINDER_TEXT = "Напоминаем: завтра состоится мероприятие «Бег, Кофе, Танцы»! Ждём вас!"
EVENT_TIME = datetime(2025, 4, 12, 18, 0)  # Дата мероприятия


async def start_scheduler(bot: Bot, interval_seconds=3600):
    while True:
        now = datetime.now()

        if (EVENT_TIME - now).total_seconds() <= 24 * 3600:
            print("Проверка непрошедших напоминаний...")

            try:
                pool = bot.dp.pool  # Получаем пул через диспетчер
            except AttributeError:
                print("❌ Не удалось получить пул подключения к БД.")
                await asyncio.sleep(interval_seconds)
                continue

            users_to_notify = await get_unnotified_participants(pool)

            for user_id in users_to_notify:
                try:
                    await bot.send_message(user_id, REMINDER_TEXT)
                    await mark_reminder_sent(pool, user_id)
                    print(f"✅ Напоминание отправлено пользователю: {user_id}")
                except Exception as e:
                    print(f"❌ Не удалось отправить сообщение для {user_id}: {e}")

        print(f"⏳ Ожидание следующей проверки через {interval_seconds // 60} минут...")
        await asyncio.sleep(interval_seconds)