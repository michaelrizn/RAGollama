from langchain_chroma import Chroma
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_community.document_loaders import WebBaseLoader, PyMuPDFLoader, TextLoader
from langchain.schema import Document
import os
from app.db_utils import add_documents_to_db, remove_existing_documents


def is_valid_file_or_url(path):
    """
    Проверяет, является ли путь файлом или URL.

    Args:
        path (str): Путь к файлу или URL.

    Returns:
        bool: True, если это валидный файл или URL.
    """
    if os.path.isfile(path):
        return True
    if path.startswith("http://") or path.startswith("https://"):
        return True
    return False


def initialize_database(vectorstore, persist_directory, log_func=None):
    """
    Инициализирует базу данных с тестовой записью, если она не существует.

    Args:
        vectorstore: Экземпляр векторного хранилища.
        persist_directory (str): Путь к директории базы данных.
        log_func (callable, optional): Функция для логирования.
    """
    try:
        # Убедимся, что директория для базы существует
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
            if log_func:
                log_func(f"Директория для базы данных создана: {persist_directory}")

        # Проверяем, есть ли записи в базе
        all_docs = vectorstore._collection.get()
        if not all_docs['ids']:
            if log_func:
                log_func("База данных пуста. Добавление тестовой записи.")
            test_document = Document(
                page_content="Это тестовая запись для инициализации базы данных.",
                metadata={"source": "test_source", "tag": "test"}
            )
            add_documents_to_db(vectorstore, [test_document], log_func=log_func)
            if log_func:
                log_func("Тестовая запись успешно добавлена.")
    except Exception as e:
        if log_func:
            log_func(f"Ошибка при инициализации базы данных: {e}")
        raise


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
        # Логируем полученный путь
        if log_func:
            log_func(f"Исходный путь: {source}")

        # Проверка пути
        if not is_valid_file_or_url(source):
            raise ValueError(f"File path {source} is not a valid file or url")

        # Инициализация векторного хранилища
        embeddings = NomicEmbeddings(
            model=config.vector_db.embedding_model,
            inference_mode=config.vector_db.inference_mode
        )
        vectorstore = Chroma(
            persist_directory=config.vector_db.persist_directory,
            embedding_function=embeddings
        )
        initialize_database(vectorstore, config.vector_db.persist_directory, log_func)

        # Определяем, является ли источник файлом или URL
        is_url = source.startswith("http://") or source.startswith("https://")
        stored_source = source if is_url else os.path.basename(source)  # Название файла или полная ссылка

        # Удаляем старые записи с таким же source, если они есть
        if log_func:
            log_func(f"Удаление старых записей для source: {stored_source}")
        remove_existing_documents(vectorstore, stored_source)

        # Загрузка содержимого документа
        if document_content is None:
            if is_url:
                loader = WebBaseLoader(source)
            elif source.endswith(".pdf"):
                loader = PyMuPDFLoader(source)
            elif source.endswith(".txt"):
                loader = TextLoader(source)
            else:
                raise ValueError(f"Неподдерживаемый формат файла: {source}. Допустимы только .txt и .pdf")

            # Проверка файла перед загрузкой
            if not is_url:  # Для URL проверка не требуется
                absolute_path = os.path.abspath(source)
                if log_func:
                    log_func(f"Абсолютный путь к файлу: {absolute_path}")
                if not os.path.isfile(absolute_path):
                    raise FileNotFoundError(f"Файл {absolute_path} не найден.")
                if os.path.getsize(absolute_path) == 0:
                    raise ValueError(f"Файл {absolute_path} пуст.")

            try:
                documents = loader.load()
                # Добавляем тег в метаданные
                for doc in documents:
                    doc.metadata["tag"] = tag
                    doc.metadata["source"] = stored_source
            except Exception as e:
                if log_func:
                    log_func(f"Ошибка загрузки файла: {source}. Причина: {e}")
                raise ValueError(f"Error loading {source}: {e}")
        else:
            documents = [Document(page_content=document_content, metadata={"source": stored_source, "tag": tag})]

        # Добавление документов в векторное хранилище
        if log_func:
            log_func(f"Добавление документа в хранилище: {stored_source} с тегом: {tag}")
        add_documents_to_db(vectorstore, documents, log_func=log_func)

    except Exception as e:
        if log_func:
            log_func(f"Ошибка при добавлении документа: {e}")
        raise
