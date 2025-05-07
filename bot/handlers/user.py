import os
import csv
import tempfile
from aiogram import Router, F
from aiogram.types import Message, Contact, FSInputFile
from aiogram.filters import CommandStart, Command
from bot.keyboards.reply import kb_share_contact
from bot.database.db import get_all_participants, add_participant, get_all_participants_data

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
        "Пожалуйста, напишите ваш никнейм в Telegram."
    )

    if not username:
        await message.answer("Введите свой никнейм в Telegram:")
        return

    # Сохраняем username
    message.bot.db_state[user_id] = {"username": username}
    await message.answer("Поделитесь своим номером телефона. \nНажмите кнопку внизу.", reply_markup=kb_share_contact)


@router.message(F.text)
async def process_username(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    state = message.bot.db_state.get(user_id, {})

    if "username" not in state:
        state["username"] = text
        message.bot.db_state[user_id] = state
        await message.answer("Поделитесь своим номером телефона. Нажмите кнопку внизу.", reply_markup=kb_share_contact)


@router.message(F.contact)
async def process_phone(message: Message):
    user_id = message.from_user.id
    phone_number = message.contact.phone_number
    state = message.bot.db_state.get(user_id, {})

    username = state.get("username")

    pool = message.bot.dp.pool

    try:
        await add_participant(pool, user_id, username, phone_number)
        del message.bot.db_state[user_id]
        await message.answer(
            "Спасибо! \nВы зарегистрированы мероприятие «Бег, Кофе, Танцы». \n"
            "За день до события мы напомним вам о встрече!"
        )
    except Exception as e:
        await message.answer("⚠️ Произошла ошибка при регистрации. Попробуйте позже.")
        print(f"Ошибка добавления участника: {e}")


@router.message(Command("list"))
async def cmd_list(message: Message):
    pool = message.bot.dp.pool
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