"""
Клавиатуры для пользователей
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import List, Dict, Any


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="🕶️ Каталог очков")
    builder.button(text="🎯 Подбор по параметрам")
    builder.button(text="🛒 Моя корзина")
    builder.button(text="❓ Вопросы (FAQ)")
    builder.button(text="💬 Оставить отзыв")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def get_subscription_keyboard(channel_username: str) -> InlineKeyboardMarkup:
    """Клавиатура для подписки на канал"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="📢 Подписаться на канал",
        url=f"https://t.me/{channel_username}"
    )
    builder.button(
        text="✅ Я подписался",
        callback_data="check_subscription"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_categories_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура с категориями товаров"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.button(
            text=f"{category.get('emoji', '📦')} {category['name']}",
            callback_data=f"category_{category['id']}"
        )
    
    builder.button(text="🔙 Назад в меню", callback_data="back_to_main")

    builder.adjust(1)
    return builder.as_markup()


def get_products_keyboard(products: List[Dict[str, Any]], category_id: int, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура с товарами в категории"""
    builder = InlineKeyboardBuilder()
    
    # Пагинация
    start = page * per_page
    end = start + per_page
    page_products = products[start:end]
    
    for product in page_products:
        price_text = f" - {product['price']}₽" if product.get('price') else ""
        stock_emoji = "✅" if product.get('in_stock', True) else "❌"
        
        builder.button(
            text=f"{stock_emoji} {product['name']}{price_text}",
            callback_data=f"product_{product['id']}"
        )
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"products_page_{category_id}_{page-1}"
        ))
    
    if end < len(products):
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ Далее",
            callback_data=f"products_page_{category_id}_{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.button(text="🔙 К категориям", callback_data="back_to_categories")
    
    builder.adjust(1)
    return builder.as_markup()


def get_product_keyboard(product_id: int, in_stock: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для товара"""
    builder = InlineKeyboardBuilder()
    
    if in_stock:
        builder.button(
            text="🛒 Добавить в корзину",
            callback_data=f"add_to_cart_{product_id}"
        )
    else:
        builder.button(
            text="❌ Нет в наличии",
            callback_data="out_of_stock"
        )
    
    builder.button(text="🔙 Назад к товарам", callback_data="back_to_products")
    
    builder.adjust(1)
    return builder.as_markup()


def get_cart_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для корзины"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📦 Оформить заказ", callback_data="checkout")
    builder.button(text="🗑️ Очистить корзину", callback_data="clear_cart")
    builder.button(text="🛍️ Продолжить покупки", callback_data="continue_shopping")
    
    builder.adjust(1)
    return builder.as_markup()


def get_empty_cart_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для пустой корзины"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🛍️ Перейти к покупкам", callback_data="continue_shopping")
    
    return builder.as_markup()


def get_checkout_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения заказа"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Подтвердить заказ", callback_data="confirm_order")
    builder.button(text="✏️ Изменить данные заказа", callback_data="edit_order_data")
    builder.button(text="❌ Отменить оформление заказа", callback_data="cancel_order")

    builder.adjust(1)
    return builder.as_markup()


def get_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для начала подбора"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🎯 Начать подбор очков", callback_data="start_selection")
    builder.button(text="🔙 Вернуться в главное меню", callback_data="back_to_main")

    builder.adjust(1)
    return builder.as_markup()


def get_review_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для отзывов"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Оставить отзыв", callback_data="leave_review")
    builder.button(text="🔙 Вернуться в меню", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()


def get_faq_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для FAQ"""
    builder = InlineKeyboardBuilder()
    builder.button(text="❓ Часто задаваемые вопросы (FAQ)", callback_data="show_faq")
    builder.button(text="🔙 Вернуться в главное меню", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()


def get_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления заказом"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Повторить заказ", callback_data=f"repeat_order_{order_id}")
    builder.button(text="❌ Отменить заказ", callback_data=f"cancel_order_{order_id}")
    builder.button(text="📋 К списку заказов", callback_data="back_to_orders")
    builder.adjust(1)
    return builder.as_markup()


def get_orders_list_keyboard(orders: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком заказов"""
    builder = InlineKeyboardBuilder()
    for order in orders:
        builder.button(
            text=f"📦 Заказ №{order['id']} от {order['date']}",
            callback_data=f"order_{order['id']}"
        )
    builder.button(text="🔙 Вернуться в главное меню", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()

