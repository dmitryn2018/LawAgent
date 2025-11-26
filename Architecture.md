# Architecture.md — Legal AI System

## Обзор системы

Legal AI System — это комплексная AI-система для юридической фирмы, реализующая 4 основных сценария:
1. **RAG-чатбот** — юридический консультант с семантическим поиском по документам
2. **Генератор документов** — создание юридических документов по шаблонам с AI-генерацией
3. **Due Diligence** — автоматизированные юридические проверки компаний
4. **AI-редактор** — анализ рисков в документах с рекомендациями из клауз-банка

---

## Архитектура высокого уровня

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              NGINX (8080)                               │
│                         Reverse Proxy / Load Balancer                   │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌───────────────────┐                    ┌────────────────────┐
│   Frontend (3000) │                    │   Backend (8000)   │
│   React + Vite    │◄──────REST────────►│   FastAPI          │
│   Material-UI     │                    │   SQLAlchemy       │
│   TipTap Editor   │                    │   Pydantic         │
└───────────────────┘                    └─────────┬──────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────────┐
                    │                              │                      │
                    ▼                              ▼                      ▼
          ┌─────────────────┐           ┌─────────────────┐    ┌─────────────────┐
          │   PostgreSQL    │           │  LLM Provider   │    │ Embedding       │
          │   + pgvector    │           │  OpenAI/Ollama/ │    │ Provider        │
          │   (5432)        │           │  Mock           │    │ OpenAI/Mock     │
          └─────────────────┘           └─────────────────┘    └─────────────────┘
```

---

## Структура проекта

```
law-agent/
├── backend/                     # FastAPI Backend
│   ├── app/
│   │   ├── api/                 # REST API endpoints
│   │   │   ├── auth.py          # Аутентификация JWT
│   │   │   ├── chat.py          # Чатбот API
│   │   │   ├── documents.py     # Документы API
│   │   │   ├── templates.py     # Шаблоны API
│   │   │   ├── due_diligence.py # DD проверки API
│   │   │   ├── clauses.py       # Клауз-банк API
│   │   │   └── analysis.py      # Анализ документов API
│   │   ├── core/
│   │   │   ├── config.py        # Конфигурация через Pydantic Settings
│   │   │   ├── database.py      # SQLAlchemy setup, session management
│   │   │   └── security.py      # JWT, password hashing (bcrypt)
│   │   ├── models/              # SQLAlchemy ORM модели
│   │   │   ├── user.py          # User (lawyer/admin)
│   │   │   ├── document.py      # Document, DocumentChunk (с vectors)
│   │   │   ├── chat.py          # ChatSession, ChatMessage
│   │   │   ├── template.py      # Template (form schema)
│   │   │   ├── clause.py        # Clause (клауз-банк)
│   │   │   └── due_diligence.py # DueDiligenceCheck
│   │   ├── schemas/             # Pydantic schemas (request/response)
│   │   ├── services/            # Бизнес-логика
│   │   │   ├── indexing_service.py  # Чанкинг + embedding документов
│   │   │   ├── search_service.py    # Семантический поиск (pgvector)
│   │   │   ├── chat_service.py      # RAG pipeline для чатбота
│   │   │   ├── dd_service.py        # Due Diligence логика
│   │   │   ├── template_service.py  # Генерация документов
│   │   │   ├── analysis_service.py  # Анализ рисков
│   │   │   └── document_service.py  # Парсинг файлов, чанкинг
│   │   └── providers/           # Абстракция провайдеров AI
│   │       ├── llm_provider.py      # OpenAI, Ollama, Mock
│   │       └── embedding_provider.py # OpenAI, Ollama, Mock
│   ├── alembic/                 # Database migrations
│   ├── prompts/                 # Промпты для LLM
│   └── seed.py                  # Seed script для демо-данных
│
├── frontend/                    # React Frontend
│   └── src/
│       ├── api/                 # API клиент (axios)
│       ├── pages/               # Страницы приложения
│       ├── components/          # React компоненты
│       ├── contexts/            # AuthContext
│       └── types/               # TypeScript типы
│
├── seed-data/                   # Тестовые/демо данные
│   ├── documents/               # Юридические документы для RAG
│   └── dd/                      # Mock-данные для DD проверок
│
└── docker/                      # Docker конфигурации
```

---

## Слои архитектуры Backend

### 1. API Layer (`app/api/`)

REST API endpoints с использованием FastAPI:

| Роутер | Prefix | Описание |
|--------|--------|----------|
| `auth.py` | `/api/auth` | Login, logout, token refresh |
| `users.py` | `/api/users` | CRUD пользователей |
| `documents.py` | `/api/documents` | Загрузка, поиск документов |
| `chat.py` | `/api/chat` | Сессии чата, сообщения |
| `templates.py` | `/api/templates` | Шаблоны, рендеринг |
| `due_diligence.py` | `/api/dd-checks` | DD проверки |
| `clauses.py` | `/api/clauses` | Клауз-банк |
| `analysis.py` | `/api/analysis` | Анализ документов |

### 2. Service Layer (`app/services/`)

Инкапсуляция бизнес-логики:

```
┌────────────────────────────────────────────────────────────────────────┐
│                           Service Layer                                │
├────────────────┬────────────────┬────────────────┬────────────────────┤
│ ChatService    │ DDService      │ TemplateService│ AnalysisService    │
│                │                │                │                    │
│ - RAG pipeline │ - Load seed    │ - Render DOCX  │ - Risk detection   │
│ - Context      │   data         │ - AI generation│ - Parse LLM output │
│   building     │ - AI analysis  │ - Form→Doc     │ - Clause matching  │
│ - History      │ - Risk calc    │                │                    │
└───────┬────────┴────────┬───────┴────────────────┴────────────────────┘
        │                 │
        ▼                 ▼
┌────────────────┐ ┌────────────────┐
│ SearchService  │ │ IndexingService│
│                │ │                │
│ - Vector search│ │ - Chunking     │
│ - Filtering    │ │ - Embedding    │
│ - Ranking      │ │ - Storage      │
└────────────────┘ └────────────────┘
```

### 3. Provider Layer (`app/providers/`)

Абстракция для AI-провайдеров с паттерном Strategy:

```python
# llm_provider.py
class LLMProvider(ABC):
    @abstractmethod
    async def generate(prompt, system_prompt, temperature, max_tokens) -> str
    @abstractmethod
    async def generate_chat(messages, temperature, max_tokens) -> Dict

# Реализации:
class OpenAIProvider(LLMProvider)      # GPT-4o-mini
class OllamaProvider(LLMProvider)      # Llama 3.1 (self-hosted)
class MockLLMProvider(LLMProvider)     # Детерминированные ответы для тестов
```

```python
# embedding_provider.py
class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(text) -> List[float]
    @abstractmethod
    async def embed_batch(texts) -> List[List[float]]

# Реализации:
class OpenAIEmbeddingProvider    # text-embedding-3-small (1536 dims)
class OllamaEmbeddingProvider    # nomic-embed-text (768 dims)
class MockEmbeddingProvider      # Детерминированные хэш-embeddings
```

### 4. Model Layer (`app/models/`)

SQLAlchemy ORM с pgvector:

```
┌──────────────┐       ┌─────────────────┐       ┌────────────────┐
│    User      │       │    Document     │       │ DocumentChunk  │
├──────────────┤       ├─────────────────┤       ├────────────────┤
│ id           │◄─┐    │ id              │◄──────│ id             │
│ email        │  │    │ title           │       │ document_id FK │
│ password_hash│  │    │ document_type   │       │ chunk_index    │
│ role         │  │    │ jurisdiction    │       │ text           │
│ is_active    │  │    │ content         │       │ embedding      │ ← Vector(1536)
└──────────────┘  │    │ indexing_status │       │ start_char     │
                  │    │ uploaded_by FK  │       │ end_char       │
                  │    └─────────────────┘       └────────────────┘
                  │
┌──────────────┐  │    ┌─────────────────┐       ┌────────────────┐
│ ChatSession  │◄─┤    │  ChatMessage    │       │   Template     │
├──────────────┤  │    ├─────────────────┤       ├────────────────┤
│ id           │  │    │ id              │       │ id             │
│ user_id FK   │──┘    │ session_id FK   │       │ name           │
│ jurisdiction │       │ role            │       │ category       │
│ mode         │       │ content         │       │ form_schema    │ ← JSON
└──────────────┘       │ sources         │ ←JSON │ optional_sects │
                       └─────────────────┘       └────────────────┘

┌──────────────────┐   ┌─────────────────┐
│ DueDiligenceCheck│   │     Clause      │
├──────────────────┤   ├─────────────────┤
│ id               │   │ id              │
│ user_id FK       │   │ title           │
│ company_name     │   │ body            │
│ check_type       │   │ category        │
│ status           │   │ tags            │ ← JSON
│ raw_data         │←J │ jurisdiction    │
│ ai_summary       │   │ practice_area   │
│ risk_indicators  │←J └─────────────────┘
│ risk_items       │←J
└──────────────────┘
```

---

## Реализация тест-кейсов (Mock система)

### Архитектура Mock-провайдеров

Система поддерживает полностью автономную работу без внешних API через переключение провайдеров:

```
LLM_PROVIDER=mock        # Использовать MockLLMProvider
EMBEDDING_PROVIDER=mock  # Использовать MockEmbeddingProvider
```

#### MockLLMProvider

**Файл:** `backend/app/providers/llm_provider.py`

Генерирует контекстно-зависимые ответы на основе ключевых слов в промпте:

```python
class MockLLMProvider(LLMProvider):
    async def generate(self, prompt, ...):
        prompt_lower = prompt.lower()
        
        if "договор" in prompt_lower or "contract" in prompt_lower:
            return """На основании анализа представленного договора:
            **Краткое содержание:** ...
            **Ключевые условия:** ...
            **Рекомендации:** ..."""
            
        elif "риск" in prompt_lower or "анализ" in prompt_lower:
            return """**Анализ рисков документа:**
            1. **Высокий риск:** Отсутствие ограничения ответственности...
            2. **Средний риск:** Неопределенность в сроках..."""
            
        elif "проверк" in prompt_lower or "due diligence" in prompt_lower:
            return """**Отчет о проверке компании**
            **1. Общая информация:** ...
            **Общая оценка риска: СРЕДНИЙ**"""
            
        elif "одобрени" in prompt_lower or "корпоративн" in prompt_lower:
            return """**Юридическое заключение...**
            Согласно ст. 46 ФЗ "Об ООО"..."""
```

#### MockEmbeddingProvider

**Файл:** `backend/app/providers/embedding_provider.py`

Генерирует детерминированные embeddings на основе хэша текста:

```python
class MockEmbeddingProvider(EmbeddingProvider):
    def _generate_mock_embedding(self, text: str) -> List[float]:
        # MD5 хэш текста → 1536-мерный вектор
        text_hash = hashlib.md5(text.encode()).hexdigest()
        embedding = []
        for i in range(1536):
            char_idx = i % len(text_hash)
            val = (ord(text_hash[char_idx]) - 48) / 100.0
            embedding.append(val)
        return embedding
```

**Важно:** Одинаковый текст всегда даёт одинаковый embedding, что обеспечивает воспроизводимость тестов.

---

## Seed-данные и их обработка

### Структура seed-data/

```
seed-data/
├── documents/                    # Документы для RAG-индекса
│   ├── corporate_law_ru.txt      # Корпоративное право РФ
│   ├── court_practice_ru.txt     # Судебная практика
│   ├── ma_practice_memo.txt      # M&A методология
│   └── uk_contract_law.txt       # Английское договорное право
│
└── dd/                           # Mock-данные для DD
    ├── testcorp.json             # "ТестКорп" - низкий риск
    └── riskcompany.json          # "РискКомпани" - высокий риск
```

### Обработка документов (RAG Pipeline)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Document Processing Flow                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. ЗАГРУЗКА (seed.py)                                                   │
│     ┌──────────────┐                                                     │
│     │ .txt/.docx/  │                                                     │
│     │ .pdf файлы   │                                                     │
│     └──────┬───────┘                                                     │
│            │                                                             │
│            ▼                                                             │
│  2. ИЗВЛЕЧЕНИЕ ТЕКСТА (DocumentService)                                  │
│     ┌──────────────────────────────────────┐                             │
│     │ - TXT: прямое чтение UTF-8           │                             │
│     │ - DOCX: python-docx → paragraphs     │                             │
│     │ - PDF: PyPDF2 → page.extract_text()  │                             │
│     └──────┬───────────────────────────────┘                             │
│            │                                                             │
│            ▼                                                             │
│  3. СОЗДАНИЕ ЗАПИСИ В БД (Document)                                      │
│     ┌──────────────────────────────────────┐                             │
│     │ documents table:                      │                             │
│     │ - title, content, jurisdiction        │                             │
│     │ - document_type, practice_area        │                             │
│     │ - indexing_status = "pending"         │                             │
│     └──────┬───────────────────────────────┘                             │
│            │                                                             │
│            ▼                                                             │
│  4. ИНДЕКСАЦИЯ (IndexingService)                                         │
│     ┌──────────────────────────────────────┐                             │
│     │ a) Чанкинг текста:                   │                             │
│     │    - chunk_size = 1000 chars         │                             │
│     │    - overlap = 100 chars             │                             │
│     │    - break at sentence boundaries    │                             │
│     │                                       │                             │
│     │ b) Генерация embeddings:             │                             │
│     │    - embed_batch(chunk_texts)        │                             │
│     │    - Vector(1536) → pgvector         │                             │
│     │                                       │                             │
│     │ c) Сохранение в document_chunks      │                             │
│     └──────────────────────────────────────┘                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Пример чанкинга** (`DocumentService.chunk_text`):

```python
def chunk_text(text: str, chunk_size=1000, overlap=100) -> list:
    """
    Разбивает текст на перекрывающиеся фрагменты,
    пытаясь разрывать на границах предложений.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        # Ищем конец предложения в последних 20% чанка
        for sep in [". ", ".\n", "!\n", "?\n", "\n\n"]:
            pos = text.rfind(sep, end - 200, end)
            if pos > start:
                end = pos + len(sep)
                break
        
        chunks.append({
            "text": text[start:end],
            "start_char": start,
            "end_char": end
        })
        start = end - overlap
    return chunks
```

### Обработка DD mock-данных

**Файл:** `backend/app/services/dd_service.py`

```python
def _load_seed_data(company_name: str, jurisdiction: str) -> Dict:
    """
    1. Нормализует имя компании
    2. Ищет соответствующий JSON в seed-data/dd/
    3. Если не найден - генерирует дефолтные данные
    """
    normalized = company_name.lower().replace(" ", "_").replace("ооо", "")
    
    seed_path = "/app/seed-data/dd"
    for seed_file in os.listdir(seed_path):
        if normalized in seed_file.lower():
            return json.load(open(f"{seed_path}/{seed_file}"))
    
    return _generate_demo_data(company_name, jurisdiction)
```

**Структура DD mock-файла** (`testcorp.json`):

```json
{
  "company_info": {
    "name": "ООО \"ТестКорп\"",
    "inn": "7701234567",
    "ogrn": "1027700123456",
    "registration_date": "2015-03-15",
    "authorized_capital": "10 000 000 руб.",
    "status": "Действующее"
  },
  "court_cases": [
    {
      "case_number": "А40-12345/2023",
      "role": "Ответчик",
      "claim_amount": "5 000 000 руб.",
      "status": "Рассматривается"
    }
  ],
  "debts": {
    "tax_debt": "0 руб.",
    "enforcement_proceedings": []
  },
  "sanctions_flags": {
    "ofac_list": false,
    "eu_sanctions": false
  },
  "beneficial_owners": [
    {"name": "Иванов И.И.", "share": "60%"}
  ]
}
```

**Алгоритм расчёта рисков:**

```python
def _calculate_risk_indicators(raw_data: Dict) -> Dict[str, str]:
    legal_risk = "low"
    financial_risk = "low"
    regulatory_risk = "low"
    
    # Court cases → Legal risk
    if len(raw_data.get("court_cases", [])) > 3:
        legal_risk = "high"
    elif len(raw_data.get("court_cases", [])) > 0:
        legal_risk = "medium"
    
    # Enforcement proceedings → Financial risk
    if raw_data.get("debts", {}).get("enforcement_proceedings"):
        financial_risk = "high"
    
    # Sanctions → Regulatory risk
    if any(raw_data.get("sanctions_flags", {}).values()):
        regulatory_risk = "high"
    
    # Overall = max(all risks)
    overall = "high" if "high" in [legal_risk, financial_risk, regulatory_risk] \
              else "medium" if "medium" in [...] else "low"
    
    return {"overall": overall, "legal": legal_risk, ...}
```

---

## Документы для RAG-индекса

### 1. corporate_law_ru.txt

**Назначение:** База знаний по корпоративному праву РФ

**Содержание:**
- ФЗ "Об обществах с ограниченной ответственностью"
- Переход долей к третьим лицам
- Преимущественное право покупки
- Крупные сделки и сделки с заинтересованностью
- Иностранные инвестиции (ФЗ-57)

**Тест-кейсы:**
- Вопрос: "Нужно ли корпоративное одобрение для отчуждения 25% доли?"
- Ожидаемые источники: corporate_law_ru.txt, court_practice_ru.txt

### 2. court_practice_ru.txt

**Назначение:** Судебная практика по корпоративным спорам

**Содержание:**
- Споры о переходе долей (нарушение преимущественного права)
- Споры об одобрении крупных сделок
- Сделки с заинтересованностью
- Сроки исковой давности

### 3. uk_contract_law.txt

**Назначение:** Английское договорное право (для мульти-юрисдикции)

**Содержание:**
- Formation of Contract (offer, acceptance, consideration)
- Terms (express, implied, conditions vs warranties)
- Remedies (damages, specific performance)
- UCTA 1977, Consumer Rights Act 2015
- Force Majeure vs Frustration

### 4. ma_practice_memo.txt

**Назначение:** Внутренний меморандум по M&A сделкам

**Содержание:**
- Этапы Due Diligence
- Структура SPA (Share Purchase Agreement)
- Заверения и гарантии продавца
- Механизмы защиты покупателя (Locked Box, Escrow, MAC)
- Корпоративные одобрения

---

## Шаблоны документов (Templates)

### Архитектура генерации документов

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Template Rendering Flow                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────┐  │
│  │   Frontend  │      │   Backend   │      │    TemplateService      │  │
│  │             │      │   API       │      │                         │  │
│  │ form_data   │─────►│ POST /render│─────►│ 1. Check template file  │  │
│  │ include_    │      │             │      │                         │  │
│  │ sections    │      │             │      │ 2a. If file exists:     │  │
│  │ use_ai      │      │             │      │     DocxTemplate.render │  │
│  └─────────────┘      └─────────────┘      │                         │  │
│                                            │ 2b. If no file:         │  │
│                                            │     _generate_from_form │  │
│                                            │                         │  │
│                                            │ 3. If use_ai=true:      │  │
│                                            │     LLM.generate()      │  │
│                                            └───────────┬─────────────┘  │
│                                                        │                │
│                                                        ▼                │
│                                            ┌─────────────────────────┐  │
│                                            │   rendered_text         │  │
│                                            │   file_id (optional)    │  │
│                                            │   download_url          │  │
│                                            └─────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Шаблоны в seed.py

**NDA (Соглашение о конфиденциальности):**

```python
{
    "name": "NDA (Соглашение о конфиденциальности)",
    "category": "nda",
    "jurisdiction": "RU",
    "form_schema": {
        "fields": [
            {"name": "party1", "type": "text", "label": "Раскрывающая сторона", "required": True},
            {"name": "party2", "type": "text", "label": "Получающая сторона", "required": True},
            {"name": "subject", "type": "textarea", "label": "Предмет раскрытия", "required": True},
            {"name": "term", "type": "text", "label": "Срок действия", "default": "3 (три) года"},
            {"name": "governing_law", "type": "select", "label": "Применимое право",
             "options": ["Российской Федерации", "Англии и Уэльса", "Штата Нью-Йорк"]}
        ]
    },
    "optional_sections": ["arbitration_clause", "liquidated_damages"]
}
```

**SPA (Договор купли-продажи долей):**

```python
{
    "name": "SPA (Договор купли-продажи долей) - упрощённый",
    "category": "spa",
    "form_schema": {
        "fields": [
            {"name": "seller", "type": "text", "label": "Продавец"},
            {"name": "buyer", "type": "text", "label": "Покупатель"},
            {"name": "company", "type": "text", "label": "Компания (объект сделки)"},
            {"name": "shares", "type": "text", "label": "Размер доли", "default": "100%"},
            {"name": "price", "type": "text", "label": "Цена сделки"},
            {"name": "payment_terms", "type": "textarea", "label": "Условия оплаты"}
        ]
    },
    "optional_sections": ["representations", "indemnification", "non_compete"]
}
```

---

## Клауз-банк (Clause Bank)

### Структура клауз

Каждая клауза имеет:
- **category:** arbitration, force_majeure, confidentiality, liability, termination, governing_law, etc.
- **jurisdiction:** RU, UK, или NULL (универсальная)
- **practice_area:** Corporate, M&A, Litigation
- **tags:** ["standard", "buyer_friendly", "seller_friendly", "balanced"]
- **body:** Полный текст клаузы с плейсхолдерами

### Примеры клауз из seed.py

**Арбитражная оговорка (ICC):**
```
Все споры... подлежат разрешению в Международном арбитражном суде ICC...
Место арбитража: [город]
Язык: русский
Количество арбитров: один / три
```

**MAC Clause (Material Adverse Change):**
```
Покупатель вправе отказаться от исполнения Договора без компенсации
в случае наступления Существенного неблагоприятного изменения...

Не признаются MAC:
- общие изменения экономической ситуации
- изменения, затрагивающие отрасль в целом
- изменения, вызванные объявлением о сделке
```

### Matching клауз к контексту

`AnalysisService.suggest_clauses`:

```python
def suggest_clauses(context, category, jurisdiction, practice_area, db):
    # 1. Фильтрация по параметрам
    query = db.query(Clause).filter(Clause.is_active == True)
    if category:
        query = query.filter(Clause.category == category)
    if jurisdiction:
        query = query.filter(
            (Clause.jurisdiction == jurisdiction) | 
            (Clause.jurisdiction.is_(None))  # универсальные клаузы
        )
    
    # 2. Keyword-based relevance scoring
    for clause in clauses:
        context_words = set(context.lower().split())
        clause_words = set((clause.title + clause.body).lower().split())
        common = context_words & clause_words - stop_words
        relevance = 0.5 + min(0.4, len(common) * 0.05)
        
    # 3. Sort by relevance, return top 10
```

---

## Промпты для LLM

### 1. chatbot_question.txt

```
Вы - опытный юридический консультант AI-системы юридической фирмы.
Ваша задача - отвечать на вопросы по праву, используя предоставленный контекст.

Правила:
1. Отвечайте точно и по существу
2. Ссылайтесь на источники
3. Если информации недостаточно - честно сообщите
4. Используйте профессиональную терминологию
5. Структурируйте ответ

Формат ответа:
- Краткий вывод (2-3 предложения)
- Развёрнутый ответ с обоснованием
- Ссылки на применимые нормы
- Рекомендации по дальнейшим действиям

Контекст из документов:
{context}
```

### 2. dd_report.txt

```
Вы - опытный юрист, специализирующийся на due diligence.
Составьте структурированный отчёт о проверке компании.

Формат отчёта:
1. ОБЩАЯ ИНФОРМАЦИЯ О КОМПАНИИ
2. СУДЕБНЫЕ СПОРЫ И ПРАВОВЫЕ РИСКИ - Уровень риска: [низкий/средний/высокий]
3. ФИНАНСОВЫЕ РИСКИ - Уровень риска: [низкий/средний/высокий]
4. РЕГУЛЯТОРНЫЕ РИСКИ - Уровень риска: [низкий/средний/высокий]
5. ВЫВОДЫ И РЕКОМЕНДАЦИИ

Данные для анализа:
{data}
```

### 3. document_analysis.txt

```
Вы - опытный юрист-аналитик. Проведите анализ юридического документа.

Формат ответа:
1. КРАТКОЕ СОДЕРЖАНИЕ [2-3 абзаца]
2. ВЫЯВЛЕННЫЕ РИСКИ
   - Название риска
   - Уровень (низкий/средний/высокий)
   - Цитата из документа
   - Рекомендация
3. РЕКОМЕНДАЦИИ ПО ДОРАБОТКЕ
4. КЛЮЧЕВЫЕ УСЛОВИЯ
5. СТОРОНЫ ДОГОВОРА
```

---

## Семантический поиск (RAG)

### SearchService Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Semantic Search Flow                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  User Query: "Нужно ли одобрение для отчуждения 25% доли?"              │
│       │                                                                  │
│       ▼                                                                  │
│  ┌────────────────────┐                                                  │
│  │ EmbeddingProvider  │                                                  │
│  │ embed(query)       │ → [0.012, -0.034, 0.089, ...]  (1536 dims)       │
│  └────────┬───────────┘                                                  │
│           │                                                              │
│           ▼                                                              │
│  ┌────────────────────────────────────────────────────────┐              │
│  │  PostgreSQL + pgvector                                  │              │
│  │                                                         │              │
│  │  SELECT c.*, d.title,                                   │              │
│  │         1 - (c.embedding <=> '{query_vec}'::vector)     │              │
│  │           as relevance                                  │              │
│  │  FROM document_chunks c                                 │              │
│  │  JOIN documents d ON d.id = c.document_id               │              │
│  │  WHERE d.indexing_status = 'indexed'                    │              │
│  │    AND d.jurisdiction = 'RU'  -- optional filter        │              │
│  │  ORDER BY c.embedding <=> '{query_vec}'::vector         │              │
│  │  LIMIT 7                                                │              │
│  └────────┬───────────────────────────────────────────────┘              │
│           │                                                              │
│           ▼                                                              │
│  ┌────────────────────────────────────────────────────────┐              │
│  │  Results (top 7 chunks):                                │              │
│  │  1. corporate_law_ru.txt:chunk_3 (relevance: 0.89)      │              │
│  │  2. court_practice_ru.txt:chunk_1 (relevance: 0.85)     │              │
│  │  3. corporate_law_ru.txt:chunk_5 (relevance: 0.82)      │              │
│  │  ...                                                    │              │
│  └────────────────────────────────────────────────────────┘              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Cosine Distance в pgvector

```sql
-- Оператор <=> вычисляет косинусное расстояние
-- relevance = 1 - distance (чем ближе к 1, тем лучше)

-- Создание индекса для ускорения поиска
CREATE INDEX ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

---

## Docker-инфраструктура

### docker-compose.yml

| Сервис | Image | Port | Описание |
|--------|-------|------|----------|
| postgres | pgvector/pgvector:pg16 | 5432 | БД с векторным расширением |
| backend | ./backend/Dockerfile | 8000 | FastAPI + uvicorn |
| frontend | ./frontend/Dockerfile | 3000 | Vite dev server |
| nginx | nginx:alpine | 8080 | Reverse proxy |

### Volumes

```yaml
volumes:
  postgres_data:      # Персистентное хранилище БД
  backend_storage:    # Сгенерированные файлы

# Bind mount для hot-reload в dev:
- ./backend:/app
- ./seed-data:/app/seed-data
- ./frontend:/app
```

### Переменные окружения

```bash
# LLM Configuration
LLM_PROVIDER=mock|openai|ollama
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Embedding Configuration
EMBEDDING_PROVIDER=mock|openai|ollama
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/legal_ai

# Security
SECRET_KEY=...
JWT_SECRET_KEY=...
JWT_EXPIRE_MINUTES=1440  # 24 hours
```

---

## Flow тест-кейсов

### Сценарий 1: RAG Chatbot

```
1. Юрист входит в систему (lawyer@example.com)
2. Создаёт новый чат с jurisdiction=RU
3. Задаёт вопрос: "Нужно ли корпоративное одобрение для отчуждения 25% доли?"
4. Система:
   a) SearchService.search(query, jurisdiction="RU", top_k=7)
   b) Строит контекст из найденных чанков
   c) ChatService.generate_response() → LLM с system prompt + context
   d) Сохраняет sources в ChatMessage
5. Возвращает ответ со ссылками на источники
```

### Сценарий 2: Due Diligence

```
1. Юрист вводит: company_name="ТестКорп", check_type="ma_dd"
2. Система:
   a) DDService._load_seed_data("ТестКорп") → testcorp.json
   b) DDService._generate_analysis() → LLM анализ raw_data
   c) DDService._calculate_risk_indicators() → {overall: "medium", ...}
   d) DDService._extract_risk_items() → список конкретных рисков
3. Возвращает структурированный отчёт с risk_indicators
```

### Сценарий 3: Template Generation

```
1. Юрист выбирает шаблон NDA
2. Заполняет форму: party1="ООО Альфа", party2="ООО Бета", ...
3. TemplateService.render_template():
   a) Если use_ai=false: _generate_nda(form_data) → hardcoded template
   b) Если use_ai=true: LLM.generate() с template_generation.txt
4. Возвращает rendered_text для preview/download
```

### Сценарий 4: Document Analysis

```
1. Юрист загружает/вставляет текст договора в редактор
2. AnalysisService.analyze_document(text):
   a) LLM анализ с document_analysis.txt prompt
   b) _parse_analysis() → извлечение структуры из LLM ответа
   c) _detect_common_risks(text) → regex-based fallback
3. Возвращает: summary, risks[], recommendations[], key_terms[]
4. UI подсвечивает risk.spans в редакторе
```

---

## Тестирование

### Mock режим

Для запуска без внешних API:

```bash
# .env
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=mock
```

### Характеристики Mock-провайдеров

| Аспект | MockLLM | MockEmbedding |
|--------|---------|---------------|
| Детерминированность | Да (по ключевым словам) | Да (MD5 hash) |
| Латентность | ~0ms | ~0ms |
| Качество | Шаблонные ответы | Работающий поиск |
| Тест-кейсы | Все 4 сценария | RAG поиск |

### Seed данные для тестов

```bash
# Загрузка демо-данных
docker-compose exec backend python seed.py

# Результат:
# - 3 пользователя (admin, lawyer, lawyer2)
# - 4 документа (проиндексированы в pgvector)
# - 3 шаблона (NDA, SPA, Employment)
# - 10 клауз (арбитраж, форс-мажор, конфиденциальность, etc.)
```

---

## Partner-focused UX Enhancements (v1.1)

Расширения системы для двух типов партнёров: банковский (акцент на безопасности и ревью) и M&A (акцент на влиянии на сделку).

### Runtime Meta Endpoint

**API:** `GET /api/meta/runtime`

Возвращает информацию о текущих AI-провайдерах:

```json
{
  "llm_provider": "openai" | "ollama" | "mock",
  "embedding_provider": "openai" | "ollama" | "mock"
}
```

**Файл:** `app/api/meta.py`

**UI:** В шапке приложения (Layout.tsx) отображается Security Badge:
- 🔒 "AI: локальный" (зелёный) — для ollama/mock
- ⚠️ "AI: внешний" (жёлтый) — для openai

### Расширенный анализ документов

**Новые поля в `DocumentAnalysisResponse`:**

```python
class DocumentAnalysisResponse(BaseModel):
    summary: str
    risks: List[DocumentRisk]
    recommendations: List[str]
    key_terms: Optional[List[str]]
    parties: Optional[List[str]]
    overall_risk_level: str  # NEW: "low" | "medium" | "high"
    deal_impact: Optional[DealImpact]  # NEW
```

**Структура `DealImpact`:**

```python
class DealImpact(BaseModel):
    price: str      # Влияние на цену/оценку
    structure: str  # Влияние на структуру сделки
    control: str    # Влияние на контроль/управление
```

**Расширение `DocumentRisk`:**

```python
class DocumentRisk(BaseModel):
    # ... existing fields ...
    impact_on_deal: Optional[str]  # NEW: "deal_breaker" | "negotiable" | "cosmetic"
```

**UI:**
- Цветной бейдж общего риска (🟢/🟡/🔴) над редактором
- Бейджи impact_on_deal рядом с каждым риском
- Отдельный таб "Сделка" с блоком влияния на цену/структуру/контроль

### Review Status (статус ревью юристом)

**Модель:** `SavedAnalysis` (app/models/analysis.py)

```python
class SavedAnalysis(Base):
    id: int
    document_text_hash: str  # SHA-256 хэш текста
    analysis_data: JSON      # Полные данные анализа
    review_status: str       # "unreviewed" | "reviewed"
    reviewed_by_id: int FK
    reviewed_at: datetime
    created_at: datetime
    updated_at: datetime
```

**API Endpoints:**

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/analysis/save` | Сохранить анализ |
| GET | `/api/analysis/saved/{id}` | Получить анализ по ID |
| GET | `/api/analysis/saved/by-hash/{hash}` | Получить по хэшу документа |
| POST | `/api/analysis/saved/{id}/review` | Отметить как проверенный |

**UI:**
- Бейдж "Не проверено" (серый) / "Проверено: ФИО, дата" (зелёный)
- Кнопка "Отметить как проверено" для авторизованных пользователей

### Client Letter Generation (генерация письма клиенту)

**API:** `POST /api/analysis/client-letter`

```json
// Request
{
  "summary": "...",
  "risks": [...],
  "deal_impact": {...},
  "language": "ru" | "en"
}

// Response
{
  "letter_text": "..."
}
```

**Prompt:** `prompts/client_letter.txt`

**UI:** Кнопка "✉️ Письмо клиенту" → модальное окно с текстом + кнопка копирования

### Impact on Deal в DD-отчётах

**Расширение `RiskItem` в DD:**

```python
class RiskItem(BaseModel):
    category: str
    severity: str
    title: str
    description: str
    impact_on_deal: Optional[str]  # NEW: "deal_breaker" | "negotiable" | "cosmetic"
```

Логика присвоения в `dd_service.py`:
- Судебные иски > 10M руб → deal_breaker
- Исполнительные производства → deal_breaker
- Санкции → deal_breaker
- Судебные иски < 1M руб → cosmetic
- Остальное → negotiable

### Partner/Junior View Mode

Переключатель режима отображения на страницах анализа и DD:

**Режим "Партнёр":**
- Только топ-3 критических риска (high severity / deal_breaker)
- Блок deal_impact
- Общий уровень риска
- Скрытые raw data в DD

**Режим "Джун":**
- Все риски
- Все рекомендации
- Все key_terms
- Raw data в DD

### Sources Display (отображение источников в чате)

Под каждым ответом ассистента:
- Строка "📚 Основано на: [Doc1], [Doc2], ..." (всегда видна)
- Раскрываемый аккордеон с подробностями и сниппетами

**Поле `ChatMessage.sources`:**

```json
[
  {
    "document_id": 1,
    "chunk_id": 3,
    "title": "corporate_law_ru.txt",
    "snippet": "...",
    "relevance": 0.89
  }
]
```

### Обновлённая таблица API роутеров

| Роутер | Prefix | Описание |
|--------|--------|----------|
| `auth.py` | `/api/auth` | Login, logout, token refresh |
| `users.py` | `/api/users` | CRUD пользователей |
| `documents.py` | `/api/documents` | Загрузка, поиск документов |
| `chat.py` | `/api/chat` | Сессии чата, сообщения |
| `templates.py` | `/api/templates` | Шаблоны, рендеринг |
| `due_diligence.py` | `/api/dd-checks` | DD проверки |
| `clauses.py` | `/api/clauses` | Клауз-банк |
| `analysis.py` | `/api/analysis` | Анализ документов, review, client letter |
| `meta.py` | `/api/meta` | **NEW:** Runtime info |

---

## Заключение

Система реализует полноценный production-ready архитектурный паттерн:

1. **Layered Architecture:** API → Service → Provider → Model
2. **Strategy Pattern:** Сменяемые LLM/Embedding провайдеры
3. **RAG Pipeline:** Chunking → Embedding → Vector Search → Context Building
4. **Mock System:** Полностью автономная работа для тестирования
5. **Seed Data:** Реалистичные юридические документы и mock-данные для DD
6. **Partner-focused UX:** Режимы отображения Partner/Junior, security badges, deal impact analysis
