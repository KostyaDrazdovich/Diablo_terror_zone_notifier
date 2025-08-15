# Python 3.13 slim
FROM python:3.13-slim

# Система: инструменты для сборки asyncpg при необходимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Переменные среды
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

# Установка зависимостей
COPY requirements/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники
COPY src/ ./src/

# Непривилегированный пользователь
RUN useradd -m botuser
USER botuser

# Запуск
CMD ["python", "-m", "bot.app"]