"""
Вспомогательные функции
"""
import re
import logging
from decimal import Decimal
from typing import Optional
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


def format_price(price: Decimal) -> str:
    """Форматирование цены для отображения"""
    return f"{price:,.0f} ₽"


def validate_phone(phone: str) -> bool:
    """Валидация номера телефона"""
    # Убираем все символы кроме цифр и +
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # Проверяем российский номер
    patterns = [
        r'^\+7\d{10}$',  # +7XXXXXXXXXX
        r'^8\d{10}$',    # 8XXXXXXXXXX
        r'^7\d{10}$',    # 7XXXXXXXXXX
    ]
    
    return any(re.match(pattern, clean_phone) for pattern in patterns)


def normalize_phone(phone: str) -> str:
    """Нормализация номера телефона"""
    # Убираем все символы кроме цифр
    digits = re.sub(r'\D', '', phone)
    
    # Приводим к формату +7XXXXXXXXXX
    if digits.startswith('8') and len(digits) == 11:
        digits = '7' + digits[1:]
    elif digits.startswith('7') and len(digits) == 11:
        pass
    else:
        return phone  # Возвращаем как есть, если не можем нормализовать
    
    return f"+{digits}"


async def check_subscription(bot: Bot, user_id: int, channel_id: str) -> bool:
    """Проверка подписки пользователя на канал"""
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramBadRequest as e:
        logger.warning(f"Ошибка проверки подписки для пользователя {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при проверке подписки: {e}")
        return False


def get_cart_from_fsm_data(fsm_data: dict) -> list:
    """Получение корзины из FSM данных"""
    if not fsm_data:
        return []
    return fsm_data.get('cart', [])


def add_to_cart(fsm_data: dict, product_id: int, quantity: int = 1) -> dict:
    """Добавление товара в корзину"""
    if not fsm_data:
        fsm_data = {}
    
    cart = fsm_data.get('cart', [])
    
    # Ищем товар в корзине
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            break
    else:
        # Товара нет в корзине, добавляем новый
        cart.append({
            'product_id': product_id,
            'quantity': quantity
        })
    
    fsm_data['cart'] = cart
    return fsm_data


def remove_from_cart(fsm_data: dict, product_id: int) -> dict:
    """Удаление товара из корзины"""
    if not fsm_data:
        return {}
    
    cart = fsm_data.get('cart', [])
    cart = [item for item in cart if item['product_id'] != product_id]
    
    fsm_data['cart'] = cart
    return fsm_data


def update_cart_quantity(fsm_data: dict, product_id: int, quantity: int) -> dict:
    """Обновление количества товара в корзине"""
    if not fsm_data:
        return {}
    
    cart = fsm_data.get('cart', [])
    
    for item in cart:
        if item['product_id'] == product_id:
            if quantity <= 0:
                cart.remove(item)
            else:
                item['quantity'] = quantity
            break
    
    fsm_data['cart'] = cart
    return fsm_data


def clear_cart(fsm_data: dict) -> dict:
    """Очистка корзины"""
    if not fsm_data:
        return {}
    
    fsm_data['cart'] = []
    return fsm_data


def is_product_in_cart(fsm_data: dict, product_id: int) -> bool:
    """Проверка наличия товара в корзине"""
    cart = get_cart_from_fsm_data(fsm_data)
    return any(item['product_id'] == product_id for item in cart)


def get_cart_total_items(fsm_data: dict) -> int:
    """Получение общего количества товаров в корзине"""
    cart = get_cart_from_fsm_data(fsm_data)
    return sum(item['quantity'] for item in cart)


def calculate_cart_total(cart_items: list, products: dict) -> Decimal:
    """Расчет общей стоимости корзины"""
    total = Decimal(0)
    for item in cart_items:
        product = products.get(item['product_id'])
        if product:
            total += product.price * item['quantity']
    return total


def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезка текста до указанной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def escape_markdown(text: str) -> str:
    """Экранирование специальных символов для Markdown"""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text