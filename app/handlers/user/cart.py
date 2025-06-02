"""
Обработчики корзины
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database import user_crud, product_crud
from app.utils import (
    MessageTexts,
    get_cart_keyboard,
    get_cart_item_keyboard,
    add_to_cart,
    remove_from_cart,
    update_cart_quantity,
    clear_cart,
    get_cart_from_fsm_data,
    calculate_cart_total
)

logger = logging.getLogger(__name__)
cart_router = Router()


@cart_router.message(F.text == "🛒 Корзина")
async def cart_command(message: Message, session: AsyncSession):
    """Показать корзину"""
    try:
        user = await user_crud.get_by_telegram_id(session, message.from_user.id)
        cart_items = get_cart_from_fsm_data(user.fsm_data if user else {})
        
        if not cart_items:
            await message.answer(
                MessageTexts.CART_EMPTY,
                reply_markup=get_cart_keyboard(has_items=False)
            )
            return
        
        # Получаем информацию о товарах
        products = {}
        for item in cart_items:
            product = await product_crud.get(session, item['product_id'])
            if product:
                products[product.id] = product
        
        # Формируем текст корзины
        items_text = []
        total = calculate_cart_total(cart_items, products)
        
        for item in cart_items:
            product = products.get(item['product_id'])
            if product:
                items_text.append(MessageTexts.format_cart_item(item, product))
        
        text = MessageTexts.CART_TEMPLATE.format(
            items="\n".join(items_text),
            total=f"{total:,.0f} ₽"
        )
        
        await message.answer(
            text,
            reply_markup=get_cart_keyboard(has_items=True)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cart_command: {e}")
        await message.answer(MessageTexts.ERROR_GENERAL)


@cart_router.callback_query(F.data == "cart")
async def cart_callback(callback: CallbackQuery, session: AsyncSession):
    """Callback для показа корзины"""
    try:
        user = await user_crud.get_by_telegram_id(session, callback.from_user.id)
        cart_items = get_cart_from_fsm_data(user.fsm_data if user else {})
        
        if not cart_items:
            await callback.message.edit_text(
                MessageTexts.CART_EMPTY,
                reply_markup=get_cart_keyboard(has_items=False)
            )
            return
        
        # Получаем информацию о товарах
        products = {}
        for item in cart_items:
            product = await product_crud.get(session, item['product_id'])
            if product:
                products[product.id] = product
        
        # Формируем текст корзины
        items_text = []
        total = calculate_cart_total(cart_items, products)
        
        for item in cart_items:
            product = products.get(item['product_id'])
            if product:
                items_text.append(MessageTexts.format_cart_item(item, product))
        
        text = MessageTexts.CART_TEMPLATE.format(
            items="\n".join(items_text),
            total=f"{total:,.0f} ₽"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_cart_keyboard(has_items=True)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cart_callback: {e}")
        await callback.answer(MessageTexts.ERROR_GENERAL, show_alert=True)


@cart_router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart_callback(callback: CallbackQuery, session: AsyncSession):
    """Добавить товар в корзину"""
    try:
        product_id = int(callback.data.split("_")[3])
        user = await user_crud.get_by_telegram_id(session, callback.from_user.id)
        
        if not user:
            await callback.answer("Ошибка: пользователь не найден", show_alert=True)
            return
        
        # Добавляем товар в корзину
        new_fsm_data = add_to_cart(user.fsm_data or {}, product_id)
        await user_crud.update_fsm_state(session, user.id, data=new_fsm_data)
        await session.commit()
        
        await callback.answer("✅ Товар добавлен в корзину!")
        
        # Обновляем клавиатуру
        product = await product_crud.get(session, product_id)
        if product:
            # Обновляем кнопки товара
            from app.utils.keyboards import get_product_detail_keyboard
            await callback.message.edit_reply_markup(
                reply_markup=get_product_detail_keyboard(product, in_cart=True)
            )
        
    except Exception as e:
        logger.error(f"Ошибка в add_to_cart_callback: {e}")
        await callback.answer(MessageTexts.ERROR_GENERAL, show_alert=True)


@cart_router.callback_query(F.data == "clear_cart")
async def clear_cart_callback(callback: CallbackQuery, session: AsyncSession):
    """Очистить корзину"""
    try:
        user = await user_crud.get_by_telegram_id(session, callback.from_user.id)
        
        if user:
            new_fsm_data = clear_cart(user.fsm_data or {})
            await user_crud.update_fsm_state(session, user.id, data=new_fsm_data)
            await session.commit()
        
        await callback.message.edit_text(
            MessageTexts.CART_EMPTY,
            reply_markup=get_cart_keyboard(has_items=False)
        )
        
        await callback.answer("🗑 Корзина очищена")
        
    except Exception as e:
        logger.error(f"Ошибка в clear_cart_callback: {e}")
        await callback.answer(MessageTexts.ERROR_GENERAL, show_alert=True)