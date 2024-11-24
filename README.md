# Проект: Векторное хранилище документов с API и CLI

## Описание
Этот проект предоставляет возможности для работы с векторным хранилищем документов с использованием:
- API (FastAPI) для взаимодействия с векторным хранилищем через HTTP-запросы.
- CLI для выполнения операций через командную строку.
- Интеграции с Ollama для общения с моделью чат-бота с учетом контекста и тегов.

Основные возможности:
1. Добавление документов (файлов или URL) в векторное хранилище.
2. Поиск документов по запросу и тегам.
3. Общение с моделью чат-бота с использованием контекста из векторного хранилища.

---

## Структура проекта

```
project/
├── app/
│   ├── __init__.py
│   ├── config.py            # Конфигурация проекта
│   ├── logger.py            # Логирование
│   ├── db_utils.py          # Утилиты для работы с векторным хранилищем
│   ├── search_utils.py      # Реализация поиска документов
│   ├── document_utils.py    # Реализация добавления документов
│   ├── chat_utils.py        # Общение с Ollama
│   ├── api.py               # Реализация API (FastAPI)
│   ├── cli.py               # Реализация CLI (Click)
├── chroma_db/               # Директория для векторного хранилища
├── requirements.txt         # Зависимости проекта
├── config.yaml              # Конфигурационный файл
├── README.md                # Описание проекта
```

---

## Установка и настройка

### Требования
- Python 3.9+
- Установленный Ollama (для работы с моделями)

### Установка
1. Клонируйте репозиторий:
    ```bash
    git clone <repository_url>
    cd <repository_folder>
    ```

2. Создайте и активируйте виртуальное окружение:
    ```bash
    python -m venv .venv
    source .venv/bin/activate # Для Linux/Mac
    .venv\Scripts\activate  # Для Windows
    ```

3. Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```

4. Проверьте и настройте конфигурацию в `config.yaml`.

---

## Использование

### Запуск API
Для запуска API используйте команду:
```bash
uvicorn app.api:app --reload
```

После запуска API будет доступно по адресу: [http://127.0.0.1:8000](http://127.0.0.1:8000).

#### Эндпоинты API
- **`GET /`** - Корневой маршрут.
- **`POST /add-document`** - Добавление документа (файла или URL) в хранилище.
    - Параметры запроса (JSON):
      ```json
      {
          "source": "путь_до_файла_или_URL",
          "tag": "тег"
      }
      ```
- **`POST /search`** - Поиск документов в хранилище.
    - Параметры запроса (JSON):
      ```json
      {
          "query": "поисковый запрос",
          "tag": "тег (опционально)"
      }
      ```
- **`POST /chat`** - Общение с моделью чат-бота с использованием контекста из хранилища.
    - Параметры запроса (JSON):
      ```json
      {
          "query": "вопрос",
          "context": "дополнительный контекст (опционально)",
          "tag": "тег (опционально)"
      }
      ```

### Использование CLI

Запуск CLI:
```bash
python -m app.cli
```

#### Команды CLI

- **Добавление документа:**
    ```bash
    python -m app.cli add-document --source "путь_до_файла_или_URL" --tag "тег"
    ```
    Или интерактивный режим:
    ```bash
    python -m app.cli add-document --interactive
    ```

- **Поиск документов:**
    ```bash
    python -m app.cli search --query "поисковый запрос" --tag "тег"
    ```

- **Общение с моделью:**
    ```bash
    python -m app.cli chat --query "вопрос" --context "дополнительный контекст" --tag "тег"
    ```

---

## Конфигурация

Пример файла `config.yaml`:
```yaml
user_agent: "MyStandaloneScript/1.0"

vector_db:
  persist_directory: "./chroma_db"
  embedding_model: "nomic-embed-text-v1.5"
  inference_mode: "local"

ollama:
  default_model: "llama3.2:1b-instruct-fp16"

logging:
  level: "INFO"
  format: "%(asctime)s - %(levelname)s - %(message)s"
```

---

## Примеры запросов

### Добавление документа через API
```bash
curl -X POST "http://127.0.0.1:8000/add-document" \
-H "Content-Type: application/json" \
-d '{"source": "path/to/file.txt", "tag": "example_tag"}'
```

### Поиск документов через API
```bash
curl -X POST "http://127.0.0.1:8000/search" \
-H "Content-Type: application/json" \
-d '{"query": "example query", "tag": "example_tag"}'
```

### Общение с моделью через API
```bash
curl -X POST "http://127.0.0.1:8000/chat" \
-H "Content-Type: application/json" \
-d '{"query": "example question", "context": "example context", "tag": "example_tag"}'
```

---

## Логирование

Все логи записываются в консоль. Уровень логирования и формат настраиваются в `config.yaml`.

---

## Зависимости
Список всех зависимостей проекта содержится в файле `requirements.txt`:
```
fastapi
uvicorn
click
langchain
langchain_community
langchain-ollama
langchain-nomic
tiktoken
scikit-learn
streamlit
beautifulsoup4
tavily-python
nomic[local]
gpt4all
watchdog
faiss-cpu
chromadb
pymupdf
selenium
requests
PyYAML
```

---

## Примечания
1. Перед использованием убедитесь, что сервер Ollama запущен. Если он не запущен, приложение попытается автоматически его стартовать.
2. Для добавления файлов убедитесь, что указанный путь корректен и файл доступен для чтения.
3. Поиск с тегом "all" игнорирует фильтрацию по тегам и выполняет поиск по всему хранилищу.

---

## Контакты
Если у вас есть вопросы или предложения, свяжитесь с нами через [email@example.com].
