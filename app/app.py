# app/app.py

import sys
import click

@click.group()
def main():
    """Главная точка входа для приложения."""
    pass

@main.command()
def api():
    """Запустить API сервер."""
    import subprocess
    subprocess.run(["uvicorn", "app.api:app", "--reload"])

@main.command()
def cli_interface():
    """Запустить CLI интерфейс."""
    from app.cli import cli as cli_app
    cli_app()

if __name__ == "__main__":
    main()