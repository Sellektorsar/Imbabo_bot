"""
FSM состояния для пользовательских диалогов
"""
from aiogram.fsm.state import State, StatesGroup


class PersonalSelectionStates(StatesGroup):
    """Состояния для персонального подбора очков"""
    
    waiting_for_gender = State()
    waiting_for_style = State()
    waiting_for_budget = State()


class OrderStates(StatesGroup):
    """Состояния для оформления заказа"""
    
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_promo_code = State()
    confirming_order = State()


class ReviewStates(StatesGroup):
    """Состояния для сбора отзывов"""
    
    waiting_for_review = State()