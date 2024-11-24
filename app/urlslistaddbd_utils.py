import os
from langchain_chroma import Chroma
from langchain_nomic.embeddings import NomicEmbeddings
from langchain.schema import Document
from app.document_utils import add_document_to_store
from app.db_utils import remove_existing_documents

def initialize_vector_store(persist_directory="chroma_db", log_func=None):
    """
    Инициализирует базу данных с тестовой записью, если она не существует.

    Args:
        persist_directory (str): Директория для сохранения базы.
        log_func (callable, optional): Функция для логирования.

    Returns:
        vectorstore: Инициализированное векторное хранилище.
    """
    embeddings = NomicEmbeddings(model="nomic-embed-text-v1.5", inference_mode="local")
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

    # Проверяем и инициализируем базу данных
    try:
        all_docs = vectorstore._collection.get()
        if not all_docs['ids']:
            if log_func:
                log_func("База данных пуста. Добавление тестовой записи.")
            test_document = Document(
                page_content="Это тестовая запись для инициализации базы данных.",
                metadata={"source": "test_source", "tag": "test"}
            )
            vectorstore.add_documents([test_document])
            if log_func:
                log_func("Тестовая запись успешно добавлена.")
    except Exception as e:
        if log_func:
            log_func(f"Ошибка при инициализации базы данных: {e}")
        raise

    return vectorstore

def add_urls_from_file(file_path, config, log_func=None):
    """
    Добавляет записи из файла с URL и тегами в векторное хранилище.

    Args:
        file_path (str): Путь к файлу, содержащему список URL и тегов.
        config (Config): Конфигурационный объект.
        log_func (callable, optional): Функция для логирования.

    Raises:
        FileNotFoundError: Если файл не найден.
        ValueError: Если формат строки некорректный.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден.")

    vectorstore = initialize_vector_store(config.vector_db.persist_directory, log_func=log_func)

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue  # Пропуск пустых строк

            try:
                url, tag = line.split(",")  # Ожидаемый формат: URL,тег
                url = url.strip()
                tag = tag.strip()

                if log_func:
                    log_func(f"Проверка и удаление существующих записей для URL или файла: {url}")

                # Определяем, является ли источник URL или файлом
                if url.startswith("http://") or url.startswith("https://"):
                    source = url  # Для URL сохраняем полную ссылку
                else:
                    source = os.path.basename(url)  # Для файлов сохраняем только имя

                    # Проверка допустимого формата файла
                    if not (url.endswith(".txt") or url.endswith(".pdf")):
                        raise ValueError(f"Неподдерживаемый формат файла: {url}. Допустимы только .txt и .pdf")

                    # Проверяем наличие файла
                    absolute_path = os.path.abspath(url)
                    if not os.path.isfile(absolute_path):
                        raise FileNotFoundError(f"Файл {absolute_path} не найден.")
                    if os.path.getsize(absolute_path) == 0:
                        raise ValueError(f"Файл {absolute_path} пуст.")

                # Удаляем старые записи, если они существуют
                remove_existing_documents(vectorstore, source)

                if log_func:
                    log_func(f"Добавление источника: {source} с тегом: {tag}")

                # Добавляем новый документ
                add_document_to_store(source=url, tag=tag, config=config, log_func=log_func)

            except ValueError as ve:
                if log_func:
                    log_func(f"Ошибка обработки строки: {line}. {ve}")
                raise ve
            except FileNotFoundError as fnfe:
                if log_func:
                    log_func(f"Ошибка: {fnfe}")
                raise fnfe
            except Exception as e:
                if log_func:
                    log_func(f"Непредвиденная ошибка: {e}")
                raise e

    if log_func:
        log_func("Все записи успешно добавлены.")
