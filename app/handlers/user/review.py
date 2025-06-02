"""
Обработчики отзывов
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.states import ReviewStates
from app.utils import MessageTexts

logger = logging.getLogger(__name__)
review_router = Router()


@review_router.message(F.text == "💬 Оставить отзыв")
async def review_start(message: Message, state: FSMContext):
    """Начать сбор отзыва"""
    try:
        await message.answer(MessageTexts.REVIEW_REQUEST)
        await state.set_state(ReviewStates.waiting_for_review)
        
    except Exception as e:
        logger.error(f"Ошибка в review_start: {e}")
        await message.answer(MessageTexts.ERROR_GENERAL)


@review_router.message(ReviewStates.waiting_for_review)
async def process_review(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка отзыва"""
    try:
        # TODO: Сохранить отзыв в базу данных
        # TODO: Переслать отзыв администратору
        
        await message.answer(MessageTexts.REVIEW_THANKS)
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка в process_review: {e}")
        await message.answer(MessageTexts.ERROR_GENERAL)