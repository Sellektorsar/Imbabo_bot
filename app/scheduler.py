"""
Планировщик задач для автоматических рассылок и ретаргетинга
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import db_manager
from database.crud import (
    user_crud, mailing_campaign_crud, mailing_message_crud, 
    order_crud, autopost_content_crud
)
from app.models import User, MailingCampaign, Order
from app.utils.formatting import format_cart_summary

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Планировщик автоматических задач"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        
    async def start(self):
        """Запуск планировщика"""
        # Ежедневные рассылки в 10:00
        self.scheduler.add_job(
            self.send_daily_mailings,
            CronTrigger(hour=10, minute=0),
            id="daily_mailings",
            replace_existing=True
        )
        
        # Проверка брошенных корзин каждые 2 часа
        self.scheduler.add_job(
            self.check_abandoned_carts,
            IntervalTrigger(hours=2),
            id="abandoned_carts",
            replace_existing=True
        )
        
        # Автопостинг в канал каждые 4 часа
        self.scheduler.add_job(
            self.autopost_to_channel,
            IntervalTrigger(hours=4),
            id="autopost_channel",
            replace_existing=True
        )
        
        # Очистка старых сообщений рассылок раз в неделю
        self.scheduler.add_job(
            self.cleanup_old_mailings,
            CronTrigger(day_of_week=0, hour=2, minute=0),  # Воскресенье в 2:00
            id="cleanup_mailings",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Планировщик задач запущен")
    
    async def stop(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        logger.info("Планировщик задач остановлен")
    
    async def send_daily_mailings(self):
        """Отправка ежедневных рассылок"""
        logger.info("Начинаем отправку ежедневных рассылок")
        
        async with db_manager.async_session() as session:
            try:
                # Получаем активные рассылки, запланированные на сегодня
                today = datetime.now().date()
                campaigns = await mailing_campaign_crud.get_scheduled_for_date(session, today)
                
                for campaign in campaigns:
                    await self._send_campaign(session, campaign)
                    
            except Exception as e:
                logger.error(f"Ошибка при отправке ежедневных рассылок: {e}")
    
    async def check_abandoned_carts(self):
        """Проверка и напоминание о брошенных корзинах"""
        logger.info("Проверяем брошенные корзины")
        
        async with db_manager.async_session() as session:
            try:
                # Получаем пользователей с непустыми корзинами, которые не активны последние 2 часа
                cutoff_time = datetime.utcnow() - timedelta(hours=2)
                users_with_carts = await user_crud.get_users_with_abandoned_carts(session, cutoff_time)
                
                for user in users_with_carts:
                    await self._send_cart_reminder(user)
                    
            except Exception as e:
                logger.error(f"Ошибка при проверке брошенных корзин: {e}")
    
    async def autopost_to_channel(self):
        """Автопостинг в канал"""
        logger.info("Выполняем автопостинг в канал")
        
        if not settings.channel_id:
            logger.warning("ID канала не настроен")
            return
            
        async with db_manager.async_session() as session:
            try:
                # Получаем контент для автопостинга
                content = await autopost_content_crud.get_next_for_posting(session)
                
                if content:
                    await self._post_to_channel(session, content)
                    
            except Exception as e:
                logger.error(f"Ошибка при автопостинге: {e}")
    
    async def cleanup_old_mailings(self):
        """Очистка старых записей рассылок"""
        logger.info("Очищаем старые записи рассылок")
        
        async with db_manager.async_session() as session:
            try:
                # Удаляем записи старше 30 дней
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                deleted_count = await mailing_message_crud.delete_older_than(session, cutoff_date)
                await session.commit()
                
                logger.info(f"Удалено {deleted_count} старых записей рассылок")
                
            except Exception as e:
                logger.error(f"Ошибка при очистке старых рассылок: {e}")
    
    async def _send_campaign(self, session: AsyncSession, campaign: MailingCampaign):
        """Отправка рассылки"""
        logger.info(f"Отправляем рассылку: {campaign.title}")
        
        try:
            # Получаем получателей в зависимости от сегмента
            recipients = await self._get_campaign_recipients(session, campaign)
            
            sent_count = 0
            failed_count = 0
            
            for user in recipients:
                try:
                    # Проверяем, не отправляли ли уже этому пользователю
                    existing = await mailing_message_crud.get_by_campaign_and_user(
                        session, campaign.id, user.telegram_id
                    )
                    
                    if existing:
                        continue
                    
                    # Отправляем сообщение
                    success = await self._send_message_to_user(user, campaign)
                    
                    # Записываем результат
                    message_data = {
                        'campaign_id': campaign.id,
                        'user_id': user.telegram_id,
                        'sent_at': datetime.utcnow(),
                        'is_delivered': success
                    }
                    
                    await mailing_message_crud.create(session, message_data)
                    
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                    
                    # Небольшая задержка между отправками
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки пользователю {user.telegram_id}: {e}")
                    failed_count += 1
            
            # Обновляем статистику кампании
            await mailing_campaign_crud.update(session, campaign.id, {
                'sent_count': sent_count,
                'failed_count': failed_count,
                'status': 'completed' if sent_count > 0 else 'failed'
            })
            
            await session.commit()
            
            logger.info(f"Рассылка завершена. Отправлено: {sent_count}, Ошибок: {failed_count}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке рассылки {campaign.id}: {e}")
    
    async def _get_campaign_recipients(self, session: AsyncSession, campaign: MailingCampaign) -> List[User]:
        """Получение получателей рассылки"""
        if campaign.target_audience == 'all':
            return await user_crud.get_all_active(session)
        elif campaign.target_audience == 'subscribers':
            return await user_crud.get_subscribers(session)
        elif campaign.target_audience == 'customers':
            return await user_crud.get_customers(session)
        else:
            return await user_crud.get_all_active(session)
    
    async def _send_message_to_user(self, user: User, campaign: MailingCampaign) -> bool:
        """Отправка сообщения пользователю"""
        try:
            content = campaign.content
            
            if content.get('photo'):
                await self.bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=content['photo'],
                    caption=content.get('text', ''),
                    reply_markup=self._build_inline_keyboard(content.get('buttons', [])),
                    parse_mode="HTML"
                )
            else:
                await self.bot.send_message(
                    chat_id=user.telegram_id,
                    text=content.get('text', ''),
                    reply_markup=self._build_inline_keyboard(content.get('buttons', [])),
                    parse_mode="HTML"
                )
            
            return True
            
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(f"Не удалось отправить сообщение пользователю {user.telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {user.telegram_id}: {e}")
            return False
    
    async def _send_cart_reminder(self, user: User):
        """Отправка напоминания о брошенной корзине"""
        try:
            if not user.cart_data:
                return
            
            cart_summary = format_cart_summary(user.cart_data)
            
            text = f"""
🛒 <b>Вы забыли про свою корзину!</b>

{cart_summary}

Завершите оформление заказа, чтобы не упустить эти замечательные очки! 😎

Используйте промокод <code>COMEBACK10</code> и получите скидку 10% на первую покупку!
"""
            
            from app.keyboards.user import get_cart_keyboard
            
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=text,
                reply_markup=get_cart_keyboard(),
                parse_mode="HTML"
            )
            
            logger.info(f"Отправлено напоминание о корзине пользователю {user.telegram_id}")
            
        except (TelegramBadRequest, TelegramForbiddenError):
            logger.warning(f"Не удалось отправить напоминание пользователю {user.telegram_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки напоминания пользователю {user.telegram_id}: {e}")
    
    async def _post_to_channel(self, session: AsyncSession, content):
        """Публикация в канал"""
        try:
            if content.content.get('photo'):
                await self.bot.send_photo(
                    chat_id=settings.channel_id,
                    photo=content.content['photo'],
                    caption=content.content.get('text', ''),
                    reply_markup=self._build_inline_keyboard(content.content.get('buttons', [])),
                    parse_mode="HTML"
                )
            else:
                await self.bot.send_message(
                    chat_id=settings.channel_id,
                    text=content.content.get('text', ''),
                    reply_markup=self._build_inline_keyboard(content.content.get('buttons', [])),
                    parse_mode="HTML"
                )
            
            # Обновляем время последней публикации
            await autopost_content_crud.update(session, content.id, {
                'last_posted_at': datetime.utcnow()
            })
            await session.commit()
            
            logger.info(f"Опубликован пост в канал: {content.title}")
            
        except Exception as e:
            logger.error(f"Ошибка публикации в канал: {e}")
    
    def _build_inline_keyboard(self, buttons_data: list):
        """Построение inline клавиатуры из данных"""
        if not buttons_data:
            return None
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = []
        for row in buttons_data:
            button_row = []
            for button in row:
                button_row.append(InlineKeyboardButton(
                    text=button['text'],
                    url=button.get('url'),
                    callback_data=button.get('callback_data')
                ))
            keyboard.append(button_row)
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Глобальный экземпляр планировщика
scheduler: TaskScheduler = None


async def init_scheduler(bot: Bot):
    """Инициализация планировщика"""
    global scheduler
    scheduler = TaskScheduler(bot)
    await scheduler.start()


async def shutdown_scheduler():
    """Остановка планировщика"""
    global scheduler
    if scheduler:
        await scheduler.stop()