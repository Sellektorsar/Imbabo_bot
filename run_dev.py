"""
Скрипт для запуска бота в режиме разработки
"""
import asyncio
import logging
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from main import main

if __name__ == "__main__":
    # Настройка логирования для разработки
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/dev.log', encoding='utf-8')
        ]
    )
    
    # Создаем директорию для логов если её нет
    Path('logs').mkdir(exist_ok=True)
    
    print("🚀 Запуск бота в режиме разработки...")
    print("📝 Логи сохраняются в logs/dev.log")
    print("🛑 Для остановки нажмите Ctrl+C")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")
        sys.exit(1)