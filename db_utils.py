# db_utils.py - отдельный модуль для хранения общих функций, связанных с работой с векторной базой
# данных

from langchain.text_splitter import RecursiveCharacterTextSplitter

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