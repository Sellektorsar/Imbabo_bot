"""
Система логирования и обработки ошибок
"""
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional
from functools import wraps

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config import settings


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Настройка системы логирования"""
    
    # Создаем директорию для логов
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Настройка форматирования
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Очищаем существующие обработчики
    root_logger.handlers.clear()
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Файловый обработчик
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Настройка логгеров библиотек
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Получить логгер с указанным именем"""
    return logging.getLogger(name)


class ErrorHandler:
    """Обработчик ошибок"""
    
    def __init__(self, bot: Bot, admin_ids: list):
        self.bot = bot
        self.admin_ids = admin_ids
        self.logger = get_logger(__name__)
    
    async def handle_error(self, error: Exception, context: dict = None):
        """Обработка ошибки"""
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        
        # Логируем ошибку
        self.logger.error(
            f"Ошибка {error_info['error_type']}: {error_info['error_message']}",
            extra={'context': error_info['context']}
        )
        
        # Отправляем уведомление администраторам
        await self._notify_admins(error_info)
    
    async def _notify_admins(self, error_info: dict):
        """Уведомление администраторов об ошибке"""
        if not self.admin_ids:
            return
        
        message = self._format_error_message(error_info)
        
        for admin_id in self.admin_ids:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode="HTML"
                )
            except TelegramAPIError as e:
                self.logger.warning(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    
    def _format_error_message(self, error_info: dict) -> str:
        """Форматирование сообщения об ошибке"""
        lines = [
            "🚨 <b>Ошибка в боте</b>",
            "",
            f"<b>Тип:</b> {error_info['error_type']}",
            f"<b>Сообщение:</b> {error_info['error_message']}",
            f"<b>Время:</b> {error_info['timestamp']}",
        ]
        
        if error_info.get('context'):
            lines.append("")
            lines.append("<b>Контекст:</b>")
            for key, value in error_info['context'].items():
                lines.append(f"• {key}: {value}")
        
        return "\n".join(lines)


def error_handler(logger: Optional[logging.Logger] = None):
    """Декоратор для обработки ошибок в функциях"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if logger:
                    logger.error(f"Ошибка в {func.__name__}: {e}")
                    logger.debug(traceback.format_exc())
                raise
        return wrapper
    return decorator


def log_user_action(action: str, user_id: int, details: dict = None):
    """Логирование действий пользователя"""
    logger = get_logger('user_actions')
    
    log_data = {
        'action': action,
        'user_id': user_id,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    
    logger.info(f"Пользователь {user_id} выполнил действие: {action}", extra=log_data)


def log_admin_action(action: str, admin_id: int, details: dict = None):
    """Логирование действий администратора"""
    logger = get_logger('admin_actions')
    
    log_data = {
        'action': action,
        'admin_id': admin_id,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    
    logger.info(f"Администратор {admin_id} выполнил действие: {action}", extra=log_data)


def log_order_event(event: str, order_id: int, user_id: int, details: dict = None):
    """Логирование событий заказов"""
    logger = get_logger('orders')
    
    log_data = {
        'event': event,
        'order_id': order_id,
        'user_id': user_id,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    
    logger.info(f"Заказ {order_id}: {event}", extra=log_data)


def log_mailing_event(event: str, campaign_id: int, details: dict = None):
    """Логирование событий рассылок"""
    logger = get_logger('mailings')
    
    log_data = {
        'event': event,
        'campaign_id': campaign_id,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    
    logger.info(f"Рассылка {campaign_id}: {event}", extra=log_data)


class PerformanceLogger:
    """Логгер производительности"""
    
    def __init__(self, logger_name: str = 'performance'):
        self.logger = get_logger(logger_name)
    
    def __call__(self, func_name: str = None):
        def decorator(func):
            name = func_name or func.__name__
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = datetime.now()
                
                try:
                    result = await func(*args, **kwargs)
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    self.logger.info(
                        f"Функция {name} выполнена за {execution_time:.3f}с",
                        extra={'execution_time': execution_time, 'function': name}
                    )
                    
                    return result
                    
                except Exception as e:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    self.logger.error(
                        f"Функция {name} завершилась с ошибкой за {execution_time:.3f}с: {e}",
                        extra={'execution_time': execution_time, 'function': name, 'error': str(e)}
                    )
                    
                    raise
            
            return wrapper
        return decorator


# Глобальный экземпляр обработчика ошибок
error_handler_instance: Optional[ErrorHandler] = None


def init_error_handler(bot: Bot, admin_ids: list):
    """Инициализация обработчика ошибок"""
    global error_handler_instance
    error_handler_instance = ErrorHandler(bot, admin_ids)


async def handle_global_error(error: Exception, context: dict = None):
    """Глобальная обработка ошибок"""
    if error_handler_instance:
        await error_handler_instance.handle_error(error, context)
    else:
        logger = get_logger(__name__)
        logger.error(f"Необработанная ошибка: {error}")


# Создаем экземпляр логгера производительности
performance_logger = PerformanceLogger()