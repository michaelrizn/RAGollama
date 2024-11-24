from fastapi import APIRouter, HTTPException, Query, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os

router = APIRouter()

# Подключение папки для шаблонов
templates = Jinja2Templates(directory="templates")

# Путь к базе данных
DB_PATH = os.path.join("chroma_db", "chroma.sqlite3")

# Проверка существования базы данных
if not os.path.exists(DB_PATH):
    raise RuntimeError(f"База данных не найдена по пути: {DB_PATH}")


def get_db_connection():
    """
    Устанавливает соединение с базой данных.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подключения к базе данных: {str(e)}")


@router.get("/", response_class=HTMLResponse)
async def table_metadata_page(request: Request, page: int = Query(1, ge=1), search: str = Query(None)):
    """
    Рендеринг таблицы с данными из таблицы embedding_metadata с поддержкой поиска.
    """
    page_size = 50
    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    conn = get_db_connection()
    cursor = conn.cursor()

    # Запрос данных с поддержкой поиска
    if search:
        query = """
            SELECT * FROM embedding_metadata
            WHERE key LIKE ? OR string_value LIKE ?
        """
        cursor.execute(query, (f"%{search}%", f"%{search}%"))
    else:
        query = "SELECT * FROM embedding_metadata"
        cursor.execute(query)

    records = cursor.fetchall()

    # Ограничение на текущую страницу
    paginated_records = records[start_index:end_index]
    total_pages = (len(records) + page_size - 1) // page_size

    # Формирование данных для отображения
    results = [
        {
            "id": record["id"],
            "key": record["key"],
            "string_value": record["string_value"],
        }
        for record in paginated_records
    ]

    conn.close()

    return templates.TemplateResponse("table.html", {
        "request": request,
        "records": results,
        "page": page,
        "total_pages": total_pages,
        "search": search,
    })


@router.get("/edit/{record_id}", response_class=HTMLResponse)
async def edit_record_page(request: Request, record_id: int):
    """
    Рендеринг страницы редактирования записи.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Проверка существования записи в таблице embedding_metadata
    cursor.execute("SELECT * FROM embedding_metadata WHERE id = ?", (record_id,))
    record_row = cursor.fetchone()
    if not record_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Запись не найдена")

    # Формирование объекта записи
    record = {
        "id": record_row["id"],
        "key": record_row["key"],
        "string_value": record_row["string_value"],
    }

    conn.close()
    return templates.TemplateResponse("edit_record.html", {"request": request, "record": record})


@router.post("/edit/{record_id}")
async def edit_record(record_id: int, key: str = Form(...), string_value: str = Form(None)):
    """
    Обновление записи через форму.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Обновление записи в базе данных
    cursor.execute(
        "UPDATE embedding_metadata SET key = ?, string_value = ? WHERE id = ?",
        (key, string_value, record_id)
    )

    conn.commit()
    conn.close()
    return RedirectResponse(url="/table/", status_code=303)