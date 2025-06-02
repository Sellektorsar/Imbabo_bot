"""
Главный файл Telegram-бота @imbabo_bot_v2
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import db_manager
from app.handlers import user_router, admin_router
from app.middlewares.database import DatabaseMiddleware
from app.middlewares.subscription import SubscriptionMiddleware
from app.scheduler import init_scheduler, shutdown_scheduler
from app.utils.logging import setup_logging, init_error_handler

# Настройка логирования
setup_logging(
    log_level=getattr(settings, 'log_level', 'INFO'),
    log_file="logs/bot.log"
)

logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота"""
    
    # Создание бота и диспетчера
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Подключение middleware
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())
    
    # Подключение роутеров
    dp.include_router(user_router)
    dp.include_router(admin_router)
    
    try:
        # Создание таблиц базы данных
        await db_manager.create_tables()
        logger.info("База данных инициализирована")
        
        # Инициализация обработчика ошибок
        # Преобразуем admin_ids в список целых чисел
        if isinstance(settings.admin_ids, str):
            admin_ids = [int(admin_id.strip()) for admin_id in settings.admin_ids.split(',') if admin_id.strip()]
        elif isinstance(settings.admin_ids, (list, tuple)):
            admin_ids = [int(admin_id) for admin_id in settings.admin_ids if str(admin_id).strip()]
        else:
            admin_ids = []
            logger.warning("ADMIN_IDS не задан или имеет неверный формат")
        init_error_handler(bot, admin_ids)
        logger.info("Обработчик ошибок инициализирован")
        
        # Запуск планировщика задач
        await init_scheduler(bot)
        logger.info("Планировщик задач запущен")
        
        # Запуск бота
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        # Остановка планировщика
        await shutdown_scheduler()
        logger.info("Планировщик задач остановлен")
        
        # Закрытие соединений
        await db_manager.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)