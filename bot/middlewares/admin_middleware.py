from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable


class AdminOnlyMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем, является ли команда админской
        if event.text in ["/list", "/export", "/broadcast"]:
            if event.from_user.id in self.admin_ids:
                return await handler(event, data)
            else:
                await event.answer("❌ У вас нет прав на выполнение этой команды.")
                return None
        else:
            return await handler(event, data)