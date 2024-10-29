import streamlit as st
from langchain_community.document_loaders import WebBaseLoader, PyMuPDFLoader, TextLoader
import os

def manage_vector_store_page(vectorstore, add_documents_to_db):
    """
    Управление содержимым векторной базы данных на отдельной странице.
    :param vectorstore: Экземпляр векторной базы данных.
    :param add_documents_to_db: Функция для добавления документов в базу данных.
    """
    # Флажок для управления отображением элементов
    if 'show_db_controls' not in st.session_state:
        st.session_state['show_db_controls'] = False

    if st.sidebar.button("Manage Vector Store Contents"):
        st.session_state['show_db_controls'] = not st.session_state['show_db_controls']

    if st.session_state['show_db_controls']:
        # Кнопки для добавления, редактирования и удаления документов
        uploaded_file = st.file_uploader("Upload a document to add to the vector store",
                                         type=["pdf", "txt"])
        if uploaded_file is not None:
            file_path = os.path.join("/tmp", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            if uploaded_file.type == "application/pdf":
                loader = PyMuPDFLoader(file_path)
            elif uploaded_file.type == "text/plain":
                loader = TextLoader(file_path)
            else:
                st.error("Unsupported file type.")
                return

            documents = loader.load()
            add_documents_to_db(vectorstore, documents)
            st.success("Document added to vector store.")

        url_input = st.text_input("Enter URL to add document from:", key="url_input")

        # Initialize button states and visibility flags in session state if not exists
        if 'show_url_button' not in st.session_state:
            st.session_state['show_url_button'] = True
        if 'show_urlslist_button' not in st.session_state:
            st.session_state['show_urlslist_button'] = True

        if st.session_state['show_url_button']:
            if st.button("Add from URL"):
                if url_input:
                    st.session_state['show_url_button'] = False
                    try:
                        loader = WebBaseLoader([url_input])
                        documents = loader.load()
                        add_documents_to_db(vectorstore, documents)
                        st.success("Document added from URL to vector store.")
                    finally:
                        st.rerun()

        # Кнопка для добавления URL из файла urlslist.txt
        if st.session_state['show_urlslist_button']:
            if st.button("Add URLs from urlslist.txt"):
                st.session_state['show_urlslist_button'] = False
                try:
                    url_list_path = "urlslist.txt"
                    if os.path.exists(url_list_path):
                        with open(url_list_path, "r") as f:
                            url_list = f.read().split(",")
                        url_list = [url.strip() for url in url_list if url.strip()]

                        added_urls = []
                        updated_urls = []

                        for url in url_list:
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
                            add_documents_to_db(vectorstore, documents)

                        # Вывод результатов
                        st.write("URLs processing completed.")
                        if added_urls:
                            st.write("New URLs added:")
                            for added_url in added_urls:
                                st.write(f"- {added_url}")
                        if updated_urls:
                            st.write("Updated URLs (existing documents were deleted and replaced):")
                            for updated_url in updated_urls:
                                st.write(f"- {updated_url}")
                    else:
                        st.error("The file urlslist.txt does not exist.")
                finally:
                    st.rerun()

        # Форма для поиска документов в базе данных
        search_query = st.text_input("Search documents in vector store:", key="search_query")
        if search_query:
            try:
                search_results = vectorstore.similarity_search(search_query, k=50)
                if search_results:
                    # Параметры пагинации для результатов поиска
                    if 'search_current_page' not in st.session_state:
                        st.session_state['search_current_page'] = 0

                    search_results_per_page = 5
                    total_search_pages = (len(search_results) + search_results_per_page - 1) // search_results_per_page
                    search_start_idx = st.session_state['search_current_page'] * search_results_per_page
                    search_end_idx = min(search_start_idx + search_results_per_page, len(search_results))
                    current_search_results = search_results[search_start_idx:search_end_idx]

                    # Отображение результатов поиска с пагинацией
                    st.write("Search Results:")
                    for i, result in enumerate(current_search_results, start=search_start_idx + 1):
                        preview_content = result.page_content[:200]  # Отображаем первые 200 символов документа
                        st.write(f"Result {i}: {preview_content}...")
                        st.write(f"Metadata: {result.metadata}")
                        if st.button(f"Delete Document {i}", key=f"delete_search_{i}"):
                            # Удаляем вектор по его embedding_id
                            embedding_id = result.metadata.get('embedding_id')
                            if embedding_id:
                                vectorstore._collection.delete(ids=[embedding_id])
                                st.success(f"Document {i} deleted from vector store.")
                                st.rerun()
                        if st.button(f"Edit Document {i}", key=f"edit_search_{i}"):
                            new_content = st.text_area(f"Edit Content for Document {i}", value=result.page_content, key=f"edit_content_{i}")
                            if st.button(f"Save Changes for Document {i}", key=f"save_edit_{i}"):
                                # Обновляем содержимое документа
                                vectorstore._collection.update(ids=[result.metadata.get('id', result.metadata.get('source'))], documents=[new_content])
                                st.success(f"Document {i} updated successfully.")
                                st.rerun()
                        st.markdown("---")

                    # Кнопки навигации для результатов поиска
                    col1, col2, col3 = st.columns([1, 1, 1])
                    if st.session_state['search_current_page'] > 0:
                        with col1:
                            if st.button("Previous Page", key="search_previous_page"):
                                st.session_state['search_current_page'] -= 1
                                st.rerun()
                    with col2:
                        st.write(f"Page {st.session_state['search_current_page'] + 1} of {total_search_pages}")
                    if st.session_state['search_current_page'] < total_search_pages - 1:
                        with col3:
                            if st.button("Next Page", key="search_next_page"):
                                st.session_state['search_current_page'] += 1
                                st.rerun()
                else:
                    st.warning("No matching documents found in the vector store.")
            except AttributeError as e:
                st.error(f"Error searching documents in vector store: {str(e)}")

        # Инициализация параметров пагинации
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = 0

        # Просмотр записей в базе данных с пагинацией
        if st.button("View All Documents") or 'view_all_documents_clicked' in st.session_state:
            st.session_state['view_all_documents_clicked'] = True
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
                                st.rerun()
                    with col2:
                        st.write(f"Page {st.session_state['current_page'] + 1} of {total_pages}")
                    if st.session_state['current_page'] < total_pages - 1:
                        with col3:
                            if st.button("Next Page", key="next_page_top"):
                                st.session_state['current_page'] += 1
                                st.rerun()

                    for i, (doc, metadata, doc_id) in enumerate(zip(current_documents, current_metadatas, current_ids), start=start_idx + 1):
                        preview_content = doc[:200]  # Отображаем первые 200 символов документа
                        st.write(f"Document {i}: {preview_content}...")
                        st.write(f"Metadata: {metadata}")
                        if st.button(f"Delete Document {i}", key=f"delete_{i}"):
                            # Удаляем вектор по его id
                            vectorstore._collection.delete(ids=[doc_id])
                            st.success(f"Document {i} deleted from vector store.")
                            st.rerun()
                        if st.button(f"Edit Document {i}", key=f"edit_{i}"):
                            new_content = st.text_area(f"Edit Content for Document {i}", value=doc, key=f"edit_content_{i}")
                            if st.button(f"Save Changes for Document {i}", key=f"save_edit_{i}"):
                                # Обновляем содержимое документа
                                vectorstore._collection.update(ids=[doc_id], documents=[new_content])
                                st.success(f"Document {i} updated successfully.")
                                st.rerun()
                        st.markdown("---")  # Добавляем горизонтальный разделитель между записями

                    # Нижние кнопки навигации
                    col1, col2, col3 = st.columns([1, 1, 1])
                    if st.session_state['current_page'] > 0:
                        with col1:
                            if st.button("Previous Page", key="previous_page_bottom"):
                                st.session_state['current_page'] -= 1
                                st.rerun()
                    with col2:
                        st.write(f"Page {st.session_state['current_page'] + 1} of {total_pages}")
                    if st.session_state['current_page'] < total_pages - 1:
                        with col3:
                            if st.button("Next Page", key="next_page_bottom"):
                                st.session_state['current_page'] += 1
                                st.rerun()
                else:
                    st.warning("No documents found in the vector store.")
            except AttributeError as e:
                st.error(f"Error retrieving documents from vector store: {str(e)}")
