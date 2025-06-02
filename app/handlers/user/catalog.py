"""
Обработчики каталога товаров
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database import category_crud, product_crud
from app.utils import (
    MessageTexts,
    get_categories_keyboard,
    get_products_keyboard,
    get_product_detail_keyboard
)

logger = logging.getLogger(__name__)
catalog_router = Router()


@catalog_router.message(F.text == "🛍 Каталог")
async def catalog_command(message: Message, session: AsyncSession):
    """Показать каталог товаров - Интерес (Interest)"""
    try:
        categories = await category_crud.get_active_categories(session)
        
        if not categories:
            await message.answer("😔 Каталог временно недоступен. Попробуйте позже.")
            return
        
        await message.answer(
            MessageTexts.CATALOG_INTRO,
            reply_markup=get_categories_keyboard(categories)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в catalog_command: {e}")
        await message.answer(MessageTexts.ERROR_GENERAL)


@catalog_router.callback_query(F.data == "catalog")
async def catalog_callback(callback: CallbackQuery, session: AsyncSession):
    """Callback для возврата в каталог"""
    try:
        categories = await category_crud.get_active_categories(session)
        
        await callback.message.edit_text(
            MessageTexts.CATALOG_INTRO,
            reply_markup=get_categories_keyboard(categories)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в catalog_callback: {e}")
        await callback.answer(MessageTexts.ERROR_GENERAL, show_alert=True)


@catalog_router.callback_query(F.data.startswith("category_"))
async def category_callback(callback: CallbackQuery, session: AsyncSession):
    """Показать товары в категории"""
    try:
        category_id = int(callback.data.split("_")[1])
        products = await product_crud.get_by_category(session, category_id)
        
        if not products:
            await callback.answer(
                "В этой категории пока нет товаров",
                show_alert=True
            )
            return
        
        await callback.message.edit_text(
            f"Товары в категории:",
            reply_markup=get_products_keyboard(products, category_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в category_callback: {e}")
        await callback.answer(MessageTexts.ERROR_GENERAL, show_alert=True)


@catalog_router.callback_query(F.data.startswith("product_"))
async def product_callback(callback: CallbackQuery, session: AsyncSession):
    """Показать детали товара - Желание (Desire)"""
    try:
        product_id = int(callback.data.split("_")[1])
        product = await product_crud.get(session, product_id)
        
        if not product:
            await callback.answer("Товар не найден", show_alert=True)
            return
        
        # Проверяем, есть ли товар в корзине (заглушка)
        in_cart = False  # TODO: реализовать проверку корзины
        
        text = MessageTexts.PRODUCT_DETAIL_TEMPLATE.format(
            unique_mark="⭐ " if product.is_unique else "",
            name=product.name,
            metaphoric_description=product.metaphoric_description or product.description,
            price=product.display_price,
            availability="✅ В наличии" if product.is_available else "❌ Нет в наличии",
            category_name=product.category.name if product.category else ""
        )
        
        if product.photo_url:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=product.photo_url,
                caption=text,
                reply_markup=get_product_detail_keyboard(product, in_cart)
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=get_product_detail_keyboard(product, in_cart)
            )
        
    except Exception as e:
        logger.error(f"Ошибка в product_callback: {e}")
        await callback.answer(MessageTexts.ERROR_GENERAL, show_alert=True)