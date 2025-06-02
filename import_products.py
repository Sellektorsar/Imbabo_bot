import os
import json
from app.models import product as product_model
from app.models import category as category_model
from database.database import get_db
from sqlalchemy.future import select

IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images')
JSON_PATH = os.path.join(os.path.dirname(__file__), 'products.json')

async def import_products():
    async for session in get_db():
        with open(JSON_PATH, encoding='utf-8') as f:
            products = json.load(f)
        for prod in products:
            # Найти или создать категорию
            category = await session.execute(
                select(category_model.Category).where(category_model.Category.name == prod['category'])
            )
            category = category.scalar()
            if not category:
                category = category_model.Category(name=prod['category'])
                session.add(category)
                await session.commit()
                await session.refresh(category)
            # Создать товар
            product = product_model.Product(
                name=prod['name'],
                description=prod['description'],
                price=prod['price'],
                category_id=int(category.id)  # Приведение к int для устранения предупреждения
            )
            session.add(product)
            await session.commit()
            await session.refresh(product)
            # Добавить одно изображение (если есть отдельная таблица)
            if hasattr(product_model, 'ProductImage') and 'images' in prod and prod['images']:
                img_name = prod['images'][0]  # Берём только первое изображение
                img_path = os.path.join(IMAGES_DIR, img_name)
                if os.path.exists(img_path):
                    image = product_model.ProductImage(product_id=product.id, file_path=img_name)
                    session.add(image)
            await session.commit()
        session.close()  # Закрытие сессии после завершения работы

if __name__ == "__main__":
    import asyncio
    asyncio.run(import_products())
