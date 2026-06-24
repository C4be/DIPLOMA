FROM python:3.13.2-slim


# PYTHONDONTWRITEBYTECODE: Запрещает Python писать .pyc файлы
# PYTHONUNBUFFERED: Гарантирует, что логи сразу попадут в консоль Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# --- ЭТАП КЭШИРОВАНИЯ ЗАВИСИМОСТЕЙ ---
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- ЭТАП КОПИРОВАНИЯ КОДА ---
COPY src/ .

# Открываем порт (информативно)
EXPOSE 8000

# Запускаем приложение
# --host 0.0.0.0 обязательно для доступа извне контейнера
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]