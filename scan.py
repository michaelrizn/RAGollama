import streamlit as st
import json
import sqlite3
import os

# Функция для логирования
log_messages = []

def log(message):
    log_messages.append(message)
    st.session_state.logs = "\n".join(log_messages)
    st.sidebar.write(st.session_state.logs)

def scan_vector_store(vectorstore, tag=None, key=None):
    """
    Функция для поиска в векторной базе данных по ключевым словам и тегу.
    :param vectorstore: Экземпляр векторной базы данных.
    :param tag: Тег для фильтрации результатов поиска (опционально).
    :param key: Ключ для фильтрации метаданных (опционально).
    """
    # Получение списка уникальных тегов из базы данных
    try:
        conn = sqlite3.connect(os.path.join('./chroma_db', 'chroma.sqlite3'))
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT string_value FROM embedding_metadata WHERE key='tag'")
        unique_tags = [row[0] for row in cursor.fetchall()]
        conn.close()
        log(f"Successfully retrieved unique tags from vector store: {unique_tags}")
    except Exception as e:
        log(f"Error retrieving unique tags from vector store: {e}")
        unique_tags = []

    unique_tags = [""] + unique_tags  # Добавляем пустое значение в начало списка

    # Выбор тега из выпадающего списка
    tag_value = st.selectbox("Filter by tag (optional):", unique_tags, key="tag_input_scan")
    search_query = st.text_input("Enter search query for vector store:", key="search_query_input_unique")

    if st.button("Search Vector Store", key="search_vector_store_btn_unique"):
        st.session_state['show_results'] = True
        st.session_state['show_scan_interface'] = True
        log(f"Initiated search with query: '{search_query}' and tag: '{tag_value}'")

    if st.button("Clear Search Results", key="clear_search_results_btn_unique"):
        st.session_state['trigger_search'] = False
        st.session_state['show_scan_interface'] = False
        st.session_state['show_results'] = False
        st.rerun()
        log("Cleared search results.")

    try:
        if st.session_state.get('show_results', False):
            results = []
            if tag_value:
                try:
                    db_path = './chroma_db/chroma.sqlite3'
                    if not os.path.exists(db_path):
                        log(f"Database file not found at {db_path}. Please make sure the file exists and is accessible.")
                        st.error(f"Database file not found at {db_path}. Please make sure the file exists and is accessible.")
                        return

                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    log(f"Searching for tag: {tag_value}")
                    query = "SELECT DISTINCT id FROM embedding_metadata WHERE key = 'tag' AND string_value = ?"
                    cursor.execute(query, (tag_value.strip(),))
                    rows = cursor.fetchall()
                    document_ids = [row[0] for row in rows]

                    # Извлекаем все метаданные и содержимое для найденных документов
                    if document_ids:
                        placeholders = ', '.join('?' for _ in document_ids)
                        query = f"SELECT * FROM embedding_metadata WHERE id IN ({placeholders})"
                        cursor.execute(query, document_ids)
                        results = cursor.fetchall()
                    conn.close()
                except sqlite3.Error as e:
                    log(f"Unable to open database file: {e}")
                    st.error(f"Unable to open database file: {e}")
                    return
            elif search_query:
                log(f"Performing similarity search for query: '{search_query}'")
                results = vectorstore.similarity_search(query=search_query, k=5)

            if results:
                log(f"Found {len(results)} results.")
                st.write("Search results:")
                current_id = None
                current_document = {}
                for result in results:
                    result_id, key, string_value, int_value, float_value, bool_value = result
                    if result_id != current_id:
                        if current_document:
                            # Выводим текущий документ
                            st.write(f"Document ID: {current_id}")
                            for k, v in current_document.items():
                                st.write(f"{k}: {v}")
                            st.markdown('---')
                        current_id = result_id
                        current_document = {}
                    # Сохраняем метаданные в текущем документе
                    current_document[key] = string_value or int_value or float_value or bool_value

                # Выводим последний документ
                if current_document:
                    st.write(f"Document ID: {current_id}")
                    for k, v in current_document.items():
                        st.write(f"{k}: {v}")
                    st.markdown('---')
            else:
                log("No relevant documents found in the vector store.")
                st.write("No relevant documents found in the vector store.")
            st.session_state['show_results'] = False
    except Exception as e:
        log(f"Error during search: {e}")
        st.error(f"Error during search: {e}")

if 'vectorstore' in st.session_state:
    if st.sidebar.button("Scan Vector Store", key="scan_vector_store_btn_unique"):
        st.session_state['show_scan_interface'] = not st.session_state.get('show_scan_interface', False)
        log("Toggled Scan Vector Store interface.")
    if st.session_state.get('show_scan_interface', False):
        with st.container():
            st.write("Manage or Edit Documents in Vector Store")
            if st.button("View All Documents", key="view_all_documents_btn") or 'view_all_documents_clicked' in st.session_state:
                st.session_state['view_all_documents_clicked'] = True
                log("Viewing all documents in vector store.")
                try:
                    all_documents = st.session_state.vectorstore._collection.get()
                    documents = all_documents['documents']
                    metadatas = all_documents['metadatas']
                    ids = all_documents['ids']

                    if documents:
                        if 'current_page' not in st.session_state:
                            st.session_state['current_page'] = 0

                        documents_per_page = 10
                        total_pages = (len(documents) + documents_per_page - 1) // documents_per_page
                        start_idx = st.session_state['current_page'] * documents_per_page
                        end_idx = min(start_idx + documents_per_page, len(documents))
                        current_documents = documents[start_idx:end_idx]
                        current_metadatas = metadatas[start_idx:end_idx]
                        current_ids = ids[start_idx:end_idx]

                        for i, (doc, metadata, doc_id) in enumerate(
                                zip(current_documents, current_metadatas, current_ids),
                                start=start_idx + 1):
                            preview_content = doc[:200]
                            st.write(f"Document {i}: {preview_content}...")
                            st.write(f"Metadata: {metadata}")
                            if st.button(f"Delete Document {i}", key=f"delete_{i}"):
                                st.session_state.vectorstore._collection.delete(ids=[doc_id])
                                log(f"Document {i} deleted from vector store.")
                                st.success(f"Document {i} deleted from vector store.")
                                st.rerun()
                            if st.button(f"Edit Document {i}", key=f"edit_{i}"):
                                new_content = st.text_area(f"Edit Content for Document {i}", value=doc, key=f"edit_content_{i}")
                                if st.button(f"Save Changes for Document {i}", key=f"save_edit_{i}"):
                                    st.session_state.vectorstore._collection.update(ids=[doc_id], documents=[new_content])
                                    log(f"Document {i} updated successfully.")
                                    st.success(f"Document {i} updated successfully.")
                                    st.rerun()
                            st.markdown("---")
                except AttributeError as e:
                    log(f"Error retrieving documents from vector store: {str(e)}")
                    st.error(f"Error retrieving documents from vector store: {str(e)}")
            st.markdown("### Vector Store Search")
            tag_filter = st.text_input("Enter value for metadata filter (optional):", key="tag_filter_input_unique").strip()
            scan_vector_store(st.session_state.vectorstore, tag=tag_filter)
else:
    log("Vectorstore not initialized.")
    st.write("Vectorstore not initialized.")
