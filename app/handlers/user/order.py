"""
Обработчики оформления заказов
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database import user_crud, order_crud, promo_code_crud
from app.states import OrderStates
from app.utils import MessageTexts, validate_phone, normalize_phone

logger = logging.getLogger(__name__)
order_router = Router()


@order_router.callback_query(F.data == "checkout")
async def checkout_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начать оформление заказа - Действие (Action)"""
    try:
        await callback.message.edit_text(MessageTexts.ORDER_START)
        await state.set_state(OrderStates.waiting_for_name)
        
    except Exception as e:
        logger.error(f"Ошибка в checkout_callback: {e}")
        await callback.answer(MessageTexts.ERROR_GENERAL, show_alert=True)


@order_router.message(OrderStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    try:
        await state.update_data(name=message.text.strip())
        await message.answer(MessageTexts.ORDER_PHONE)
        await state.set_state(OrderStates.waiting_for_phone)
        
    except Exception as e:
        logger.error(f"Ошибка в process_name: {e}")
        await message.answer(MessageTexts.ERROR_GENERAL)


@order_router.message(OrderStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка телефона"""
    try:
        phone = message.text.strip()
        
        if not validate_phone(phone):
            await message.answer(MessageTexts.ERROR_PHONE_FORMAT)
            return
        
        normalized_phone = normalize_phone(phone)
        await state.update_data(phone=normalized_phone)
        await message.answer(MessageTexts.ORDER_ADDRESS)
        await state.set_state(OrderStates.waiting_for_address)
        
    except Exception as e:
        logger.error(f"Ошибка в process_phone: {e}")
        await message.answer(MessageTexts.ERROR_GENERAL)


@order_router.message(OrderStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка адреса"""
    try:
        await state.update_data(address=message.text.strip())
        
        from app.utils.keyboards import get_promo_code_keyboard
        await message.answer(
            MessageTexts.ORDER_PROMO_CODE,
            reply_markup=get_promo_code_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_promo_code)
        
    except Exception as e:
        logger.error(f"Ошибка в process_address: {e}")
        await message.answer(MessageTexts.ERROR_GENERAL)


# Заглушки для остальных состояний
@order_router.callback_query(F.data == "skip_promo", OrderStates.waiting_for_promo_code)
async def skip_promo_callback(callback: CallbackQuery, state: FSMContext):
    """Пропустить промокод"""
    await callback.message.edit_text("Промокод пропущен. Подготавливаем заказ...")
    # TODO: Реализовать подтверждение заказа


@order_router.callback_query(F.data == "confirm_order")
async def confirm_order_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подтвердить заказ"""
    await callback.answer("Заказ подтвержден! (В разработке)")
    # TODO: Реализовать создание заказа