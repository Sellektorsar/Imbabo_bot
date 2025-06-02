"""
Модель автопостинга в канал
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class AutopostContent(Base, TimestampMixin):
    """Модель контента для автопостинга в канал"""
    
    __tablename__ = "autopost_content"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Содержание поста
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    photo_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Кнопки
    buttons: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Планирование
    post_type: Mapped[str] = mapped_column(String(50), default="regular", nullable=False)  # regular, promo, news
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Статус
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)  # draft, scheduled, posted, failed
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Повторяющиеся посты
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurrence_pattern: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # daily, weekly, monthly
    
    def __repr__(self):
        return f"<AutopostContent(id={self.id}, type={self.post_type}, status={self.status})>"