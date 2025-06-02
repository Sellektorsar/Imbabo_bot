"""
Обработчики FAQ
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import MessageTexts, get_faq_keyboard

logger = logging.getLogger(__name__)
faq_router = Router()


@faq_router.message(F.text == "❓ FAQ")
async def faq_command(message: Message, session: AsyncSession):
    """Показать FAQ"""
    try:
        # TODO: Получить FAQ из базы данных
        faq_items = []  # Заглушка
        
        if not faq_items:
            await message.answer("FAQ временно недоступен")
            return
        
        await message.answer(
            MessageTexts.FAQ_INTRO,
            reply_markup=get_faq_keyboard(faq_items)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в faq_command: {e}")
        await message.answer(MessageTexts.ERROR_GENERAL)


@faq_router.callback_query(F.data.startswith("faq_"))
async def faq_answer_callback(callback: CallbackQuery, session: AsyncSession):
    """Показать ответ на вопрос FAQ"""
    try:
        faq_id = int(callback.data.split("_")[1])
        # TODO: Получить ответ из базы данных
        
        await callback.answer("FAQ в разработке", show_alert=True)
        
    except Exception as e:
        logger.error(f"Ошибка в faq_answer_callback: {e}")
        await callback.answer(MessageTexts.ERROR_GENERAL, show_alert=True)