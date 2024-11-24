from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma


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

    # Разделение документов на части для векторизации
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000,
        chunk_overlap=200
    )
    new_doc_splits = text_splitter.split_documents(documents)

    # Добавление документов в базу
    vectorstore.add_documents(new_doc_splits)

    # Удаляем вызов persist
    # В новой версии, если используется langchain_community, вызов persist не требуется

    if log_func:
        log_func(
            f"Добавлено {len(new_doc_splits)} новых частей документов в векторную базу данных."
        )


def remove_existing_documents(vectorstore, source, log_func=None):
    """
    Удаляет существующие записи из базы данных, если их источник совпадает с указанным.

    Args:
        vectorstore: Экземпляр векторного хранилища.
        source: Источник документа (например, имя файла или URL).
        log_func (callable, optional): Функция для логирования сообщений.
    """
    try:
        # Получение всех документов из базы данных
        all_docs = vectorstore._collection.get()

        # Поиск совпадающих записей по источнику
        matching_ids = [
            doc_id for doc_id, metadata in zip(all_docs['ids'], all_docs['metadatas'])
            if metadata.get('source') == source
        ]

        if matching_ids:
            # Удаление записей с совпадающим источником
            vectorstore._collection.delete(ids=matching_ids)
            if log_func:
                log_func(f"Удалены существующие записи для источника: {source}")
    except Exception as e:
        if log_func:
            log_func(f"Ошибка при удалении существующих записей: {e}")
        raise e