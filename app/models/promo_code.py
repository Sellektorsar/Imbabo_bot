"""
Модели промокодов
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from enum import Enum
from sqlalchemy import String, Boolean, Integer, ForeignKey, DECIMAL, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class PromoCodeType(str, Enum):
    """Типы промокодов"""
    PERCENT = "percent"
    FIXED = "fixed"


class PromoCode(Base, TimestampMixin):
    """Модель промокода"""
    
    __tablename__ = "promo_codes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Тип скидки
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)  # percent, fixed
    discount_value: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    # Ограничения
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Лимит использований
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_order_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), nullable=True)
    
    # Временные ограничения
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Специальные флаги
    is_first_purchase_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Связи
    uses = relationship("UserPromoUse", back_populates="promo_code", lazy="select")
    orders = relationship("Order", back_populates="promo_code", lazy="select")
    
    def __repr__(self):
        return f"<PromoCode(id={self.id}, code={self.code}, discount={self.discount_value})>"
    
    def is_valid(self, user_id: int = None, order_amount: Decimal = None) -> tuple[bool, str]:
        """Проверка валидности промокода"""
        now = datetime.utcnow()
        
        if not self.is_active:
            return False, "Промокод неактивен"
        
        if self.valid_from and now < self.valid_from:
            return False, "Промокод еще не активен"
        
        if self.valid_until and now > self.valid_until:
            return False, "Промокод истек"
        
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, "Промокод исчерпан"
        
        if self.min_order_amount and order_amount and order_amount < self.min_order_amount:
            return False, f"Минимальная сумма заказа: {self.min_order_amount} ₽"
        
        return True, "OK"
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        """Расчет размера скидки"""
        if self.discount_type == "percent":
            return amount * (self.discount_value / 100)
        elif self.discount_type == "fixed":
            return min(self.discount_value, amount)
        return Decimal(0)


class UserPromoUse(Base, TimestampMixin):
    """Модель использования промокода пользователем"""
    
    __tablename__ = "user_promo_uses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    promo_code_id: Mapped[int] = mapped_column(Integer, ForeignKey("promo_codes.id"), nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("orders.id"), nullable=True)
    
    # Связи
    user = relationship("User", back_populates="promo_uses", lazy="select")
    promo_code = relationship("PromoCode", back_populates="uses", lazy="select")
    order = relationship("Order", back_populates="promo_use", lazy="select")
    
    def __repr__(self):
        return f"<UserPromoUse(user_id={self.user_id}, promo_code_id={self.promo_code_id})>"