import click
from app.config import Config
from app.logger import setup_logger
from app.search_utils import search_documents
from app.document_utils import add_document_to_store
from app.chat_utils import chat_with_model


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


if __name__ == '__main__':
    cli()