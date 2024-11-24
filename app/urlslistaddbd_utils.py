# urlslistaddbd_utils.py

import os
import requests
from app.urlparser_utils import read_urls_from_file
from app.document_utils import add_document_to_store
from langchain_chroma import Chroma  # Обновлённый импорт
from langchain_nomic.embeddings import NomicEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document  # Добавили импорт Document

def initialize_vector_store(persist_directory="chroma_db"):
    """
    Инициализация векторного хранилища.
    """
    embeddings = NomicEmbeddings(model="nomic-embed-text-v1.5", inference_mode="local")
    return Chroma(persist_directory=persist_directory, embedding_function=embeddings)

def add_urls_from_file(config, log_func=None, url_list_path="urlslist.txt", username=None, password=None):
    """
    Добавляет URL из файла в векторное хранилище.

    Args:
        config: Конфигурационный объект.
        log_func: Функция для логирования.
        url_list_path (str): Путь к файлу со списком URL.
        username (str, optional): Логин для авторизации.
        password (str, optional): Пароль для авторизации.
    """
    session = requests.Session()

    # Установка User-Agent
    user_agent = os.getenv("USER_AGENT", "MyCustomUserAgent/1.0")
    session.headers.update({'User-Agent': user_agent})

    # Если логин и пароль предоставлены, используем их для авторизации
    if username and password:
        session.auth = (username, password)
        if log_func:
            log_func("Используется предоставленная авторизация.")

    try:
        vectorstore = initialize_vector_store(config.vector_db.persist_directory)
        urls = read_urls_from_file(url_list_path)

        for url, tag in urls:
            try:
                # Проверка существования URL в базе данных
                all_docs = vectorstore._collection.get()
                matching_ids = [
                    doc_id for doc_id, metadata in zip(all_docs['ids'], all_docs['metadatas'])
                    if metadata.get('source') == url
                ]

                if matching_ids:
                    vectorstore._collection.delete(ids=matching_ids)
                    if log_func:
                        log_func(f"Существующие записи для URL '{url}', Тег: '{tag}' найдены и удалены.")

                # Получение содержимого страницы
                response = session.get(url)
                if response.status_code == 401:
                    if log_func:
                        log_func(f"Требуется авторизация для доступа к URL: {url}")
                    continue
                elif not response.ok:
                    if log_func:
                        log_func(f"Ошибка доступа к {url}: {response.status_code}")
                    continue

                content = response.text

                # Разбиение документа на части
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                chunks = text_splitter.split_text(content)

                # Добавление частей в векторное хранилище
                for chunk in chunks:
                    document = Document(page_content=chunk, metadata={"source": url, "tag": tag})  # Создаём объект Document
                    add_document_to_store(
                        source=url,
                        tag=tag,
                        config=config,
                        log_func=log_func,
                        document=document  # Передаём объект Document
                    )

                if log_func:
                    log_func(f"URL '{url}' успешно добавлен с тегом '{tag}'.")

            except Exception as e:
                if log_func:
                    log_func(f"Ошибка при обработке URL '{url}': {e}")

    except Exception as e:
        if log_func:
            log_func(f"Ошибка при добавлении URL из файла: {e}")
        raise e