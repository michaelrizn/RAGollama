# app/urlparser.py

import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.logger import setup_logger
from app.config import Config

def scrape_confluence_links(base_url, session, logger):
    """Сбор ссылок на подкатегории или страницы в Confluence"""
    response = session.get(base_url)

    if not response.ok:
        logger.error(f"Ошибка доступа к {base_url}: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = []

    # Извлечение всех ссылок с параметром "pageId"
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if 'pageId' in href:  # Условие фильтрации для Confluence
            full_url = urljoin(base_url, href)
            links.append(full_url)

    return links

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

    url_entries = content.split(",")
    url_list = []
    for entry in url_entries:
        entry = entry.strip()
        if not entry:
            continue
        if ";" in entry:
            url, tag = entry.split(";", 1)
            url = url.strip()
            tag = tag.strip(";").strip()  # Убираем лишнюю точку с запятой в конце
        else:
            url = entry
            tag = ""
        url_list.append((url, tag))
    return url_list

def main(config: Config, logger):
    # Ввод исходного URL
    base_url = input("Введите URL страницы: ").strip()
    if not base_url:
        logger.error("URL не может быть пустым.")
        return

    # Ввод тега
    tag = input("Введите тег для списка URL: ").strip()
    if not tag:
        logger.error("Тег не может быть пустым.")
        return

    session = requests.Session()
    logger.info(f"Обработка страницы {base_url}...")

    # Сбор ссылок
    links = scrape_confluence_links(base_url, session, logger)

    # Сохранение результата в файл
    output_file = 'urlslist.txt'
    with open(output_file, 'w', encoding='utf-8') as file:
        for url in links:
            file.write(f"{url};{tag};,\n")

    logger.info(f"Список подкатегорий успешно сохранен в '{output_file}'.")