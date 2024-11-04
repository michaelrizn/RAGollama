import os
import streamlit as st
import sqlite3
from langchain_ollama import ChatOllama
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_nomic.embeddings import NomicEmbeddings
from langchain.schema import Document
from langchain_core.messages import HumanMessage, SystemMessage
import json
from editor import manage_vector_store_page
from scan import scan_vector_store

# Функция для логирования
log_messages = []

def log(message):
    log_messages.append(message)
    st.session_state.logs = "\n".join(log_messages)

# Установка переменной окружения USER_AGENT
if not os.getenv("USER_AGENT"):
    os.environ["USER_AGENT"] = "MyStreamlitApp/1.0"
    print("USER_AGENT environment variable set to: MyStreamlitApp/1.0")

# Функции для работы с векторной базой данных
DB_PATH = "./chroma_db"

def initialize_vector_db():
    """
    Инициализация векторной базы данных Chroma. Если база данных не существует, она будет создана.
    """
    if not os.path.exists(DB_PATH):
        log("Vector database not found. Creating a new one...")
        os.makedirs(DB_PATH, exist_ok=True)
        return create_vector_db(
            [Document(page_content="initial document", metadata={"source": "initial"})])
    else:
        log("Vector database found and ready to use.")
        return Chroma(persist_directory=DB_PATH,
                     embedding_function=NomicEmbeddings(model="nomic-embed-text-v1.5",
                                                      inference_mode="local"))

def create_vector_db(documents):
    """
    Создание векторной базы данных из документов с использованием Chroma.
    :param documents: Список документов для добавления в базу данных.
    :return: Экземпляр Chroma с добавленными документами.
    """
    log("Creating vector database...")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=200
    )
    doc_splits = text_splitter.split_documents(documents)
    log(f"Documents split into {len(doc_splits)} chunks for vectorization.")

    embeddings = NomicEmbeddings(model="nomic-embed-text-v1.5", inference_mode="local")
    vectorstore = Chroma.from_documents(doc_splits, embeddings, persist_directory=DB_PATH)
    vectorstore.persist()
    log("Vector database created successfully and persisted locally.")
    return vectorstore

# Инициализация состояния для хранения векторной базы данных
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = initialize_vector_db()
    log("Initialized vectorstore for session state.")

# Функция для общения с моделью
def chat_with_model(query, context=None, metadata=None):
    log(f"User query: {query}")
    local_llm = "llama3.2:1b-instruct-fp16"
    llm = ChatOllama(model=local_llm, temperature=0)
    log("Initializing connection to the model...")
    try:
        system_prompt = "You are a helpful AI assistant. Answer the question using your knowledge. If context is provided, use it to enhance your answer but don't limit yourself to it."
        content = f"Question: {query}"
        if context:
            content += f"\nAdditional context: {context}"
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=content)
        ]
        log(f"Prompt being sent to the model: {messages}")
        response = llm.invoke(messages)
        response_text = response.content if hasattr(response, 'content') else str(response)
        log(f"Model response: {response_text}")
        return response_text
    except Exception as e:
        log(f"Error invoking the model: {e}")
        return "An error occurred while generating a response. Please try again."

# Обновленная функция для поиска ответа в векторной базе данных
def retrieve_answer_from_vectorstore(query, tag=None):
    if st.session_state.vectorstore is not None:
        log("Searching for relevant context in vector store...")
        try:
            if tag:
                # Используем встроенную фильтрацию Chroma для поиска только среди документов с указанным тегом
                filter_dict = {"tag": tag}
                log(f"Performing similarity search with tag filter: {tag}")
                results = st.session_state.vectorstore.similarity_search(query, k=3, filter=filter_dict)
            else:
                # Обычный поиск по запросу без фильтра
                log("Performing similarity search without tag filter.")
                results = st.session_state.vectorstore.similarity_search(query, k=3)

            if results:
                log(f"Found {len(results)} results.")
                return results
            else:
                log("No relevant documents found in the vector store.")
        except Exception as e:
            log(f"Error retrieving from vector store: {e}")
    return None

# Интерфейс для общения с чат-ботом
# Получение списка уникальных тегов из базы данных
try:
    conn = sqlite3.connect(os.path.join(DB_PATH, 'chroma.sqlite3'))
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT string_value FROM embedding_metadata WHERE key='tag'")
    unique_tags = [row[0] for row in cursor.fetchall()]
    conn.close()
    log(f"Successfully retrieved unique tags from vector store: {unique_tags}")
except Exception as e:
    log(f"Error retrieving unique tags from vector store: {e}")
    unique_tags = []

unique_tags = [""] + unique_tags  # Добавляем пустое значение в начало списка

tag_filter = st.selectbox("Filter by tag (optional):", unique_tags, key="tag_input")
user_query = st.text_input("Ask the chatbot:", key="chat_input")

# Создание фрейма для вывода ответа модели
response_frame = st.empty()

# Добавлена функция для отправки по нажатию Enter
def submit_chat():
    if user_query:
        # Получаем дополнительный контекст из базы данных с учетом фильтрации по тегу
        relevant_docs = retrieve_answer_from_vectorstore(user_query, tag_filter if tag_filter else None)
        context = None
        metadata = []
        if relevant_docs:
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            # Собираем метаданные из документов
            for doc in relevant_docs:
                metadata.append(doc.metadata)

        # Получаем ответ от модели
        response = chat_with_model(user_query, context, metadata)

        # Отображаем ответ
        if metadata:
            formatted_metadata = "\n".join([f"source - {meta.get('source', 'N/A')} | tag - {meta.get('tag', 'N/A')}" for meta in metadata])
            response_frame.write(response + "\n\nМетаданные:\n" + formatted_metadata)
        else:
            response_frame.write(response)

# Создаем колонки для кнопок
col1, col2 = st.columns([1, 0.1])

# Убрано отображение кнопки "Chat", чтобы общение было только по Enter
submit_chat()

# Кнопка для управления содержимым векторной базы данных
manage_vector_store_page(st.session_state.vectorstore, None)

# Кнопка для сканирования векторной базы данных
if st.sidebar.button("Scan Vector Store", key="scan_vector_store_btn_unique"):
    st.session_state['show_scan_interface'] = not st.session_state.get('show_scan_interface', False)

if st.session_state.get('show_scan_interface', False):
    scan_vector_store(st.session_state.vectorstore)

# Отображение логов в боковой панели
st.sidebar.header("Logs")
if 'logs' in st.session_state:
    st.sidebar.write(st.session_state.logs)
