"""
Административная панель - управление FAQ
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.crud import faq_crud

faq_admin_router = Router()

logger = logging.getLogger(__name__)


class FAQStates(StatesGroup):
    """Состояния для управления FAQ"""
    waiting_question = State()
    waiting_answer = State()
    waiting_order = State()
    editing_question = State()
    editing_answer = State()
    editing_order = State()


def get_faq_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления FAQ"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Добавить FAQ", callback_data="faq_add")],
        [InlineKeyboardButton(text="📋 Список FAQ", callback_data="faq_list")],
        [InlineKeyboardButton(text="🔙 Назад в админку", callback_data="admin_main")]
    ])
    return keyboard


def get_faq_list_keyboard(faqs: list, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура со списком FAQ"""
    buttons = []
    
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_faqs = faqs[start_idx:end_idx]
    
    for faq in page_faqs:
        status_icon = "✅" if faq.is_active else "❌"
        text = f"{status_icon} {faq.question[:30]}..."
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"faq_detail_{faq.id}"
        )])
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"faq_list_{page-1}"))
    if end_idx < len(faqs):
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"faq_list_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_faq")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_faq_detail_keyboard(faq_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра FAQ"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"faq_edit_{faq_id}"),
            InlineKeyboardButton(text="🔄 Переключить статус", callback_data=f"faq_toggle_{faq_id}")
        ],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"faq_delete_{faq_id}")],
        [InlineKeyboardButton(text="🔙 К списку", callback_data="faq_list")]
    ])
    return keyboard


def get_faq_edit_keyboard(faq_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для редактирования FAQ"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❓ Вопрос", callback_data=f"faq_edit_question_{faq_id}"),
            InlineKeyboardButton(text="💬 Ответ", callback_data=f"faq_edit_answer_{faq_id}")
        ],
        [InlineKeyboardButton(text="🔢 Порядок", callback_data=f"faq_edit_order_{faq_id}")],
        [InlineKeyboardButton(text="🔙 К FAQ", callback_data=f"faq_detail_{faq_id}")]
    ])
    return keyboard


@faq_admin_router.callback_query(F.data == "admin_faq")
async def show_faq_management(callback: CallbackQuery, session: AsyncSession):
    """Показать панель управления FAQ"""
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    text = """
🔧 <b>Управление FAQ</b>

Здесь вы можете управлять часто задаваемыми вопросами:
• Добавлять новые вопросы и ответы
• Редактировать существующие
• Изменять порядок отображения
• Активировать/деактивировать вопросы
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_faq_management_keyboard(),
        parse_mode="HTML"
    )


@faq_admin_router.callback_query(F.data == "faq_add")
async def start_add_faq(callback: CallbackQuery, state: FSMContext):
    """Начать добавление FAQ"""
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    await state.set_state(FAQStates.waiting_question)
    
    text = """
📝 <b>Добавление нового FAQ</b>

Введите вопрос:
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_faq")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@faq_admin_router.message(FAQStates.waiting_question)
async def process_faq_question(message: Message, state: FSMContext):
    """Обработка вопроса FAQ"""
    await state.update_data(question=message.text)
    await state.set_state(FAQStates.waiting_answer)
    
    text = f"""
📝 <b>Добавление нового FAQ</b>

Вопрос: <i>{message.text}</i>

Теперь введите ответ:
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_faq")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@faq_admin_router.message(FAQStates.waiting_answer)
async def process_faq_answer(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ответа FAQ"""
    data = await state.get_data()
    question = data.get('question')
    
    # Получаем максимальный порядок
    all_faqs = await faq_crud.get_all(session)
    max_order = max([faq.order for faq in all_faqs], default=0)
    
    # Создаем FAQ
    faq_data = {
        'question': question,
        'answer': message.text,
        'order': max_order + 1,
        'is_active': True
    }
    
    try:
        new_faq = await faq_crud.create(session, faq_data)
        await session.commit()
        
        text = f"""
✅ <b>FAQ успешно добавлен!</b>

Вопрос: <i>{question}</i>
Ответ: <i>{message.text}</i>
Порядок: {max_order + 1}
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 К списку FAQ", callback_data="faq_list")],
            [InlineKeyboardButton(text="🔙 В админку", callback_data="admin_main")]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка создания FAQ: {e}")
        await message.answer("❌ Ошибка при создании FAQ. Попробуйте еще раз.")
    
    await state.clear()


@faq_admin_router.callback_query(F.data.startswith("faq_list"))
async def show_faq_list(callback: CallbackQuery, session: AsyncSession):
    """Показать список FAQ"""
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    # Извлекаем номер страницы
    parts = callback.data.split("_")
    page = int(parts[2]) if len(parts) > 2 else 0
    
    faqs = await faq_crud.get_all(session)
    
    if not faqs:
        text = "📋 <b>Список FAQ пуст</b>\n\nДобавьте первый вопрос!"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Добавить FAQ", callback_data="faq_add")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_faq")]
        ])
    else:
        text = f"📋 <b>Список FAQ</b> (всего: {len(faqs)})\n\n"
        keyboard = get_faq_list_keyboard(faqs, page)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@faq_admin_router.callback_query(F.data.startswith("faq_detail_"))
async def show_faq_detail(callback: CallbackQuery, session: AsyncSession):
    """Показать детали FAQ"""
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    faq_id = int(callback.data.split("_")[2])
    faq = await faq_crud.get_by_id(session, faq_id)
    
    if not faq:
        await callback.answer("❌ FAQ не найден")
        return
    
    status = "✅ Активен" if faq.is_active else "❌ Неактивен"
    
    text = f"""
📋 <b>FAQ #{faq.id}</b>

<b>Вопрос:</b>
{faq.question}

<b>Ответ:</b>
{faq.answer}

<b>Порядок:</b> {faq.order}
<b>Статус:</b> {status}
<b>Создан:</b> {faq.created_at.strftime('%d.%m.%Y %H:%M')}
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_faq_detail_keyboard(faq_id),
        parse_mode="HTML"
    )


@faq_admin_router.callback_query(F.data.startswith("faq_toggle_"))
async def toggle_faq_status(callback: CallbackQuery, session: AsyncSession):
    """Переключить статус FAQ"""
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    faq_id = int(callback.data.split("_")[2])
    faq = await faq_crud.get_by_id(session, faq_id)
    
    if not faq:
        await callback.answer("❌ FAQ не найден")
        return
    
    # Переключаем статус
    await faq_crud.update(session, faq_id, {'is_active': not faq.is_active})
    await session.commit()
    
    status = "активирован" if not faq.is_active else "деактивирован"
    await callback.answer(f"✅ FAQ {status}")
    
    # Обновляем отображение
    await show_faq_detail(callback, session)


@faq_admin_router.callback_query(F.data.startswith("faq_delete_"))
async def delete_faq(callback: CallbackQuery, session: AsyncSession):
    """Удалить FAQ"""
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    faq_id = int(callback.data.split("_")[2])
    
    try:
        await faq_crud.delete(session, faq_id)
        await session.commit()
        
        await callback.answer("✅ FAQ удален")
        
        # Возвращаемся к списку
        await show_faq_list(callback, session)
        
    except Exception as e:
        logger.error(f"Ошибка удаления FAQ: {e}")
        await callback.answer("❌ Ошибка при удалении FAQ")


@faq_admin_router.callback_query(F.data.startswith("faq_edit_"))
async def show_faq_edit_menu(callback: CallbackQuery, session: AsyncSession):
    """Показать меню редактирования FAQ"""
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    faq_id = int(callback.data.split("_")[2])
    faq = await faq_crud.get_by_id(session, faq_id)
    
    if not faq:
        await callback.answer("❌ FAQ не найден")
        return
    
    text = f"""
✏️ <b>Редактирование FAQ #{faq.id}</b>

<b>Текущий вопрос:</b>
{faq.question}

<b>Текущий ответ:</b>
{faq.answer}

<b>Порядок:</b> {faq.order}

Что хотите изменить?
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_faq_edit_keyboard(faq_id),
        parse_mode="HTML"
    )


@faq_admin_router.callback_query(F.data.startswith("faq_edit_question_"))
async def start_edit_question(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование вопроса"""
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    faq_id = int(callback.data.split("_")[3])
    await state.update_data(faq_id=faq_id)
    await state.set_state(FAQStates.editing_question)
    
    text = """
✏️ <b>Редактирование вопроса</b>

Введите новый вопрос:
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"faq_edit_{faq_id}")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@faq_admin_router.message(FAQStates.editing_question)
async def process_edit_question(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка нового вопроса"""
    data = await state.get_data()
    faq_id = data.get('faq_id')
    
    try:
        await faq_crud.update(session, faq_id, {'question': message.text})
        await session.commit()
        
        await message.answer("✅ Вопрос обновлен!")
        await state.clear()
        
        # Показываем обновленный FAQ
        callback_data = f"faq_detail_{faq_id}"
        fake_callback = type('obj', (object,), {
            'data': callback_data,
            'message': message,
            'from_user': message.from_user
        })
        await show_faq_detail(fake_callback, session)
        
    except Exception as e:
        logger.error(f"Ошибка обновления вопроса: {e}")
        await message.answer("❌ Ошибка при обновлении вопроса")
        await state.clear()


@faq_admin_router.callback_query(F.data.startswith("faq_edit_answer_"))
async def start_edit_answer(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование ответа"""
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    faq_id = int(callback.data.split("_")[3])
    await state.update_data(faq_id=faq_id)
    await state.set_state(FAQStates.editing_answer)
    
    text = """
✏️ <b>Редактирование ответа</b>

Введите новый ответ:
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"faq_edit_{faq_id}")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@faq_admin_router.message(FAQStates.editing_answer)
async def process_edit_answer(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка нового ответа"""
    data = await state.get_data()
    faq_id = data.get('faq_id')
    
    try:
        await faq_crud.update(session, faq_id, {'answer': message.text})
        await session.commit()
        
        await message.answer("✅ Ответ обновлен!")
        await state.clear()
        
        # Показываем обновленный FAQ
        callback_data = f"faq_detail_{faq_id}"
        fake_callback = type('obj', (object,), {
            'data': callback_data,
            'message': message,
            'from_user': message.from_user
        })
        await show_faq_detail(fake_callback, session)
        
    except Exception as e:
        logger.error(f"Ошибка обновления ответа: {e}")
        await message.answer("❌ Ошибка при обновлении ответа")
        await state.clear()


@faq_admin_router.callback_query(F.data.startswith("faq_edit_order_"))
async def start_edit_order(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование порядка"""
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    faq_id = int(callback.data.split("_")[3])
    await state.update_data(faq_id=faq_id)
    await state.set_state(FAQStates.editing_order)
    
    text = """
✏️ <b>Редактирование порядка</b>

Введите новый порядок (число):
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"faq_edit_{faq_id}")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@faq_admin_router.message(FAQStates.editing_order)
async def process_edit_order(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка нового порядка"""
    data = await state.get_data()
    faq_id = data.get('faq_id')
    
    try:
        order = int(message.text)
        await faq_crud.update(session, faq_id, {'order': order})
        await session.commit()
        
        await message.answer("✅ Порядок обновлен!")
        await state.clear()
        
        # Показываем обновленный FAQ
        callback_data = f"faq_detail_{faq_id}"
        fake_callback = type('obj', (object,), {
            'data': callback_data,
            'message': message,
            'from_user': message.from_user
        })
        await show_faq_detail(fake_callback, session)
        
    except ValueError:
        await message.answer("❌ Введите корректное число")
    except Exception as e:
        logger.error(f"Ошибка обновления порядка: {e}")
        await message.answer("❌ Ошибка при обновлении порядка")
        await state.clear()