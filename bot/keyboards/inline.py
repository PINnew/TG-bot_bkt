from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🚀 Начать регистрацию", callback_data="register")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
