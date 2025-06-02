# 🔄 API Потоки и Взаимодействия @imbabo_bot_v2

## 📋 Обзор API Потоков

Документ описывает все потоки взаимодействия пользователей и администраторов с ботом, включая FSM состояния и бизнес-логику.

## 👤 Пользовательские Потоки

### 🚀 Поток Регистрации и Приветствия

```mermaid
sequenceDiagram
    participant U as Пользователь
    participant B as Бот
    participant DB as База данных
    participant TG as Telegram API

    U->>B: /start
    B->>DB: Проверить пользователя
    alt Новый пользователь
        B->>DB: Создать пользователя
        B->>U: Приветственное сообщение
    else Существующий пользователь
        B->>U: Сообщение возвращения
    end
    
    B->>TG: Проверить подписку на канал
    alt Не подписан
        B->>U: Предложение подписаться
        U->>B: Подписался
        B->>TG: Повторная проверка
    end
    
    B->>U: Главное меню
    B->>DB: Обновить aida_stage = 'attention'
```

**Обработчик:** `app/handlers/user/common.py:start_command`

### 🛍️ Поток Просмотра Каталога

```mermaid
sequenceDiagram
    participant U as Пользователь
    participant B as Бот
    participant DB as База данных

    U->>B: /каталог или кнопка "Каталог"
    B->>DB: Получить категории
    B->>U: Список категорий
    
    U->>B: Выбрать категорию
    B->>DB: Получить товары категории
    B->>U: Список товаров (пагинация)
    
    U->>B: Выбрать товар
    B->>DB: Получить детали товара
    B->>U: Карточка товара + кнопки
    B->>DB: Обновить aida_stage = 'interest'
    
    alt Добавить в корзину
        U->>B: "Добавить в корзину"
        B->>DB: Добавить в корзину пользователя
        B->>U: Подтверждение + варианты действий
        B->>DB: Обновить aida_stage = 'desire'
    else Продолжить просмотр
        U->>B: "Назад к товарам"
        B->>U: Список товаров
    end
```

**Обработчики:** 
- `app/handlers/user/catalog.py`
- `app/services/cart_service.py`

### 🎯 Поток Персонального Подбора

```mermaid
stateDiagram-v2
    [*] --> SelectionStart: /подбор
    SelectionStart --> GenderSelection: Начать подбор
    GenderSelection --> StyleSelection: Выбрать пол
    StyleSelection --> BudgetSelection: Выбрать стиль
    BudgetSelection --> Processing: Указать бюджет
    Processing --> Results: Найти товары
    Results --> ProductView: Выбрать товар
    ProductView --> AddToCart: Добавить в корзину
    ProductView --> Results: Назад к результатам
    AddToCart --> [*]: Товар добавлен
    Results --> [*]: Завершить подбор
```

**FSM Состояния:**
```python
class PersonalSelectionStates(StatesGroup):
    waiting_for_gender = State()
    waiting_for_style = State()
    waiting_for_budget = State()
```

**Обработчик:** `app/handlers/user/personal_selection.py`

### 🛒 Поток Оформления Заказа

```mermaid
sequenceDiagram
    participant U as Пользователь
    participant B as Бот
    participant DB as База данных
    participant A as Администратор

    U->>B: "Оформить заказ" из корзины
    B->>DB: Получить содержимое корзины
    B->>U: Сводка заказа
    
    B->>U: Запросить имя
    U->>B: Ввести имя
    B->>U: Запросить телефон
    U->>B: Ввести телефон
    B->>U: Запросить адрес
    U->>B: Ввести адрес
    
    B->>U: Предложить промокод
    alt Есть промокод
        U->>B: Ввести промокод
        B->>DB: Проверить промокод
        B->>U: Применить скидку
    end
    
    B->>U: Итоговая сводка + подтверждение
    U->>B: Подтвердить заказ
    
    B->>DB: Создать заказ
    B->>DB: Очистить корзину
    B->>DB: Обновить aida_stage = 'action'
    B->>U: Подтверждение заказа
    B->>A: Уведомление о новом заказе
```

**FSM Состояния:**
```python
class OrderStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_promo = State()
    waiting_for_confirmation = State()
```

**Обработчик:** `app/handlers/user/orders.py`

### ⭐ Поток Сбора Отзывов

```mermaid
stateDiagram-v2
    [*] --> ReviewStart: /отзыв
    ReviewStart --> ProductSelection: Выбрать товар (опционально)
    ProductSelection --> ReviewInput: Товар выбран
    ReviewStart --> ReviewInput: Общий отзыв
    ReviewInput --> ReviewSubmit: Ввести текст/аудио
    ReviewSubmit --> [*]: Отзыв отправлен админу
```

**Обработчик:** `app/handlers/user/reviews.py`

## 👨‍💼 Административные Потоки

### 📦 Поток Управления Каталогом

```mermaid
sequenceDiagram
    participant A as Администратор
    participant B as Бот
    participant DB as База данных

    A->>B: /admin
    B->>B: Проверить права администратора
    B->>A: Админ меню
    
    A->>B: "Управление каталогом"
    B->>A: Меню каталога
    
    alt Добавить категорию
        A->>B: "Добавить категорию"
        B->>A: Запросить название
        A->>B: Ввести название
        B->>DB: Создать категорию
        B->>A: Подтверждение
    else Добавить товар
        A->>B: "Добавить товар"
        B->>DB: Получить категории
        B->>A: Выбрать категорию
        A->>B: Выбрать категорию
        
        loop Сбор данных товара
            B->>A: Запросить поле (название, описание, цена, фото)
            A->>B: Ввести данные
        end
        
        B->>DB: Создать товар
        B->>A: Подтверждение создания
    end
```

**FSM Состояния:**
```python
class ProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_metaphoric_description = State()
    waiting_for_price = State()
    waiting_for_photo = State()
    waiting_for_gender = State()
    waiting_for_style = State()

class CategoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
```

**Обработчик:** `app/handlers/admin/catalog.py`

### 🎫 Поток Управления Промокодами

```mermaid
stateDiagram-v2
    [*] --> PromoMenu: Управление промокодами
    PromoMenu --> CreatePromo: Создать промокод
    PromoMenu --> ViewPromos: Просмотр промокодов
    PromoMenu --> EditPromo: Редактировать
    
    CreatePromo --> EnterCode: Ввести код
    EnterCode --> SelectType: Выбрать тип скидки
    SelectType --> EnterValue: Ввести размер
    EnterValue --> SetLimits: Настроить ограничения
    SetLimits --> [*]: Промокод создан
    
    ViewPromos --> PromoDetails: Выбрать промокод
    PromoDetails --> EditPromo: Редактировать
    PromoDetails --> DeactivatePromo: Деактивировать
    EditPromo --> [*]: Изменения сохранены
    DeactivatePromo --> [*]: Промокод деактивирован
```

**Обработчик:** `app/handlers/admin/promo.py`

### 📊 Поток Просмотра Статистики

```mermaid
sequenceDiagram
    participant A as Администратор
    participant B as Бот
    participant DB as База данных

    A->>B: "Статистика"
    B->>DB: Запросить общую статистику
    B->>A: Основные метрики
    
    A->>B: "Детальная статистика"
    B->>A: Меню детализации
    
    alt Статистика продаж
        A->>B: "Продажи"
        B->>DB: Запросить данные продаж
        B->>A: График продаж + топ товары
    else Статистика пользователей
        A->>B: "Пользователи"
        B->>DB: Запросить данные пользователей
        B->>A: Статистика по AIDA + активность
    else Статистика промокодов
        A->>B: "Промокоды"
        B->>DB: Запросить использование промокодов
        B->>A: Эффективность промокодов
    end
```

**Обработчик:** `app/handlers/admin/stats.py`

## 🔄 Автоматические Потоки

### 📧 Поток Рассылок

```mermaid
sequenceDiagram
    participant S as Планировщик
    participant B as Бот
    participant DB as База данных
    participant U as Пользователи

    S->>DB: Проверить запланированные рассылки
    DB->>S: Список рассылок
    
    loop Для каждой рассылки
        S->>DB: Получить получателей
        S->>DB: Получить контент рассылки
        
        loop Для каждого пользователя
            S->>B: Отправить сообщение
            B->>U: Сообщение рассылки
            S->>DB: Записать статус отправки
        end
        
        S->>DB: Обновить статистику рассылки
    end
```

**Сервис:** `app/services/mailing_service.py`

### 🔔 Поток Ретаргетинга (Брошенные корзины)

```mermaid
sequenceDiagram
    participant S as Планировщик
    participant DB as База данных
    participant B as Бот
    participant U as Пользователь

    S->>DB: Найти пользователей с товарами в корзине
    DB->>S: Список пользователей (корзина > 24ч)
    
    loop Для каждого пользователя
        S->>DB: Получить содержимое корзины
        S->>B: Отправить напоминание
        B->>U: "Не забудьте о своих очках!"
        S->>DB: Записать отправку напоминания
    end
```

**Планировщик:** `app/scheduler.py`

### 📱 Поток Автопостинга в Канал

```mermaid
sequenceDiagram
    participant S as Планировщик
    participant DB as База данных
    participant TG as Telegram API
    participant C as Канал

    S->>DB: Проверить расписание постов
    DB->>S: Контент для публикации
    
    S->>TG: Отправить пост в канал
    TG->>C: Опубликовать пост
    S->>DB: Обновить время последней публикации
```

## 🔐 Middleware и Безопасность

### 🛡️ Поток Проверки Прав

```mermaid
flowchart TD
    A[Входящее сообщение] --> B{Админская команда?}
    B -->|Да| C[AdminCheckMiddleware]
    B -->|Нет| F[UserMiddleware]
    
    C --> D{Telegram ID в списке админов?}
    D -->|Да| E[Разрешить доступ]
    D -->|Нет| G[Отклонить запрос]
    
    F --> H{Подписан на канал?}
    H -->|Да| I[Разрешить доступ]
    H -->|Нет| J[Предложить подписку]
    
    E --> K[Выполнить обработчик]
    I --> K
    G --> L[Игнорировать]
    J --> M[Показать сообщение о подписке]
```

**Middleware:** 
- `app/middlewares/admin_check.py`
- `app/middlewares/subscription_check.py`

## 📊 Метрики и Аналитика

### 📈 Отслеживание AIDA Воронки

```python
# Обновление этапа AIDA
async def update_aida_stage(user_id: int, stage: str):
    """
    Stages: attention -> interest -> desire -> action
    """
    await user_crud.update_aida_stage(user_id, stage)
    
    # Логирование для аналитики
    logger.info(f"User {user_id} moved to AIDA stage: {stage}")
```

### 📊 Конверсионная Аналитика

```sql
-- Конверсия по этапам AIDA
WITH aida_funnel AS (
    SELECT 
        aida_stage,
        COUNT(*) as users_count
    FROM users 
    GROUP BY aida_stage
)
SELECT 
    aida_stage,
    users_count,
    LAG(users_count) OVER (ORDER BY 
        CASE aida_stage
            WHEN 'attention' THEN 1
            WHEN 'interest' THEN 2  
            WHEN 'desire' THEN 3
            WHEN 'action' THEN 4
        END
    ) as prev_stage_count,
    ROUND(
        users_count * 100.0 / LAG(users_count) OVER (ORDER BY 
            CASE aida_stage
                WHEN 'attention' THEN 1
                WHEN 'interest' THEN 2
                WHEN 'desire' THEN 3
                WHEN 'action' THEN 4
            END
        ), 2
    ) as conversion_rate
FROM aida_funnel;
```

## 🔄 Обработка Ошибок

### ⚠️ Стратегия Обработки Ошибок

```python
@error_handler
async def handle_telegram_error(update: Update, exception: Exception):
    """Глобальный обработчик ошибок"""
    
    if isinstance(exception, TelegramBadRequest):
        # Обработка ошибок Telegram API
        logger.warning(f"Telegram API error: {exception}")
        
    elif isinstance(exception, DatabaseError):
        # Ошибки базы данных
        logger.error(f"Database error: {exception}")
        await send_error_to_admin(exception)
        
    elif isinstance(exception, ValidationError):
        # Ошибки валидации
        await update.message.reply_text(
            "❌ Некорректные данные. Попробуйте еще раз."
        )
    
    else:
        # Неожиданные ошибки
        logger.critical(f"Unexpected error: {exception}")
        await send_error_to_admin(exception)
```

Эта архитектура API обеспечивает:
- ✅ Четкое разделение пользовательских и административных потоков
- ✅ Надежную обработку состояний FSM
- ✅ Автоматизацию маркетинговых процессов
- ✅ Безопасность и контроль доступа
- ✅ Детальную аналитику и метрики