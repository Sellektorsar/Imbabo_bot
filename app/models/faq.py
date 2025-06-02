"""
Модель FAQ
"""
from sqlalchemy import String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class FAQ(Base, TimestampMixin):
    """Модель часто задаваемых вопросов"""
    
    __tablename__ = "faq"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Содержание
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Настройки
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Категория (опционально)
    category: Mapped[str] = mapped_column(String(100), default="general", nullable=False)
    
    def __repr__(self):
        return f"<FAQ(id={self.id}, question={self.question[:50]}...)>"