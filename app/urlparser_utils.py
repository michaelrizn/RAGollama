# urlparser_utils.py

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def parse_and_save_urls(base_url, tag, output_file="urlslist.txt", log_func=None, username=None, password=None):
    """
    Парсинг ссылок с веб-страницы и сохранение их в файл без дубликатов.
    При этом для каждого URL указывается, был ли он добавлен или перезаписан.

    Args:
        base_url (str): Базовый URL страницы для парсинга.
        tag (str): Тег для сохранения вместе с URL.
        output_file (str): Путь к файлу для сохранения URL.
        log_func (callable, optional): Функция для логирования.
        username (str, optional): Имя пользователя для авторизации.
        password (str, optional): Пароль для авторизации.

    Raises:
        Exception: Если страница недоступна или произошла ошибка при записи файла.
    """
    session = requests.Session()

    # Установка User-Agent
    user_agent = os.getenv("USER_AGENT", "MyCustomUserAgent/1.0")
    session.headers.update({'User-Agent': user_agent})

    try:
        # Чтение существующих URL из файла
        existing_urls = set()
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if ',' in line:
                        existing_url = line.split(',', 1)[0].strip()
                        existing_urls.add(existing_url)

        # Если логин и пароль предоставлены, используем их для авторизации
        if username and password:
            session.auth = (username, password)
            if log_func:
                log_func("Используется предоставленная авторизация.")

        response = session.get(base_url)

        if response.status_code == 401:  # Требуется авторизация
            if log_func:
                log_func("Требуется авторизация для доступа к странице.")
            # Если логин и пароль не были предоставлены, запрашиваем у пользователя
            if not (username and password):
                username = input("Введите логин: ")
                password = input("Введите пароль: ")
                session.auth = (username, password)
                response = session.get(base_url)

        if not response.ok:
            raise Exception(f"Ошибка доступа к странице {base_url}: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        new_links = set()

        # Извлечение всех ссылок с параметром "pageId"
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if 'pageId' in href:  # Фильтрация для Confluence
                full_url = urljoin(base_url, href)
                new_links.add(full_url)  # Множество автоматически исключает дубликаты

        if log_func:
            log_func(f"Найдено {len(new_links)} уникальных ссылок на странице {base_url}.")

        # Определение добавленных и перезаписанных URL
        added_urls = new_links - existing_urls
        overwritten_urls = new_links & existing_urls

        # Логирование для каждого URL с тегом
        for url in added_urls:
            if log_func:
                log_func(f"URL добавлен: {url}, Тег: {tag}")

        for url in overwritten_urls:
            if log_func:
                log_func(f"URL перезаписан: {url}, Тег: {tag}")

        # Объединение новых и существующих URL для перезаписи файла
        combined_urls = new_links  # Так как мы перезаписываем файл, достаточно новых уникальных URL

        # Сохранение ссылок в файл (перезапись файла при каждом выполнении)
        with open(output_file, 'w', encoding='utf-8') as f:
            for link in combined_urls:
                f.write(f"{link},{tag}\n")

        if log_func:
            log_func(f"Файл {output_file} успешно обновлен.")

    except Exception as e:
        if log_func:
            log_func(f"Ошибка при парсинге ссылок: {e}")
        raise e

def read_urls_from_file(url_list_path="urlslist.txt"):
    """
    Чтение и разбор URL из указанного файла.

    Args:
        url_list_path (str): Путь к файлу со списком URL.
    Returns:
        Список кортежей (url, tag).
    """
    if not os.path.exists(url_list_path):
        raise FileNotFoundError(f"The file {url_list_path} does not exist.")

    with open(url_list_path, "r", encoding="utf-8") as f:
        content = f.read()

    url_entries = content.strip().split("\n")
    url_list = []
    for entry in url_entries:
        if "," in entry:
            url, tag = entry.split(",", 1)
            url = url.strip()
            tag = tag.strip()
            url_list.append((url, tag))
    return url_list