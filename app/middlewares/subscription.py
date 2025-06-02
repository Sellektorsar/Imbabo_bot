"""
Middleware для проверки подписки на канал
"""
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import user_crud
from app.utils import check_subscription, get_subscription_keyboard, MessageTexts

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    """Middleware для проверки подписки пользователя на канал"""
    
    # Команды и callback'и, которые доступны без подписки
    ALLOWED_WITHOUT_SUBSCRIPTION = {
        "/start",
        "check_subscription",
        "back_to_main"
    }
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # Проверяем только сообщения и callback'и от пользователей
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)
        
        user_id = event.from_user.id
        session: AsyncSession = data.get("session")
        
        # Проверяем, является ли пользователь администратором
        if user_id in settings.admin_ids_list:
            return await handler(event, data)
        
        # Определяем команду или callback
        command_or_callback = None
        if isinstance(event, Message):
            if event.text and event.text.startswith('/'):
                command_or_callback = event.text.split()[0]
            else:
                command_or_callback = event.text
        elif isinstance(event, CallbackQuery):
            command_or_callback = event.data
        
        # Разрешаем определенные команды без проверки подписки
        if command_or_callback in self.ALLOWED_WITHOUT_SUBSCRIPTION:
            return await handler(event, data)
        
        try:
            # Получаем пользователя из базы данных
            user = await user_crud.get_by_telegram_id(session, user_id)
            
            # Если пользователь не найден, создаем его
            if not user:
                user = await user_crud.create_or_update(
                    session,
                    telegram_id=user_id,
                    username=event.from_user.username,
                    first_name=event.from_user.first_name,
                    last_name=event.from_user.last_name
                )
                await session.commit()
            
            # Проверяем подписку
            if not user.is_subscribed:
                # Проверяем актуальную подписку в Telegram
                is_subscribed = await check_subscription(
                    event.bot if isinstance(event, Message) else event.message.bot,
                    user_id,
                    settings.channel_id
                )
                
                if is_subscribed:
                    # Обновляем статус в базе данных
                    await user_crud.update(session, user_id, is_subscribed=True)
                    await session.commit()
                else:
                    # Отправляем сообщение о необходимости подписки
                    if isinstance(event, Message):
                        await event.answer(
                            MessageTexts.SUBSCRIPTION_REQUIRED,
                            reply_markup=get_subscription_keyboard(settings.channel_id)
                        )
                    elif isinstance(event, CallbackQuery):
                        await event.answer(
                            "Для использования бота необходимо подписаться на канал!",
                            show_alert=True
                        )
                    return
            
            # Если все проверки пройдены, выполняем обработчик
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Ошибка в SubscriptionMiddleware: {e}")
            # В случае ошибки пропускаем проверку и выполняем обработчик
            return await handler(event, data)