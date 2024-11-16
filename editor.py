import streamlit as st
from langchain_community.document_loaders import WebBaseLoader, PyMuPDFLoader, TextLoader
import os
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_community.vectorstores import Chroma
import requests

# Импорт функций из утилитного модуля
from db_utils import add_documents_to_db

# Функция для логирования
log_messages = []


def log(message):
    log_messages.append(message)
    st.session_state.logs = "\n".join(log_messages)


def authenticate(username, password):
    """
    Простая функция аутентификации.
    Замените эту логику на более безопасную (например, проверка в базе данных).
    """
    valid_users = {
        "admin": "password123",
        "user1": "mypassword"
    }
    return valid_users.get(username) == password


def fetch_protected_page(url, username, password):
    """
    Функция для получения содержимого защищённой страницы после аутентификации.
    """
    with requests.Session() as session:
        login_url = "https://example.com/login"  # Замените на реальный URL для входа
        payload = {
            'username': username,
            'password': password
        }
        response = session.post(login_url, data=payload)

        if response.status_code == 200:
            protected_response = session.get(url)
            if protected_response.status_code == 200:
                return protected_response.text
            else:
                st.error("Не удалось получить доступ к защищённой странице.")
                log("Не удалось получить доступ к защищённой странице.")
        else:
            st.error("Ошибка аутентификации.")
            log("Ошибка аутентификации.")
    return None


def add_documents_from_protected_url(vectorstore, url):
    """
    Добавление документов из защищённого URL с использованием введённых пользователем учетных данных.
    """
    username = st.session_state.get('username')
    password = st.session_state.get('password')

    if not username or not password:
        st.error("Необходимы учетные данные для доступа к защищенной странице.")
        log("Необходимы учетные данные для доступа к защищенной странице.")
        return

    page_content = fetch_protected_page(url, username, password)
    if page_content:
        loader = TextLoader(page_content)
        documents = loader.load()
        for doc in documents:
            doc.metadata['tag'] = st.session_state.get('protected_url_tag', '')
            doc.metadata['source'] = url
        add_documents_to_db(vectorstore, documents, log)
        st.success("Документ добавлен из защищённой страницы.")
        log(f"Защищенный URL {url} добавлен в векторную базу данных.")


def manage_vector_store_page(vectorstore, _):
    """
    Управление содержимым векторной базы данных на отдельной странице.
    """
    # Флажок для управления отображением элементов
    if 'show_db_controls' not in st.session_state:
        st.session_state['show_db_controls'] = False

    if st.sidebar.button("Управлять содержимым Vector Store"):
        st.session_state['show_db_controls'] = not st.session_state['show_db_controls']

    if st.session_state['show_db_controls']:
        with st.container():
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            # Информационное сообщение
            st.info("""
                **Файл или отдельный URL добавляются только по кнопке в интерфейсе.  
                После каждого нового добавления нужно перезагрузить страницу целиком (так задумано :))**
            """)

            # Кнопки для добавления, редактирования и удаления документов
            uploaded_file = st.file_uploader(
                "Загрузите документ для добавления в векторное хранилище",
                type=["pdf", "txt"])
            tag_text = st.text_input("Введите тег для документа:", key="file_tag")

            if uploaded_file is not None:
                if st.button("Добавить загруженный документ в Vector Store"):
                    st.session_state['show_db_controls'] = False
                    file_path = os.path.join("/tmp", uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    log(f"Загруженный файл: {uploaded_file.name}")

                    # Проверка, существует ли файл с таким же именем в базе данных
                    all_docs = vectorstore._collection.get()
                    matching_ids = [
                        doc_id for doc_id, metadata in zip(all_docs['ids'], all_docs['metadatas'])
                        if metadata.get('source') == uploaded_file.name
                    ]

                    if matching_ids:
                        # Удаление всех существующих записей с таким именем файла
                        vectorstore._collection.delete(ids=matching_ids)
                        log(f"Документ с именем {uploaded_file.name} уже существует и будет заменен.")

                    if uploaded_file.type == "application/pdf":
                        loader = PyMuPDFLoader(file_path)
                    elif uploaded_file.type == "text/plain":
                        loader = TextLoader(file_path)
                    else:
                        st.error("Неподдерживаемый тип файла.")
                        log("Неподдерживаемый тип файла.")
                        return

                    documents = loader.load()
                    for doc in documents:
                        doc.metadata['tag'] = tag_text
                        doc.metadata['source'] = uploaded_file.name
                    add_documents_to_db(vectorstore, documents, log)
                    st.success("Документ добавлен в векторное хранилище.")
                    log("Документ добавлен в векторное хранилище.")

            st.markdown('---')  # Горизонтальная линия
            url_input = st.text_input("Введите URL для добавления документа:", key="url_input")
            url_tag = st.text_input("Введите тег для URL:", key="url_tag")

            # Инициализация кнопок и флагов видимости
            if 'show_url_button' not in st.session_state:
                st.session_state['show_url_button'] = True

            if st.session_state['show_url_button']:
                if st.button("Добавить по URL"):
                    st.session_state['show_url_button'] = False
                    st.markdown('---')
                    if url_input:
                        try:
                            loader = WebBaseLoader([url_input])
                            documents = loader.load()
                            for doc in documents:
                                doc.metadata['tag'] = url_tag
                                doc.metadata['source'] = url_input
                            add_documents_to_db(vectorstore, documents, log)
                            st.success("Содержимое URL добавлено в векторное хранилище.")
                            log(f"Содержимое URL {url_input} добавлено в векторное хранилище.")
                        except Exception as e:
                            st.error(f"Ошибка при обработке URL: {e}")
                            log(f"Ошибка при обработке URL: {e}")
                    log('Обработка URL завершена.')

            # Инициализация параметров пагинации
            if 'current_page' not in st.session_state:
                st.session_state['current_page'] = 0

            # Просмотр записей в базе данных с пагинацией
            if st.button(
                    "Просмотреть все документы") or 'view_all_documents_clicked' in st.session_state:
                st.session_state['view_all_documents_clicked'] = True
                log("Просмотр всех документов в векторном хранилище.")
                try:
                    all_documents = vectorstore._collection.get()
                    documents = all_documents['documents']
                    metadatas = all_documents['metadatas']
                    ids = all_documents['ids']

                    if documents:
                        documents_per_page = 10
                        total_pages = (
                                                  len(documents) + documents_per_page - 1) // documents_per_page
                        start_idx = st.session_state['current_page'] * documents_per_page
                        end_idx = min(start_idx + documents_per_page, len(documents))
                        current_documents = documents[start_idx:end_idx]
                        current_metadatas = metadatas[start_idx:end_idx]
                        current_ids = ids[start_idx:end_idx]

                        # Верхние кнопки навигации
                        col1, col2, col3 = st.columns([1, 1, 1])
                        if st.session_state['current_page'] > 0:
                            with col1:
                                if st.button("Предыдущая страница", key="previous_page_top"):
                                    st.session_state['current_page'] -= 1
                                    log("Переход на предыдущую страницу.")
                                    st.experimental_rerun()
                        with col2:
                            st.write(
                                f"Страница {st.session_state['current_page'] + 1} из {total_pages}")
                        if st.session_state['current_page'] < total_pages - 1:
                            with col3:
                                if st.button("Следующая страница", key="next_page_top"):
                                    st.session_state['current_page'] += 1
                                    log("Переход на следующую страницу.")
                                    st.experimental_rerun()

                        for i, (doc, metadata, doc_id) in enumerate(
                                zip(current_documents, current_metadatas, current_ids),
                                start=start_idx + 1):
                            preview_content = doc[:200]  # Отображаем первые 200 символов документа
                            st.write(f"Документ {i}: {preview_content}...")
                            st.write(f"Метаданные: {metadata}")
                            if st.button(f"Удалить документ {i}", key=f"delete_{i}"):
                                # Удаляем вектор по его id
                                vectorstore._collection.delete(ids=[doc_id])
                                st.success(f"Документ {i} удалён из векторного хранилища.")
                                log(f"Документ {i} удалён из векторного хранилища.")
                                st.experimental_rerun()
                            if st.button(f"Редактировать документ {i}", key=f"edit_{i}"):
                                new_content = st.text_area(
                                    f"Редактировать содержимое документа {i}",
                                    value=doc, key=f"edit_content_{i}")
                                if st.button(f"Сохранить изменения для документа {i}",
                                             key=f"save_edit_{i}"):
                                    # Обновляем содержимое документа
                                    vectorstore._collection.update(ids=[doc_id],
                                                                   documents=[new_content])
                                    st.success(f"Документ {i} успешно обновлён.")
                                    log(f"Документ {i} успешно обновлён.")
                                    st.experimental_rerun()
                            st.markdown("---")  # Горизонтальный разделитель между записями

                        # Нижние кнопки навигации
                        col1, col2, col3 = st.columns([1, 1, 1])
                        if st.session_state['current_page'] > 0:
                            with col1:
                                if st.button("Предыдущая страница", key="previous_page_bottom"):
                                    st.session_state['current_page'] -= 1
                                    log("Переход на предыдущую страницу.")
                                    st.experimental_rerun()
                        with col2:
                            st.write(
                                f"Страница {st.session_state['current_page'] + 1} из {total_pages}")
                        if st.session_state['current_page'] < total_pages - 1:
                            with col3:
                                if st.button("Следующая страница", key="next_page_bottom"):
                                    st.session_state['current_page'] += 1
                                    log("Переход на следующую страницу.")
                                    st.experimental_rerun()
                    else:
                        st.warning("В векторном хранилище нет документов.")
                        log("В векторном хранилище нет документов.")
                except AttributeError as e:
                    st.error(f"Ошибка при получении документов из векторного хранилища: {str(e)}")
                    log(f"Ошибка при получении документов из векторного хранилища: {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    # Аутентификация
    with st.sidebar:
        st.header("Аутентификация")
        username = st.text_input("Логин", key="username")
        password = st.text_input("Пароль", type="password", key="password")
        if st.button("Войти"):
            if authenticate(username, password):
                st.session_state['authenticated'] = True
                st.success("Успешный вход!")
                log(f"Пользователь '{username}' успешно аутентифицирован.")
            else:
                st.error("Неверный логин или пароль.")
                log(f"Неудачная попытка аутентификации пользователя '{username}'.")

    # Проверка аутентификации
    if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
        st.warning("Пожалуйста, войдите в систему для доступа к функционалу.")
    else:
        st.text_input("Задайте вопрос чат-боту:", key="chat_input")
        # Инициализация векторного хранилища, если оно ещё не инициализировано
        if 'vectorstore' not in st.session_state:
            # Здесь необходимо инициализировать ваше векторное хранилище, например:
            # embeddings = NomicEmbeddings(api_key="YOUR_NOMIC_API_KEY")
            # st.session_state.vectorstore = Chroma(persist_directory="db", embedding_function=embeddings)
            # Для примера используем пустое хранилище
            embeddings = NomicEmbeddings(model="nomic-embed-text-v1.5", inference_mode="local")
            st.session_state.vectorstore = Chroma(persist_directory="chroma_db",
                                                  embedding_function=embeddings)
            log("Инициализировано векторное хранилище.")

        manage_vector_store_page(st.session_state.vectorstore, None)

    # Логи отображаются в боковой панели
    with st.sidebar:
        st.markdown('---')
        st.header("Логи")
        if 'logs' in st.session_state:
            st.text_area("Логи", st.session_state.logs, height=200)
        else:
            st.text_area("Логи", "", height=200)