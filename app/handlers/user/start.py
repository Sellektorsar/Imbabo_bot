"""
Обработчики команды /start и проверки подписки
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db, user_crud
from app.utils import (
    MessageTexts, 
    get_main_menu_keyboard, 
    get_subscription_keyboard,
    check_subscription
)

logger = logging.getLogger(__name__)
start_router = Router()


@start_router.message(CommandStart())
async def start_command(message: Message, session: AsyncSession = None):
    """Обработчик команды /start - Внимание (Attention)"""
    if session is None:
        async for db_session in get_db():
            session = db_session
            break
    
    try:
        # Создаем или обновляем пользователя
        user = await user_crud.create_or_update(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            aida_stage="attention"
        )
        
        # Проверяем подписку на канал
        is_subscribed = await check_subscription(
            message.bot, 
            message.from_user.id, 
            settings.channel_id
        )
        
        if is_subscribed:
            # Обновляем статус подписки
            await user_crud.update(session, user.id, is_subscribed=True, aida_stage="interest")
            
            await message.answer(
                MessageTexts.SUBSCRIPTION_SUCCESS,
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await message.answer(
                MessageTexts.WELCOME_MESSAGE,
                reply_markup=get_subscription_keyboard(settings.channel_id)
            )
            
            await message.answer(
                MessageTexts.SUBSCRIPTION_REQUIRED,
                reply_markup=get_subscription_keyboard(settings.channel_id)
            )
        
        await session.commit()
        
    except Exception as e:
        logger.error(f"Ошибка в start_command: {e}")
        await message.answer(MessageTexts.ERROR_GENERAL)


@start_router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, session: AsyncSession = None):
    """Проверка подписки на канал"""
    if session is None:
        async for db_session in get_db():
            session = db_session
            break
    
    try:
        # Проверяем подписку
        is_subscribed = await check_subscription(
            callback.bot,
            callback.from_user.id,
            settings.channel_id
        )
        
        if is_subscribed:
            # Обновляем статус пользователя
            await user_crud.update(
                session,
                callback.from_user.id,
                is_subscribed=True,
                aida_stage="interest"
            )
            
            await callback.message.edit_text(
                MessageTexts.SUBSCRIPTION_SUCCESS,
                reply_markup=None
            )
            
            await callback.message.answer(
                "Выберите действие:",
                reply_markup=get_main_menu_keyboard()
            )
            
            await session.commit()
        else:
            await callback.answer(
                "❌ Вы еще не подписались на канал!",
                show_alert=True
            )
    
    except Exception as e:
        logger.error(f"Ошибка в check_subscription_callback: {e}")
        await callback.answer(MessageTexts.ERROR_SUBSCRIPTION_CHECK, show_alert=True)


@start_router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery):
    """Возврат в главное меню"""
    try:
        await callback.message.edit_text(
            "Главное меню:",
            reply_markup=None
        )
        
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в back_to_main_callback: {e}")
        await callback.answer(MessageTexts.ERROR_GENERAL, show_alert=True)