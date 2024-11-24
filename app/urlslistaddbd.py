# app/urlslistaddbd.py

import os
import sys
import logging
from langchain_community.document_loaders import WebBaseLoader
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.db_utils import add_documents_to_db

def initialize_vector_store(config, logger):
    """
    Инициализация векторного хранилища.

    Args:
        config: Конфигурационный объект.
        logger: Объект логгера.
    Returns:
        Инициализированное векторное хранилище.
    """
    try:
        embeddings = NomicEmbeddings(model=config.vector_db.embedding_model, inference_mode=config.vector_db.inference_mode)
        vectorstore = Chroma(persist_directory=config.vector_db.persist_directory,
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