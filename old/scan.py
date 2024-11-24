import streamlit as st
import json
import sqlite3
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re


# Функция для логирования
def log(message):
    if 'log_messages' not in st.session_state:
        st.session_state.log_messages = []
    st.session_state.log_messages.append(message)
    st.session_state.logs = "\n".join(st.session_state.log_messages)
    st.sidebar.write(st.session_state.logs)


def scan_site(url):
    """
    Сканирует указанный URL и извлекает непосредственные подразделы (ссылки) на этой странице.
    :param url: URL страницы для сканирования.
    :return: Список найденных URL.
    """
    visited = set()
    urls = []
    # Регулярное выражение для поиска ссылок на страницы Confluence
    page_id_pattern = re.compile(r'viewpage\.action\?pageId=\d+')

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            log(f"Не удалось получить доступ к {url} (статус код: {response.status_code})")
            return []
        soup = BeautifulSoup(response.text, 'html.parser')

        # Поиск всех ссылок, соответствующих паттерну Confluence
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if page_id_pattern.search(href):
                absolute_url = urljoin(url, href).split('#')[0]
                # Избегаем добавления основной страницы
                if absolute_url not in visited and absolute_url != url:
                    visited.add(absolute_url)
                    urls.append(absolute_url)
                    log(f"Найден URL подраздела: {absolute_url}")
    except requests.RequestException as e:
        log(f"Ошибка при доступе к {url}: {e}")

    return list(visited)


def scan_vector_store(vectorstore):
    """
    Функция для поиска в векторной базе данных по ключевым словам и тегу.
    :param vectorstore: Экземпляр векторной базы данных.
    """
    # Получение списка уникальных тегов из базы данных
    try:
        conn = sqlite3.connect(os.path.join('./chroma_db', 'chroma.sqlite3'))
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT string_value FROM embedding_metadata WHERE key='tag'")
        unique_tags = [row[0] for row in cursor.fetchall()]
        conn.close()
        log(f"Успешно получены уникальные теги из векторного хранилища: {unique_tags}")
    except Exception as e:
        log(f"Ошибка при получении уникальных тегов из векторного хранилища: {e}")
        unique_tags = []

    unique_tags = [""] + unique_tags  # Добавляем пустое значение в начало списка

    # Выбор тега из выпадающего списка с уникальным ключом
    tag_value = st.selectbox("Filter by tag (optional):", unique_tags, key="tag_input_scan_unique")

    # Ввод поискового запроса с уникальным ключом
    search_query = st.text_input("Enter search query for vector store:",
                                 key="search_query_input_unique_unique")

    # Кнопка поиска с уникальным ключом
    if st.button("Search Vector Store", key="search_vector_store_btn_unique"):
        st.session_state['show_results'] = True
        st.session_state['show_scan_interface'] = True
        log(f"Инициирован поиск с запросом: '{search_query}' и тегом: '{tag_value}'")

    # Кнопка очистки результатов поиска с уникальным ключом
    if st.button("Clear Search Results", key="clear_search_results_btn_unique"):
        st.session_state['trigger_search'] = False
        st.session_state['show_scan_interface'] = False
        st.session_state['show_results'] = False
        st.session_state.logs = ""
        st.rerun()
        log("Результаты поиска очищены.")

    try:
        if st.session_state.get('show_results', False):
            results = []
            if tag_value:
                # Используем встроенную фильтрацию Chroma для поиска только среди документов с указанным тегом
                filter_dict = {"tag": tag_value}
                log(f"Выполняется поиск по запросу с фильтром по тегу: {tag_value}")
                log(f"Применён фильтр: {filter_dict}")
                results = vectorstore.similarity_search(query=search_query, k=5, filter=filter_dict)

                # Дополнительно логируем метаданные найденных документов
                if results:
                    for idx, doc in enumerate(results):
                        log(f"Результат {idx + 1}: tag={doc.metadata.get('tag', 'N/A')}, source={doc.metadata.get('source', 'N/A')}")
            elif search_query:
                # Обычный поиск по запросу без фильтра
                log("Выполняется обычный поиск без фильтра по тегу.")
                results = vectorstore.similarity_search(query=search_query, k=5)
                # Логирование метаданных результатов
                if results:
                    for idx, doc in enumerate(results):
                        log(f"Результат {idx + 1}: tag={doc.metadata.get('tag', 'N/A')}, source={doc.metadata.get('source', 'N/A')}")

            if results:
                log(f"Найдено {len(results)} результатов.")
                st.write("Search results:")
                for i, doc in enumerate(results, start=1):
                    st.write(f"Document {i}: {doc.page_content[:200]}...")
                    st.write(f"Metadata: {doc.metadata}")
                    st.markdown('---')
            else:
                log("Не найдено релевантных документов в векторном хранилище.")
                st.write("No relevant documents found in the vector store.")
            st.session_state['show_results'] = False
    except Exception as e:
        log(f"Ошибка во время поиска: {e}")
        st.error(f"Error during search: {e}")


# Основной блок кода
if 'vectorstore' in st.session_state:
    # Кнопка "Scan Vector Store" с уникальным ключом
    if st.sidebar.button("Scan Vector Store", key="scan_vector_store_btn_unique_main"):
        st.session_state['show_scan_interface'] = not st.session_state.get('show_scan_interface',
                                                                           False)
        log("Интерфейс сканирования векторного хранилища переключён.")

    if st.session_state.get('show_scan_interface', False):
        with st.container():
            st.write("Manage or Edit Documents in Vector Store")

            # Кнопка "View All Documents" с уникальным ключом
            if st.button("View All Documents", key="view_all_documents_btn_unique"):
                st.session_state['view_all_documents_clicked'] = True
                log("Просмотр всех документов в векторном хранилище.")
                try:
                    all_documents = st.session_state.vectorstore._collection.get()
                    documents = all_documents['documents']
                    metadatas = all_documents['metadatas']
                    ids = all_documents['ids']

                    if documents:
                        if 'current_page' not in st.session_state:
                            st.session_state['current_page'] = 0

                        documents_per_page = 10
                        total_pages = (
                                                  len(documents) + documents_per_page - 1) // documents_per_page
                        start_idx = st.session_state['current_page'] * documents_per_page
                        end_idx = min(start_idx + documents_per_page, len(documents))
                        current_documents = documents[start_idx:end_idx]
                        current_metadatas = metadatas[start_idx:end_idx]
                        current_ids = ids[start_idx:end_idx]

                        # Верхние кнопки навигации с уникальными ключами
                        col1, col2, col3 = st.columns([1, 1, 1])
                        if st.session_state['current_page'] > 0:
                            with col1:
                                if st.button("Previous Page", key="previous_page_top_unique"):
                                    st.session_state['current_page'] -= 1
                                    log("Навигация на предыдущую страницу.")
                                    st.rerun()
                        with col2:
                            st.write(
                                f"Page {st.session_state['current_page'] + 1} of {total_pages}")
                        if st.session_state['current_page'] < total_pages - 1:
                            with col3:
                                if st.button("Next Page", key="next_page_top_unique"):
                                    st.session_state['current_page'] += 1
                                    log("Навигация на следующую страницу.")
                                    st.rerun()

                        for i, (doc, metadata, doc_id) in enumerate(
                                zip(current_documents, current_metadatas, current_ids),
                                start=start_idx + 1):
                            preview_content = doc[:200]  # Отображаем первые 200 символов документа
                            st.write(f"Document {i}: {preview_content}...")
                            st.write(f"Metadata: {metadata}")

                            # Кнопка "Delete Document" с уникальным ключом
                            if st.button(f"Delete Document {i}", key=f"delete_{i}_unique"):
                                # Удаляем вектор по его id
                                st.session_state.vectorstore._collection.delete(ids=[doc_id])
                                st.success(f"Document {i} deleted from vector store.")
                                log(f"Документ {i} удалён из векторного хранилища.")
                                st.rerun()

                            # Кнопка "Edit Document" с уникальным ключом
                            if st.button(f"Edit Document {i}", key=f"edit_{i}_unique"):
                                new_content = st.text_area(f"Edit Content for Document {i}",
                                                           value=doc,
                                                           key=f"edit_content_{i}_unique")
                                # Кнопка "Save Changes" с уникальным ключом
                                if st.button(f"Save Changes for Document {i}",
                                             key=f"save_edit_{i}_unique"):
                                    # Обновляем содержимое документа
                                    st.session_state.vectorstore._collection.update(ids=[doc_id],
                                                                                    documents=[
                                                                                        new_content])
                                    st.success(f"Document {i} updated successfully.")
                                    log(f"Документ {i} обновлён успешно.")
                                    st.rerun()
                            st.markdown(
                                "---")  # Добавляем горизонтальный разделитель между записями

                        # Нижние кнопки навигации с уникальными ключами
                        col1, col2, col3 = st.columns([1, 1, 1])
                        if st.session_state['current_page'] > 0:
                            with col1:
                                if st.button("Previous Page", key="previous_page_bottom_unique"):
                                    st.session_state['current_page'] -= 1
                                    log("Навигация на предыдущую страницу.")
                                    st.rerun()
                        with col2:
                            st.write(
                                f"Page {st.session_state['current_page'] + 1} of {total_pages}")
                        if st.session_state['current_page'] < total_pages - 1:
                            with col3:
                                if st.button("Next Page", key="next_page_bottom_unique"):
                                    st.session_state['current_page'] += 1
                                    log("Навигация на следующую страницу.")
                                    st.rerun()
                    else:
                        st.warning("No documents found in the vector store.")
                        log("Векторное хранилище пусто.")
                except AttributeError as e:
                    log(f"Ошибка при получении документов из векторного хранилища: {str(e)}")
                    st.error(f"Error retrieving documents from vector store: {str(e)}")

            # Раздел поиска векторного хранилища
            st.markdown("### Vector Store Search")
            # Поле ввода для фильтрации метаданных с уникальным ключом
            tag_filter = st.text_input("Enter value for metadata filter (optional):",
                                       key="tag_filter_input_unique_2").strip()
            scan_vector_store(st.session_state.vectorstore, tag=tag_filter)
else:
    log("Vectorstore not initialized.")
    st.write("Vectorstore not initialized.")
