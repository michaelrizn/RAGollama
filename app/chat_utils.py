import subprocess
import requests
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from app.search_utils import search_documents

def ensure_ollama_running(log_func=None):
    """
    Проверяет, запущен ли сервер Ollama. Если нет, запускает его.
    """
    try:
        # Проверяем доступность Ollama на порту 11434
        response = requests.get("http://127.0.0.1:11434/health", timeout=5)
        if response.status_code == 200:
            if log_func:
                log_func("Сервер Ollama уже запущен.")
            return True
    except requests.ConnectionError:
        if log_func:
            log_func("Сервер Ollama не запущен. Попытка запуска...")

    # Пытаемся запустить Ollama
    try:
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if log_func:
            log_func("Сервер Ollama успешно запущен.")
        return True
    except Exception as e:
        if log_func:
            log_func(f"Не удалось запустить сервер Ollama: {e}")
        raise RuntimeError("Не удалось запустить сервер Ollama") from e

def chat_with_model(query, context=None, tag=None, model="llama3.2:1b-instruct-fp16", temperature=0.7, config=None, log_func=None):
    """
    Отправляет запрос к модели чатбота и возвращает ответ.

    Args:
        query (str): Вопрос пользователя.
        context (str, optional): Дополнительный контекст для модели.
        tag (str, optional): Тег для фильтрации документов в базе данных.
        model (str): Название модели (по умолчанию из конфигурации).
        temperature (float): Температура для генерации ответа.
        config (Config, optional): Конфигурационный объект.
        log_func (callable, optional): Функция для логирования.

    Returns:
        str: Ответ модели.
    """
    try:
        # Проверяем и запускаем Ollama, если требуется
        ensure_ollama_running(log_func)

        if log_func:
            log_func(f"Инициализация модели: {model}")

        # Если указан тег, ищем документы
        search_results = None
        if tag:
            search_results = search_documents(query=query, tag=tag, config=config, log_func=log_func)
            if tag.lower() != "all" and not search_results:
                return f"Тег '{tag}' не найден в базе данных."

        # Формируем контекст из поиска, если есть результаты
        search_context = "\n\n".join([doc['content'] for doc in search_results]) if search_results else ""

        # Составляем полный запрос
        full_context = ""
        if context:
            full_context += f"Context: {context}\n"
        if search_context:
            full_context += f"Search Results: {search_context}\n"
        full_query = f"{full_context}Question: {query}"

        if log_func:
            log_func(f"Полный запрос к модели:\n{full_query}")

        # Создаём экземпляр модели
        llm = ChatOllama(model=model, temperature=temperature)

        # Составляем системное сообщение
        system_prompt = (
            "You are an AI assistant. Answer the question clearly and concisely in Russian. "
            "Use provided context if available."
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=full_query)
        ]

        if log_func:
            log_func(f"Отправка сообщений в модель: {messages}")

        # Получаем ответ от модели
        response = llm.invoke(messages)
        response_text = response.content if hasattr(response, 'content') else str(response)

        if log_func:
            log_func(f"Ответ модели: {response_text}")
        return response_text

    except Exception as e:
        if log_func:
            log_func(f"Ошибка при взаимодействии с моделью: {e}")
        raise e