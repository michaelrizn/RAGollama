import streamlit as st
from langchain_community.document_loaders import WebBaseLoader, PyMuPDFLoader, TextLoader
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_community.vectorstores import Chroma

# Функция для логирования
log_messages = []

def log(message):
    log_messages.append(message)
    st.session_state.logs = "\n".join(log_messages)


def add_documents_to_db(vectorstore, documents):
    """
    Добавление новых документов в существующую векторную базу данных с использованием Chroma.
    :param vectorstore: Экземпляр существующей векторной базы данных.
    :param documents: Список новых документов для добавления.
    """
    log("Adding new documents to the vector database...")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=200
    )
    new_doc_splits = text_splitter.split_documents(documents)
    vectorstore.add_documents(new_doc_splits)
    vectorstore.persist()
    log(f"Added {len(new_doc_splits)} new document chunks to the vector database and persisted changes.")


def manage_vector_store_page(vectorstore, _):
    """
    Управление содержимым векторной базы данных на отдельной странице.
    :param vectorstore: Экземпляр векторной базы данных.
    """
    # Флажок для управления отображением элементов
    if 'show_db_controls' not in st.session_state:
        st.session_state['show_db_controls'] = False

    if st.sidebar.button("Manage Vector Store Contents"):
        st.session_state['show_db_controls'] = not st.session_state['show_db_controls']

    if st.session_state['show_db_controls']:
        with st.container():
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            # Кнопки для добавления, редактирования и удаления документов
            uploaded_file = st.file_uploader("Upload a document to add to the vector store",
                                           type=["pdf", "txt"])
            tag_text = st.text_input("Enter a tag for the document:", key="file_tag")

            if uploaded_file is not None:
                if st.button("Add Uploaded Document to Vector Store"):
                    st.session_state['show_db_controls'] = False
                    file_path = os.path.join("/tmp", uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    log(f"Uploaded file: {uploaded_file.name}")

                    # Проверка, существует ли файл с таким же именем в базе данных
                    all_docs = vectorstore._collection.get()
                    matching_ids = []
                    for i, metadata in enumerate(all_docs['metadatas']):
                        if 'source' in metadata and metadata['source'] == uploaded_file.name:
                            matching_ids.append(all_docs['ids'][i])

                    if matching_ids:
                        # Удаление всех существующих записей с таким именем файла
                        vectorstore._collection.delete(ids=matching_ids)
                        log(f"Document with name {uploaded_file.name} already exists and will be replaced.")

                    if uploaded_file.type == "application/pdf":
                        loader = PyMuPDFLoader(file_path)
                    elif uploaded_file.type == "text/plain":
                        loader = TextLoader(file_path)
                    else:
                        st.error("Unsupported file type.")
                        log("Unsupported file type.")
                        return

                    documents = loader.load()
                    for doc in documents:
                        doc.metadata['tag'] = tag_text
                        doc.metadata['source'] = uploaded_file.name
                    add_documents_to_db(vectorstore, documents)
                    st.success("Document added to vector store.")
                    log("Document added to vector store.")

            st.markdown('---')  # Added horizontal line here
            url_input = st.text_input("Enter URL to add document from:", key="url_input")
            url_tag = st.text_input("Enter a tag for the URL:", key="url_tag")

            # Initialize button states and visibility flags in session state if not exists
            if 'show_url_button' not in st.session_state:
                st.session_state['show_url_button'] = True
            if 'show_urlslist_button' not in st.session_state:
                st.session_state['show_urlslist_button'] = True

            if st.session_state['show_url_button']:
                if st.button("Add from URL"):
                    st.session_state['show_url_button'] = False
                    st.markdown('---')
                    if url_input:
                        try:
                            loader = WebBaseLoader([url_input])
                            documents = loader.load()
                            for doc in documents:
                                doc.metadata['tag'] = url_tag
                                doc.metadata['source'] = url_input
                            add_documents_to_db(vectorstore, documents)
                            st.success("URL content added to vector store.")
                            log(f"URL content from {url_input} added to vector store.")
                        except Exception as e:
                            st.error(f"Error processing URL: {e}")
                            log(f"Error processing URL: {e}")
                    log('URL processing completed.')

            if st.session_state['show_urlslist_button']:
                st.markdown('---')
                if st.button("Add URLs from urlslist.txt"):
                    log('Starting URL processing from urlslist.txt...')
                    url_list_path = "urlslist.txt"
                    try:
                        if os.path.exists(url_list_path):
                            with open(url_list_path, "r") as f:
                                url_list = f.read().split(",")
                            url_list = [url.strip() for url in url_list if url.strip()]

                            added_urls = []
                            updated_urls = []

                            for url_entry in url_list:
                                if ";" in url_entry:
                                    url, tag = url_entry.split(";")[:2]
                                    url = url.strip()
                                    tag = tag.strip()
                                else:
                                    url = url_entry
                                    tag = ""

                                # Проверка, существует ли URL в базе данных
                                all_docs = vectorstore._collection.get()
                                matching_ids = []

                                for i, metadata in enumerate(all_docs['metadatas']):
                                    if 'source' in metadata and metadata['source'] == url:
                                        matching_ids.append(all_docs['ids'][i])

                                if matching_ids:
                                    # Удаление всех существующих записей с таким URL
                                    vectorstore._collection.delete(ids=matching_ids)
                                    updated_urls.append(url)
                                else:
                                    added_urls.append(url)

                                # Добавление нового документа в базу данных
                                loader = WebBaseLoader([url])
                                documents = loader.load()
                                for doc in documents:
                                    doc.metadata['tag'] = tag
                                    doc.metadata['source'] = url
                                add_documents_to_db(vectorstore, documents)

                            # Вывод результатов
                            log("URLs processing completed.")
                            if added_urls:
                                log(f"New URLs added: {', '.join(added_urls)}")
                            if updated_urls:
                                log(f"Updated URLs (existing documents were deleted and replaced): {', '.join(updated_urls)}")
                        else:
                            st.error("The file urlslist.txt does not exist.")
                            log("The file urlslist.txt does not exist.")
                    except Exception as e:
                        st.error(f"Error processing URLs: {e}")
                        log(f"Error processing URLs: {e}")
                    st.rerun()

            # Инициализация параметров пагинации
            if 'current_page' not in st.session_state:
                st.session_state['current_page'] = 0

            # Просмотр записей в базе данных с пагинацией
            if st.button("View All Documents") or 'view_all_documents_clicked' in st.session_state:
                st.session_state['view_all_documents_clicked'] = True
                log("Viewing all documents in the vector store.")
                try:
                    all_documents = vectorstore._collection.get()
                    documents = all_documents['documents']
                    metadatas = all_documents['metadatas']
                    ids = all_documents['ids']

                    if documents:
                        documents_per_page = 10
                        total_pages = (len(documents) + documents_per_page - 1) // documents_per_page
                        start_idx = st.session_state['current_page'] * documents_per_page
                        end_idx = min(start_idx + documents_per_page, len(documents))
                        current_documents = documents[start_idx:end_idx]
                        current_metadatas = metadatas[start_idx:end_idx]
                        current_ids = ids[start_idx:end_idx]

                        # Верхние кнопки навигации
                        col1, col2, col3 = st.columns([1, 1, 1])
                        if st.session_state['current_page'] > 0:
                            with col1:
                                if st.button("Previous Page", key="previous_page_top"):
                                    st.session_state['current_page'] -= 1
                                    log("Navigated to previous page.")
                                    st.rerun()
                        with col2:
                            st.write(f"Page {st.session_state['current_page'] + 1} of {total_pages}")
                        if st.session_state['current_page'] < total_pages - 1:
                            with col3:
                                if st.button("Next Page", key="next_page_top"):
                                    st.session_state['current_page'] += 1
                                    log("Navigated to next page.")
                                    st.rerun()

                        for i, (doc, metadata, doc_id) in enumerate(
                                zip(current_documents, current_metadatas, current_ids),
                                start=start_idx + 1):
                            preview_content = doc[:200]  # Отображаем первые 200 символов документа
                            st.write(f"Document {i}: {preview_content}...")
                            st.write(f"Metadata: {metadata}")
                            if st.button(f"Delete Document {i}", key=f"delete_{i}"):
                                # Удаляем вектор по его id
                                vectorstore._collection.delete(ids=[doc_id])
                                st.success(f"Document {i} deleted from vector store.")
                                log(f"Document {i} deleted from vector store.")
                                st.rerun()
                            if st.button(f"Edit Document {i}", key=f"edit_{i}"):
                                new_content = st.text_area(f"Edit Content for Document {i}",
                                                         value=doc, key=f"edit_content_{i}")
                                if st.button(f"Save Changes for Document {i}",
                                           key=f"save_edit_{i}"):
                                    # Обновляем содержимое документа
                                    vectorstore._collection.update(ids=[doc_id],
                                                                documents=[new_content])
                                    st.success(f"Document {i} updated successfully.")
                                    log(f"Document {i} updated successfully.")
                                    st.rerun()
                            st.markdown("---")  # Добавляем горизонтальный разделитель между записями

                        # Нижние кнопки навигации
                        col1, col2, col3 = st.columns([1, 1, 1])
                        if st.session_state['current_page'] > 0:
                            with col1:
                                if st.button("Previous Page", key="previous_page_bottom"):
                                    st.session_state['current_page'] -= 1
                                    log("Navigated to previous page.")
                                    st.rerun()
                        with col2:
                            st.write(f"Page {st.session_state['current_page'] + 1} of {total_pages}")
                        if st.session_state['current_page'] < total_pages - 1:
                            with col3:
                                if st.button("Next Page", key="next_page_bottom"):
                                    st.session_state['current_page'] += 1
                                    log("Navigated to next page.")
                                    st.rerun()
                    else:
                        st.warning("No documents found in the vector store.")
                        log("No documents found in the vector store.")
                except AttributeError as e:
                    st.error(f"Error retrieving documents from vector store: {str(e)}")
                    log(f"Error retrieving documents from vector store: {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    st.text_input("Ask the chatbot:", key="chat_input")
    manage_vector_store_page(st.session_state.vectorstore, None)

# Логи отображаются в боковой панели

