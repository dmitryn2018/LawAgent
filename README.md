# Legal AI System - Pilot

AI-система для юридической фирмы с четырьмя основными сценариями:
1. **Чатбот юриста** - RAG-based chatbot с доступом к правовым материалам
2. **Генератор документов** - создание документов по шаблонам
3. **Due Diligence проверки** - автоматизированные юридические проверки
4. **Редактор с AI-ассистентом** - Word-подобный редактор с анализом рисков

## Быстрый старт

### Требования
- Docker и Docker Compose
- (Опционально) OpenAI API ключ для dev-режима

### Запуск

1. Скопируйте файл окружения:
```bash
cp .env.example .env
```

2. Заполните переменные окружения в `.env`:
   - `OPENAI_API_KEY` - ваш OpenAI API ключ (или оставьте `LLM_PROVIDER=mock` для тестов)
   - `SECRET_KEY` и `JWT_SECRET_KEY` - сгенерируйте уникальные ключи

3. Запустите сервисы:
```bash
docker-compose up --build
```

4. Загрузите демо-данные:
```bash
docker-compose exec backend python seed.py
```

5. Откройте приложение: http://localhost:8080

## Демо-сценарии

### Учётные данные
- **Юрист:** lawyer@example.com / password123
- **Администратор:** admin@example.com / password123

### Сценарий 1: Чатбот
1. Войдите как юрист
2. Перейдите в раздел "Чатбот"
3. Выберите юрисдикцию: РФ
4. Задайте вопрос: "Нужно ли корпоративное одобрение для сделки по отчуждению 25% доли в ООО в пользу иностранного инвестора?"
5. Просмотрите ответ с источниками

### Сценарий 2: Генератор документов
1. Перейдите в раздел "Документы" → "Шаблоны"
2. Выберите шаблон NDA
3. Заполните форму: стороны, юрисдикция, предмет
4. Нажмите "Сгенерировать"
5. Скачайте или откройте в редакторе

### Сценарий 3: Due Diligence
1. Перейдите в раздел "Проверки"
2. Введите название компании: "ТестКорп"
3. Выберите тип: M&A Due Diligence
4. Запустите проверку
5. Просмотрите структурированный отчёт

### Сценарий 4: Редактор с AI
1. Перейдите в раздел "Редактор"
2. Загрузите или создайте документ
3. Нажмите "Анализировать"
4. Просмотрите риски в боковой панели
5. Используйте клауз-банк для вставки формулировок

## Структура проекта

```
law-agent/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── providers/      # LLM/Embedding providers
│   ├── alembic/            # Database migrations
│   └── prompts/            # LLM prompts
├── frontend/               # React + TypeScript frontend
│   ├── src/
│   │   ├── pages/          # Page components
│   │   ├── components/     # Reusable components
│   │   ├── api/            # API client
│   │   ├── contexts/       # React contexts
│   │   └── types/          # TypeScript types
├── seed-data/              # Demo data
│   ├── documents/          # Sample documents
│   ├── templates/          # DOCX templates
│   ├── clauses/            # Clause bank
│   └── dd/                 # Due diligence samples
├── docker/                 # Docker configs
└── docker-compose.yml
```

## API Документация

После запуска доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Технологии

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- PostgreSQL + pgvector
- OpenAI API / Ollama

### Frontend
- React 18 + TypeScript
- Vite
- Material-UI (MUI)
- TipTap (редактор)
- React Router

## Разработка

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Лицензия

Proprietary - All rights reserved

Requests: volkova_taya01@mail.ru
