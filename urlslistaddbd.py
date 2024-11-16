import os
import sys
import logging
from langchain_community.document_loaders import WebBaseLoader
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Установка переменной окружения USER_AGENT, если она не установлена
if not os.getenv("USER_AGENT"):
    os.environ["USER_AGENT"] = "MyStandaloneScript/1.0"
    print("USER_AGENT environment variable set to: MyStandaloneScript/1.0")

def setup_logging():
    """
    Настройка логирования для скрипта.

    Returns:
        Logger объект.
    """
    logger = logging.getLogger('URLsListAddBD')
    logger.setLevel(logging.INFO)

    # Создание обработчиков
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)

    # Создание форматтера и добавление его к обработчику
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(formatter)

    # Добавление обработчика к логгеру
    logger.addHandler(c_handler)

    return logger

def initialize_vector_store(persist_directory="chroma_db"):
    """
    Инициализация векторного хранилища.

    Args:
        persist_directory (str): Директория для сохранения векторного хранилища.
    Returns:
        Инициализированное векторное хранилище.
    """
    try:
        embeddings = NomicEmbeddings(model="nomic-embed-text-v1.5", inference_mode="local")
        vectorstore = Chroma(persist_directory=persist_directory,
                             embedding_function=embeddings)
        return vectorstore
    except Exception as e:
        logger.error(f"Ошибка при инициализации векторного хранилища: {e}")
        raise e

def read_urls_from_file(url_list_path="urlslist.txt"):
    """
    Чтение и разбор URL из указанного файла.

    Args:
        url_list_path (str): Путь к файлу со списком URL.
    Returns:
        Список кортежей (url, tag).
    """
    if not os.path.exists(url_list_path):
        raise FileNotFoundError(f"The file {url_list_path} does not exist.")

    with open(url_list_path, "r", encoding="utf-8") as f:
        content = f.read()

    url_entries = content.split(",")
    url_list = []
    for entry in url_entries:
        entry = entry.strip()
        if not entry:
            continue
        if ";" in entry:
            url, tag = entry.split(";", 1)
            url = url.strip()
            tag = tag.strip(";").strip()  # Убираем лишнюю точку с запятой в конце
        else:
            url = entry
            tag = ""
        url_list.append((url, tag))
    return url_list

def add_documents_to_db(vectorstore, documents, log_func=None):
    """
    Добавляет новые документы в существующую векторную базу данных с использованием Chroma.

    Args:
        vectorstore: Экземпляр векторного хранилища.
        documents: Список документов для добавления.
        log_func (callable, optional): Функция для логирования сообщений.
    """
    if log_func:
        log_func("Добавление новых документов в векторную базу данных...")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=200
    )
    new_doc_splits = text_splitter.split_documents(documents)
    vectorstore.add_documents(new_doc_splits)
    vectorstore.persist()
    if log_func:
        log_func(f"Добавлено {len(new_doc_splits)} новых частей документов в векторную базу данных и изменения сохранены.")

def process_urls(vectorstore, url_list, logger):
    """
    Обработка каждого URL: проверка на дублирование, удаление при необходимости и добавление в векторное хранилище.

    Args:
        vectorstore: Экземпляр векторного хранилища.
        url_list (list): Список кортежей (url, tag).
        logger: Объект логгера для записи сообщений.
    """
    added_urls = []
    updated_urls = []

    for url, tag in url_list:
        try:
            # Проверка, существует ли URL уже в базе данных
            all_docs = vectorstore._collection.get()
            matching_ids = [
                doc_id for doc_id, metadata in zip(all_docs['ids'], all_docs['metadatas'])
                if metadata.get('source') == url
            ]

            if matching_ids:
                # Удаление существующих записей с тем же URL
                vectorstore._collection.delete(ids=matching_ids)
                updated_urls.append(url)
                logger.info(f"Существующие записи для URL '{url}' найдены и удалены.")
            else:
                added_urls.append(url)
                logger.info(f"Добавление нового URL '{url}' в векторное хранилище.")

            # Добавление нового документа в базу данных
            loader = WebBaseLoader([url])
            documents = loader.load()
            for doc in documents:
                doc.metadata['tag'] = tag
                doc.metadata['source'] = url
            add_documents_to_db(vectorstore, documents, logger.info)

        except Exception as e:
            logger.error(f"Ошибка при обработке URL '{url}': {e}")

    # Логирование итогов
    logger.info("Обработка URL завершена.")
    if added_urls:
        logger.info(f"Добавлены новые URL: {', '.join(added_urls)}")
    if updated_urls:
        logger.info(f"Обновлены URL (существующие документы были удалены и заменены): {', '.join(updated_urls)}")

def main():
    """
    Основная функция для выполнения скрипта.
    """
    global logger
    logger = setup_logging()

    # Инициализация векторного хранилища
    try:
        vectorstore = initialize_vector_store()
        logger.info("Векторное хранилище инициализировано.")
    except Exception as e:
        logger.error(f"Не удалось инициализировать векторное хранилище: {e}")
        sys.exit(1)

    # Чтение URL из файла
    try:
        url_list = read_urls_from_file()
        logger.info(f"Прочитано {len(url_list)} URL из 'urlslist.txt'.")
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    # Обработка URL
    process_urls(vectorstore, url_list, logger)

if __name__ == "__main__":
    main()