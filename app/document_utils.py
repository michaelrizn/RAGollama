from langchain_community.vectorstores import Chroma
from langchain_nomic.embeddings import NomicEmbeddings
from langchain.schema import Document
from langchain_community.document_loaders import WebBaseLoader, PyMuPDFLoader, TextLoader
import os
from app.db_utils import add_documents_to_db, remove_existing_documents


def add_document_to_store(source, tag, config, log_func=None):
    """
    Добавляет документ (из файла или URL) в векторное хранилище.

    Args:
        source (str): Путь до файла или URL источника.
        tag (str): Тег.
        config (Config): Конфигурационный объект.
        log_func (callable, optional): Функция для логирования.
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

        # Проверка, файл или URL
        if os.path.exists(source):
            # Если источник — файл
            file_type = os.path.splitext(source)[1].lower()
            if file_type == ".pdf":
                loader = PyMuPDFLoader(source)
            elif file_type == ".txt":
                loader = TextLoader(source)
            else:
                raise ValueError("Неподдерживаемый тип файла.")
        elif source.startswith("http://") or source.startswith("https://"):
            # Если источник — URL
            loader = WebBaseLoader([source])
        else:
            raise ValueError("Источник должен быть файлом или URL.")

        # Удаление существующих записей
        remove_existing_documents(vectorstore, source, log_func=log_func)

        # Загрузка и добавление новых документов
        documents = loader.load()
        for doc in documents:
            doc.metadata['tag'] = tag
            doc.metadata['source'] = source
        add_documents_to_db(vectorstore, documents, log_func=log_func)

        if log_func:
            log_func(f"Документ из '{source}' успешно добавлен с тегом: {tag}.")
    except Exception as e:
        if log_func:
            log_func(f"Ошибка при добавлении документа: {e}")
        raise e