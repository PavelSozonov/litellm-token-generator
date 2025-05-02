FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Клонирование и установка LiteLLM
RUN git clone https://github.com/BerriAI/litellm.git /app \
    && pip install -e . \
    && pip install 'litellm[proxy]' \
    && pip install prisma

# Создание конфигурационного файла
RUN mkdir -p /app/config
COPY config/config.yaml /app/config/

EXPOSE 4000

CMD ["litellm", "--config", "/app/config/config.yaml", "--host", "0.0.0.0", "--port", "4000"]
