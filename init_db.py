"""
Скрипт для инициализации базы данных с тестовыми данными
"""
import asyncio
import logging
from decimal import Decimal

from database import DatabaseManager, get_db
from database.crud import category_crud, product_crud, promo_code_crud
from app.models import FAQ

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    """Инициализация базы данных с тестовыми данными"""
    
    # Создаем таблицы
    db_manager = DatabaseManager()
    await db_manager.create_tables()
    logger.info("Таблицы созданы")
    
    async for session in get_db():
        try:
            # Создаем категории
            categories_data = [
                {"name": "🕶 Солнцезащитные очки", "description": "Стильная защита от солнца", "sort_order": 1},
                {"name": "👓 Имиджевые очки", "description": "Очки для создания образа", "sort_order": 2},
                {"name": "🏃 Спортивные очки", "description": "Очки для активного образа жизни", "sort_order": 3},
                {"name": "✨ Премиум коллекция", "description": "Эксклюзивные модели", "sort_order": 4}
            ]
            
            created_categories = []
            for cat_data in categories_data:
                category = await category_crud.create(session, **cat_data)
                created_categories.append(category)
                logger.info(f"Создана категория: {category.name}")
            
            # Создаем товары
            products_data = [
                {
                    "name": "Ray-Ban Aviator Classic",
                    "description": "Классические очки-авиаторы",
                    "metaphoric_description": "Крылья свободы на вашем лице. Эти очки превращают каждый день в приключение, а каждый взгляд — в полет к мечте.",
                    "price": Decimal("12500"),
                    "category_id": created_categories[0].id,
                    "photo_url": "https://example.com/aviator.jpg",
                    "is_available": True,
                    "is_featured": True,
                    "is_unique": False,
                    "gender": "unisex",
                    "style": "classic",
                    "sort_order": 1
                },
                {
                    "name": "Oakley Holbrook",
                    "description": "Спортивные солнцезащитные очки",
                    "metaphoric_description": "Броня для ваших глаз. Созданы для тех, кто не боится вызовов и всегда готов к действию.",
                    "price": Decimal("8900"),
                    "category_id": created_categories[2].id,
                    "photo_url": "https://example.com/holbrook.jpg",
                    "is_available": True,
                    "is_featured": True,
                    "is_unique": False,
                    "gender": "male",
                    "style": "sport",
                    "sort_order": 1
                },
                {
                    "name": "Chanel CH3281",
                    "description": "Элегантные женские очки",
                    "metaphoric_description": "Воплощение французской элегантности. Каждая линия этих очков шепчет о роскоши и безупречном вкусе.",
                    "price": Decimal("25000"),
                    "category_id": created_categories[3].id,
                    "photo_url": "https://example.com/chanel.jpg",
                    "is_available": True,
                    "is_featured": True,
                    "is_unique": True,
                    "gender": "female",
                    "style": "fashion",
                    "sort_order": 1
                },
                {
                    "name": "Tom Ford FT5401",
                    "description": "Имиджевые очки для мужчин",
                    "metaphoric_description": "Символ мужской харизмы. Эти очки не просто корректируют зрение — они создают образ успешного человека.",
                    "price": Decimal("18500"),
                    "category_id": created_categories[1].id,
                    "photo_url": "https://example.com/tomford.jpg",
                    "is_available": True,
                    "is_featured": False,
                    "is_unique": True,
                    "gender": "male",
                    "style": "classic",
                    "sort_order": 2
                },
                {
                    "name": "Gucci GG0061S",
                    "description": "Модные женские солнцезащитные очки",
                    "metaphoric_description": "Магия итальянского дизайна. Эти очки превращают обычную прогулку в подиум, а вас — в звезду.",
                    "price": Decimal("22000"),
                    "category_id": created_categories[0].id,
                    "photo_url": "https://example.com/gucci.jpg",
                    "is_available": True,
                    "is_featured": True,
                    "is_unique": True,
                    "gender": "female",
                    "style": "fashion",
                    "sort_order": 2
                }
            ]
            
            for prod_data in products_data:
                product = await product_crud.create(session, **prod_data)
                logger.info(f"Создан товар: {product.name}")
            
            # Создаем промокоды
            promo_codes_data = [
                {
                    "code": "FIRST10",
                    "discount_type": "percentage",
                    "discount_value": Decimal("10"),
                    "is_first_purchase_only": True,
                    "is_active": True,
                    "usage_limit": 1000,
                    "used_count": 0
                },
                {
                    "code": "SUMMER2024",
                    "discount_type": "percentage", 
                    "discount_value": Decimal("15"),
                    "is_first_purchase_only": False,
                    "is_active": True,
                    "usage_limit": 500,
                    "used_count": 0
                }
            ]
            
            for promo_data in promo_codes_data:
                promo = await promo_code_crud.create(session, **promo_data)
                logger.info(f"Создан промокод: {promo.code}")
            
            # Создаем FAQ
            faq_data = [
                {
                    "question": "Как оформить заказ?",
                    "answer": "Выберите товары в каталоге, добавьте их в корзину и нажмите 'Оформить заказ'. Следуйте инструкциям бота.",
                    "sort_order": 1,
                    "is_active": True
                },
                {
                    "question": "Какие способы доставки доступны?",
                    "answer": "Мы доставляем по всей России курьерской службой. Стоимость доставки рассчитывается индивидуально.",
                    "sort_order": 2,
                    "is_active": True
                },
                {
                    "question": "Можно ли вернуть товар?",
                    "answer": "Да, вы можете вернуть товар в течение 14 дней с момента получения, если он не подошел.",
                    "sort_order": 3,
                    "is_active": True
                }
            ]
            
            for faq_item in faq_data:
                faq = FAQ(**faq_item)
                session.add(faq)
                logger.info(f"Создан FAQ: {faq.question}")
            
            await session.commit()
            logger.info("Тестовые данные успешно добавлены!")
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации данных: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
            break


if __name__ == "__main__":
    asyncio.run(init_database())