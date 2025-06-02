"""
Простой тест для проверки работы бота
"""
import asyncio
import logging
from aiogram import Bot
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_bot():
    """Тест подключения к Telegram API"""
    try:
        bot = Bot(token=settings.bot_token)
        
        # Получаем информацию о боте
        me = await bot.get_me()
        logger.info(f"Бот подключен: @{me.username} ({me.first_name})")
        
        # Проверяем webhook
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Webhook URL: {webhook_info.url}")
        
        await bot.session.close()
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании бота: {e}")


if __name__ == "__main__":
    asyncio.run(test_bot())