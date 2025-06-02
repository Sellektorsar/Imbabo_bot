#!/usr/bin/env python3
"""
Скрипт для тестирования админ панели бота
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent))

from database.database import get_session
from database.crud import category_crud, product_crud
from decimal import Decimal


async def test_admin_functions():
    """Тестирование основных функций админ панели"""
    print("🧪 Тестирование админ панели...")
    
    async with get_session() as session:
        # Тест 1: Создание категории
        print("\n📂 Тест 1: Создание категории")
        try:
            category_data = {
                "name": "Тестовая категория",
                "description": "Описание тестовой категории",
                "is_active": True,
                "sort_order": 1
            }
            category = await category_crud.create(session, category_data)
            print(f"✅ Категория создана: {category.name} (ID: {category.id})")
        except Exception as e:
            print(f"❌ Ошибка создания категории: {e}")
            return
        
        # Тест 2: Создание товара
        print("\n📦 Тест 2: Создание товара")
        try:
            product_data = {
                "name": "Тестовые очки",
                "description": "Обычное описание тестовых очков",
                "metaphoric_description": "Эти очки превратят вас в звезду!",
                "price": Decimal("5000.00"),
                "category_id": category.id,
                "is_available": True,
                "gender": "unisex",
                "style": "classic",
                "photo_url": "https://example.com/photo.jpg"
            }
            product = await product_crud.create(session, product_data)
            print(f"✅ Товар создан: {product.name} (ID: {product.id})")
        except Exception as e:
            print(f"❌ Ошибка создания товара: {e}")
            return
        
        # Тест 3: Получение списка категорий
        print("\n📋 Тест 3: Получение списка категорий")
        try:
            categories = await category_crud.get_all(session)
            print(f"✅ Найдено категорий: {len(categories)}")
            for cat in categories:
                print(f"   - {cat.name} (активна: {cat.is_active})")
        except Exception as e:
            print(f"❌ Ошибка получения категорий: {e}")
        
        # Тест 4: Получение списка товаров
        print("\n📦 Тест 4: Получение списка товаров")
        try:
            products = await product_crud.get_all(session)
            print(f"✅ Найдено товаров: {len(products)}")
            for prod in products:
                print(f"   - {prod.name} - {prod.price}₽ (доступен: {prod.is_available})")
        except Exception as e:
            print(f"❌ Ошибка получения товаров: {e}")
        
        # Тест 5: Обновление товара
        print("\n✏️ Тест 5: Обновление товара")
        try:
            updated_product = await product_crud.update(session, product.id, {
                "price": Decimal("6000.00"),
                "description": "Обновленное описание"
            })
            print(f"✅ Товар обновлен: новая цена {updated_product.price}₽")
        except Exception as e:
            print(f"❌ Ошибка обновления товара: {e}")
        
        # Тест 6: Получение товаров по категории
        print("\n🔍 Тест 6: Получение товаров по категории")
        try:
            category_products = await product_crud.get_by_category(session, category.id)
            print(f"✅ Товаров в категории '{category.name}': {len(category_products)}")
        except Exception as e:
            print(f"❌ Ошибка получения товаров по категории: {e}")
        
        print("\n🎉 Все тесты завершены!")


async def create_sample_data():
    """Создание примерных данных для демонстрации"""
    print("📦 Создание примерных данных...")
    
    async with get_session() as session:
        # Создаем категории
        categories_data = [
            {
                "name": "🕶️ Солнцезащитные очки",
                "description": "Стильные очки для защиты от солнца",
                "is_active": True,
                "sort_order": 1
            },
            {
                "name": "👓 Имиджевые очки",
                "description": "Очки для создания стильного образа",
                "is_active": True,
                "sort_order": 2
            },
            {
                "name": "🏃 Спортивные очки",
                "description": "Очки для активного образа жизни",
                "is_active": True,
                "sort_order": 3
            }
        ]
        
        created_categories = []
        for cat_data in categories_data:
            try:
                category = await category_crud.create(session, cat_data)
                created_categories.append(category)
                print(f"✅ Создана категория: {category.name}")
            except Exception as e:
                print(f"❌ Ошибка создания категории {cat_data['name']}: {e}")
        
        # Создаем товары
        products_data = [
            {
                "name": "Ray-Ban Aviator Classic",
                "description": "Классические очки-авиаторы с металлической оправой",
                "metaphoric_description": "Почувствуйте себя пилотом истребителя! Эти очки превратят вас в героя голливудского фильма.",
                "price": Decimal("15000.00"),
                "category_id": created_categories[0].id,
                "is_available": True,
                "gender": "unisex",
                "style": "classic",
                "photo_url": "https://example.com/rayban-aviator.jpg"
            },
            {
                "name": "Oakley Holbrook",
                "description": "Спортивные очки с поляризованными линзами",
                "metaphoric_description": "Для тех, кто не боится вызовов! Покорите любые вершины в этих очках.",
                "price": Decimal("12000.00"),
                "category_id": created_categories[2].id,
                "is_available": True,
                "gender": "male",
                "style": "sport",
                "photo_url": "https://example.com/oakley-holbrook.jpg"
            },
            {
                "name": "Chanel CH3281",
                "description": "Элегантные женские очки с кристаллами",
                "metaphoric_description": "Воплощение французской элегантности. Каждый взгляд через эти очки - произведение искусства.",
                "price": Decimal("25000.00"),
                "category_id": created_categories[1].id,
                "is_available": True,
                "gender": "female",
                "style": "fashion",
                "photo_url": "https://example.com/chanel-ch3281.jpg"
            }
        ]
        
        for prod_data in products_data:
            try:
                product = await product_crud.create(session, prod_data)
                print(f"✅ Создан товар: {product.name} - {product.price}₽")
            except Exception as e:
                print(f"❌ Ошибка создания товара {prod_data['name']}: {e}")
        
        print("\n🎉 Примерные данные созданы!")


async def main():
    """Главная функция"""
    print("🤖 Тестирование админ панели бота @imbabo_bot_v2")
    print("=" * 50)
    
    choice = input("\nВыберите действие:\n1. Запустить тесты\n2. Создать примерные данные\n3. Оба действия\nВаш выбор (1-3): ")
    
    if choice in ["1", "3"]:
        await test_admin_functions()
    
    if choice in ["2", "3"]:
        print("\n" + "=" * 50)
        await create_sample_data()
    
    print("\n✅ Готово!")


if __name__ == "__main__":
    asyncio.run(main())