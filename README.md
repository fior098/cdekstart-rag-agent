# Start RAG Agent

Чат-бот для консультации по правилам международной стажировки. Построен на основе LangGraph + FastAPI + ChromaDB.

## Что делает

- Отвечает на вопросы по базе знаний о стажировке
- Поддерживает историю диалога (контекст) в рамках сессии
- Задаёт уточняющий вопрос, если запрос неоднозначен (например, не указана страна)
- Не выдумывает ответы — только строго по документам

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone <url>
cd cdekstart-rag-agent
```

### 2. Создать файл .env

```bash
cp .env.example .env
```

Отредактировать `.env` под нужный провайдер.

### 3. Запустить

```bash
docker-compose up --build
```

API будет доступен по адресу: `http://localhost:8000`

## Настройка LLM провайдера

В файле `.env` установите переменную `LLM_PROVIDER`:

| Значение | Описание |
|----------|----------|
| `openai` | OpenAI API (GPT-4o-mini по умолчанию) |
| `ollama` | Локальная модель через Ollama |
| `gigachat`| GigaChat API от Сбера |

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_PROVIDER=openai
```

### Ollama (локально)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

После запуска контейнеров загрузить модели:

```bash
docker exec -it cdekstart-rag-agent-ollama-1 ollama pull llama3
docker exec -it cdekstart-rag-agent-ollama-1 ollama pull nomic-embed-text
```

### GigaChat

```env
LLM_PROVIDER=gigachat
GIGACHAT_API_KEY=...
GIGACHAT_MODEL=GigaChat
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

> GigaChat не предоставляет embedding API в langchain-community,
> поэтому для эмбеддингов используйте OpenAI или Ollama.

## API

### POST /chat

```json
{
  "session_id": "user-123",
  "message": "Какая стипендия?"
}
```

Ответ:

```json
{
  "session_id": "user-123",
  "response": "Уточните, пожалуйста, какая страна вас интересует: Германия (Берлин) или Франция (Париж)?",
  "needs_clarification": true
}
```

### GET /health

Проверка состояния сервиса.

### DELETE /session/{session_id}

Очистить историю диалога для сессии.

## Ограничения

- Контекст сессии хранится в памяти. При перезапуске сервиса история диалогов сбрасывается.
- При использовании Ollama качество ответов зависит от выбранной модели.
- Для работы с OpenAI требуется действующий API-ключ с балансом.
- История диалога ограничена последними 20 сообщениями на сессию.
