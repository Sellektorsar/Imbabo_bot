"""
Модель пользователя
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Модель пользователя бота"""
    
    __tablename__ = "users"
    
    # Основные поля
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram ID
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Контактная информация
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Статусы и состояния
    is_subscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # FSM состояние
    fsm_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fsm_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # AIDA этап
    aida_stage: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # attention, interest, desire, action
    
    # Маркетинговые данные
    used_first_purchase_promo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Связи
    orders = relationship("Order", back_populates="user", lazy="select")
    reviews = relationship("Review", back_populates="user", lazy="select")
    promo_uses = relationship("UserPromoUse", back_populates="user", lazy="select")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, first_name={self.first_name})>"
    
    @property
    def full_name(self) -> str:
        """Полное имя пользователя"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) or self.username or f"User {self.id}"