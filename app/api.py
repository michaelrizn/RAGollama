from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.config import Config
from app.logger import setup_logger
from app.search_utils import search_documents
from app.document_utils import add_document_to_store
from app.chat_utils import chat_with_model

# Инициализация FastAPI
app = FastAPI()

# Загрузка конфигурации
config = Config.load("config.yaml")

# Настройка логирования
logger = setup_logger(config)


# Модели для API
class AddDocumentRequest(BaseModel):
    source: str
    tag: str


class SearchRequest(BaseModel):
    query: str
    tag: str = None


class ChatRequest(BaseModel):
    query: str
    context: str = None
    tag: str = None


@app.get("/")
async def root():
    """
    Корневой маршрут.
    """
    return {"message": "Добро пожаловать в API хранилища документов"}


@app.post("/add-document")
async def add_document_api(request: AddDocumentRequest):
    """
    Добавление документа (файла или URL) в векторное хранилище через API.
    """
    try:
        add_document_to_store(
            source=request.source,
            tag=request.tag.strip(),
            config=config,
            log_func=logger.info
        )
        return {"message": f"Документ '{request.source}' успешно добавлен с тегом: {request.tag}"}
    except Exception as e:
        logger.error(f"Ошибка при добавлении документа: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при добавлении документа")


@app.post("/search")
async def search_documents_api(request: SearchRequest):
    """
    Поиск документов в векторном хранилище через API.
    """
    try:
        results = search_documents(
            query=request.query,
            tag=request.tag,
            config=config,
            log_func=logger.info
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при выполнении поиска")


@app.post("/chat")
async def chat_with_model_api(request: ChatRequest):
    """
    Общение с моделью через API.
    """
    try:
        response = chat_with_model(
            query=request.query,
            context=request.context,
            tag=request.tag,
            config=config,
            log_func=logger.info
        )
        return {"response": response}
    except Exception as e:
        logger.error(f"Ошибка при общении с моделью: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при общении с моделью")