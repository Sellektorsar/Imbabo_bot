#!/usr/bin/env python3
"""
Скрипт для проверки настройки админ панели
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from database.database import db_manager
from database.crud import category_crud, product_crud


async def check_admin_setup():
    """Проверка настройки админ панели"""
    print("🔧 Проверка настройки админ панели @imbabo_bot_v2\n")
    
    # Проверка настроек
    print("📋 Проверка конфигурации:")
    print(f"   ✅ BOT_TOKEN: {'✓ Настроен' if settings.bot_token != 'test_token_here' else '❌ Нужно настроить'}")
    print(f"   ✅ ADMIN_IDS: {settings.admin_ids_list}")
    print(f"   ✅ CHANNEL_ID: {settings.channel_id}")
    print(f"   ✅ DATABASE_URL: {settings.database_url}")
    print()
    
    # Проверка базы данных
    print("🗄️ Проверка базы данных:")
    try:
        async with db_manager.async_session() as session:
            # Проверяем категории
            categories = await category_crud.get_all(session)
            print(f"   📂 Категорий в БД: {len(categories)}")
            
            # Проверяем товары
            products = await product_crud.get_all(session)
            print(f"   📦 Товаров в БД: {len(products)}")
            
            if categories:
                print("\n   📂 Существующие категории:")
                for cat in categories:
                    status = "✅" if cat.is_active else "❌"
                    print(f"      {status} {cat.name}")
            
            if products:
                print("\n   📦 Существующие товары:")
                for prod in products[:5]:  # Показываем первые 5
                    status = "✅" if prod.is_available else "❌"
                    print(f"      {status} {prod.name} - {prod.price:,.0f}₽")
                if len(products) > 5:
                    print(f"      ... и еще {len(products) - 5} товаров")
        
        print("   ✅ База данных работает корректно")
        
    except Exception as e:
        print(f"   ❌ Ошибка подключения к БД: {e}")
        return False
    
    print()
    
    # Инструкции для пользователя
    print("📝 Инструкции для начала работы:")
    print()
    
    if settings.bot_token == 'test_token_here':
        print("❗ ВАЖНО: Настройте реальный токен бота в .env файле")
        print("   1. Получите токен у @BotFather")
        print("   2. Замените BOT_TOKEN в .env файле")
        print()
    
    print("🔑 Настройка доступа к админ панели:")
    print("   1. Получите ваш Telegram ID:")
    print("      - Напишите боту @userinfobot")
    print("      - Отправьте /start")
    print("      - Скопируйте ваш ID")
    print()
    print("   2. Добавьте ваш ID в .env файл:")
    print(f"      ADMIN_IDS=ваш_id,{','.join(map(str, settings.admin_ids_list))}")
    print()
    print("   3. Перезапустите бота")
    print()
    
    print("🚀 Запуск админ панели:")
    print("   1. Запустите бота: python main.py")
    print("   2. Напишите боту: /admin")
    print("   3. Выберите: 📦 Управление каталогом")
    print("   4. Начните с создания категории")
    print()
    
    print("📖 Подробная инструкция в файле: ADMIN_GUIDE.md")
    print()
    
    return True


async def create_sample_data():
    """Создание примера данных для тестирования"""
    print("🎯 Создание тестовых данных...")
    
    try:
        async with db_manager.async_session() as session:
            # Создаем категорию если её нет
            categories = await category_crud.get_all(session)
            if not categories:
                category = await category_crud.create(session, {
                    "name": "Солнцезащитные очки",
                    "description": "Стильные очки для защиты от солнца",
                    "is_active": True,
                    "sort_order": 1
                })
                print(f"   ✅ Создана категория: {category.name}")
                
                # Создаем тестовый товар
                product = await product_crud.create(session, {
                    "category_id": category.id,
                    "name": "Ray-Ban Aviator Classic",
                    "description": "Классические очки-авиаторы с металлической оправой",
                    "metaphoric_description": "Почувствуйте себя пилотом истребителя! Легендарные очки, которые покорили Голливуд.",
                    "price": 15000,
                    "is_available": True,
                    "stock_quantity": 10,
                    "gender": "unisex",
                    "style": "classic",
                    "is_featured": True,
                    "is_unique": False,
                    "sort_order": 1
                })
                print(f"   ✅ Создан товар: {product.name}")
            else:
                print("   ℹ️ Тестовые данные уже существуют")
                
    except Exception as e:
        print(f"   ❌ Ошибка создания тестовых данных: {e}")


if __name__ == "__main__":
    print("=" * 60)
    
    # Основная проверка
    result = asyncio.run(check_admin_setup())
    
    if result:
        # Предложение создать тестовые данные
        create_sample = input("Создать тестовые данные для проверки? (y/n): ").lower().strip()
        if create_sample in ['y', 'yes', 'да', 'д']:
            asyncio.run(create_sample_data())
    
    print("=" * 60)
    print("✅ Проверка завершена!")