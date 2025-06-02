"""
Модели заказов
"""
from decimal import Decimal
from typing import Optional
from enum import Enum
from sqlalchemy import String, Text, Integer, ForeignKey, DECIMAL, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class OrderStatus(str, Enum):
    """Статусы заказов"""
    NEW = "new"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(Base, TimestampMixin):
    """Модель заказа"""
    
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    promo_code_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("promo_codes.id"), nullable=True)
    
    # Статус заказа
    status: Mapped[str] = mapped_column(String(50), default="new", nullable=False)  # new, processing, completed, cancelled
    
    # Финансовая информация
    subtotal: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)  # Сумма без скидки
    discount_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)  # Итоговая сумма
    
    # Данные доставки
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    delivery_address: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Дополнительная информация
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="orders", lazy="select")
    promo_code = relationship("PromoCode", back_populates="orders", lazy="select")
    items = relationship("OrderItem", back_populates="order", lazy="select", cascade="all, delete-orphan")
    promo_use = relationship("UserPromoUse", back_populates="order", lazy="select", uselist=False)
    
    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, total={self.total_amount}, status={self.status})>"
    
    @property
    def display_total(self) -> str:
        """Отформатированная итоговая сумма"""
        return f"{self.total_amount:,.0f} ₽"
    
    @property
    def items_count(self) -> int:
        """Количество товаров в заказе"""
        return sum(item.quantity for item in self.items)


class OrderItem(Base, TimestampMixin):
    """Модель позиции заказа"""
    
    __tablename__ = "order_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Данные на момент заказа (для истории)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Связи
    order = relationship("Order", back_populates="items", lazy="select")
    product = relationship("Product", back_populates="order_items", lazy="select")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, product={self.product_name}, qty={self.quantity})>"
    
    @property
    def total_price(self) -> Decimal:
        """Общая стоимость позиции"""
        return self.product_price * self.quantity
    
    @property
    def display_total(self) -> str:
        """Отформатированная общая стоимость позиции"""
        return f"{self.total_price:,.0f} ₽"