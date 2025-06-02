from aiogram import Router

from .main import main_admin_router
from .catalog import catalog_admin_router
from .orders import orders_admin_router
from .promo import promo_admin_router
from .mailing import mailing_admin_router
from .stats import stats_admin_router
from .faq import faq_admin_router

# Главный роутер для всех административных функций
admin_router = Router()

# Подключаем все административные роутеры
admin_router.include_router(main_admin_router)
admin_router.include_router(catalog_admin_router)
admin_router.include_router(orders_admin_router)
admin_router.include_router(promo_admin_router)
admin_router.include_router(mailing_admin_router)
admin_router.include_router(stats_admin_router)
admin_router.include_router(faq_admin_router)