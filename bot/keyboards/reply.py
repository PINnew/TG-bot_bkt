from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

kb_share_contact = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Поделиться контактом", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)