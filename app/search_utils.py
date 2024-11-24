from langchain_community.vectorstores import Chroma
from langchain_nomic.embeddings import NomicEmbeddings

def search_documents(query, tag, config, log_func=None):
    """
    Выполняет поиск документов в векторном хранилище.

    Args:
        query (str): Поисковой запрос.
        tag (str): Тег для фильтрации (опционально).
        config (Config): Конфигурационный объект.
        log_func (callable, optional): Функция для логирования.

    Returns:
        list: Найденные документы в формате {content, metadata}.
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

        # Выполняем поиск
        results = []
        if tag:
            if tag.lower() == "all":
                results = vectorstore.similarity_search(query, k=5)
                if log_func:
                    log_func("Поиск по всей базе данных выполнен успешно.")
            else:
                filter_dict = {"tag": tag}
                results = vectorstore.similarity_search(query, k=5, filter=filter_dict)
                if log_func:
                    log_func(f"Поиск с фильтром по тегу '{tag}' выполнен успешно.")
        else:
            results = vectorstore.similarity_search(query, k=5)
            if log_func:
                log_func("Поиск без фильтрации по тегу выполнен успешно.")

        # Форматируем результаты
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in results
        ]
    except Exception as e:
        if log_func:
            log_func(f"Ошибка при выполнении поиска: {e}")
        raise e