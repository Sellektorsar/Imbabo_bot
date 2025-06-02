"""
CRUD операции для работы с базой данных
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    User, Category, Product, Order, OrderItem, 
    PromoCode, UserPromoUse, Review, FAQ,
    MailingCampaign, MailingMessage, AutopostContent
)


class BaseCRUD:
    """Базовый класс для CRUD операций"""
    
    def __init__(self, model):
        self.model = model
    
    async def get(self, session: AsyncSession, id: int):
        """Получить объект по ID"""
        result = await session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()
    
    async def get_all(self, session: AsyncSession, skip: int = 0, limit: int = 100):
        """Получить все объекты с пагинацией"""
        result = await session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, session: AsyncSession, **kwargs):
        """Создать новый объект"""
        obj = self.model(**kwargs)
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj
    
    async def update(self, session: AsyncSession, id: int, **kwargs):
        """Обновить объект"""
        await session.execute(
            update(self.model).where(self.model.id == id).values(**kwargs)
        )
        return await self.get(session, id)
    
    async def delete(self, session: AsyncSession, id: int):
        """Удалить объект"""
        await session.execute(delete(self.model).where(self.model.id == id))


class UserCRUD(BaseCRUD):
    """CRUD для пользователей"""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_telegram_id(self, session: AsyncSession, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        result = await session.execute(
            select(User).where(User.id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def create_or_update(self, session: AsyncSession, telegram_id: int, **kwargs) -> User:
        """Создать или обновить пользователя"""
        user = await self.get_by_telegram_id(session, telegram_id)
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            user.last_activity = datetime.utcnow()
        else:
            user = User(id=telegram_id, last_activity=datetime.utcnow(), **kwargs)
            session.add(user)
        
        await session.flush()
        await session.refresh(user)
        return user
    
    async def update_fsm_state(self, session: AsyncSession, telegram_id: int, state: str = None, data: dict = None):
        """Обновить FSM состояние пользователя"""
        await session.execute(
            update(User)
            .where(User.id == telegram_id)
            .values(fsm_state=state, fsm_data=data, last_activity=datetime.utcnow())
        )
    
    async def get_subscribed_users(self, session: AsyncSession) -> List[User]:
        """Получить всех подписанных пользователей"""
        result = await session.execute(
            select(User).where(and_(User.is_subscribed == True, User.is_blocked == False))
        )
        return result.scalars().all()
    
    async def get_users_with_abandoned_carts(self, session: AsyncSession, hours_ago: int = 24) -> List[User]:
        """Получить пользователей с брошенными корзинами"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_ago)
        result = await session.execute(
            select(User).where(
                and_(
                    User.fsm_data.isnot(None),
                    User.fsm_data.op('->>')('cart').isnot(None),
                    User.last_activity < cutoff_time,
                    User.is_blocked == False
                )
            )
        )
        return result.scalars().all()


class CategoryCRUD(BaseCRUD):
    """CRUD для категорий"""
    
    def __init__(self):
        super().__init__(Category)
    
    async def get_active_categories(self, session: AsyncSession) -> List[Category]:
        """Получить активные категории"""
        result = await session.execute(
            select(Category)
            .where(Category.is_active == True)
            .order_by(Category.sort_order, Category.name)
        )
        return result.scalars().all()


class ProductCRUD(BaseCRUD):
    """CRUD для товаров"""
    
    def __init__(self):
        super().__init__(Product)
    
    async def get_by_category(self, session: AsyncSession, category_id: int, skip: int = 0, limit: int = 10) -> List[Product]:
        """Получить товары по категории"""
        result = await session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(and_(Product.category_id == category_id, Product.is_available == True))
            .order_by(Product.sort_order, Product.name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def search_products(self, session: AsyncSession, filters: Dict[str, Any]) -> List[Product]:
        """Поиск товаров по фильтрам"""
        query = select(Product).options(selectinload(Product.category)).where(Product.is_available == True)
        
        if filters.get('gender'):
            query = query.where(or_(Product.gender == filters['gender'], Product.gender == 'unisex'))
        
        if filters.get('style'):
            query = query.where(Product.style == filters['style'])
        
        if filters.get('max_price'):
            query = query.where(Product.price <= filters['max_price'])
        
        if filters.get('min_price'):
            query = query.where(Product.price >= filters['min_price'])
        
        query = query.order_by(Product.sort_order, Product.name).limit(3)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_featured_products(self, session: AsyncSession, limit: int = 5) -> List[Product]:
        """Получить рекомендуемые товары"""
        result = await session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(and_(Product.is_featured == True, Product.is_available == True))
            .order_by(Product.sort_order)
            .limit(limit)
        )
        return result.scalars().all()


class OrderCRUD(BaseCRUD):
    """CRUD для заказов"""
    
    def __init__(self):
        super().__init__(Order)
    
    async def create_order(self, session: AsyncSession, user_id: int, cart_items: List[Dict], 
                          customer_data: Dict, promo_code: PromoCode = None) -> Order:
        """Создать заказ из корзины"""
        # Расчет суммы
        subtotal = Decimal(0)
        order_items = []
        
        for item in cart_items:
            product = await session.get(Product, item['product_id'])
            if not product or not product.is_available:
                continue
            
            item_total = product.price * item['quantity']
            subtotal += item_total
            
            order_items.append({
                'product_id': product.id,
                'product_name': product.name,
                'product_price': product.price,
                'quantity': item['quantity']
            })
        
        # Применение промокода
        discount_amount = Decimal(0)
        if promo_code:
            discount_amount = promo_code.calculate_discount(subtotal)
        
        total_amount = subtotal - discount_amount
        
        # Создание заказа
        order = Order(
            user_id=user_id,
            promo_code_id=promo_code.id if promo_code else None,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total_amount,
            **customer_data
        )
        session.add(order)
        await session.flush()
        
        # Создание позиций заказа
        for item_data in order_items:
            order_item = OrderItem(order_id=order.id, **item_data)
            session.add(order_item)
        
        # Обновление использования промокода
        if promo_code:
            promo_code.used_count += 1
            promo_use = UserPromoUse(
                user_id=user_id,
                promo_code_id=promo_code.id,
                order_id=order.id
            )
            session.add(promo_use)
        
        await session.flush()
        await session.refresh(order)
        return order
    
    async def get_user_orders(self, session: AsyncSession, user_id: int) -> List[Order]:
        """Получить заказы пользователя"""
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_orders_by_status(self, session: AsyncSession, status: str) -> List[Order]:
        """Получить заказы по статусу"""
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.user))
            .where(Order.status == status)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()


class PromoCodeCRUD(BaseCRUD):
    """CRUD для промокодов"""
    
    def __init__(self):
        super().__init__(PromoCode)
    
    async def get_by_code(self, session: AsyncSession, code: str) -> Optional[PromoCode]:
        """Получить промокод по коду"""
        result = await session.execute(
            select(PromoCode).where(PromoCode.code == code.upper())
        )
        return result.scalar_one_or_none()
    
    async def check_user_promo_usage(self, session: AsyncSession, user_id: int, promo_code_id: int) -> bool:
        """Проверить, использовал ли пользователь промокод"""
        result = await session.execute(
            select(UserPromoUse).where(
                and_(UserPromoUse.user_id == user_id, UserPromoUse.promo_code_id == promo_code_id)
            )
        )
        return result.scalar_one_or_none() is not None


class MailingCampaignCRUD(BaseCRUD):
    """CRUD для рассылок"""
    
    def __init__(self):
        super().__init__(MailingCampaign)
    
    async def get_by_status(self, session: AsyncSession, status: str) -> List[MailingCampaign]:
        """Получить кампании по статусу"""
        result = await session.execute(
            select(self.model).where(self.model.status == status)
        )
        return result.scalars().all()
    
    async def get_active_campaigns(self, session: AsyncSession) -> List[MailingCampaign]:
        """Получить активные кампании"""
        return await self.get_by_status(session, "active")
    
    async def get_scheduled_campaigns(self, session: AsyncSession) -> List[MailingCampaign]:
        """Получить запланированные кампании"""
        return await self.get_by_status(session, "scheduled")
    
    async def get_scheduled_for_date(self, session: AsyncSession, date) -> List[MailingCampaign]:
        """Получить кампании, запланированные на определенную дату"""
        result = await session.execute(
            select(self.model).where(
                and_(
                    self.model.status == "scheduled",
                    func.date(self.model.scheduled_at) == date
                )
            )
        )
        return result.scalars().all()


class MailingMessageCRUD(BaseCRUD):
    """CRUD для сообщений рассылок"""
    
    def __init__(self):
        super().__init__(MailingMessage)
    
    async def get_by_campaign(self, session: AsyncSession, campaign_id: int) -> List[MailingMessage]:
        """Получить сообщения кампании"""
        result = await session.execute(
            select(self.model)
            .where(self.model.campaign_id == campaign_id)
            .options(selectinload(self.model.user))
        )
        return result.scalars().all()
    
    async def get_pending_messages(self, session: AsyncSession) -> List[MailingMessage]:
        """Получить сообщения в очереди на отправку"""
        result = await session.execute(
            select(self.model)
            .where(self.model.status == "pending")
            .options(selectinload(self.model.campaign))
        )
        return result.scalars().all()
    
    async def get_by_campaign_and_user(self, session: AsyncSession, campaign_id: int, user_id: int) -> Optional[MailingMessage]:
        """Получить сообщение по кампании и пользователю"""
        result = await session.execute(
            select(self.model).where(
                and_(
                    self.model.campaign_id == campaign_id,
                    self.model.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def delete_older_than(self, session: AsyncSession, cutoff_date) -> int:
        """Удалить записи старше указанной даты"""
        result = await session.execute(
            delete(self.model).where(self.model.created_at < cutoff_date)
        )
        return result.rowcount


class ReviewCRUD(BaseCRUD):
    """CRUD для отзывов"""
    
    def __init__(self):
        super().__init__(Review)
    
    async def get_by_user(self, session: AsyncSession, user_id: int) -> List[Review]:
        """Получить отзывы пользователя"""
        result = await session.execute(
            select(self.model).where(self.model.user_id == user_id)
        )
        return result.scalars().all()


class FAQCrud(BaseCRUD):
    """CRUD для FAQ"""
    
    def __init__(self):
        super().__init__(FAQ)
    
    async def get_active(self, session: AsyncSession) -> List[FAQ]:
        """Получить активные FAQ"""
        result = await session.execute(
            select(self.model).where(self.model.is_active == True).order_by(self.model.order)
        )
        return result.scalars().all()


class AutopostContentCRUD(BaseCRUD):
    """CRUD для автопостинга"""
    
    def __init__(self):
        super().__init__(AutopostContent)
    
    async def get_next_for_posting(self, session: AsyncSession) -> Optional[AutopostContent]:
        """Получить следующий контент для публикации"""
        now = datetime.utcnow()
        
        # Ищем контент, который готов к публикации
        result = await session.execute(
            select(self.model).where(
                and_(
                    self.model.is_active == True,
                    or_(
                        self.model.last_posted_at.is_(None),
                        self.model.last_posted_at < now - timedelta(hours=self.model.interval_hours)
                    )
                )
            ).order_by(
                self.model.last_posted_at.asc().nullsfirst(),
                self.model.created_at.asc()
            ).limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_active_content(self, session: AsyncSession) -> List[AutopostContent]:
        """Получить весь активный контент"""
        result = await session.execute(
            select(self.model).where(self.model.is_active == True).order_by(self.model.created_at.desc())
        )
        return result.scalars().all()


# Экземпляры CRUD классов
user_crud = UserCRUD()
category_crud = CategoryCRUD()
product_crud = ProductCRUD()
order_crud = OrderCRUD()
promo_code_crud = PromoCodeCRUD()
mailing_campaign_crud = MailingCampaignCRUD()
mailing_message_crud = MailingMessageCRUD()
review_crud = ReviewCRUD()
faq_crud = FAQCrud()
autopost_content_crud = AutopostContentCRUD()