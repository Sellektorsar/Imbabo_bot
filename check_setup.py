"""
Скрипт для проверки корректности настройки проекта
"""
import asyncio
import sys
from pathlib import Path

def check_files():
    """Проверка наличия необходимых файлов"""
    print("🔍 Проверка файлов...")
    
    required_files = [
        ".env.example",
        "requirements.txt", 
        "main.py",
        "init_db.py",
        "docker-compose.yml",
        "Dockerfile",
        "Makefile"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
        else:
            print(f"  ✅ {file}")
    
    if missing_files:
        print(f"  ❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    
    return True

def check_directories():
    """Проверка структуры директорий"""
    print("\n📁 Проверка структуры директорий...")
    
    required_dirs = [
        "app",
        "app/handlers",
        "app/handlers/user", 
        "app/middlewares",
        "app/models",
        "app/states",
        "app/utils",
        "database",
        "config"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
        else:
            print(f"  ✅ {dir_path}/")
    
    if missing_dirs:
        print(f"  ❌ Отсутствуют директории: {', '.join(missing_dirs)}")
        return False
    
    return True

def check_config():
    """Проверка конфигурации"""
    print("\n⚙️ Проверка конфигурации...")
    
    try:
        from config import settings
        print(f"  ✅ Конфигурация загружена")
        print(f"  📊 База данных: {settings.database_url}")
        print(f"  🤖 Токен бота: {'✅ Установлен' if settings.bot_token else '❌ Не установлен'}")
        print(f"  👥 Админы: {len(settings.admin_ids_list)} пользователей")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка конфигурации: {e}")
        return False

def check_database():
    """Проверка подключения к базе данных"""
    print("\n💾 Проверка базы данных...")
    
    try:
        from database import DatabaseManager
        print("  ✅ Модули базы данных импортированы")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка импорта БД: {e}")
        return False

async def check_bot_connection():
    """Проверка подключения к Telegram API"""
    print("\n🤖 Проверка подключения к Telegram API...")
    
    try:
        from config import settings
        if not settings.bot_token or settings.bot_token == "your_bot_token_here":
            print("  ⚠️ Токен бота не настроен в .env файле")
            return False
            
        from aiogram import Bot
        bot = Bot(token=settings.bot_token)
        
        me = await bot.get_me()
        print(f"  ✅ Подключение успешно: @{me.username}")
        await bot.session.close()
        return True
    except Exception as e:
        print(f"  ❌ Ошибка подключения: {e}")
        return False

def check_dependencies():
    """Проверка установленных зависимостей"""
    print("\n📦 Проверка зависимостей...")
    
    required_packages = [
        "aiogram",
        "sqlalchemy", 
        "asyncpg",
        "apscheduler",
        "pydantic",
        "python-dotenv"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")
    
    if missing_packages:
        print(f"\n  💡 Установите недостающие пакеты:")
        print(f"     pip install {' '.join(missing_packages)}")
        return False
    
    return True

async def main():
    """Основная функция проверки"""
    print("🚀 Проверка настройки проекта @imbabo_bot_v2\n")
    
    checks = [
        ("Файлы", check_files()),
        ("Директории", check_directories()),
        ("Зависимости", check_dependencies()),
        ("Конфигурация", check_config()),
        ("База данных", check_database()),
    ]
    
    # Асинхронная проверка подключения к боту
    bot_check = await check_bot_connection()
    checks.append(("Telegram API", bot_check))
    
    print("\n" + "="*50)
    print("📋 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
    print("="*50)
    
    all_passed = True
    for name, result in checks:
        status = "✅ ПРОЙДЕНО" if result else "❌ ОШИБКА"
        print(f"{name:20} {status}")
        if not result:
            all_passed = False
    
    print("="*50)
    
    if all_passed:
        print("🎉 Все проверки пройдены! Проект готов к запуску.")
        print("\n💡 Следующие шаги:")
        print("   1. Настройте .env файл с вашими данными")
        print("   2. Запустите: make init-db")
        print("   3. Запустите: make dev")
    else:
        print("⚠️ Обнаружены проблемы. Исправьте их перед запуском.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())