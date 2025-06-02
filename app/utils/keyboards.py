"""
Клавиатуры для бота
"""
from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.models import Category, Product


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="🛍 Каталог"),
        KeyboardButton(text="🎯 Подбор очков")
    )
    builder.row(
        KeyboardButton(text="🛒 Корзина"),
        KeyboardButton(text="❓ FAQ")
    )
    builder.row(
        KeyboardButton(text="💬 Оставить отзыв")
    )
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def get_subscription_keyboard(channel_username: str) -> InlineKeyboardMarkup:
    """Клавиатура для подписки на канал"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📢 Подписаться на канал",
            url=f"https://t.me/{channel_username.replace('@', '')}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✅ Проверить подписку",
            callback_data="check_subscription"
        )
    )
    
    return builder.as_markup()


def get_categories_keyboard(categories: List[Category]) -> InlineKeyboardMarkup:
    """Клавиатура с категориями товаров"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=category.name,
                callback_data=f"category_{category.id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_main"
        )
    )
    
    return builder.as_markup()


def get_products_keyboard(products: List[Product], category_id: int, page: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура с товарами в категории"""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        availability = "✅" if product.is_available else "❌"
        unique_mark = "⭐" if product.is_unique else ""
        
        builder.row(
            InlineKeyboardButton(
                text=f"{availability} {unique_mark} {product.name} - {product.display_price}",
                callback_data=f"product_{product.id}"
            )
        )
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"products_page_{category_id}_{page-1}")
        )
    
    nav_buttons.append(
        InlineKeyboardButton(text="🔙 К категориям", callback_data="catalog")
    )
    
    # Можно добавить кнопку "Далее" если есть еще товары
    # if len(products) == 10:  # Если показали максимум товаров на странице
    #     nav_buttons.append(
    #         InlineKeyboardButton(text="➡️", callback_data=f"products_page_{category_id}_{page+1}")
    #     )
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    return builder.as_markup()


def get_product_detail_keyboard(product: Product, in_cart: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра товара"""
    builder = InlineKeyboardBuilder()
    
    if product.is_available:
        if not in_cart:
            builder.row(
                InlineKeyboardButton(
                    text="🛒 Добавить в корзину",
                    callback_data=f"add_to_cart_{product.id}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="✅ В корзине",
                    callback_data="noop"
                )
            )
    else:
        builder.row(
            InlineKeyboardButton(
                text="❌ Нет в наличии",
                callback_data="noop"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 К товарам",
            callback_data=f"category_{product.category_id}"
        ),
        InlineKeyboardButton(
            text="🛒 Корзина",
            callback_data="cart"
        )
    )
    
    return builder.as_markup()


def get_cart_keyboard(has_items: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для корзины"""
    builder = InlineKeyboardBuilder()
    
    if has_items:
        builder.row(
            InlineKeyboardButton(
                text="📦 Оформить заказ",
                callback_data="checkout"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🗑 Очистить корзину",
                callback_data="clear_cart"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🛍 Продолжить покупки",
            callback_data="catalog"
        )
    )
    
    return builder.as_markup()


def get_cart_item_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления товаром в корзине"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="➖", callback_data=f"cart_decrease_{product_id}"),
        InlineKeyboardButton(text="➕", callback_data=f"cart_increase_{product_id}"),
        InlineKeyboardButton(text="🗑", callback_data=f"cart_remove_{product_id}")
    )
    
    return builder.as_markup()


def get_order_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения заказа"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить заказ",
            callback_data="confirm_order"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить данные",
            callback_data="edit_order_data"
        ),
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="cancel_order"
        )
    )
    
    return builder.as_markup()


def get_personal_selection_gender_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора пола при подборе"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="👨 Мужской", callback_data="gender_male"),
        InlineKeyboardButton(text="👩 Женский", callback_data="gender_female")
    )
    builder.row(
        InlineKeyboardButton(text="👫 Унисекс", callback_data="gender_unisex")
    )
    
    return builder.as_markup()


def get_personal_selection_style_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора стиля при подборе"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🕴 Классический", callback_data="style_classic"),
        InlineKeyboardButton(text="🏃 Спортивный", callback_data="style_sport")
    )
    builder.row(
        InlineKeyboardButton(text="✨ Модный", callback_data="style_fashion"),
        InlineKeyboardButton(text="🌟 Авангард", callback_data="style_avant_garde")
    )
    
    return builder.as_markup()


def get_personal_selection_budget_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора бюджета при подборе"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="💰 До 5,000 ₽", callback_data="budget_5000"),
        InlineKeyboardButton(text="💎 5,000-10,000 ₽", callback_data="budget_10000")
    )
    builder.row(
        InlineKeyboardButton(text="👑 10,000-20,000 ₽", callback_data="budget_20000"),
        InlineKeyboardButton(text="💸 Без ограничений", callback_data="budget_unlimited")
    )
    
    return builder.as_markup()


def get_faq_keyboard(faq_items: List) -> InlineKeyboardMarkup:
    """Клавиатура для FAQ"""
    builder = InlineKeyboardBuilder()
    
    for faq in faq_items:
        builder.row(
            InlineKeyboardButton(
                text=faq.question[:50] + "..." if len(faq.question) > 50 else faq.question,
                callback_data=f"faq_{faq.id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Главное меню",
            callback_data="back_to_main"
        )
    )
    
    return builder.as_markup()


def get_promo_code_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ввода промокода"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🎁 Ввести промокод",
            callback_data="enter_promo"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="➡️ Продолжить без промокода",
            callback_data="skip_promo"
        )
    )
    
    return builder.as_markup()