from aiogram import Router
from .start import start_router
from .catalog import catalog_router
from .cart import cart_router
from .order import order_router
from .personal_selection import selection_router
from .review import review_router
from .faq import faq_router

# Создаем основной роутер для пользователей
user_router = Router()

# Подключаем все роутеры
user_router.include_router(start_router)
user_router.include_router(catalog_router)
user_router.include_router(cart_router)
user_router.include_router(order_router)
user_router.include_router(selection_router)
user_router.include_router(review_router)
user_router.include_router(faq_router)