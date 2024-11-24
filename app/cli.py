# cli.py

import click
from app.config import Config
from app.logger import setup_logger
from app.search_utils import search_documents
from app.document_utils import add_document_to_store
from app.chat_utils import chat_with_model
from app.urlparser_utils import parse_and_save_urls
from app.urlslistaddbd_utils import add_urls_from_file as add_urls_from_file_util  # Переименованный импорт

@click.group()
def cli():
    """CLI интерфейс для управления векторным хранилищем документов."""
    pass

@cli.command()
@click.option('--interactive', is_flag=True, help='Запустить в интерактивном режиме.')
@click.option('--source', default=None, help='Путь до файла или URL источника.')
@click.option('--tag', default=None, help='Тег для документа.')
def add_document(interactive, source, tag):
    """
    Добавляет новый документ в векторное хранилище из файла или URL с указанным тегом.
    Если источник уже существует, старая запись будет удалена.
    """
    config = Config.load("config.yaml")
    logger = setup_logger(config)

    if interactive:
        click.echo("Интерактивный режим добавления документа")
        source = click.prompt("Введите путь до файла или URL источника")
        tag = click.prompt("Введите тег")

    if not source or not tag:
        click.echo("Ошибка: необходимо указать источник и тег.")
        return

    try:
        add_document_to_store(
            source=source,
            tag=tag.strip(),
            config=config,
            log_func=logger.info
        )
        click.echo(f"Документ '{source}' успешно добавлен с тегом: {tag}.")
    except Exception as e:
        logger.error(f"Ошибка при добавлении документа: {e}")
        click.echo(f"Ошибка при добавлении документа: {e}")

@cli.command()
@click.option('--query', prompt='Поисковой запрос', help='Поисковой запрос для векторного хранилища.')
@click.option('--tag', default=None, help='Фильтр по тегу (опционально).')
def search(query, tag):
    """
    Ищет документы в векторном хранилище по запросу и опционально по тегу.
    """
    config = Config.load("config.yaml")
    logger = setup_logger(config)

    try:
        results = search_documents(
            query=query,
            tag=tag,
            config=config,
            log_func=logger.info
        )

        if results:
            click.echo(f"Найдено {len(results)} результат(ов):")
            for i, doc in enumerate(results, start=1):
                click.echo(f"\nРезультат {i}:")
                click.echo(f"Содержимое: {doc['content'][:200]}...")
                click.echo(f"Метаданные: {doc['metadata']}")
                click.echo("---")
        else:
            click.echo("Результаты поиска не найдены.")
            logger.info("Результаты поиска не найдены.")
    except Exception as e:
        logger.error(f"Ошибка при поиске документов: {e}")
        click.echo(f"Ошибка при поиске документов: {e}")

@cli.command()
@click.option('--query', prompt='Вопрос', help='Вопрос для чатбота.')
@click.option('--context', default=None, help='Контекст для модели (опционально).')
@click.option('--tag', default=None, help='Тег для поиска (или "all" для поиска по всей базе).')
def chat(query, context, tag):
    """
    Отправляет вопрос к модели чатбота с указанным контекстом и/или тегом.
    """
    config = Config.load("config.yaml")
    logger = setup_logger(config)

    try:
        response = chat_with_model(
            query=query,
            context=context,
            tag=tag,
            config=config,
            log_func=logger.info
        )
        click.echo(f"Ответ: {response}")
    except Exception as e:
        logger.error(f"Ошибка при общении с моделью: {e}")
        click.echo(f"Ошибка при общении с моделью: {e}")

@cli.command()
@click.option('--base-url', prompt='URL страницы', help='Базовый URL для парсинга ссылок.')
@click.option('--tag', prompt='Тег для ссылок', help='Тег для найденных ссылок.')
@click.option('--username', default=None, help='Логин для авторизации (опционально).')
@click.option('--password', default=None, help='Пароль для авторизации (опционально).')
def parse_links(base_url, tag, username, password):
    """
    Парсит ссылки с указанной страницы и сохраняет их в файл.
    """
    config = Config.load("config.yaml")
    logger = setup_logger(config)

    try:
        parse_and_save_urls(
            base_url=base_url,
            tag=tag,
            username=username,
            password=password,
            output_file="urlslist.txt",
            log_func=logger.info
        )
        click.echo(f"Ссылки с {base_url} успешно сохранены в файл 'urlslist.txt'.")
    except Exception as e:
        logger.error(f"Ошибка при парсинге ссылок: {e}")
        click.echo(f"Ошибка при парсинге ссылок: {e}")

@cli.command()
@click.option('--url-list-path', default="urlslist.txt", help='Путь к файлу со списком URL (по умолчанию "urlslist.txt").')
@click.option('--username', default=None, help='Логин для авторизации (опционально).')
@click.option('--password', default=None, help='Пароль для авторизации (опционально).')
def add_urls_from_file(url_list_path, username, password):
    """
    Добавляет URL из файла в векторное хранилище.
    """
    config = Config.load("config.yaml")
    logger = setup_logger(config)

    try:
        add_urls_from_file_util(  # Использование переименованной утилиты
            config=config,
            url_list_path=url_list_path,
            username=username,
            password=password,
            log_func=logger.info
        )
        click.echo(f"URL из файла '{url_list_path}' успешно добавлены в векторное хранилище.")
    except Exception as e:
        logger.error(f"Ошибка при добавлении URL из файла: {e}")
        click.echo(f"Ошибка при добавлении URL из файла: {e}")

if __name__ == "__main__":
    cli()