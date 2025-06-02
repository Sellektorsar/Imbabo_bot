"""
Модель отзывов
"""
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Review(Base, TimestampMixin):
    """Модель отзыва"""
    
    __tablename__ = "reviews"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("products.id"), nullable=True)
    
    # Содержание отзыва
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voice_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Telegram file_id для голосового
    
    # Модерация
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="reviews", lazy="select")
    product = relationship("Product", back_populates="reviews", lazy="select")
    
    def __repr__(self):
        return f"<Review(id={self.id}, user_id={self.user_id}, product_id={self.product_id})>"
    
    @property
    def content_preview(self) -> str:
        """Превью содержания отзыва"""
        if self.text_content:
            return self.text_content[:100] + "..." if len(self.text_content) > 100 else self.text_content
        elif self.voice_file_id:
            return "[Голосовое сообщение]"
        return "[Пустой отзыв]"