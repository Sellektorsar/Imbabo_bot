"""
Конфигурация приложения
"""
import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Telegram Bot
    bot_token: str = Field(..., env="BOT_TOKEN")
    admin_ids: str = Field(default="", env="ADMIN_IDS")
    
    @property
    def admin_ids_list(self) -> List[int]:
        """Получить список ID администраторов"""
        if not self.admin_ids:
            return []
        
        # Если admin_ids уже список, возвращаем его
        if isinstance(self.admin_ids, list):
            return [int(x) for x in self.admin_ids if str(x).strip()]
        
        # Если строка, разбиваем по запятым
        return [int(x.strip()) for x in self.admin_ids.split(',') if x.strip()]
    
    channel_id: str = Field(..., env="CHANNEL_ID")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Application
    debug: bool = Field(default=False, env="DEBUG")
    webhook_url: str = Field(default="", env="WEBHOOK_URL")
    webhook_path: str = Field(default="/webhook", env="WEBHOOK_PATH")
    webapp_host: str = Field(default="0.0.0.0", env="WEBAPP_HOST")
    webapp_port: int = Field(default=8000, env="WEBAPP_PORT")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # Business Logic
    first_purchase_promo_discount: int = Field(default=10, env="FIRST_PURCHASE_PROMO_DISCOUNT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Парсинг admin_ids из строки
        if isinstance(self.admin_ids, str):
            self.admin_ids = [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]


# Глобальный экземпляр настроек
settings = Settings()