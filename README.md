# Start RAG Agent

Интеллектуальный чат-бот для консультации по правилам международной стажировки.  
Построен на основе **LangGraph + FastAPI + ChromaDB**.

---

## Что делает

- Отвечает на вопросы строго по базе знаний о стажировке (без галлюцинаций)
- Поддерживает историю диалога в рамках сессии (контекст последних 20 сообщений)
- Задаёт уточняющий вопрос, если запрос неоднозначен (например, не указана страна)
- Поддерживает несколько LLM провайдеров: OpenAI, Ollama, GigaChat

---

## Архитектура

```
User → FastAPI → LangGraph Agent
                    ├── retrieve_node       (поиск в ChromaDB)
                    ├── check_clarification (нужно ли уточнение?)
                    ├── clarification_answer (задать уточняющий вопрос)
                    └── generate_answer      (сформировать ответ)
```

---

## Быстрый старт (Docker)

### 1. Клонировать репозиторий

```bash
git clone <url>
cd cdekstart-rag-agent
```

### 2. Создать файл .env

```bash
cp .env.example .env
```

Минимальная конфигурация для Ollama (локально, бесплатно):

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### 3. Запустить контейнеры

```bash
docker-compose up --build
```

### 4. Загрузить модели в Ollama (только для Ollama провайдера)

В новом терминале:

```bash
docker exec -it cdekstart-rag-agent-ollama-1 ollama pull llama3.2:3b
docker exec -it cdekstart-rag-agent-ollama-1 ollama pull nomic-embed-text
```

> После загрузки моделей перезапустите app:  
> `docker-compose restart app`

### 5. Проверить работу

Откройте в браузере: **http://localhost:8000/docs**

---

## Установка без Docker (Python venv)

### 1. Клонировать репозиторий

```bash
git clone <url>
cd cdekstart-rag-agent
```

### 2. Создать и активировать виртуальное окружение

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Создать файл .env

```bash
cp .env.example .env
# Отредактируй .env под нужный провайдер
```

### 5. Установить Ollama (если используете Ollama)

Скачайте с [ollama.com](https://ollama.com/download) и установите.

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 6. Запустить сервер

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Сервер запустится на **http://localhost:8000**

---

## Проверка через Swagger UI

### Открыть Swagger

Перейдите в браузере по адресу:

```
http://localhost:8000/docs
```

### Отправить запрос через Swagger

1. Нажмите на **POST /chat**
2. Нажмите кнопку **"Try it out"**
3. В поле **Request body** введите:

```json
{
  "session_id": "test-session-1",
  "message": "Какая стипендия в Германии?"
}
```

4. Нажмите **"Execute"**

5. Пролистайте вниз — увидите ответ:

```json
{
  "session_id": "test-session-1",
  "response": "Стипендия в Германии (Берлин) составляет 1200 евро в месяц.",
  "needs_clarification": false
}
```


### Тест уточняющего вопроса

В поле Request body введите запрос без указания страны:

```json
{
  "session_id": "test-session-2",
  "message": "Какой налог на стипендию?"
}
```

Ожидаемый ответ:

```json
{
  "session_id": "test-session-2",
  "response": "Уточните, пожалуйста, какая страна вас интересует: Германия (Берлин) или Франция (Париж)?",
  "needs_clarification": true
}
```

---

## Проверка через консоль (curl)

### POST /chat — задать вопрос

**Linux / macOS:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"user1","message":"Какая стипендия в Германии?"}'
```

**Windows (cmd):**
```cmd
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"session_id\":\"user1\",\"message\":\"Какая стипендия в Германии?\"}"
```

**Windows (PowerShell):**
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/chat" `
  -ContentType "application/json" `
  -Body '{"session_id":"user1","message":"Какая стипендия в Германии?"}'
```

---

### Тест диалога с контекстом

```bash
# Шаг 1: неоднозначный вопрос
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"dialog1","message":"Какой налог на стипендию?"}'

# Ожидаем needs_clarification: true

# Шаг 2: уточняем страну
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"dialog1","message":"Меня интересует Франция"}'

# Ожидаем: налог 20% для Франции
```

---

### GET /health — проверка состояния

```bash
curl http://localhost:8000/health
```

Ответ:
```json
{"status": "ok"}
```

---

### DELETE /session/{session_id} — очистить историю

```bash
curl -X DELETE http://localhost:8000/session/user1
```

Ответ:
```json
{"status": "cleared", "session_id": "user1"}
```

---

### Вопрос про рабочий день в Берлине

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"user2","message":"Какой рабочий день в Берлине?"}'
```

---

### Вопрос про дедлайны

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"user3","message":"Когда дедлайн подачи документов?"}'
```

---

## Настройка LLM провайдера

В файле `.env` установите переменную `LLM_PROVIDER`:

| Значение | Описание | Стоимость |
|----------|----------|-----------|
| `openai` | OpenAI API (GPT-4o-mini) | Платно |
| `ollama` | Локальная модель | Бесплатно |
| `gigachat` | GigaChat от Сбера | Платно |

---

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_PROVIDER=openai
```

Получить ключ: [platform.openai.com](https://platform.openai.com/api-keys)

---

### Ollama (локально, бесплатно)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

> В Docker Compose замените `localhost` на `ollama`:  
> `OLLAMA_BASE_URL=http://ollama:11434`

Доступные модели:
```bash
ollama pull llama3.2:3b      # лёгкая, быстрая
ollama pull llama3.1:8b      # лучше качество
ollama pull mistral:7b       # альтернатива
```

---

### GigaChat

```env
LLM_PROVIDER=gigachat
GIGACHAT_API_KEY=ваш_ключ_здесь
GIGACHAT_MODEL=GigaChat
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxxxxx
```

>  **Ограничение**: GigaChat через `langchain-community` не поддерживает  
> embedding API. Используйте OpenAI или Ollama для эмбеддингов.

Получить ключ: [developers.sber.ru/gigachat](https://developers.sber.ru/portal/products/gigachat-api)

---

## Добавление нового LLM провайдера

Пример добавления **Anthropic Claude**:

### Шаг 1: Установить библиотеку

```bash
pip install langchain-anthropic
```

Добавить в `requirements.txt`:
```
langchain-anthropic==0.1.0
```

### Шаг 2: Обновить `app/config.py`

```python
class Settings(BaseSettings):
    LLM_PROVIDER: Literal["openai", "ollama", "gigachat", "anthropic"] = "ollama"
    
    # Добавить новые поля
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"
```

### Шаг 3: Добавить в `app/agent/nodes.py` функцию `get_llm()`

```python
def get_llm():
    # ... существующий код ...
    
    if settings.LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=0.1,
        )
```

### Шаг 4: Обновить `.env`

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-haiku-20240307
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxxxxx
```

### Шаг 5: Перезапустить сервер

```bash
# Docker
docker-compose up --build

# или venv
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Пример добавления Yandex GPT

```python
# Шаг 1
pip install yandex-chain  # или langchain-yandex

# Шаг 2 — config.py
YANDEX_API_KEY: str = ""
YANDEX_FOLDER_ID: str = ""
YANDEX_MODEL: str = "yandexgpt-lite"

# Шаг 3 — nodes.py get_llm()
if settings.LLM_PROVIDER == "yandex":
    from langchain_community.llms import YandexGPT
    return YandexGPT(
        api_key=settings.YANDEX_API_KEY,
        folder_id=settings.YANDEX_FOLDER_ID,
    )
```

---

## Структура проекта

```
cdekstart-rag-agent/
├── app/
│   ├── main.py              # FastAPI приложение
│   ├── config.py            # Настройки (pydantic-settings)
│   ├── models.py            # Pydantic модели запрос/ответ
│   └── agent/
│       ├── graph.py         # LangGraph граф
│       ├── nodes.py         # Узлы графа (retrieve, check, generate)
│       ├── state.py         # Состояние агента
│       ├── tools.py         # RAG инструмент поиска
│       └── rag/
│           └── indexer.py   # Индексация документов в ChromaDB
|           └── retriver.py
├── data/                    # База знаний (txt файлы)
│   ├── general_info.txt
│   ├── deadlines.txt
│   ├── benefits.txt
│   ├── germany_rules.txt
│   └── france_rules.txt
├── chroma_db/               # Векторная БД (создаётся автоматически)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example             # Шаблон конфигурации
├── .env                     # Настройки (не коммитить!)
├── .gitignore
└── README.md
```

---

## API Reference

### POST /chat

Отправить сообщение боту.

**Request:**
```json
{
  "session_id": "string",
  "message": "string"
}
```

**Response:**
```json
{
  "session_id": "string",
  "response": "string",
  "needs_clarification": false
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `session_id` | string | Уникальный ID сессии пользователя |
| `message` | string | Вопрос пользователя |
| `response` | string | Ответ бота |
| `needs_clarification` | boolean | true если бот просит уточнение |

---

### GET /health

Проверка состояния сервиса.

**Response:**
```json
{"status": "ok"}
```

---

### DELETE /session/{session_id}

Очистить историю диалога сессии.

**Response:**
```json
{
  "status": "cleared",
  "session_id": "user-123"
}
```

---

## Ограничения

| Ограничение | Описание |
|-------------|----------|
| История сессий | Хранится в памяти, сбрасывается при перезапуске |
| Лимит истории | Последние 20 сообщений на сессию |
| GigaChat | Не поддерживает embeddings — нужен OpenAI или Ollama |
| Ollama качество | Зависит от выбранной модели |
| OpenAI | Требует API ключ с балансом |

---

## Зависимости

```txt
fastapi==0.111.0
uvicorn==0.30.1
langchain==0.2.6
langchain-community==0.2.6
langchain-openai==0.1.13
langchain-ollama==0.1.1
langchain-chroma==0.1.2
langchain-text-splitters==0.2.0
langgraph==0.1.19
chromadb==0.5.3
python-dotenv==1.0.1
pydantic==2.7.4
pydantic-settings==2.3.4
tiktoken==0.7.0
httpx==0.27.0
```