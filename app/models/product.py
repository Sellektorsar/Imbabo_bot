"""
Модель товара
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    """Модель товара"""
    
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    
    # Основная информация
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metaphoric_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # "Метафорическое" описание
    
    # Цена и наличие
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Медиа
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    photo_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Telegram file_id
    
    # Атрибуты для подбора
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # male, female, unisex
    style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # classic, sport, fashion, etc.
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Дополнительные атрибуты
    
    # Маркетинговые поля
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_unique: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Уникальная/редкая модель
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Связи
    category = relationship("Category", back_populates="products", lazy="select")
    order_items = relationship("OrderItem", back_populates="product", lazy="select")
    reviews = relationship("Review", back_populates="product", lazy="select")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"
    
    @property
    def display_price(self) -> str:
        """Отформатированная цена для отображения"""
        return f"{self.price:,.0f} ₽"