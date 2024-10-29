import os
import streamlit as st
from langchain_ollama import ChatOllama
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_nomic.embeddings import NomicEmbeddings
from langchain.schema import Document
from langchain_core.messages import HumanMessage, SystemMessage
import json
from editor import manage_vector_store_page

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

def add_documents_to_db(vectorstore, new_documents):
    """
    Добавление новых документов в существующую векторную базу данных с использованием Chroma.
    :param vectorstore: Экземпляр существующей векторной базы данных.
    :param new_documents: Список новых документов для добавления.
    """
    log("Adding new documents to the vector database...")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=200
    )
    new_doc_splits = text_splitter.split_documents(new_documents)
    vectorstore.add_documents(new_doc_splits)
    vectorstore.persist()
    log(f"Added {len(new_doc_splits)} new document chunks to the vector database and persisted changes.")

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

# Функция для поиска ответа в векторной базе данных
def retrieve_answer_from_vectorstore(query):
    if st.session_state.vectorstore is not None:
        log("Searching for relevant context in vector store...")
        try:
            results = st.session_state.vectorstore.similarity_search(query, k=3)
            if results:
                log("Relevant documents found in vector store.")
                return results
            else:
                log("No relevant documents found in vector store.")
        except Exception as e:
            log(f"Error retrieving from vector store: {e}")
    return None

# Интерфейс для общения с чат-ботом
user_query = st.text_input("Ask the chatbot:", key="chat_input")

# Создание фрейма для вывода ответа модели
response_frame = st.empty()

# Добавлена функция для отправки по нажатию Enter
def submit_chat():
    if user_query:
        # Получаем дополнительный контекст из базы данных
        relevant_docs = retrieve_answer_from_vectorstore(user_query)
        context = None
        metadata = None
        if relevant_docs:
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            metadata = [doc.metadata for doc in relevant_docs]

        # Получаем ответ от модели
        response = chat_with_model(user_query, context, metadata)

        # Отображаем ответ
        if metadata:
            response_frame.write(response + "\n\nSources used for context:\n" + "\n".join(
                [str(meta) for meta in metadata]))
        else:
            response_frame.write(response)

# Создаем колонки для кнопок
col1, col2 = st.columns([1, 0.1])

# Убрано отображение кнопки "Chat", чтобы общение было только по Enter
submit_chat()

# Кнопка для управления содержимым векторной базы данных
manage_vector_store_page(st.session_state.vectorstore, add_documents_to_db)

# Отображение логов в боковой панели
st.sidebar.header("Logs")
if 'logs' in st.session_state:
    st.sidebar.write(st.session_state.logs)
