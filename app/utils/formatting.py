"""
Утилиты для форматирования данных
"""
from typing import Dict, Any
import json


def format_cart_summary(cart_data: Dict[str, Any]) -> str:
    """Форматирование содержимого корзины для отображения"""
    if not cart_data or not cart_data.get('items'):
        return "Корзина пуста"
    
    items = cart_data.get('items', {})
    total = cart_data.get('total', 0)
    
    lines = []
    for product_id, item in items.items():
        name = item.get('name', 'Товар')
        price = item.get('price', 0)
        quantity = item.get('quantity', 1)
        
        lines.append(f"• {name} - {price}₽ x {quantity} = {price * quantity}₽")
    
    lines.append(f"\n<b>Итого: {total}₽</b>")
    
    return "\n".join(lines)


def format_order_summary(order_data: Dict[str, Any]) -> str:
    """Форматирование данных заказа"""
    lines = [
        f"📦 <b>Заказ #{order_data.get('id', 'N/A')}</b>",
        f"👤 Покупатель: {order_data.get('customer_name', 'N/A')}",
        f"📱 Телефон: {order_data.get('customer_phone', 'N/A')}",
        f"📍 Адрес: {order_data.get('delivery_address', 'N/A')}",
        "",
        "<b>Состав заказа:</b>"
    ]
    
    items = order_data.get('items', [])
    total = 0
    
    for item in items:
        name = item.get('product_name', 'Товар')
        price = item.get('price', 0)
        quantity = item.get('quantity', 1)
        item_total = price * quantity
        total += item_total
        
        lines.append(f"• {name} - {price}₽ x {quantity} = {item_total}₽")
    
    if order_data.get('promo_discount', 0) > 0:
        lines.append(f"\n💰 Скидка по промокоду: -{order_data['promo_discount']}₽")
        total -= order_data['promo_discount']
    
    lines.append(f"\n<b>Итого к оплате: {total}₽</b>")
    
    return "\n".join(lines)


def format_product_description(product: Dict[str, Any]) -> str:
    """Форматирование описания товара"""
    lines = [
        f"🕶️ <b>{product.get('name', 'Товар')}</b>",
        "",
        product.get('description', 'Описание отсутствует'),
        "",
        f"💰 <b>Цена: {product.get('price', 0)}₽</b>"
    ]
    
    if product.get('in_stock', True):
        lines.append("✅ В наличии")
    else:
        lines.append("❌ Нет в наличии")
    
    return "\n".join(lines)


def format_user_stats(stats: Dict[str, Any]) -> str:
    """Форматирование статистики пользователей"""
    lines = [
        "👥 <b>Статистика пользователей</b>",
        "",
        f"Всего пользователей: {stats.get('total_users', 0)}",
        f"Активных: {stats.get('active_users', 0)}",
        f"Подписчиков канала: {stats.get('subscribers', 0)}",
        f"Заблокировали бота: {stats.get('blocked_users', 0)}",
        "",
        f"Новых за сегодня: {stats.get('new_today', 0)}",
        f"Новых за неделю: {stats.get('new_week', 0)}",
        f"Новых за месяц: {stats.get('new_month', 0)}"
    ]
    
    return "\n".join(lines)


def format_sales_stats(stats: Dict[str, Any]) -> str:
    """Форматирование статистики продаж"""
    lines = [
        "💰 <b>Статистика продаж</b>",
        "",
        f"Всего заказов: {stats.get('total_orders', 0)}",
        f"Выполнено: {stats.get('completed_orders', 0)}",
        f"В обработке: {stats.get('processing_orders', 0)}",
        f"Отменено: {stats.get('cancelled_orders', 0)}",
        "",
        f"Общая сумма: {stats.get('total_revenue', 0)}₽",
        f"Средний чек: {stats.get('average_order', 0)}₽",
        "",
        f"Продаж за сегодня: {stats.get('sales_today', 0)}₽",
        f"Продаж за неделю: {stats.get('sales_week', 0)}₽",
        f"Продаж за месяц: {stats.get('sales_month', 0)}₽"
    ]
    
    return "\n".join(lines)


def format_conversion_stats(stats: Dict[str, Any]) -> str:
    """Форматирование статистики конверсии AIDA"""
    lines = [
        "📊 <b>Воронка AIDA</b>",
        "",
        f"👀 Внимание (Attention): {stats.get('attention', 0)} чел.",
        f"🔍 Интерес (Interest): {stats.get('interest', 0)} чел.",
        f"❤️ Желание (Desire): {stats.get('desire', 0)} чел.",
        f"🛒 Действие (Action): {stats.get('action', 0)} чел.",
        "",
        "📈 <b>Конверсии:</b>"
    ]
    
    attention = stats.get('attention', 0)
    if attention > 0:
        interest_rate = (stats.get('interest', 0) / attention) * 100
        desire_rate = (stats.get('desire', 0) / attention) * 100
        action_rate = (stats.get('action', 0) / attention) * 100
        
        lines.extend([
            f"Внимание → Интерес: {interest_rate:.1f}%",
            f"Внимание → Желание: {desire_rate:.1f}%",
            f"Внимание → Действие: {action_rate:.1f}%"
        ])
    else:
        lines.append("Недостаточно данных для расчета")
    
    return "\n".join(lines)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезка текста до указанной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def format_price(price: float) -> str:
    """Форматирование цены"""
    return f"{int(price):,}₽".replace(",", " ")


def format_datetime(dt) -> str:
    """Форматирование даты и времени"""
    if not dt:
        return "Не указано"
    
    return dt.strftime("%d.%m.%Y %H:%M")


def format_date(dt) -> str:
    """Форматирование даты"""
    if not dt:
        return "Не указано"
    
    return dt.strftime("%d.%m.%Y")


def safe_json_loads(json_str: str, default=None):
    """Безопасная загрузка JSON"""
    if not json_str:
        return default or {}
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default or {}


def safe_json_dumps(data: Any) -> str:
    """Безопасная сериализация в JSON"""
    try:
        return json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError):
        return "{}"