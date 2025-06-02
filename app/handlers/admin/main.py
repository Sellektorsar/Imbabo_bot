"""
Главная административная панель
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings

main_admin_router = Router()


def admin_main_keyboard():
    """Главная клавиатура административной панели"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📦 Управление каталогом", callback_data="admin_catalog")
    builder.button(text="📋 Заказы", callback_data="admin_orders")
    builder.button(text="🎫 Промокоды", callback_data="admin_promo")
    builder.button(text="📢 Рассылки", callback_data="admin_mailing")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="❓ FAQ", callback_data="admin_faq")
    
    builder.adjust(2, 2, 2)
    return builder.as_markup()


@main_admin_router.message(Command("admin"))
async def admin_panel(message: Message):
    """Главная панель администратора"""
    if message.from_user.id not in settings.admin_ids_list:
        await message.answer("❌ У вас нет прав доступа к административной панели")
        return
    
    await message.answer(
        "🔧 <b>Административная панель</b>\n\n"
        f"👋 Добро пожаловать, {message.from_user.first_name}!\n"
        "Выберите раздел для управления:",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )


@main_admin_router.callback_query(F.data == "admin_main")
async def back_to_admin_main(callback: CallbackQuery):
    """Возврат к главной панели администратора"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🔧 <b>Административная панель</b>\n\n"
        f"👋 Добро пожаловать, {callback.from_user.first_name}!\n"
        "Выберите раздел для управления:",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@main_admin_router.message(Command("help_admin"))
async def admin_help(message: Message):
    """Справка по административным командам"""
    if message.from_user.id not in settings.admin_ids_list:
        await message.answer("❌ У вас нет прав доступа")
        return
    
    help_text = """
🔧 <b>Справка по административным командам</b>

<b>Основные команды:</b>
/admin - Главная панель администратора
/stats - Быстрый просмотр статистики
/help_admin - Эта справка

<b>Разделы управления:</b>
📦 <b>Каталог</b> - управление товарами и категориями
📋 <b>Заказы</b> - просмотр и обработка заказов
🎫 <b>Промокоды</b> - создание и управление скидками
📢 <b>Рассылки</b> - отправка сообщений пользователям
📊 <b>Статистика</b> - аналитика и отчеты
❓ <b>FAQ</b> - управление часто задаваемыми вопросами

<b>Быстрые действия:</b>
• Для создания нового товара: Каталог → Добавить товар
• Для просмотра новых заказов: Заказы → Новые
• Для создания рассылки: Рассылки → Создать кампанию
• Для просмотра статистики: Статистика → Общая
"""
    
    await message.answer(help_text, parse_mode="HTML")