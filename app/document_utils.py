# document_utils.py

from langchain_community.vectorstores import Chroma
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_community.document_loaders import WebBaseLoader, PyMuPDFLoader, TextLoader
import os
from app.db_utils import add_documents_to_db, remove_existing_documents

def add_document_to_store(source, tag, config, log_func=None, document_content=None):
    """
    Добавляет документ (из файла или URL) в векторное хранилище.

    Args:
        source (str): Путь до файла или URL источника.
        tag (str): Тег.
        config (Config): Конфигурационный объект.
        log_func (callable, optional): Функция для логирования.
        document_content (str, optional): Содержимое документа (для URL).
    """
    try:
        # Инициализация векторного хранилища
        embeddings = NomicEmbeddings(
            model=config.vector_db.embedding_model,
            inference_mode=config.vector_db.inference_mode
        )
        vectorstore = Chroma(
            persist_directory=config.vector_db.persist_directory,
            embedding_function=embeddings
        )

        metadata_source = source if source.startswith("http://") or source.startswith("https://") else os.path.basename(source)

        # Удаление существующих записей
        remove_existing_documents(vectorstore, metadata_source, log_func=log_func)

        if document_content:
            # Если документ уже содержит содержимое (для URL)
            documents = [{
                'page_content': document_content,
                'metadata': {'source': metadata_source, 'tag': tag}
            }]
        else:
            # Загрузка документов из файла или URL
            if os.path.exists(source):
                file_type = os.path.splitext(source)[1].lower()
                if file_type == ".pdf":
                    loader = PyMuPDFLoader(source)
                elif file_type == ".txt":
                    loader = TextLoader(source)
                else:
                    raise ValueError("Неподдерживаемый тип файла. Допустимы только .pdf и .txt.")
                documents = loader.load()
                for doc in documents:
                    doc.metadata['tag'] = tag
                    doc.metadata['source'] = metadata_source
            elif source.startswith("http://") or source.startswith("https://"):
                loader = WebBaseLoader([source])
                documents = loader.load()
                for doc in documents:
                    doc.metadata['tag'] = tag
                    doc.metadata['source'] = metadata_source
            else:
                raise ValueError("Источник должен быть файлом (.pdf или .txt) или URL.")

        # Добавление документов в базу
        add_documents_to_db(vectorstore, documents, log_func=log_func)

        if log_func:
            log_func(f"Документ из '{metadata_source}' успешно добавлен с тегом: {tag}.")
    except Exception as e:
        if log_func:
            log_func(f"Ошибка при добавлении документа: {e}")
        raise e