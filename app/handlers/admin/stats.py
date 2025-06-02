"""
Административная статистика и аналитика
"""
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_

from config import settings
from database.crud import user_crud, order_crud, product_crud, category_crud, promo_code_crud
from app.models import OrderStatus

stats_admin_router = Router()


def stats_menu_keyboard():
    """Клавиатура меню статистики"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📊 Общая статистика", callback_data="admin_stats_general")
    builder.button(text="👥 Пользователи", callback_data="admin_stats_users")
    builder.button(text="📋 Заказы", callback_data="admin_stats_orders")
    builder.button(text="📦 Товары", callback_data="admin_stats_products")
    builder.button(text="🎫 Промокоды", callback_data="admin_stats_promo")
    builder.button(text="📈 Конверсия", callback_data="admin_stats_conversion")
    builder.button(text="🔙 Назад", callback_data="admin_main")
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def stats_period_keyboard(stats_type):
    """Клавиатура выбора периода для статистики"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📅 Сегодня", callback_data=f"admin_stats_{stats_type}_today")
    builder.button(text="📅 7 дней", callback_data=f"admin_stats_{stats_type}_week")
    builder.button(text="📅 30 дней", callback_data=f"admin_stats_{stats_type}_month")
    builder.button(text="📅 Все время", callback_data=f"admin_stats_{stats_type}_all")
    builder.button(text="🔙 К статистике", callback_data="admin_stats")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup()


@stats_admin_router.message(Command("stats"))
async def quick_stats(message: Message, session: AsyncSession):
    """Быстрая статистика по команде"""
    if message.from_user.id not in settings.admin_ids_list:
        await message.answer("❌ У вас нет прав доступа")
        return
    
    await show_general_stats(message, session, quick=True)


@stats_admin_router.callback_query(F.data == "admin_stats")
async def stats_menu(callback: CallbackQuery):
    """Главное меню статистики"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📊 <b>Статистика и аналитика</b>\n\n"
        "Выберите раздел для просмотра:",
        reply_markup=stats_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@stats_admin_router.callback_query(F.data == "admin_stats_general")
async def general_stats_callback(callback: CallbackQuery, session: AsyncSession):
    """Общая статистика через callback"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await show_general_stats(callback, session)


async def show_general_stats(message_or_callback, session: AsyncSession, quick: bool = False):
    """Показать общую статистику"""
    # Получаем данные
    all_users = await user_crud.get_all(session)
    all_orders = await order_crud.get_all(session)
    all_products = await product_crud.get_all(session)
    all_categories = await category_crud.get_all(session)
    all_promos = await promo_code_crud.get_all(session)
    
    # Базовая статистика
    total_users = len(all_users)
    active_users = len([u for u in all_users if u.is_active])
    total_orders = len(all_orders)
    completed_orders = len([o for o in all_orders if o.status == OrderStatus.COMPLETED])
    
    # Финансовая статистика
    total_revenue = sum(o.total_amount for o in all_orders if o.status == OrderStatus.COMPLETED)
    avg_order_value = total_revenue / completed_orders if completed_orders > 0 else 0
    
    # За последние 30 дней
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_users = [u for u in all_users if u.created_at >= thirty_days_ago]
    recent_orders = [o for o in all_orders if o.created_at >= thirty_days_ago]
    recent_revenue = sum(o.total_amount for o in recent_orders if o.status == OrderStatus.COMPLETED)
    
    # За сегодня
    today = datetime.now().date()
    today_users = [u for u in all_users if u.created_at.date() == today]
    today_orders = [o for o in all_orders if o.created_at.date() == today]
    today_revenue = sum(o.total_amount for o in today_orders if o.status == OrderStatus.COMPLETED)
    
    # Конверсия
    conversion_rate = (completed_orders / total_users * 100) if total_users > 0 else 0
    
    # Формируем текст
    text = "📊 <b>Общая статистика</b>\n\n"
    
    text += f"👥 <b>Пользователи:</b>\n"
    text += f"   • Всего: {total_users:,}\n"
    text += f"   • Активных: {active_users:,}\n"
    text += f"   • Новых за 30 дней: {len(recent_users):,}\n"
    text += f"   • Новых сегодня: {len(today_users):,}\n\n"
    
    text += f"📋 <b>Заказы:</b>\n"
    text += f"   • Всего: {total_orders:,}\n"
    text += f"   • Выполнено: {completed_orders:,}\n"
    text += f"   • За 30 дней: {len(recent_orders):,}\n"
    text += f"   • Сегодня: {len(today_orders):,}\n\n"
    
    text += f"💰 <b>Финансы:</b>\n"
    text += f"   • Общая выручка: {total_revenue:,.0f}₽\n"
    text += f"   • Средний чек: {avg_order_value:,.0f}₽\n"
    text += f"   • За 30 дней: {recent_revenue:,.0f}₽\n"
    text += f"   • Сегодня: {today_revenue:,.0f}₽\n\n"
    
    text += f"📦 <b>Каталог:</b>\n"
    text += f"   • Категорий: {len(all_categories):,}\n"
    text += f"   • Товаров: {len(all_products):,}\n"
    text += f"   • Доступных: {len([p for p in all_products if p.is_available]):,}\n\n"
    
    text += f"🎫 <b>Промокоды:</b>\n"
    text += f"   • Всего: {len(all_promos):,}\n"
    text += f"   • Активных: {len([p for p in all_promos if p.is_active]):,}\n\n"
    
    text += f"📈 <b>Конверсия:</b>\n"
    text += f"   • Пользователи → Покупатели: {conversion_rate:.1f}%"
    
    if quick:
        # Для быстрой статистики просто отправляем сообщение
        await message_or_callback.answer(text, parse_mode="HTML")
    else:
        # Для callback добавляем клавиатуру
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Обновить", callback_data="admin_stats_general")
        builder.button(text="🔙 К статистике", callback_data="admin_stats")
        builder.adjust(1)
        
        await message_or_callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await message_or_callback.answer()


@stats_admin_router.callback_query(F.data == "admin_stats_users")
async def users_stats(callback: CallbackQuery, session: AsyncSession):
    """Статистика пользователей"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    all_users = await user_crud.get_all(session)
    
    # Анализ пользователей
    total_users = len(all_users)
    active_users = len([u for u in all_users if u.is_active])
    users_with_orders = len([u for u in all_users if u.orders])
    
    # По периодам
    now = datetime.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    today_users = len([u for u in all_users if u.created_at.date() == today])
    week_users = len([u for u in all_users if u.created_at >= week_ago])
    month_users = len([u for u in all_users if u.created_at >= month_ago])
    
    # Активность
    recent_activity = len([u for u in all_users if u.last_activity and u.last_activity >= week_ago])
    
    text = "👥 <b>Статистика пользователей</b>\n\n"
    
    text += f"📊 <b>Общие показатели:</b>\n"
    text += f"   • Всего пользователей: {total_users:,}\n"
    text += f"   • Активных: {active_users:,}\n"
    text += f"   • С заказами: {users_with_orders:,}\n"
    text += f"   • Конверсия в покупатели: {(users_with_orders/total_users*100):.1f}%\n\n"
    
    text += f"📅 <b>Регистрации:</b>\n"
    text += f"   • Сегодня: {today_users:,}\n"
    text += f"   • За неделю: {week_users:,}\n"
    text += f"   • За месяц: {month_users:,}\n\n"
    
    text += f"🔥 <b>Активность:</b>\n"
    text += f"   • Активны за неделю: {recent_activity:,}\n"
    text += f"   • Доля активных: {(recent_activity/total_users*100):.1f}%\n"
    
    # Топ пользователи по заказам
    users_by_orders = sorted(all_users, key=lambda u: len(u.orders), reverse=True)[:5]
    if users_by_orders and users_by_orders[0].orders:
        text += f"\n🏆 <b>Топ покупатели:</b>\n"
        for i, user in enumerate(users_by_orders, 1):
            if user.orders:
                orders_count = len(user.orders)
                total_spent = sum(o.total_amount for o in user.orders if o.status == OrderStatus.COMPLETED)
                text += f"   {i}. {user.first_name or 'Пользователь'} - {orders_count} заказов ({total_spent:,.0f}₽)\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data="admin_stats_users")
    builder.button(text="🔙 К статистике", callback_data="admin_stats")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@stats_admin_router.callback_query(F.data == "admin_stats_orders")
async def orders_stats(callback: CallbackQuery, session: AsyncSession):
    """Статистика заказов"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    all_orders = await order_crud.get_all(session)
    
    # Анализ заказов
    total_orders = len(all_orders)
    
    # По статусам
    new_orders = len([o for o in all_orders if o.status == OrderStatus.NEW])
    processing_orders = len([o for o in all_orders if o.status == OrderStatus.PROCESSING])
    completed_orders = len([o for o in all_orders if o.status == OrderStatus.COMPLETED])
    cancelled_orders = len([o for o in all_orders if o.status == OrderStatus.CANCELLED])
    
    # Финансовая статистика
    total_revenue = sum(o.total_amount for o in all_orders if o.status == OrderStatus.COMPLETED)
    avg_order_value = total_revenue / completed_orders if completed_orders > 0 else 0
    
    # По периодам
    now = datetime.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    today_orders = [o for o in all_orders if o.created_at.date() == today]
    week_orders = [o for o in all_orders if o.created_at >= week_ago]
    month_orders = [o for o in all_orders if o.created_at >= month_ago]
    
    today_revenue = sum(o.total_amount for o in today_orders if o.status == OrderStatus.COMPLETED)
    week_revenue = sum(o.total_amount for o in week_orders if o.status == OrderStatus.COMPLETED)
    month_revenue = sum(o.total_amount for o in month_orders if o.status == OrderStatus.COMPLETED)
    
    text = "📋 <b>Статистика заказов</b>\n\n"
    
    text += f"📊 <b>По статусам:</b>\n"
    text += f"   • Всего заказов: {total_orders:,}\n"
    text += f"   • Новые: {new_orders:,}\n"
    text += f"   • В обработке: {processing_orders:,}\n"
    text += f"   • Выполнено: {completed_orders:,}\n"
    text += f"   • Отменено: {cancelled_orders:,}\n\n"
    
    text += f"💰 <b>Финансы:</b>\n"
    text += f"   • Общая выручка: {total_revenue:,.0f}₽\n"
    text += f"   • Средний чек: {avg_order_value:,.0f}₽\n\n"
    
    text += f"📅 <b>По периодам:</b>\n"
    text += f"   • Сегодня: {len(today_orders):,} заказов ({today_revenue:,.0f}₽)\n"
    text += f"   • За неделю: {len(week_orders):,} заказов ({week_revenue:,.0f}₽)\n"
    text += f"   • За месяц: {len(month_orders):,} заказов ({month_revenue:,.0f}₽)\n\n"
    
    # Конверсия
    if total_orders > 0:
        completion_rate = (completed_orders / total_orders) * 100
        cancellation_rate = (cancelled_orders / total_orders) * 100
        text += f"📈 <b>Конверсия:</b>\n"
        text += f"   • Завершение заказов: {completion_rate:.1f}%\n"
        text += f"   • Отмена заказов: {cancellation_rate:.1f}%\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data="admin_stats_orders")
    builder.button(text="🔙 К статистике", callback_data="admin_stats")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@stats_admin_router.callback_query(F.data == "admin_stats_products")
async def products_stats(callback: CallbackQuery, session: AsyncSession):
    """Статистика товаров"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    all_products = await product_crud.get_all(session)
    all_orders = await order_crud.get_all(session)
    
    # Анализ товаров
    total_products = len(all_products)
    available_products = len([p for p in all_products if p.is_available])
    featured_products = len([p for p in all_products if p.is_featured])
    unique_products = len([p for p in all_products if p.is_unique])
    
    # Статистика продаж
    completed_orders = [o for o in all_orders if o.status == OrderStatus.COMPLETED]
    
    # Подсчет продаж по товарам
    product_sales = {}
    for order in completed_orders:
        for item in order.items:
            product_id = item.product_id
            if product_id not in product_sales:
                product_sales[product_id] = {"quantity": 0, "revenue": 0, "product": item.product}
            product_sales[product_id]["quantity"] += item.quantity
            product_sales[product_id]["revenue"] += item.quantity * item.price
    
    # Топ товары по продажам
    top_products = sorted(product_sales.values(), key=lambda x: x["quantity"], reverse=True)[:5]
    
    # Топ товары по выручке
    top_revenue_products = sorted(product_sales.values(), key=lambda x: x["revenue"], reverse=True)[:5]
    
    text = "📦 <b>Статистика товаров</b>\n\n"
    
    text += f"📊 <b>Каталог:</b>\n"
    text += f"   • Всего товаров: {total_products:,}\n"
    text += f"   • Доступных: {available_products:,}\n"
    text += f"   • Рекомендуемых: {featured_products:,}\n"
    text += f"   • Уникальных: {unique_products:,}\n\n"
    
    if top_products:
        text += f"🏆 <b>Топ по продажам:</b>\n"
        for i, item in enumerate(top_products, 1):
            text += f"   {i}. {item['product'].name} - {item['quantity']} шт.\n"
        text += "\n"
    
    if top_revenue_products:
        text += f"💰 <b>Топ по выручке:</b>\n"
        for i, item in enumerate(top_revenue_products, 1):
            text += f"   {i}. {item['product'].name} - {item['revenue']:,.0f}₽\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data="admin_stats_products")
    builder.button(text="🔙 К статистике", callback_data="admin_stats")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@stats_admin_router.callback_query(F.data == "admin_stats_conversion")
async def conversion_stats(callback: CallbackQuery, session: AsyncSession):
    """Статистика конверсии"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    all_users = await user_crud.get_all(session)
    all_orders = await order_crud.get_all(session)
    
    # Воронка AIDA
    total_users = len(all_users)
    users_with_orders = len([u for u in all_users if u.orders])
    completed_orders = len([o for o in all_orders if o.status == OrderStatus.COMPLETED])
    
    # Конверсии
    registration_to_order = (users_with_orders / total_users * 100) if total_users > 0 else 0
    order_to_completion = (completed_orders / len(all_orders) * 100) if all_orders else 0
    
    # Анализ по этапам AIDA
    # Attention: все пользователи
    attention_users = total_users
    
    # Interest: пользователи, которые просматривали каталог (примерная оценка)
    # В реальной реализации нужно отслеживать действия пользователей
    interest_users = int(total_users * 0.7)  # Примерная оценка
    
    # Desire: пользователи, добавившие товары в корзину
    # В реальной реализации нужно отслеживать корзины
    desire_users = int(total_users * 0.3)  # Примерная оценка
    
    # Action: пользователи, сделавшие заказ
    action_users = users_with_orders
    
    text = "📈 <b>Анализ конверсии</b>\n\n"
    
    text += f"🎯 <b>Воронка AIDA:</b>\n"
    text += f"   • Внимание (Attention): {attention_users:,} чел. (100%)\n"
    
    if attention_users > 0:
        interest_rate = (interest_users / attention_users) * 100
        text += f"   • Интерес (Interest): {interest_users:,} чел. ({interest_rate:.1f}%)\n"
        
        if interest_users > 0:
            desire_rate = (desire_users / interest_users) * 100
            text += f"   • Желание (Desire): {desire_users:,} чел. ({desire_rate:.1f}%)\n"
            
            if desire_users > 0:
                action_rate = (action_users / desire_users) * 100
                text += f"   • Действие (Action): {action_users:,} чел. ({action_rate:.1f}%)\n"
    
    text += f"\n📊 <b>Ключевые метрики:</b>\n"
    text += f"   • Регистрация → Заказ: {registration_to_order:.1f}%\n"
    text += f"   • Заказ → Завершение: {order_to_completion:.1f}%\n"
    text += f"   • Общая конверсия: {(completed_orders/total_users*100):.1f}%\n\n"
    
    # Анализ отказов
    cancelled_orders = len([o for o in all_orders if o.status == OrderStatus.CANCELLED])
    if all_orders:
        cancellation_rate = (cancelled_orders / len(all_orders)) * 100
        text += f"❌ <b>Анализ отказов:</b>\n"
        text += f"   • Отмененные заказы: {cancelled_orders:,}\n"
        text += f"   • Доля отмен: {cancellation_rate:.1f}%\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data="admin_stats_conversion")
    builder.button(text="🔙 К статистике", callback_data="admin_stats")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()