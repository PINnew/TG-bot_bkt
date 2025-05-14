import asyncio
from datetime import datetime, timedelta
from aiogram import Bot

from bot.database.db import get_unnotified_participants, mark_reminder_sent

REMINDER_TEXT = "Напоминаем: завтра состоится мероприятие «Бег, Кофе, Танцы»! Ждём вас!"
EVENT_TIME = datetime.now() + timedelta(minutes=10)  # тестовое событие через 2 минуты


async def start_scheduler(bot: Bot, interval_seconds=60):
    while True:
        now = datetime.now()

        if (EVENT_TIME - now).total_seconds() <= 24 * 3600:  # За 24 часа до события
            print("⏰ Проверка непрошедших напоминаний...")

            try:
                pool = bot.dp.pool
            except AttributeError:
                print("❌ Не удалось получить пул подключения к БД.")
                await asyncio.sleep(interval_seconds)
                continue

            users_to_notify = await get_unnotified_participants(pool)

            if not users_to_notify:
                print("📭 Нет пользователей для напоминания.")
                await asyncio.sleep(interval_seconds)
                continue

            print(f"📬 Найдено {len(users_to_notify)} пользователей для напоминания.")

            for user_id in users_to_notify:
                try:
                    print(f"📤 Отправляем напоминание для {user_id}")
                    await bot.send_message(user_id, REMINDER_TEXT)
                    await mark_reminder_sent(pool, user_id)
                    print(f"✅ Напоминание отправлено пользователю: {user_id}")
                except Exception as e:
                    print(f"❌ Ошибка при отправке пользователю {user_id}: {e}")

        print(f"⏳ Ожидание следующей проверки через {interval_seconds // 60} минут...")
        await asyncio.sleep(interval_seconds)