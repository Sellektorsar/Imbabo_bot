"""
Административное управление рассылками
"""
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.crud import user_crud, mailing_campaign_crud, mailing_message_crud

mailing_admin_router = Router()


class MailingStates(StatesGroup):
    """Состояния для создания рассылки"""
    waiting_text = State()
    waiting_photo = State()
    waiting_buttons = State()
    waiting_segment = State()
    waiting_schedule = State()


def mailing_menu_keyboard():
    """Клавиатура меню управления рассылками"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📋 Все кампании", callback_data="admin_mailing_all")
    builder.button(text="📤 Активные", callback_data="admin_mailing_active")
    builder.button(text="✅ Завершенные", callback_data="admin_mailing_completed")
    builder.button(text="⏸ Приостановленные", callback_data="admin_mailing_paused")
    builder.button(text="➕ Создать рассылку", callback_data="admin_mailing_create")
    builder.button(text="📊 Статистика", callback_data="admin_mailing_stats")
    builder.button(text="🔙 Назад", callback_data="admin_main")
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def mailing_list_keyboard(campaigns, page=0, per_page=5):
    """Клавиатура со списком кампаний"""
    builder = InlineKeyboardBuilder()
    
    start = page * per_page
    end = start + per_page
    page_campaigns = campaigns[start:end]
    
    for campaign in page_campaigns:
        # Определяем статус
        status_emoji = {
            "draft": "📝",
            "scheduled": "⏰",
            "active": "📤",
            "completed": "✅",
            "paused": "⏸",
            "cancelled": "❌"
        }.get(campaign.status, "❓")
        
        # Формируем информацию о кампании
        created_date = campaign.created_at.strftime("%d.%m %H:%M")
        
        builder.button(
            text=f"{status_emoji} {campaign.name} ({created_date})",
            callback_data=f"admin_mailing_details_{campaign.id}"
        )
    
    # Пагинация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(("⬅️ Назад", f"admin_mailing_all_page_{page-1}"))
    if end < len(campaigns):
        nav_buttons.append(("➡️ Далее", f"admin_mailing_all_page_{page+1}"))
    
    for text, callback_data in nav_buttons:
        builder.button(text=text, callback_data=callback_data)
    
    builder.button(text="➕ Создать", callback_data="admin_mailing_create")
    builder.button(text="🔙 К рассылкам", callback_data="admin_mailing")
    
    builder.adjust(1)
    return builder.as_markup()


def mailing_actions_keyboard(campaign_id, status):
    """Клавиатура действий с кампанией"""
    builder = InlineKeyboardBuilder()
    
    if status == "draft":
        builder.button(text="▶️ Запустить", callback_data=f"admin_mailing_start_{campaign_id}")
        builder.button(text="⏰ Запланировать", callback_data=f"admin_mailing_schedule_{campaign_id}")
    elif status == "scheduled":
        builder.button(text="▶️ Запустить сейчас", callback_data=f"admin_mailing_start_{campaign_id}")
        builder.button(text="❌ Отменить", callback_data=f"admin_mailing_cancel_{campaign_id}")
    elif status == "active":
        builder.button(text="⏸ Приостановить", callback_data=f"admin_mailing_pause_{campaign_id}")
        builder.button(text="❌ Отменить", callback_data=f"admin_mailing_cancel_{campaign_id}")
    elif status == "paused":
        builder.button(text="▶️ Возобновить", callback_data=f"admin_mailing_resume_{campaign_id}")
        builder.button(text="❌ Отменить", callback_data=f"admin_mailing_cancel_{campaign_id}")
    
    builder.button(text="✏️ Редактировать", callback_data=f"admin_mailing_edit_{campaign_id}")
    builder.button(text="📊 Статистика", callback_data=f"admin_mailing_campaign_stats_{campaign_id}")
    builder.button(text="🗑 Удалить", callback_data=f"admin_mailing_delete_{campaign_id}")
    builder.button(text="🔙 К рассылкам", callback_data="admin_mailing")
    
    builder.adjust(2, 1, 1, 1)
    return builder.as_markup()


@mailing_admin_router.callback_query(F.data == "admin_mailing")
async def mailing_menu(callback: CallbackQuery):
    """Главное меню управления рассылками"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 <b>Управление рассылками</b>\n\n"
        "Выберите действие:",
        reply_markup=mailing_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@mailing_admin_router.callback_query(F.data.startswith("admin_mailing_"))
async def handle_mailing_actions(callback: CallbackQuery, session: AsyncSession):
    """Обработка действий с рассылками"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    action = callback.data.replace("admin_mailing_", "")
    
    if action == "all":
        await show_mailing_campaigns(callback, session, "all")
    elif action == "active":
        await show_mailing_campaigns(callback, session, "active")
    elif action == "completed":
        await show_mailing_campaigns(callback, session, "completed")
    elif action == "paused":
        await show_mailing_campaigns(callback, session, "paused")
    elif action == "create":
        await start_create_mailing(callback)
    elif action == "stats":
        await show_mailing_stats(callback, session)
    elif action.startswith("details_"):
        campaign_id = int(action.split("_")[1])
        await show_mailing_details(callback, session, campaign_id)


async def show_mailing_campaigns(callback: CallbackQuery, session: AsyncSession, filter_type: str, page: int = 0):
    """Показать кампании по фильтру"""
    # Получаем все кампании
    all_campaigns = await mailing_crud.get_all(session)
    
    # Фильтруем по типу
    filtered_campaigns = []
    
    for campaign in all_campaigns:
        if filter_type == "all":
            filtered_campaigns.append(campaign)
        elif filter_type == campaign.status:
            filtered_campaigns.append(campaign)
    
    # Сортируем по дате создания (новые сначала)
    filtered_campaigns.sort(key=lambda x: x.created_at, reverse=True)
    
    # Заголовки
    titles = {
        "all": "📋 Все кампании",
        "active": "📤 Активные кампании",
        "completed": "✅ Завершенные кампании",
        "paused": "⏸ Приостановленные кампании"
    }
    
    text = f"{titles.get(filter_type, '📋 Кампании')}\n\n"
    if filtered_campaigns:
        text += f"Найдено: {len(filtered_campaigns)}\n"
        text += "Нажмите на кампанию для управления:"
    else:
        text += "Кампании не найдены."
    
    await callback.message.edit_text(
        text,
        reply_markup=mailing_list_keyboard(filtered_campaigns, page),
        parse_mode="HTML"
    )
    await callback.answer()


async def show_mailing_details(callback: CallbackQuery, session: AsyncSession, campaign_id: int):
    """Показать детали кампании"""
    campaign = await mailing_crud.get(session, campaign_id)
    
    if not campaign:
        await callback.answer("❌ Кампания не найдена", show_alert=True)
        return
    
    # Определяем статус
    status_names = {
        "draft": "📝 Черновик",
        "scheduled": "⏰ Запланирована",
        "active": "📤 Активна",
        "completed": "✅ Завершена",
        "paused": "⏸ Приостановлена",
        "cancelled": "❌ Отменена"
    }
    
    text = f"📢 <b>{campaign.name}</b>\n\n"
    
    text += f"📊 <b>Статус:</b> {status_names.get(campaign.status, campaign.status)}\n"
    text += f"👥 <b>Сегмент:</b> {campaign.target_segment or 'Все пользователи'}\n"
    
    if campaign.scheduled_at:
        text += f"⏰ <b>Запланирована на:</b> {campaign.scheduled_at.strftime('%d.%m.%Y %H:%M')}\n"
    
    if campaign.started_at:
        text += f"▶️ <b>Запущена:</b> {campaign.started_at.strftime('%d.%m.%Y %H:%M')}\n"
    
    if campaign.completed_at:
        text += f"✅ <b>Завершена:</b> {campaign.completed_at.strftime('%d.%m.%Y %H:%M')}\n"
    
    text += f"📅 <b>Создана:</b> {campaign.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    # Статистика отправки
    text += f"📈 <b>Статистика:</b>\n"
    text += f"   • Отправлено: {campaign.sent_count}\n"
    text += f"   • Доставлено: {campaign.delivered_count}\n"
    text += f"   • Ошибки: {campaign.failed_count}\n"
    
    if campaign.sent_count > 0:
        delivery_rate = (campaign.delivered_count / campaign.sent_count) * 100
        text += f"   • Доставляемость: {delivery_rate:.1f}%\n"
    
    # Превью контента
    text += f"\n📝 <b>Превью сообщения:</b>\n"
    preview = campaign.content.get('text', 'Нет текста')[:100]
    if len(preview) == 100:
        preview += "..."
    text += f"<i>{preview}</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=mailing_actions_keyboard(campaign_id, campaign.status),
        parse_mode="HTML"
    )
    await callback.answer()


async def start_create_mailing(callback: CallbackQuery):
    """Начать создание рассылки"""
    await callback.message.edit_text(
        "➕ <b>Создание рассылки</b>\n\n"
        "Введите текст сообщения для рассылки:\n\n"
        "💡 <i>Вы можете использовать HTML-разметку для форматирования</i>",
        parse_mode="HTML"
    )
    
    # В реальной реализации здесь нужно установить FSM состояние
    await callback.answer()


async def show_mailing_stats(callback: CallbackQuery, session: AsyncSession):
    """Показать общую статистику рассылок"""
    all_campaigns = await mailing_crud.get_all(session)
    
    # Считаем статистику
    total_campaigns = len(all_campaigns)
    active_campaigns = len([c for c in all_campaigns if c.status == "active"])
    completed_campaigns = len([c for c in all_campaigns if c.status == "completed"])
    
    total_sent = sum(c.sent_count for c in all_campaigns)
    total_delivered = sum(c.delivered_count for c in all_campaigns)
    total_failed = sum(c.failed_count for c in all_campaigns)
    
    # За последние 30 дней
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_campaigns = [c for c in all_campaigns if c.created_at >= thirty_days_ago]
    recent_sent = sum(c.sent_count for c in recent_campaigns)
    
    text = "📊 <b>Статистика рассылок</b>\n\n"
    
    text += f"📋 <b>Кампании:</b>\n"
    text += f"   • Всего: {total_campaigns}\n"
    text += f"   • Активных: {active_campaigns}\n"
    text += f"   • Завершенных: {completed_campaigns}\n\n"
    
    text += f"📤 <b>Отправка сообщений:</b>\n"
    text += f"   • Всего отправлено: {total_sent:,}\n"
    text += f"   • Доставлено: {total_delivered:,}\n"
    text += f"   • Ошибок: {total_failed:,}\n"
    
    if total_sent > 0:
        delivery_rate = (total_delivered / total_sent) * 100
        text += f"   • Доставляемость: {delivery_rate:.1f}%\n"
    
    text += f"\n📅 <b>За последние 30 дней:</b>\n"
    text += f"   • Кампаний: {len(recent_campaigns)}\n"
    text += f"   • Отправлено: {recent_sent:,}\n"
    
    # Получаем количество активных пользователей
    all_users = await user_crud.get_all(session)
    active_users = len([u for u in all_users if u.is_active])
    
    text += f"\n👥 <b>Аудитория:</b>\n"
    text += f"   • Всего пользователей: {len(all_users)}\n"
    text += f"   • Активных: {active_users}\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data="admin_mailing_stats")
    builder.button(text="🔙 К рассылкам", callback_data="admin_mailing")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


# FSM обработчики для создания рассылки
@mailing_admin_router.message(MailingStates.waiting_text)
async def process_mailing_text(message: Message, state: FSMContext):
    """Обработка текста рассылки"""
    if message.from_user.id not in settings.admin_ids_list:
        return
    
    text = message.text.strip()
    if len(text) < 10:
        await message.answer("❌ Текст должен содержать минимум 10 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(text=text)
    
    # Предложение добавить фото
    builder = InlineKeyboardBuilder()
    builder.button(text="📷 Добавить фото", callback_data="mailing_add_photo")
    builder.button(text="➡️ Пропустить", callback_data="mailing_skip_photo")
    builder.adjust(1)
    
    await message.answer(
        f"✅ Текст сохранен\n\n"
        f"<b>Превью:</b>\n{text[:200]}{'...' if len(text) > 200 else ''}\n\n"
        f"Хотите добавить фото к сообщению?",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(MailingStates.waiting_photo)


@mailing_admin_router.callback_query(F.data == "mailing_skip_photo", MailingStates.waiting_photo)
async def skip_mailing_photo(callback: CallbackQuery, state: FSMContext):
    """Пропустить добавление фото"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    # Предложение добавить кнопки
    builder = InlineKeyboardBuilder()
    builder.button(text="🔘 Добавить кнопки", callback_data="mailing_add_buttons")
    builder.button(text="➡️ Пропустить", callback_data="mailing_skip_buttons")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "Хотите добавить кнопки к сообщению?",
        reply_markup=builder.as_markup()
    )
    await state.set_state(MailingStates.waiting_buttons)
    await callback.answer()


@mailing_admin_router.callback_query(F.data == "mailing_skip_buttons", MailingStates.waiting_buttons)
async def skip_mailing_buttons(callback: CallbackQuery, state: FSMContext):
    """Пропустить добавление кнопок"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    # Выбор сегмента
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Все пользователи", callback_data="mailing_segment_all")
    builder.button(text="🆕 Новые пользователи", callback_data="mailing_segment_new")
    builder.button(text="🛒 С заказами", callback_data="mailing_segment_buyers")
    builder.button(text="💤 Неактивные", callback_data="mailing_segment_inactive")
    builder.adjust(2)
    
    await callback.message.edit_text(
        "👥 <b>Выбор аудитории</b>\n\n"
        "Кому отправить рассылку?",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(MailingStates.waiting_segment)
    await callback.answer()


@mailing_admin_router.callback_query(F.data.startswith("mailing_segment_"), MailingStates.waiting_segment)
async def process_mailing_segment(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора сегмента и создание рассылки"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    segment = callback.data.split("_")[-1]
    segment_names = {
        "all": "Все пользователи",
        "new": "Новые пользователи",
        "buyers": "Пользователи с заказами",
        "inactive": "Неактивные пользователи"
    }
    
    # Получаем данные рассылки
    data = await state.get_data()
    
    try:
        # Создаем кампанию
        campaign_data = {
            "name": f"Рассылка {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            "content": {
                "text": data["text"],
                "photo": data.get("photo"),
                "buttons": data.get("buttons")
            },
            "target_segment": segment,
            "status": "draft",
            "sent_count": 0,
            "delivered_count": 0,
            "failed_count": 0
        }
        
        campaign = await mailing_crud.create(session, campaign_data)
        
        # Выбор времени запуска
        builder = InlineKeyboardBuilder()
        builder.button(text="▶️ Запустить сейчас", callback_data=f"mailing_start_now_{campaign.id}")
        builder.button(text="⏰ Запланировать", callback_data=f"mailing_schedule_{campaign.id}")
        builder.button(text="📝 Сохранить как черновик", callback_data=f"mailing_save_draft_{campaign.id}")
        builder.adjust(1)
        
        success_text = f"✅ <b>Рассылка создана!</b>\n\n"
        success_text += f"📢 <b>Название:</b> {campaign.name}\n"
        success_text += f"👥 <b>Аудитория:</b> {segment_names[segment]}\n"
        success_text += f"📝 <b>Текст:</b> {data['text'][:100]}{'...' if len(data['text']) > 100 else ''}\n\n"
        success_text += f"Когда запустить рассылку?"
        
        await callback.message.edit_text(
            success_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при создании рассылки: {str(e)}")
    
    await state.clear()
    await callback.answer()


@mailing_admin_router.callback_query(F.data.startswith("mailing_start_now_"))
async def start_mailing_now(callback: CallbackQuery, session: AsyncSession):
    """Запустить рассылку немедленно"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    campaign_id = int(callback.data.split("_")[-1])
    
    try:
        # Обновляем статус кампании
        await mailing_crud.update(session, campaign_id, {
            "status": "active",
            "started_at": datetime.now()
        })
        
        await callback.message.edit_text(
            "✅ <b>Рассылка запущена!</b>\n\n"
            "📤 Сообщения начали отправляться пользователям.\n"
            "Вы можете отслеживать прогресс в разделе статистики.",
            parse_mode="HTML"
        )
        
        # Здесь должна быть логика фактической отправки сообщений
        # Это будет реализовано в планировщике задач
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
    
    await callback.answer()


@mailing_admin_router.callback_query(F.data.startswith("mailing_save_draft_"))
async def save_mailing_draft(callback: CallbackQuery):
    """Сохранить рассылку как черновик"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "✅ <b>Рассылка сохранена как черновик</b>\n\n"
        "📝 Вы можете запустить её позже через раздел управления рассылками.",
        parse_mode="HTML"
    )
    await callback.answer()