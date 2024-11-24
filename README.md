# Поиск и ответ при помощи LLM, на основе RAG.

## Описание
Этот проект предоставляет возможности для работы с векторным хранилищем документов с использованием:
- API (FastAPI) для взаимодействия с векторным хранилищем через HTTP-запросы.
- CLI для выполнения операций через командную строку.
- Интеграции с Ollama для общения с моделью чат-бота с учетом контекста и тегов.
- Парсинг ссылок с веб-страниц для добавления их в хранилище.
- Добавление URL и документов из списка файлов с поддержкой проверки существующих записей.

Основные возможности:
1. Добавление документов (файлов или URL) в векторное хранилище.
2. Поиск документов по запросу и тегам.
3. Общение с моделью чат-бота с использованием контекста из векторного хранилища.
4. Парсинг ссылок с веб-страниц с добавлением тегов.
5. Добавление URL из файлов в векторное хранилище с проверкой дубликатов.

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
- **`POST /parse-links`** - Парсинг ссылок с веб-страницы.
    - Параметры запроса (JSON):
      ```json
      {
          "base_url": "URL веб-страницы",
          "tag": "тег",
          "username": "логин (опционально)",
          "password": "пароль (опционально)"
      }
      ```
- **`POST /add-urls-from-file`** - Добавление URL из файла в векторное хранилище.
    - Параметры запроса (JSON):
      ```json
      {
          "url_list_path": "путь_до_файла_с_URL"
      }
      ```
- **`DELETE /delete-by-source`** - Удаление всех документов по указанному источнику.
    - Параметры запроса (JSON):
      ```json
      {
          "source": "путь_или_URL_для_удаления"
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

- **Парсинг ссылок:**
    ```bash
    python -m app.cli parse-links --base-url "URL страницы" --tag "тег"
    ```

- **Добавление URL из файла:**
    ```bash
    python -m app.cli add-urls-from-file --url-list-path "путь_до_файла"
    ```

- **Удаление документов по источнику:**
    ```bash
    python -m app.cli delete-by-source --source "путь_или_URL"
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

### Парсинг ссылок через API
```bash
curl -X POST "http://127.0.0.1:8000/parse-links" \
-H "Content-Type: application/json" \
-d '{"base_url": "example.com", "tag": "example_tag"}'
```

Файлы старой версии проекта лежат в папке old.
Старое описание:
Приложение для поиска и простой, локальной обработки информации из своих источников. Используется RAG-архитектура, langchain, ollama. Модельки на свой вкус и мощность компьютера.

Всё собрано на коленке при помощи промпт-инжиниринга и не претендует на что-либо. Задачу свою выполняет и этого достаточно.

streamlit run app.py - запуск. Но сначала установите ollama и скачайте модель.

app.py - основной файл для главной страницы и общения с моделькой.

db_utils.py - отдельный модуль для хранения общих функций, связанных с работой с векторной базой данных.

editor.py - дополнительный функционал, можно добавить отдельно по одной ссылке или файл в БД. Можно полистать БД постранично.

scan.py - поиск по БД без участия модели.

urlparser.py - создаёт список ссылок с тегом. Работает отдельно от основного приложения, просто выполните этот файл.

urlslistaddbd.py добавляет в БД ссылки по списку из файла urlslist.txt. Работает отдельно от основного приложения, просто выполните этот файл.