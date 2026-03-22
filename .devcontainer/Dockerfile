# Используем базовый образ MS с Python (он стабильнее для дев-тулз)
FROM mcr.microsoft.com/devcontainers/python:3.11

# 1. Устанавливаем Node.js (нужен для Vue/Vite)
# Используем скрипт от nodesource для актуальной 20-й версии
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# 2. Устанавливаем системные утилиты для работы с БД и сетью
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 3. Глобальные инструменты для разработки
# Black для бэкенда, Vite для фронтенда
RUN pip install --no-cache-dir black \
    && npm install -g vite

# Устанавливаем рабочую директорию (она подмонтируется из VS Code)
WORKDIR /workspaces/safe-contact

# Настройка прав (чтобы файлы не создавались от root)
USER vscode