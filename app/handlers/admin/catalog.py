"""
Административное управление каталогом товаров
"""
from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.crud import category_crud, product_crud

catalog_admin_router = Router()


class CategoryStates(StatesGroup):
    """Состояния для создания/редактирования категории"""
    waiting_name = State()
    waiting_description = State()


class ProductStates(StatesGroup):
    """Состояния для создания/редактирования товара"""
    waiting_category = State()
    waiting_name = State()
    waiting_description = State()
    waiting_metaphoric_description = State()
    waiting_price = State()
    waiting_photo = State()
    waiting_gender = State()
    waiting_style = State()


def catalog_menu_keyboard():
    """Клавиатура меню управления каталогом"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📂 Категории", callback_data="admin_categories")
    builder.button(text="📦 Товары", callback_data="admin_products")
    builder.button(text="➕ Добавить категорию", callback_data="admin_add_category")
    builder.button(text="➕ Добавить товар", callback_data="admin_add_product")
    builder.button(text="🔙 Назад", callback_data="admin_main")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def categories_keyboard(categories):
    """Клавиатура со списком категорий"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        status = "✅" if category.is_active else "❌"
        builder.button(
            text=f"{status} {category.name}",
            callback_data=f"admin_category_{category.id}"
        )
    
    builder.button(text="➕ Добавить категорию", callback_data="admin_add_category")
    builder.button(text="🔙 Назад", callback_data="admin_catalog")
    
    builder.adjust(1)
    return builder.as_markup()


def category_actions_keyboard(category_id):
    """Клавиатура действий с категорией"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✏️ Редактировать", callback_data=f"admin_edit_category_{category_id}")
    builder.button(text="🔄 Переключить статус", callback_data=f"admin_toggle_category_{category_id}")
    builder.button(text="📦 Товары в категории", callback_data=f"admin_category_products_{category_id}")
    builder.button(text="🗑 Удалить", callback_data=f"admin_delete_category_{category_id}")
    builder.button(text="🔙 К категориям", callback_data="admin_categories")
    
    builder.adjust(2, 1, 1, 1)
    return builder.as_markup()


def products_keyboard(products, page=0, per_page=10):
    """Клавиатура со списком товаров с пагинацией"""
    builder = InlineKeyboardBuilder()
    
    start = page * per_page
    end = start + per_page
    page_products = products[start:end]
    
    for product in page_products:
        status = "✅" if product.is_available else "❌"
        price = f"{product.price:,.0f}₽"
        builder.button(
            text=f"{status} {product.name} - {price}",
            callback_data=f"admin_product_{product.id}"
        )
    
    # Пагинация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(("⬅️ Назад", f"admin_products_page_{page-1}"))
    if end < len(products):
        nav_buttons.append(("➡️ Далее", f"admin_products_page_{page+1}"))
    
    for text, callback_data in nav_buttons:
        builder.button(text=text, callback_data=callback_data)
    
    builder.button(text="➕ Добавить товар", callback_data="admin_add_product")
    builder.button(text="🔙 Назад", callback_data="admin_catalog")
    
    builder.adjust(1)
    return builder.as_markup()


@catalog_admin_router.callback_query(F.data == "admin_catalog")
async def catalog_menu(callback: CallbackQuery):
    """Главное меню управления каталогом"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📦 <b>Управление каталогом</b>\n\n"
        "Выберите действие:",
        reply_markup=catalog_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@catalog_admin_router.callback_query(F.data == "admin_categories")
async def show_categories(callback: CallbackQuery, session: AsyncSession):
    """Показать список категорий"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    categories = await category_crud.get_all(session)
    
    text = "📂 <b>Категории товаров</b>\n\n"
    if categories:
        text += f"Всего категорий: {len(categories)}\n"
        text += "Нажмите на категорию для управления:"
    else:
        text += "Категории не найдены. Создайте первую категорию."
    
    await callback.message.edit_text(
        text,
        reply_markup=categories_keyboard(categories),
        parse_mode="HTML"
    )
    await callback.answer()


@catalog_admin_router.callback_query(F.data.startswith("admin_category_"))
async def show_category_details(callback: CallbackQuery, session: AsyncSession):
    """Показать детали категории"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[-1])
    category = await category_crud.get(session, category_id)
    
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    # Получаем количество товаров в категории
    products = await product_crud.get_by_category(session, category_id)
    products_count = len(products)
    
    status = "Активна" if category.is_active else "Неактивна"
    
    text = f"📂 <b>{category.name}</b>\n\n"
    text += f"📝 <b>Описание:</b> {category.description or 'Не указано'}\n"
    text += f"📊 <b>Статус:</b> {status}\n"
    text += f"📦 <b>Товаров:</b> {products_count}\n"
    text += f"🔢 <b>Порядок:</b> {category.sort_order}\n"
    text += f"📅 <b>Создана:</b> {category.created_at.strftime('%d.%m.%Y %H:%M')}"
    
    await callback.message.edit_text(
        text,
        reply_markup=category_actions_keyboard(category_id),
        parse_mode="HTML"
    )
    await callback.answer()


@catalog_admin_router.callback_query(F.data == "admin_add_category")
async def start_add_category(callback: CallbackQuery, state: FSMContext):
    """Начать создание новой категории"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "➕ <b>Создание новой категории</b>\n\n"
        "Введите название категории:",
        parse_mode="HTML"
    )
    await state.set_state(CategoryStates.waiting_name)
    await callback.answer()


@catalog_admin_router.message(CategoryStates.waiting_name)
async def process_category_name(message: Message, state: FSMContext):
    """Обработка названия категории"""
    if message.from_user.id not in settings.admin_ids_list:
        return
    
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Название должно содержать минимум 2 символа. Попробуйте еще раз:")
        return
    
    await state.update_data(name=name)
    await message.answer(
        f"✅ Название: <b>{name}</b>\n\n"
        "Теперь введите описание категории (или отправьте '-' чтобы пропустить):",
        parse_mode="HTML"
    )
    await state.set_state(CategoryStates.waiting_description)


@catalog_admin_router.message(CategoryStates.waiting_description)
async def process_category_description(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка описания категории и создание"""
    if message.from_user.id not in settings.admin_ids_list:
        return
    
    description = message.text.strip() if message.text.strip() != '-' else None
    data = await state.get_data()
    
    try:
        # Получаем максимальный sort_order
        categories = await category_crud.get_all(session)
        max_sort_order = max([cat.sort_order for cat in categories], default=0)
        
        category = await category_crud.create(session, {
            "name": data["name"],
            "description": description,
            "is_active": True,
            "sort_order": max_sort_order + 1
        })
        
        await message.answer(
            f"✅ <b>Категория создана!</b>\n\n"
            f"📂 <b>Название:</b> {category.name}\n"
            f"📝 <b>Описание:</b> {category.description or 'Не указано'}\n"
            f"🔢 <b>Порядок:</b> {category.sort_order}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании категории: {str(e)}")
    
    await state.clear()


@catalog_admin_router.callback_query(F.data.startswith("admin_toggle_category_"))
async def toggle_category_status(callback: CallbackQuery, session: AsyncSession):
    """Переключить статус активности категории"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[-1])
    category = await category_crud.get(session, category_id)
    
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    # Переключаем статус
    new_status = not category.is_active
    await category_crud.update(session, category_id, {"is_active": new_status})
    
    status_text = "активирована" if new_status else "деактивирована"
    await callback.answer(f"✅ Категория {status_text}")
    
    # Обновляем отображение
    await show_category_details(callback, session)


@catalog_admin_router.callback_query(F.data == "admin_products")
async def show_products(callback: CallbackQuery, session: AsyncSession):
    """Показать список товаров"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    products = await product_crud.get_all(session)
    
    text = "📦 <b>Товары</b>\n\n"
    if products:
        text += f"Всего товаров: {len(products)}\n"
        text += "Нажмите на товар для управления:"
    else:
        text += "Товары не найдены. Создайте первый товар."
    
    await callback.message.edit_text(
        text,
        reply_markup=products_keyboard(products),
        parse_mode="HTML"
    )
    await callback.answer()


@catalog_admin_router.callback_query(F.data == "admin_add_product")
async def start_add_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начать создание нового товара"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    # Получаем список активных категорий
    categories = await category_crud.get_active(session)
    
    if not categories:
        await callback.answer("❌ Сначала создайте категорию", show_alert=True)
        return
    
    # Создаем клавиатуру с категориями
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category.name,
            callback_data=f"admin_select_category_{category.id}"
        )
    builder.adjust(1)
    
    await callback.message.edit_text(
        "➕ <b>Создание нового товара</b>\n\n"
        "Выберите категорию для товара:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(ProductStates.waiting_category)
    await callback.answer()


@catalog_admin_router.callback_query(F.data.startswith("admin_select_category_"), ProductStates.waiting_category)
async def process_product_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора категории для товара"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[-1])
    category = await category_crud.get(session, category_id)
    
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    await state.update_data(category_id=category_id, category_name=category.name)
    
    await callback.message.edit_text(
        f"✅ Категория: <b>{category.name}</b>\n\n"
        "Теперь введите название товара:",
        parse_mode="HTML"
    )
    await state.set_state(ProductStates.waiting_name)
    await callback.answer()


@catalog_admin_router.message(ProductStates.waiting_name)
async def process_product_name(message: Message, state: FSMContext):
    """Обработка названия товара"""
    if message.from_user.id not in settings.admin_ids_list:
        return
    
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Название должно содержать минимум 2 символа. Попробуйте еще раз:")
        return
    
    await state.update_data(name=name)
    await message.answer(
        f"✅ Название: <b>{name}</b>\n\n"
        "Введите обычное описание товара:",
        parse_mode="HTML"
    )
    await state.set_state(ProductStates.waiting_description)


@catalog_admin_router.message(ProductStates.waiting_description)
async def process_product_description(message: Message, state: FSMContext):
    """Обработка описания товара"""
    if message.from_user.id not in settings.admin_ids_list:
        return
    
    description = message.text.strip()
    await state.update_data(description=description)
    
    await message.answer(
        f"✅ Описание сохранено\n\n"
        "Теперь введите <b>метафорическое описание</b> товара "
        "(эмоциональное, для создания желания):",
        parse_mode="HTML"
    )
    await state.set_state(ProductStates.waiting_metaphoric_description)


@catalog_admin_router.message(ProductStates.waiting_metaphoric_description)
async def process_product_metaphoric_description(message: Message, state: FSMContext):
    """Обработка метафорического описания товара"""
    if message.from_user.id not in settings.admin_ids_list:
        return
    
    metaphoric_description = message.text.strip()
    await state.update_data(metaphoric_description=metaphoric_description)
    
    await message.answer(
        f"✅ Метафорическое описание сохранено\n\n"
        "Введите цену товара (в рублях, только число):",
        parse_mode="HTML"
    )
    await state.set_state(ProductStates.waiting_price)


@catalog_admin_router.message(ProductStates.waiting_price)
async def process_product_price(message: Message, state: FSMContext):
    """Обработка цены товара"""
    if message.from_user.id not in settings.admin_ids_list:
        return
    
    try:
        price = Decimal(message.text.strip())
        if price <= 0:
            raise ValueError("Цена должна быть больше 0")
        
        await state.update_data(price=price)
        
        # Создаем клавиатуру для выбора пола
        builder = InlineKeyboardBuilder()
        builder.button(text="👨 Мужской", callback_data="admin_gender_male")
        builder.button(text="👩 Женский", callback_data="admin_gender_female")
        builder.button(text="👫 Унисекс", callback_data="admin_gender_unisex")
        builder.adjust(1)
        
        await message.answer(
            f"✅ Цена: <b>{price:,.0f}₽</b>\n\n"
            "Выберите пол для товара:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await state.set_state(ProductStates.waiting_gender)
        
    except (ValueError, TypeError):
        await message.answer("❌ Неверный формат цены. Введите число (например: 15000):")


@catalog_admin_router.callback_query(F.data.startswith("admin_gender_"), ProductStates.waiting_gender)
async def process_product_gender(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора пола для товара"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    gender = callback.data.split("_")[-1]
    gender_names = {"male": "Мужской", "female": "Женский", "unisex": "Унисекс"}
    
    await state.update_data(gender=gender)
    
    # Создаем клавиатуру для выбора стиля
    builder = InlineKeyboardBuilder()
    builder.button(text="🕶️ Classic", callback_data="admin_style_classic")
    builder.button(text="🏃 Sport", callback_data="admin_style_sport")
    builder.button(text="👗 Fashion", callback_data="admin_style_fashion")
    builder.button(text="💼 Business", callback_data="admin_style_business")
    builder.adjust(2)
    
    await callback.message.edit_text(
        f"✅ Пол: <b>{gender_names[gender]}</b>\n\n"
        "Выберите стиль товара:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(ProductStates.waiting_style)
    await callback.answer()


@catalog_admin_router.callback_query(F.data.startswith("admin_style_"), ProductStates.waiting_style)
async def process_product_style(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора стиля и создание товара"""
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    style = callback.data.split("_")[-1]
    await state.update_data(style=style)
    
    # Получаем все данные
    data = await state.get_data()
    
    try:
        # Получаем максимальный sort_order для товаров
        products = await product_crud.get_all(session)
        max_sort_order = max([prod.sort_order for prod in products], default=0)
        
        # Создаем товар
        product_data = {
            "category_id": data["category_id"],
            "name": data["name"],
            "description": data["description"],
            "metaphoric_description": data["metaphoric_description"],
            "price": data["price"],
            "is_available": True,
            "stock_quantity": 0,  # По умолчанию 0, можно будет изменить
            "gender": data["gender"],
            "style": style,
            "is_featured": False,
            "is_unique": False,
            "sort_order": max_sort_order + 1
        }
        
        product = await product_crud.create(session, product_data)
        
        await callback.message.edit_text(
            f"✅ <b>Товар создан!</b>\n\n"
            f"📂 <b>Категория:</b> {data['category_name']}\n"
            f"📦 <b>Название:</b> {product.name}\n"
            f"💰 <b>Цена:</b> {product.price:,.0f}₽\n"
            f"👤 <b>Пол:</b> {product.gender}\n"
            f"🎨 <b>Стиль:</b> {product.style}\n\n"
            f"💡 <i>Товар создан без фото. Вы можете добавить фото позже через редактирование.</i>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при создании товара: {str(e)}")
    
    await state.clear()
    await callback.answer()