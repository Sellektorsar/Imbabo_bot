"""
Модели рассылок
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, BigInteger, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class MailingCampaign(Base, TimestampMixin):
    """Модель рассылки"""
    
    __tablename__ = "mailing_campaigns"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Основная информация
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    photo_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Кнопки и интерактивность
    buttons: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Inline кнопки
    
    # Настройки рассылки
    target_segment: Mapped[str] = mapped_column(String(50), default="all", nullable=False)  # all, subscribed, etc.
    
    # Планирование
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Статус
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)  # draft, scheduled, sending, sent, cancelled
    
    # Статистика
    total_recipients: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Связи
    messages = relationship("MailingMessage", back_populates="campaign", lazy="select", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MailingCampaign(id={self.id}, name={self.name}, status={self.status})>"
    
    @property
    def success_rate(self) -> float:
        """Процент успешной доставки"""
        if self.total_recipients == 0:
            return 0.0
        return (self.sent_count / self.total_recipients) * 100


class MailingMessage(Base, TimestampMixin):
    """Модель отправленного сообщения рассылки"""
    
    __tablename__ = "mailing_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey("mailing_campaigns.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # Статус отправки
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, sent, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Связи
    campaign = relationship("MailingCampaign", back_populates="messages", lazy="select")
    user = relationship("User", lazy="select")
    
    def __repr__(self):
        return f"<MailingMessage(id={self.id}, campaign_id={self.campaign_id}, user_id={self.user_id}, status={self.status})>"