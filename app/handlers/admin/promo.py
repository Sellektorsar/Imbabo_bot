"""
Административное управление промокодами
"""
from datetime import datetime, timedelta
from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.crud import promo_code_crud
from app.models import PromoCodeType

promo_admin_router = Router()


class PromoStates(StatesGroup):
    """Состояния для создания/редактирования промокода"""
    waiting_code = State()
    waiting_type = State()
    waiting_value = State()
    waiting_usage_limit = State()
    waiting_expiry_date = State()


def promo_menu_keyboard():
    """Клавиатура меню управления промокодами"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📋 Все промокоды", callback_data="admin_promo_all")
    builder.button(text="✅ Активные", callback_data="admin_promo_active")
    builder.button(text="❌ Неактивные", callback_data="admin_promo_inactive")
    builder.button(text="⏰ Истекшие", callback_data="admin_promo_expired")
    builder.button(text="➕ Создать промокод", callback_data="admin_promo_create")
    builder.button(text="📊 Статистика", callback_data="admin_promo_stats")
    builder.button(text="🔙 Назад", callback_data="admin_main")
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def promo_list_keyboard(promo_codes, page=0, per_page=5, filter_type=None):
    """Клавиатура со списком промокодов"""
    builder = InlineKeyboardBuilder()
    
    start = page * per_page
    end = start + per_page
    page_promos = promo_codes[start:end]
    
    for promo in page_promos:
        # Определяем статус
        now = datetime.now()
        is_expired = promo.expiry_date and promo.expiry_date < now
        is_limit_reached = promo.usage_limit and promo.usage_count >= promo.usage_limit
        
        if not promo.is_active:
            status = "❌"
        elif is_expired:
            status = "⏰"
        elif is_limit_reached:
            status = "🚫"
        else:
            status = "✅"
        
        # Формируем информацию о промокоде
        if promo.type == PromoCodeType.PERCENTAGE:
            value_text = f"{promo.value}%"
        else:
            value_text = f"{promo.value:,.0f}₽"
        
        usage_text = f"{promo.usage_count}"
        if promo.usage_limit:
            usage_text += f"/{promo.usage_limit}"
        
        builder.button(
            text=f"{status} {promo.code} ({value_text}) - {usage_text}",
            callback_data=f"admin_promo_details_{promo.id}"
        )
    
    # Пагинация
    nav_buttons = []
    if page > 0:
        callback_data = f"admin_promo_{filter_type}_page_{page-1}" if filter_type else f"admin_promo_all_page_{page-1}"
        nav_buttons.append(("⬅️ Назад", callback_data))
    if end < len(promo_codes):
        callback_data = f"admin_promo_{filter_type}_page_{page+1}" if filter_type else f"admin_promo_all_page_{page+1}"
        nav_buttons.append(("➡️ Далее", callback_data))
    
    for text, callback_data in nav_buttons:
        builder.button(text=text, callback_data=callback_data)
    
    builder.button(text="➕ Создать", callback_data="admin_promo_create")
    builder.button(text="🔙 К промокодам", callback_data="admin_promo")
    
    builder.adjust(1)
    return builder.as_markup()


def promo_actions_keyboard(promo_id, is_active):
    """Клавиатура действий с промокодом"""
    builder = InlineKeyboardBuilder()
    
    if is_active:
        builder.button(text="❌ Деактивировать", callback_data=f"admin_promo_deactivate_{promo_id}")
    else:
        builder.button(text="✅ Активировать", callback_data=f"admin_promo_activate_{promo_id}")
    
    builder.button(text="✏️ Редактировать", callback_data=f"admin_promo_edit_{promo_id}")
    builder.button(text="📊 Статистика", callback_data=f"admin_promo_usage_{promo_id}")
    builder.button(text="🗑 Удалить", callback_data=f"admin_promo_delete_{promo_id}")
    builder.button(text="🔙 К промокодам", callback_data="admin_promo")
    
    builder.adjust(2, 1, 1, 1)
    return builder.as_markup()


@promo_admin_router.callback_query(F.data == "admin_promo")
async def promo_menu(callback: CallbackQuery):
    """Главное меню управления промокодами"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🎫 <b>Управление промокодами</b>\n\n"
        "Выберите действие:",
        reply_markup=promo_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@promo_admin_router.callback_query(F.data.startswith("admin_promo_"))
async def handle_promo_actions(callback: CallbackQuery, session: AsyncSession):
    """Обработка действий с промокодами"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    action = callback.data.replace("admin_promo_", "")
    
    if action == "all":
        await show_promo_codes(callback, session, "all")
    elif action == "active":
        await show_promo_codes(callback, session, "active")
    elif action == "inactive":
        await show_promo_codes(callback, session, "inactive")
    elif action == "expired":
        await show_promo_codes(callback, session, "expired")
    elif action == "create":
        await start_create_promo(callback)
    elif action == "stats":
        await show_promo_stats(callback, session)
    elif action.startswith("details_"):
        promo_id = int(action.split("_")[1])
        await show_promo_details(callback, session, promo_id)
    elif action.startswith("activate_"):
        promo_id = int(action.split("_")[1])
        await toggle_promo_status(callback, session, promo_id, True)
    elif action.startswith("deactivate_"):
        promo_id = int(action.split("_")[1])
        await toggle_promo_status(callback, session, promo_id, False)


async def show_promo_codes(callback: CallbackQuery, session: AsyncSession, filter_type: str, page: int = 0):
    """Показать промокоды по фильтру"""
    # Получаем все промокоды
    all_promos = await promo_code_crud.get_all(session)
    
    # Фильтруем по типу
    now = datetime.now()
    filtered_promos = []
    
    for promo in all_promos:
        is_expired = promo.expiry_date and promo.expiry_date < now
        
        if filter_type == "all":
            filtered_promos.append(promo)
        elif filter_type == "active" and promo.is_active and not is_expired:
            filtered_promos.append(promo)
        elif filter_type == "inactive" and not promo.is_active:
            filtered_promos.append(promo)
        elif filter_type == "expired" and is_expired:
            filtered_promos.append(promo)
    
    # Сортируем по дате создания (новые сначала)
    filtered_promos.sort(key=lambda x: x.created_at, reverse=True)
    
    # Заголовки
    titles = {
        "all": "📋 Все промокоды",
        "active": "✅ Активные промокоды",
        "inactive": "❌ Неактивные промокоды",
        "expired": "⏰ Истекшие промокоды"
    }
    
    text = f"{titles[filter_type]}\n\n"
    if filtered_promos:
        text += f"Найдено: {len(filtered_promos)}\n"
        text += "Нажмите на промокод для управления:"
    else:
        text += "Промокоды не найдены."
    
    await callback.message.edit_text(
        text,
        reply_markup=promo_list_keyboard(filtered_promos, page, filter_type=filter_type),
        parse_mode="HTML"
    )
    await callback.answer()


async def show_promo_details(callback: CallbackQuery, session: AsyncSession, promo_id: int):
    """Показать детали промокода"""
    promo = await promo_code_crud.get(session, promo_id)
    
    if not promo:
        await callback.answer("❌ Промокод не найден", show_alert=True)
        return
    
    # Определяем статус
    now = datetime.now()
    is_expired = promo.expiry_date and promo.expiry_date < now
    is_limit_reached = promo.usage_limit and promo.usage_count >= promo.usage_limit
    
    if not promo.is_active:
        status = "❌ Неактивен"
    elif is_expired:
        status = "⏰ Истек"
    elif is_limit_reached:
        status = "🚫 Лимит исчерпан"
    else:
        status = "✅ Активен"
    
    # Формируем текст
    text = f"🎫 <b>Промокод: {promo.code}</b>\n\n"
    
    text += f"📊 <b>Статус:</b> {status}\n"
    
    if promo.type == PromoCodeType.PERCENTAGE:
        text += f"💰 <b>Скидка:</b> {promo.value}%\n"
    else:
        text += f"💰 <b>Скидка:</b> {promo.value:,.0f}₽\n"
    
    text += f"🔢 <b>Использований:</b> {promo.usage_count}"
    if promo.usage_limit:
        text += f" из {promo.usage_limit}"
    text += "\n"
    
    if promo.expiry_date:
        text += f"⏰ <b>Действует до:</b> {promo.expiry_date.strftime('%d.%m.%Y %H:%M')}\n"
    else:
        text += f"⏰ <b>Действует:</b> Бессрочно\n"
    
    text += f"🎯 <b>Только первая покупка:</b> {'Да' if promo.is_first_purchase_only else 'Нет'}\n"
    text += f"📅 <b>Создан:</b> {promo.created_at.strftime('%d.%m.%Y %H:%M')}"
    
    await callback.message.edit_text(
        text,
        reply_markup=promo_actions_keyboard(promo_id, promo.is_active),
        parse_mode="HTML"
    )
    await callback.answer()


async def toggle_promo_status(callback: CallbackQuery, session: AsyncSession, promo_id: int, new_status: bool):
    """Переключить статус промокода"""
    try:
        await promo_code_crud.update(session, promo_id, {"is_active": new_status})
        
        status_text = "активирован" if new_status else "деактивирован"
        await callback.answer(f"✅ Промокод {status_text}")
        
        # Обновляем отображение
        await show_promo_details(callback, session, promo_id)
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


async def start_create_promo(callback: CallbackQuery):
    """Начать создание промокода"""
    await callback.message.edit_text(
        "➕ <b>Создание промокода</b>\n\n"
        "Введите код промокода (латинские буквы и цифры, без пробелов):",
        parse_mode="HTML"
    )
    
    # Устанавливаем состояние FSM
    from aiogram.fsm.context import FSMContext
    # Здесь нужно получить state из контекста, но для упрощения пока оставим заглушку
    # В реальной реализации нужно передать state в функцию
    await callback.answer()


async def show_promo_stats(callback: CallbackQuery, session: AsyncSession):
    """Показать статистику промокодов"""
    all_promos = await promo_code_crud.get_all(session)
    
    # Считаем статистику
    total_promos = len(all_promos)
    active_promos = len([p for p in all_promos if p.is_active])
    
    now = datetime.now()
    expired_promos = len([p for p in all_promos if p.expiry_date and p.expiry_date < now])
    
    total_usage = sum(p.usage_count for p in all_promos)
    
    # Самые популярные промокоды
    popular_promos = sorted(all_promos, key=lambda x: x.usage_count, reverse=True)[:5]
    
    text = "📊 <b>Статистика промокодов</b>\n\n"
    
    text += f"📋 <b>Общая статистика:</b>\n"
    text += f"   • Всего промокодов: {total_promos}\n"
    text += f"   • Активных: {active_promos}\n"
    text += f"   • Истекших: {expired_promos}\n"
    text += f"   • Общее использование: {total_usage}\n\n"
    
    if popular_promos:
        text += f"🏆 <b>Популярные промокоды:</b>\n"
        for i, promo in enumerate(popular_promos, 1):
            if promo.usage_count > 0:
                text += f"   {i}. {promo.code} - {promo.usage_count} раз\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data="admin_promo_stats")
    builder.button(text="🔙 К промокодам", callback_data="admin_promo")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


# FSM обработчики для создания промокода
@promo_admin_router.message(PromoStates.waiting_code)
async def process_promo_code(message: Message, state: FSMContext):
    """Обработка кода промокода"""
    if message.from_user.id not in settings.admin_ids_list:
        return
    
    code = message.text.strip().upper()
    
    # Валидация кода
    if not code.replace('_', '').replace('-', '').isalnum():
        await message.answer("❌ Код должен содержать только латинские буквы, цифры, дефисы и подчеркивания. Попробуйте еще раз:")
        return
    
    if len(code) < 3 or len(code) > 20:
        await message.answer("❌ Код должен содержать от 3 до 20 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(code=code)
    
    # Выбор типа скидки
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Фиксированная сумма", callback_data="promo_type_fixed")
    builder.button(text="📊 Процент", callback_data="promo_type_percentage")
    builder.adjust(1)
    
    await message.answer(
        f"✅ Код: <b>{code}</b>\n\n"
        "Выберите тип скидки:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(PromoStates.waiting_type)


@promo_admin_router.callback_query(F.data.startswith("promo_type_"), PromoStates.waiting_type)
async def process_promo_type(callback: CallbackQuery, state: FSMContext):
    """Обработка типа промокода"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    promo_type = callback.data.split("_")[-1]
    type_enum = PromoCodeType.FIXED_AMOUNT if promo_type == "fixed" else PromoCodeType.PERCENTAGE
    
    await state.update_data(type=type_enum)
    
    if promo_type == "fixed":
        prompt = "Введите размер скидки в рублях (например: 500):"
    else:
        prompt = "Введите размер скидки в процентах (например: 15):"
    
    await callback.message.edit_text(
        f"✅ Тип скидки выбран\n\n{prompt}",
        parse_mode="HTML"
    )
    await state.set_state(PromoStates.waiting_value)
    await callback.answer()


@promo_admin_router.message(PromoStates.waiting_value)
async def process_promo_value(message: Message, state: FSMContext):
    """Обработка размера скидки"""
    if message.from_user.id not in settings.admin_ids_list:
        return
    
    try:
        value = Decimal(message.text.strip())
        data = await state.get_data()
        
        # Валидация значения
        if data["type"] == PromoCodeType.PERCENTAGE:
            if value <= 0 or value > 100:
                await message.answer("❌ Процент должен быть от 1 до 100. Попробуйте еще раз:")
                return
        else:
            if value <= 0:
                await message.answer("❌ Сумма должна быть больше 0. Попробуйте еще раз:")
                return
        
        await state.update_data(value=value)
        
        await message.answer(
            f"✅ Размер скидки: <b>{value}{'%' if data['type'] == PromoCodeType.PERCENTAGE else '₽'}</b>\n\n"
            "Введите лимит использований (число) или отправьте '-' для безлимитного промокода:",
            parse_mode="HTML"
        )
        await state.set_state(PromoStates.waiting_usage_limit)
        
    except (ValueError, TypeError):
        await message.answer("❌ Неверный формат числа. Попробуйте еще раз:")


@promo_admin_router.message(PromoStates.waiting_usage_limit)
async def process_promo_usage_limit(message: Message, state: FSMContext):
    """Обработка лимита использований"""
    if message.from_user.id not in settings.admin_ids_list:
        return
    
    text = message.text.strip()
    usage_limit = None
    
    if text != '-':
        try:
            usage_limit = int(text)
            if usage_limit <= 0:
                await message.answer("❌ Лимит должен быть больше 0. Попробуйте еще раз:")
                return
        except (ValueError, TypeError):
            await message.answer("❌ Введите число или '-' для безлимитного промокода:")
            return
    
    await state.update_data(usage_limit=usage_limit)
    
    limit_text = f"{usage_limit} раз" if usage_limit else "Безлимитный"
    
    # Выбор срока действия
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 1 день", callback_data="promo_expiry_1")
    builder.button(text="📅 7 дней", callback_data="promo_expiry_7")
    builder.button(text="📅 30 дней", callback_data="promo_expiry_30")
    builder.button(text="♾️ Бессрочно", callback_data="promo_expiry_never")
    builder.adjust(2)
    
    await message.answer(
        f"✅ Лимит использований: <b>{limit_text}</b>\n\n"
        "Выберите срок действия промокода:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(PromoStates.waiting_expiry_date)


@promo_admin_router.callback_query(F.data.startswith("promo_expiry_"), PromoStates.waiting_expiry_date)
async def process_promo_expiry(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка срока действия и создание промокода"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    expiry_type = callback.data.split("_")[-1]
    expiry_date = None
    
    if expiry_type != "never":
        days = int(expiry_type)
        expiry_date = datetime.now() + timedelta(days=days)
    
    # Получаем все данные
    data = await state.get_data()
    
    try:
        # Создаем промокод
        promo_data = {
            "code": data["code"],
            "type": data["type"],
            "value": data["value"],
            "usage_limit": data["usage_limit"],
            "expiry_date": expiry_date,
            "is_active": True,
            "is_first_purchase_only": True,  # По умолчанию только для первой покупки
            "usage_count": 0
        }
        
        promo = await promo_code_crud.create(session, promo_data)
        
        # Формируем сообщение об успехе
        expiry_text = expiry_date.strftime('%d.%m.%Y %H:%M') if expiry_date else "Бессрочно"
        value_text = f"{promo.value}%" if promo.type == PromoCodeType.PERCENTAGE else f"{promo.value:,.0f}₽"
        limit_text = f"{promo.usage_limit} раз" if promo.usage_limit else "Безлимитный"
        
        success_text = f"✅ <b>Промокод создан!</b>\n\n"
        success_text += f"🎫 <b>Код:</b> {promo.code}\n"
        success_text += f"💰 <b>Скидка:</b> {value_text}\n"
        success_text += f"🔢 <b>Лимит:</b> {limit_text}\n"
        success_text += f"⏰ <b>Действует до:</b> {expiry_text}\n"
        success_text += f"🎯 <b>Только первая покупка:</b> Да"
        
        await callback.message.edit_text(success_text, parse_mode="HTML")
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при создании промокода: {str(e)}")
    
    await state.clear()
    await callback.answer()