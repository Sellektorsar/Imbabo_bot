"""
Административное управление заказами
"""
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, desc

from config import settings
from database.crud import order_crud, user_crud
from app.models import OrderStatus

orders_admin_router = Router()


def orders_menu_keyboard():
    """Клавиатура меню управления заказами"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🆕 Новые заказы", callback_data="admin_orders_new")
    builder.button(text="⏳ В обработке", callback_data="admin_orders_processing")
    builder.button(text="✅ Выполненные", callback_data="admin_orders_completed")
    builder.button(text="❌ Отмененные", callback_data="admin_orders_cancelled")
    builder.button(text="📊 Все заказы", callback_data="admin_orders_all")
    builder.button(text="📈 Статистика", callback_data="admin_orders_stats")
    builder.button(text="🔙 Назад", callback_data="admin_main")
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def orders_list_keyboard(orders, page=0, per_page=5, status_filter=None):
    """Клавиатура со списком заказов"""
    builder = InlineKeyboardBuilder()
    
    start = page * per_page
    end = start + per_page
    page_orders = orders[start:end]
    
    for order in page_orders:
        # Форматируем информацию о заказе
        order_date = order.created_at.strftime("%d.%m %H:%M")
        total_amount = f"{order.total_amount:,.0f}₽"
        status_emoji = {
            OrderStatus.NEW: "🆕",
            OrderStatus.PROCESSING: "⏳", 
            OrderStatus.COMPLETED: "✅",
            OrderStatus.CANCELLED: "❌"
        }.get(order.status, "❓")
        
        builder.button(
            text=f"{status_emoji} #{order.id} - {total_amount} ({order_date})",
            callback_data=f"admin_order_details_{order.id}"
        )
    
    # Пагинация
    nav_buttons = []
    if page > 0:
        callback_data = f"admin_orders_{status_filter}_page_{page-1}" if status_filter else f"admin_orders_all_page_{page-1}"
        nav_buttons.append(("⬅️ Назад", callback_data))
    if end < len(orders):
        callback_data = f"admin_orders_{status_filter}_page_{page+1}" if status_filter else f"admin_orders_all_page_{page+1}"
        nav_buttons.append(("➡️ Далее", callback_data))
    
    for text, callback_data in nav_buttons:
        builder.button(text=text, callback_data=callback_data)
    
    builder.button(text="🔙 К заказам", callback_data="admin_orders")
    
    builder.adjust(1)
    return builder.as_markup()


def order_actions_keyboard(order_id, current_status):
    """Клавиатура действий с заказом"""
    builder = InlineKeyboardBuilder()
    
    # Кнопки изменения статуса в зависимости от текущего
    if current_status == OrderStatus.NEW:
        builder.button(text="⏳ В обработку", callback_data=f"admin_order_status_{order_id}_processing")
        builder.button(text="❌ Отменить", callback_data=f"admin_order_status_{order_id}_cancelled")
    elif current_status == OrderStatus.PROCESSING:
        builder.button(text="✅ Выполнен", callback_data=f"admin_order_status_{order_id}_completed")
        builder.button(text="❌ Отменить", callback_data=f"admin_order_status_{order_id}_cancelled")
    elif current_status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
        builder.button(text="🔄 Вернуть в обработку", callback_data=f"admin_order_status_{order_id}_processing")
    
    builder.button(text="👤 Профиль клиента", callback_data=f"admin_user_profile_{order_id}")
    builder.button(text="📞 Связаться", callback_data=f"admin_contact_user_{order_id}")
    builder.button(text="🔙 К заказам", callback_data="admin_orders")
    
    builder.adjust(2, 1, 1, 1)
    return builder.as_markup()


@orders_admin_router.callback_query(F.data == "admin_orders")
async def orders_menu(callback: CallbackQuery):
    """Главное меню управления заказами"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📋 <b>Управление заказами</b>\n\n"
        "Выберите категорию заказов:",
        reply_markup=orders_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@orders_admin_router.callback_query(F.data.startswith("admin_orders_"))
async def show_orders_by_status(callback: CallbackQuery, session: AsyncSession):
    """Показать заказы по статусу"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    # Парсим callback_data
    parts = callback.data.split("_")
    if len(parts) >= 3:
        status_or_action = parts[2]
        page = 0
        
        # Проверяем, есть ли номер страницы
        if len(parts) > 3 and parts[-2] == "page":
            page = int(parts[-1])
            status_or_action = parts[2]
    
    # Определяем фильтр по статусу
    status_filter = None
    title = ""
    
    if status_or_action == "new":
        status_filter = OrderStatus.NEW
        title = "🆕 Новые заказы"
    elif status_or_action == "processing":
        status_filter = OrderStatus.PROCESSING
        title = "⏳ Заказы в обработке"
    elif status_or_action == "completed":
        status_filter = OrderStatus.COMPLETED
        title = "✅ Выполненные заказы"
    elif status_or_action == "cancelled":
        status_filter = OrderStatus.CANCELLED
        title = "❌ Отмененные заказы"
    elif status_or_action == "all":
        title = "📊 Все заказы"
    elif status_or_action == "stats":
        await show_orders_stats(callback, session)
        return
    
    # Получаем заказы
    if status_filter:
        orders = await order_crud.get_by_status(session, status_filter)
    else:
        orders = await order_crud.get_all(session)
    
    # Сортируем по дате создания (новые сначала)
    orders.sort(key=lambda x: x.created_at, reverse=True)
    
    text = f"{title}\n\n"
    if orders:
        text += f"Найдено заказов: {len(orders)}\n"
        text += "Нажмите на заказ для просмотра деталей:"
    else:
        text += "Заказы не найдены."
    
    await callback.message.edit_text(
        text,
        reply_markup=orders_list_keyboard(orders, page, status_filter=status_or_action),
        parse_mode="HTML"
    )
    await callback.answer()


@orders_admin_router.callback_query(F.data.startswith("admin_order_details_"))
async def show_order_details(callback: CallbackQuery, session: AsyncSession):
    """Показать детали заказа"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[-1])
    order = await order_crud.get_with_items(session, order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    # Получаем информацию о пользователе
    user = await user_crud.get(session, order.user_id)
    
    # Формируем текст с деталями заказа
    status_emoji = {
        OrderStatus.NEW: "🆕",
        OrderStatus.PROCESSING: "⏳",
        OrderStatus.COMPLETED: "✅", 
        OrderStatus.CANCELLED: "❌"
    }.get(order.status, "❓")
    
    status_text = {
        OrderStatus.NEW: "Новый",
        OrderStatus.PROCESSING: "В обработке",
        OrderStatus.COMPLETED: "Выполнен",
        OrderStatus.CANCELLED: "Отменен"
    }.get(order.status, "Неизвестно")
    
    text = f"{status_emoji} <b>Заказ #{order.id}</b>\n\n"
    
    # Информация о клиенте
    text += f"👤 <b>Клиент:</b>\n"
    text += f"   • Имя: {user.first_name or 'Не указано'}\n"
    if user.username:
        text += f"   • Username: @{user.username}\n"
    text += f"   • ID: {user.id}\n"
    
    # Контактная информация
    text += f"\n📞 <b>Контакты:</b>\n"
    text += f"   • Имя: {order.customer_name}\n"
    text += f"   • Телефон: {order.customer_phone}\n"
    text += f"   • Адрес: {order.delivery_address}\n"
    
    # Информация о заказе
    text += f"\n📦 <b>Детали заказа:</b>\n"
    text += f"   • Статус: {status_text}\n"
    text += f"   • Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    
    # Промокод
    if order.promo_code_used:
        text += f"   • Промокод: {order.promo_code_used}\n"
        text += f"   • Скидка: {order.discount_amount:,.0f}₽\n"
    
    # Состав заказа
    text += f"\n🛍 <b>Состав заказа:</b>\n"
    for item in order.items:
        text += f"   • {item.product.name}\n"
        text += f"     Количество: {item.quantity} шт.\n"
        text += f"     Цена: {item.price:,.0f}₽\n"
        text += f"     Сумма: {item.quantity * item.price:,.0f}₽\n\n"
    
    # Итоговая сумма
    text += f"💰 <b>Итого: {order.total_amount:,.0f}₽</b>"
    
    await callback.message.edit_text(
        text,
        reply_markup=order_actions_keyboard(order_id, order.status),
        parse_mode="HTML"
    )
    await callback.answer()


@orders_admin_router.callback_query(F.data.startswith("admin_order_status_"))
async def change_order_status(callback: CallbackQuery, session: AsyncSession):
    """Изменить статус заказа"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    # Парсим callback_data: admin_order_status_{order_id}_{new_status}
    parts = callback.data.split("_")
    order_id = int(parts[3])
    new_status = parts[4]
    
    # Преобразуем строку в enum
    status_mapping = {
        "new": OrderStatus.NEW,
        "processing": OrderStatus.PROCESSING,
        "completed": OrderStatus.COMPLETED,
        "cancelled": OrderStatus.CANCELLED
    }
    
    new_status_enum = status_mapping.get(new_status)
    if not new_status_enum:
        await callback.answer("❌ Неверный статус", show_alert=True)
        return
    
    # Обновляем статус заказа
    try:
        await order_crud.update(session, order_id, {"status": new_status_enum})
        
        status_text = {
            OrderStatus.NEW: "Новый",
            OrderStatus.PROCESSING: "В обработке", 
            OrderStatus.COMPLETED: "Выполнен",
            OrderStatus.CANCELLED: "Отменен"
        }.get(new_status_enum)
        
        await callback.answer(f"✅ Статус изменен на: {status_text}")
        
        # Обновляем отображение заказа
        await show_order_details(callback, session)
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


async def show_orders_stats(callback: CallbackQuery, session: AsyncSession):
    """Показать статистику заказов"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    # Получаем все заказы
    all_orders = await order_crud.get_all(session)
    
    # Считаем статистику
    total_orders = len(all_orders)
    
    # По статусам
    new_orders = len([o for o in all_orders if o.status == OrderStatus.NEW])
    processing_orders = len([o for o in all_orders if o.status == OrderStatus.PROCESSING])
    completed_orders = len([o for o in all_orders if o.status == OrderStatus.COMPLETED])
    cancelled_orders = len([o for o in all_orders if o.status == OrderStatus.CANCELLED])
    
    # Финансовая статистика
    total_revenue = sum(o.total_amount for o in all_orders if o.status == OrderStatus.COMPLETED)
    avg_order_value = total_revenue / completed_orders if completed_orders > 0 else 0
    
    # За последние 30 дней
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_orders = [o for o in all_orders if o.created_at >= thirty_days_ago]
    recent_revenue = sum(o.total_amount for o in recent_orders if o.status == OrderStatus.COMPLETED)
    
    # За сегодня
    today = datetime.now().date()
    today_orders = [o for o in all_orders if o.created_at.date() == today]
    today_revenue = sum(o.total_amount for o in today_orders if o.status == OrderStatus.COMPLETED)
    
    text = "📈 <b>Статистика заказов</b>\n\n"
    
    text += f"📊 <b>Общая статистика:</b>\n"
    text += f"   • Всего заказов: {total_orders}\n"
    text += f"   • Новые: {new_orders}\n"
    text += f"   • В обработке: {processing_orders}\n"
    text += f"   • Выполнено: {completed_orders}\n"
    text += f"   • Отменено: {cancelled_orders}\n\n"
    
    text += f"💰 <b>Финансы:</b>\n"
    text += f"   • Общая выручка: {total_revenue:,.0f}₽\n"
    text += f"   • Средний чек: {avg_order_value:,.0f}₽\n\n"
    
    text += f"📅 <b>За последние 30 дней:</b>\n"
    text += f"   • Заказов: {len(recent_orders)}\n"
    text += f"   • Выручка: {recent_revenue:,.0f}₽\n\n"
    
    text += f"🗓 <b>Сегодня:</b>\n"
    text += f"   • Заказов: {len(today_orders)}\n"
    text += f"   • Выручка: {today_revenue:,.0f}₽"
    
    # Клавиатура
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data="admin_orders_stats")
    builder.button(text="🔙 К заказам", callback_data="admin_orders")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@orders_admin_router.callback_query(F.data.startswith("admin_contact_user_"))
async def contact_user(callback: CallbackQuery, session: AsyncSession):
    """Связаться с пользователем"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[-1])
    order = await order_crud.get(session, order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    user = await user_crud.get(session, order.user_id)
    
    contact_text = f"📞 <b>Контактная информация</b>\n\n"
    contact_text += f"👤 <b>Клиент:</b> {user.first_name or 'Не указано'}\n"
    if user.username:
        contact_text += f"🔗 <b>Username:</b> @{user.username}\n"
    contact_text += f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
    contact_text += f"📱 <b>Телефон:</b> {order.customer_phone}\n"
    contact_text += f"📍 <b>Адрес:</b> {order.delivery_address}\n\n"
    contact_text += f"💡 <i>Нажмите на ID чтобы скопировать</i>"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Написать в ЛС", url=f"tg://user?id={user.id}")
    builder.button(text="🔙 К заказу", callback_data=f"admin_order_details_{order_id}")
    builder.adjust(1)
    
    await callback.message.edit_text(
        contact_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()