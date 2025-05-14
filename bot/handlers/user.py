import asyncio
import os
import csv
import tempfile

import aiogram
from aiogram import Router, F
from aiogram.types import Message, Contact, FSInputFile
from aiogram.filters import CommandStart, Command
from bot.keyboards.reply import kb_share_contact
from bot.database.db import get_all_participants, add_participant, get_all_participants_data
# from bot.keyboards.inline import get_start_keyboard
from bot.database.db import get_participant_by_id
from aiogram.exceptions import TelegramForbiddenError

# Загрузка переменных окружения
from dotenv import load_dotenv
load_dotenv()

# Получение списка админов
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))

router = Router(name="user_router")


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    await message.answer(
        "Добро пожаловать!\nРегистрируйтесь на мероприятие «Бег, Кофе, Танцы». \n"
        "Пожалуйста, напишите никнейм и номер телефона свой."
    )

    if not username:
        await message.answer("Введите свой никнейм в Telegram:")
        return
    else:
        # Сохраняем username
        message.bot.db_state[user_id] = {"username": username}
        await message.answer("<<Поделиться контактом>> кнопка внизу.", reply_markup=kb_share_contact)


@router.message(F.text)
async def process_username(message: Message):
    user_id = message.from_user.id

    # Проверка: уже зарегистрирован?
    pool = message.bot.dp.pool
    existing_user = await get_participant_by_id(pool, user_id)
    if existing_user:
        return  # Не продолжаем, если уже зарегистрирован

    # Проверяем, есть ли username в состоянии
    state = message.bot.db_state.get(user_id, {})
    if "username" in state:
        return  # Уже есть username, ждём контакт

    # Если username ещё не установлен
    state["username"] = message.text.strip()
    message.bot.db_state[user_id] = state

    await message.answer(
        "Поделитесь своим номером телефона. \nНажмите кнопку внизу.",
        reply_markup=kb_share_contact
    )


@router.message(F.contact)
async def process_phone(message: Message):
    user_id = message.from_user.id
    phone_number = message.contact.phone_number
    state = message.bot.db_state.get(user_id, {})

    username = state.get("username")

    # Проверка: уже зарегистрирован?
    pool = message.bot.dp.pool
    existing_user = await get_participant_by_id(pool, user_id)
    if existing_user:
        await message.answer("Вы уже зарегистрированы!")
        return

    try:
        await add_participant(pool, user_id, username, phone_number)
        del message.bot.db_state[user_id]
        await message.answer(
            "Спасибо! \n"
            "Вы зарегистрированы, мероприятие «Бег, Кофе, Танцы». \n"
            "За день до события мы напомним вам о встрече!"
        )
    except Exception as e:
        await message.answer("⚠️ Произошла ошибка при регистрации. Попробуйте позже.")
        print(f"Ошибка добавления участника: {e}")
    finally:
        # ВСЕГДА удаляем состояние, даже если была ошибка
        if user_id in message.bot.db_state:
            del message.bot.db_state[user_id]


@router.message(Command("list"))
async def cmd_list(message: Message):
    user_id = message.from_user.id
    pool = message.bot.dp.pool

    # Отладка: проверяем, есть ли пользователь в БД
    existing_user = await get_participant_by_id(pool, user_id)
    if not existing_user:
        await message.answer("Вы не зарегистрированы.")
        return

    # Получаем общее количество участников
    participants = await get_all_participants(pool)
    count = len(participants)

    await message.answer(f"На мероприятие зарегистрировано {count} человек.")


@router.message(Command("export"))
async def cmd_export(message: Message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав на выполнение этой команды.")
        return

    pool = message.bot.dp.pool
    participants = await get_all_participants_data(pool)

    if not participants:
        await message.answer("⚠️ Нет зарегистрированных участников.")
        return

    with tempfile.NamedTemporaryFile(mode='w+', newline='', encoding='utf-8', delete=False) as tmpfile:
        fieldnames = ['telegram_user_id', 'username', 'phone_number', 'registration_time', 'reminder_sent']
        writer = csv.DictWriter(tmpfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(participants)
        tmpfile_path = tmpfile.name

    csv_file_path = "participants_export.csv"
    os.rename(tmpfile_path, csv_file_path)

    file = FSInputFile(csv_file_path)
    await message.answer_document(file, caption="📎 Все зарегистрированные участники:")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    user_id = message.from_user.id

    # Проверка прав администратора
    if user_id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав на выполнение этой команды.")
        return

    # Извлекаем текст сообщения
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Используйте: /broadcast [сообщение]")
        return

    broadcast_text = args[1]

    pool = message.bot.dp.pool
    participants = await get_all_participants(pool)

    success_count = 0
    blocked_count = 0

    for user_id in participants:
        try:
            await message.bot.send_message(user_id, broadcast_text)
            success_count += 1
            await asyncio.sleep(0.05)  # чтобы не спамить слишком быстро
        except aiogram.exceptions.TelegramForbiddenError:
            print(f"Пользователь {user_id} заблокировал бота.")
            blocked_count += 1
        except Exception as e:
            print(f"Ошибка при отправке пользователю {user_id}: {e}")

    await message.answer(
        f"✅ Рассылка завершена!\n"
        f"📬 Сообщение получили: {success_count} человек.\n"
        f"🚫 Заблокировали бота: {blocked_count} человек."
    )
