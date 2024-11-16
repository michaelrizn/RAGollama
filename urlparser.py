# парсит подкатегории сайта и создаёт список с указанным тегом в файл urlslist.txt

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def authenticate(session, base_url):
    """Авторизация на сайте, если требуется"""
    print(f"Требуется авторизация для доступа к {base_url}")
    username = input("Введите логин: ")
    password = input("Введите пароль: ")
    session.auth = (username, password)
    response = session.get(base_url)
    if response.ok:
        print("Успешная авторизация.")
    else:
        print(f"Ошибка авторизации: {response.status_code}. Проверьте логин и пароль.")
        exit()


def scrape_confluence_links(base_url, session):
    """Сбор ссылок на подкатегории или страницы в Confluence"""
    response = session.get(base_url)
    if response.status_code == 401:
        authenticate(session, base_url)
        response = session.get(base_url)

    if not response.ok:
        print(f"Ошибка доступа к {base_url}: {response.status_code}")
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


def main():
    # Ввод исходного URL
    base_url = input("Введите URL страницы: ").strip()
    if not base_url:
        print("URL не может быть пустым.")
        return

    # Ввод тега
    tag = input("Введите тег для списка URL: ").strip()
    if not tag:
        print("Тег не может быть пустым.")
        return

    session = requests.Session()
    print(f"Обработка страницы {base_url}...")

    # Сбор ссылок
    links = scrape_confluence_links(base_url, session)

    # Сохранение результата в файл
    output_file = 'urlslist.txt'
    with open(output_file, 'w', encoding='utf-8') as file:
        for url in links:
            file.write(f"{url};{tag};,\n")

    print(f"Список подкатегорий успешно сохранен в '{output_file}'.")


if __name__ == "__main__":
    main()