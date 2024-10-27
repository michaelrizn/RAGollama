import os
import streamlit as st
from langchain_ollama import ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader, PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_nomic.embeddings import NomicEmbeddings
from langchain.schema import Document
from langchain_core.messages import HumanMessage, SystemMessage
import json

# Функция для логирования
log_messages = []


def log(message):
    log_messages.append(message)
    if len(log_messages) > 50:  # Ограничение для предотвращения слишком большого объема данных
        log_messages.pop(0)
    st.session_state.logs = "\n".join(log_messages)


# Установка переменной окружения USER_AGENT
if not os.getenv("USER_AGENT"):
    os.environ["USER_AGENT"] = "MyStreamlitApp/1.0"
    print("USER_AGENT environment variable set to: MyStreamlitApp/1.0")


# Функции для работы с векторной базой данных
def create_vector_db(documents):
    """
    Создание векторной базы данных из документов с использованием FAISS.

    :param documents: Список документов для добавления в базу данных.
    :return: Экземпляр FAISS с добавленными документами.
    """
    log("Creating vector database...")
    # Разделение документов на части для лучшего векторного представления
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=200
    )
    doc_splits = text_splitter.split_documents(documents)
    log(f"Documents split into {len(doc_splits)} chunks for vectorization.")

    # Создание векторного хранилища с использованием эмбеддингов Nomic
    embeddings = NomicEmbeddings(model="nomic-embed-text-v1.5", inference_mode="local")
    vectorstore = FAISS.from_documents(doc_splits, embeddings)
    log("Vector database created successfully.")
    return vectorstore


def add_documents_to_db(vectorstore, new_documents):
    """
    Добавление новых документов в существующую векторную базу данных с использованием FAISS.

    :param vectorstore: Экземпляр существующей векторной базы данных.
    :param new_documents: Список новых документов для добавления.
    """
    log("Adding new documents to the vector database...")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=200
    )
    new_doc_splits = text_splitter.split_documents(new_documents)
    vectorstore.add_documents(new_doc_splits)
    log(f"Added {len(new_doc_splits)} new document chunks to the vector database.")


# Инициализация состояния для хранения векторной базы данных
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
    log("Initialized session state for vectorstore as None.")


# Функция для общения с моделью
def chat_with_model(query, output_format="text"):
    log(f"User query: {query}")
    """
    Общение с моделью на основе запроса пользователя.

    :param query: Вопрос пользователя для чат-бота.
    :param output_format: Формат ответа ("json" или "text").
    :return: Ответ модели на заданный вопрос.
    """
    # Проверка доступности модели
    local_llm = "llama3.2:1b-instruct-fp16"
    llm = ChatOllama(model=local_llm, temperature=0)
    log("Initializing connection to the model...")
    try:
        # Формирование промпта для модели
        prompt = HumanMessage(content=query)
        log(f"Prompt being sent to the model: {prompt}")
        response = llm.invoke([prompt])
        response_text = response.content if hasattr(response, 'content') else str(response)
        log(f"Model response: {response_text}")
        return response_text
    except Exception as e:
        log(f"Error invoking the model: {e}")
        return "An error occurred while generating a response. Please try again."


# Главная страница Streamlit приложения
st.title("Chatbot with Vector Store Management")
log("Streamlit application initialized.")

# Создание базы данных, если еще не создана
if st.session_state.vectorstore is None:
    if st.button("Create Vector DB"):
        log("Create Vector DB button clicked.")
        # Создание пустой векторной базы данных с заглушкой для дальнейшего добавления документов
        st.session_state.vectorstore = create_vector_db(
            [Document(page_content="initial document", metadata={"source": "initial"})])
        st.success("Vector DB created successfully!")

# Интерфейс для добавления документов в векторную базу данных
st.header("Add Files or URLs to Vector Store")

url = st.text_input("Enter a URL to add to the vector database:")
if st.button("Add URL") or (url and st.session_state.vectorstore):
    if st.session_state.vectorstore is None:
        st.warning("Please create the Vector DB before adding documents.")
    elif url:
        log(f"URL provided by user: {url}")
        try:
            new_doc = WebBaseLoader(url).load()
            add_documents_to_db(st.session_state.vectorstore, new_doc)
            st.success("URL added to vector database successfully!")
        except Exception as e:
            log(f"Failed to add URL: {e}")
            st.error(f"Failed to add URL: {e}")

uploaded_file = st.file_uploader("Upload a file to add to the vector database:")
if uploaded_file and st.session_state.vectorstore is not None:
    log(f"File uploaded by user: {uploaded_file.name}")
    try:
        new_doc = PyMuPDFLoader(uploaded_file).load()
        add_documents_to_db(st.session_state.vectorstore, new_doc)
        st.success("File added to vector database successfully!")
    except Exception as e:
        log(f"Failed to add file: {e}")
        st.error(f"Failed to add file: {e}")

# Просмотр содержимого векторной базы данных
if st.session_state.vectorstore is not None:
    st.header("Current Vector Store Contents")
    log("Retrieving documents from vector store...")
    try:
        docs = st.session_state.vectorstore.similarity_search('', k=10)
        if docs:
            for i, doc in enumerate(docs):
                st.write(f"Document {i + 1}: {doc.page_content[:200]}...")
                st.write(f"Metadata: {doc.metadata}")
                log(f"Document {i + 1}: {doc.page_content[:200]}...")
                log(f"Metadata: {doc.metadata}")
        else:
            st.write("The vector store is currently empty.")
            log("The vector store is currently empty.")
    except Exception as e:
        log(f"Error retrieving documents: {e}")
        st.write(f"Error retrieving documents: {e}")

# Интерфейс для общения с чат-ботом
st.header("Chat with the Bot")
user_query = st.text_input("Ask the chatbot:", key="chat_input")


# Добавлена функция для отправки по нажатию Enter
def submit_chat():
    if st.session_state.vectorstore is not None and user_query:
        try:
            log("Retriever initialized for chat.")
            log(f"User query: {user_query}")
            answer = chat_with_model(user_query)
            log(f"Chatbot answer: {answer}")
            st.session_state.chat_output = answer
        except Exception as e:
            log(f"Error during chat: {e}")
            st.session_state.chat_output = f"Error during chat: {e}"


if 'chat_output' in st.session_state:
    st.write(st.session_state.chat_output)
    log(f"Chat output: {st.session_state.chat_output}")

# Добавлена кнопка и функция для обработки нажатия Enter
if st.button("Chat") or user_query:
    log("Chat button clicked or Enter pressed.")
    submit_chat()

# Отображение логов в боковой панели
st.sidebar.header("Logs")
if 'logs' in st.session_state:
    st.sidebar.text_area("Logs:", st.session_state.logs,
                         height=800)  # Увеличен размер высоты панели логов
