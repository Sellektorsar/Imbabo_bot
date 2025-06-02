.PHONY: help install dev test clean docker-build docker-run init-db

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	pip install -r requirements.txt

dev: ## Запустить бота в режиме разработки
	python run_dev.py

test: ## Запустить тесты
	python test_bot.py

init-db: ## Инициализировать базу данных с тестовыми данными
	python init_db.py

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -f imbabo_bot.db

docker-build: ## Собрать Docker образ
	docker build -t imbabo_bot .

docker-run: ## Запустить через Docker Compose
	docker-compose up -d

docker-logs: ## Показать логи Docker контейнера
	docker-compose logs -f bot

docker-stop: ## Остановить Docker контейнеры
	docker-compose down

format: ## Форматировать код
	black app/ database/ config/
	isort app/ database/ config/

lint: ## Проверить код линтером
	flake8 app/ database/ config/
	mypy app/ database/ config/

requirements: ## Обновить requirements.txt
	pip freeze > requirements.txt

backup-db: ## Создать резервную копию базы данных
	cp imbabo_bot.db imbabo_bot_backup_$(shell date +%Y%m%d_%H%M%S).db

restore-db: ## Восстановить базу данных из резервной копии (указать файл: make restore-db FILE=backup.db)
	cp $(FILE) imbabo_bot.db