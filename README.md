Приложение для поиска и простой, локальной обработки информации из своих источников. Используется RAG-архитектура, langchain, ollama. Модельки на свой вкус и мощность компьютера.

Всё собрано на коленке при помощи промпт-инжиниринга и не претендует на что-либо. Задачу свою выполняет и этого достаточно.

streamlit run app.py - запуск

app.py - основной файл для главной страницы и общения с моделькой

db_utils.py - отдельный модуль для хранения общих функций, связанных с работой с векторной базой данных

editor.py - дополнительный функционал, можно добавить отдельно по одной ссылке или файл в БД. Можно полистать БД постранично.

scan.py - поиск по БД без участия модели

urlparser.py - создаёт список ссылок с тегом

urlslistaddbd.py добавляет в БД ссылки по списку из файла urlslist.txt