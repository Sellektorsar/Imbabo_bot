"""
Обработчики персонального подбора очков
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database import product_crud
from app.states import PersonalSelectionStates
from app.utils import (
    MessageTexts,
    get_personal_selection_gender_keyboard,
    get_personal_selection_style_keyboard,
    get_personal_selection_budget_keyboard
)

logger = logging.getLogger(__name__)
selection_router = Router()


@selection_router.message(F.text == "🎯 Подбор очков")
async def personal_selection_start(message: Message, state: FSMContext):
    """Начать персональный подбор - Интерес/Желание (Interest/Desire)"""
    try:
        await message.answer(
            MessageTexts.PERSONAL_SELECTION_INTRO,
            reply_markup=get_personal_selection_gender_keyboard()
        )
        await state.set_state(PersonalSelectionStates.waiting_for_gender)
        
    except Exception as e:
        logger.error(f"Ошибка в personal_selection_start: {e}")
        await message.answer(MessageTexts.ERROR_GENERAL)


@selection_router.callback_query(F.data.startswith("gender_"), PersonalSelectionStates.waiting_for_gender)
async def process_gender(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора пола"""
    try:
        gender = callback.data.split("_")[1]
        await state.update_data(gender=gender)
        
        await callback.message.edit_text(
            MessageTexts.PERSONAL_SELECTION_STYLE,
            reply_markup=get_personal_selection_style_keyboard()
        )
        await state.set_state(PersonalSelectionStates.waiting_for_style)
        
    except Exception as e:
        logger.error(f"Ошибка в process_gender: {e}")
        await callback.answer(MessageTexts.ERROR_GENERAL, show_alert=True)


@selection_router.callback_query(F.data.startswith("style_"), PersonalSelectionStates.waiting_for_style)
async def process_style(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора стиля"""
    try:
        style = callback.data.split("_")[1]
        await state.update_data(style=style)
        
        await callback.message.edit_text(
            MessageTexts.PERSONAL_SELECTION_BUDGET,
            reply_markup=get_personal_selection_budget_keyboard()
        )
        await state.set_state(PersonalSelectionStates.waiting_for_budget)
        
    except Exception as e:
        logger.error(f"Ошибка в process_style: {e}")
        await callback.answer(MessageTexts.ERROR_GENERAL, show_alert=True)


@selection_router.callback_query(F.data.startswith("budget_"), PersonalSelectionStates.waiting_for_budget)
async def process_budget(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора бюджета и показ результатов"""
    try:
        budget = callback.data.split("_")[1]
        data = await state.get_data()
        
        # Формируем фильтры для поиска
        filters = {
            'gender': data.get('gender'),
            'style': data.get('style')
        }
        
        # Обрабатываем бюджет
        if budget == "5000":
            filters['max_price'] = 5000
        elif budget == "10000":
            filters['min_price'] = 5000
            filters['max_price'] = 10000
        elif budget == "20000":
            filters['min_price'] = 10000
            filters['max_price'] = 20000
        # unlimited - без ограничений по цене
        
        # Ищем подходящие товары
        products = await product_crud.search_products(session, filters)
        
        if not products:
            await callback.message.edit_text(MessageTexts.PERSONAL_SELECTION_NO_RESULTS)
        else:
            results_text = []
            for product in products:
                results_text.append(MessageTexts.format_product_for_selection(product))
            
            text = MessageTexts.PERSONAL_SELECTION_RESULTS.format(
                results="\n".join(results_text)
            )
            
            await callback.message.edit_text(text)
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка в process_budget: {e}")
        await callback.answer(MessageTexts.ERROR_GENERAL, show_alert=True)