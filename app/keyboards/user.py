"""
Клавиатуры для пользователей
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import List, Dict, Any


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="🕶️ Каталог")
    builder.button(text="🎯 Подбор очков")
    builder.button(text="🛒 Корзина")
    builder.button(text="❓ FAQ")
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
    
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    
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
    builder.button(text="✏️ Изменить данные", callback_data="edit_order_data")
    builder.button(text="❌ Отменить", callback_data="cancel_order")
    
    builder.adjust(1)
    return builder.as_markup()


def get_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для начала подбора"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🎯 Начать подбор", callback_data="start_selection")
    builder.button(text="🔙 Главное меню", callback_data="back_to_main")
    
    builder.adjust(1)
    return builder.as_markup()


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора пола"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="👨 Мужской", callback_data="gender_male")
    builder.button(text="👩 Женский", callback_data="gender_female")
    builder.button(text="🤷 Не важно", callback_data="gender_any")
    
    builder.adjust(1)
    return builder.as_markup()


def get_style_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора стиля"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="😎 Классический", callback_data="style_classic")
    builder.button(text="🕶️ Спортивный", callback_data="style_sport")
    builder.button(text="🌟 Модный", callback_data="style_fashion")
    builder.button(text="🤓 Имиджевый", callback_data="style_image")
    
    builder.adjust(2)
    return builder.as_markup()


def get_budget_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора бюджета"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="💰 До 2000₽", callback_data="budget_low")
    builder.button(text="💎 2000-5000₽", callback_data="budget_medium")
    builder.button(text="👑 Свыше 5000₽", callback_data="budget_high")
    builder.button(text="🤷 Не важно", callback_data="budget_any")
    
    builder.adjust(2)
    return builder.as_markup()


def get_selection_results_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура с результатами подбора"""
    builder = InlineKeyboardBuilder()
    
    for i, product in enumerate(products[:3], 1):  # Максимум 3 товара
        builder.button(
            text=f"{i}. {product['name']} - {product['price']}₽",
            callback_data=f"product_{product['id']}"
        )
    
    builder.button(text="🔄 Новый подбор", callback_data="start_selection")
    builder.button(text="🔙 Главное меню", callback_data="back_to_main")
    
    builder.adjust(1)
    return builder.as_markup()


def get_faq_keyboard(faq_items: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура с вопросами FAQ"""
    builder = InlineKeyboardBuilder()
    
    for item in faq_items:
        builder.button(
            text=item['question'][:50] + ("..." if len(item['question']) > 50 else ""),
            callback_data=f"faq_{item['id']}"
        )
    
    builder.button(text="🔙 Главное меню", callback_data="back_to_main")
    
    builder.adjust(1)
    return builder.as_markup()


def get_faq_item_keyboard(faq_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для отдельного FAQ"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔙 К вопросам", callback_data="back_to_faq")
    builder.button(text="💬 Связаться с поддержкой", callback_data="contact_support")
    
    builder.adjust(1)
    return builder.as_markup()


def get_review_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа отзыва"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📝 Текстовый отзыв", callback_data="review_text")
    builder.button(text="🎤 Голосовой отзыв", callback_data="review_voice")
    builder.button(text="❌ Отмена", callback_data="cancel_review")
    
    builder.adjust(1)
    return builder.as_markup()


def get_promo_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для промокода"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🎫 Ввести промокод", callback_data="enter_promo")
    builder.button(text="⏭️ Пропустить", callback_data="skip_promo")
    
    builder.adjust(1)
    return builder.as_markup()


def get_contact_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для связи с поддержкой"""
    builder = InlineKeyboardBuilder()
    
    if hasattr(get_contact_keyboard, 'support_username'):
        builder.button(
            text="💬 Написать в поддержку",
            url=f"https://t.me/{get_contact_keyboard.support_username}"
        )
    
    builder.button(text="🔙 Назад", callback_data="back_to_faq")
    
    builder.adjust(1)
    return builder.as_markup()


# Функция для установки username поддержки
def set_support_username(username: str):
    """Установить username для поддержки"""
    get_contact_keyboard.support_username = username