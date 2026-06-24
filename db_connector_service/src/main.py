

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import text
import sqlparse
import asyncio
import time
from database import AsyncSessionLocal
from schema import (
    generate_full_schema,
    generate_tables_graph,
    generate_table_description,
    generate_table_sample_rows,
)
from typing import List, Dict, Any


app = FastAPI(title="DB_CONNECTOR_SERVICE")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

class QueryRequest(BaseModel):
    sql: str




MAX_ROWS = 2000
QUERY_TIMEOUT_SECONDS = 15.0

DANGEROUS_KEYWORDS = {
    "DROP", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "ALTER", "CREATE",
    "REPLACE", "GRANT", "REVOKE", "EXECUTE", "CALL", "PREPARE", "DEALLOCATE"
}

ALLOWED_STATEMENTS = {"SELECT", "WITH"}  # CTE разрешены


def is_safe_sql(parsed: sqlparse.sql.Statement) -> tuple[bool, str | None]:
    """Проверяет AST с помощью sqlparse"""
    if not parsed.is_group:
        token = parsed.get_real_name() or str(parsed).strip().upper()
        if token not in ALLOWED_STATEMENTS:
            return False, f"Разрешены только {', '.join(ALLOWED_STATEMENTS)}"

    # Проверяем наличие опасных ключевых слов в любом месте
    for token in parsed.tokens:
        if token.is_keyword and str(token).upper() in DANGEROUS_KEYWORDS:
            return False, f"Запрещённое ключевое слово: {token}"

    # Проверяем, есть ли UNION ALL без явного SELECT (очень грубая защита от инъекций)
    sql_upper = str(parsed).upper()
    if "UNION ALL" in sql_upper and "SELECT" not in sql_upper.split("UNION ALL")[0]:
        return False, "Подозрительное использование UNION ALL"

    return True, None


@app.post("/query")
async def execute_query(
    req: QueryRequest,
    db = Depends(get_db)
):
    original_sql = req.sql.strip()

    if not original_sql:
        raise HTTPException(400, "Пустой запрос")

    # 1. Нормализация и парсинг
    parsed = sqlparse.parse(original_sql)
    if not parsed:
        raise HTTPException(400, "Не удалось распарсить SQL")

    main_statement = parsed[0]

    # 2. Проверка безопасности через AST
    is_safe, reason = is_safe_sql(main_statement)
    if not is_safe:
        raise HTTPException(400, f"Небезопасный запрос: {reason}")

    # 3. Добавляем LIMIT по умолчанию, если его нет
    sql_lower = original_sql.lower()
    if "limit" not in sql_lower:
        # очень примитивная вставка — в продакшене лучше использовать sqlparse для точной вставки
        if original_sql.rstrip().endswith(";"):
            sql = original_sql.rstrip()[:-1] + f" LIMIT {MAX_ROWS};"
        else:
            sql = original_sql + f" LIMIT {MAX_ROWS}"
    else:
        sql = original_sql

    # 4. Выполнение с таймаутом
    try:
        async with asyncio.timeout(QUERY_TIMEOUT_SECONDS):
            start = time.perf_counter()
            result = await db.execute(text(sql))
            rows: List[Dict[str, Any]] = [dict(row) for row in result.mappings()]
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

        row_count = len(rows)
        if row_count > MAX_ROWS:
            rows = rows[:MAX_ROWS]

        # Формируем CSV только если нужно (экономим память)
        csv_str = ""
        if rows:
            headers = list(rows[0].keys())
            csv_lines = [",".join(str(h) for h in headers)]
            csv_lines.extend(
                ",".join(str(row.get(h, "")) for h in headers)
                for row in rows
            )
            csv_str = "\n".join(csv_lines)

        return {
            "query": sql,
            "rows": len(rows),
            "execution_time_ms": duration_ms,
            "columns": list(rows[0].keys()) if rows else [],
            "results_json": rows,
            "results_csv": csv_str,
            "error": ""
        }

    except asyncio.TimeoutError:
        raise HTTPException(504, f"Запрос превысил таймаут ({QUERY_TIMEOUT_SECONDS} сек)")
    except Exception as e:
        # Здесь можно добавить более детальное логирование
        error_msg = str(e).split("\n")[0]  # убираем длинные стеки от sqlalchemy
        raise HTTPException(400, f"Ошибка выполнения SQL: {error_msg}")

# @app.post("/query")
# async def execute_query(req: QueryRequest, db=Depends(get_db)):
#     sql = req.sql.strip()

#     # Безопасность: только SELECT
#     upper = sql.upper()
#     if not (upper.startswith("SELECT") or upper.startswith("WITH")):
#         raise HTTPException(400, "Only SELECT/WITH queries allowed")

#     start = time.perf_counter()
#     try:
#         result = await db.execute(text(sql))
#         rows = [dict(row) for row in result.mappings()]
#         duration = time.perf_counter() - start

#         # CSV-строка для удобства LLM
#         if rows:
#             headers = list(rows[0].keys())
#             csv = [",".join(headers)]
#             csv.extend([",".join(str(row.get(h, "")) for h in headers) for row in rows])
#             csv_str = "\n".join(csv)
#         else:
#             csv_str = ""

#         return {
#             "query": sql,
#             "rows": len(rows),
#             "execution_time_ms": round(duration * 1000, 2),
#             "columns": list(rows[0].keys()) if rows else [],
#             "results_json": rows,
#             "results_csv": csv_str,
#             "error": ""
#         }
#     except Exception as e:
#         return {
#             "query": sql,
#             "rows": 0,
#             "execution_time_ms": 0,
#             "columns": [],
#             "results_json": {},
#             "results_csv": "",
#             "error": f"SQL Error: {str(e)}"
#         }
#         # raise HTTPException(400, f"SQL Error: {str(e)}")


@app.get("/schema")
async def get_schema():
    return {
        'schema': await generate_full_schema()
    }


@app.get("/schema/tables", response_class=PlainTextResponse)
async def get_tables_graph():
    return await generate_tables_graph()


@app.get("/schema/table/{table_name}", response_class=PlainTextResponse)
async def get_table(table_name: str):
    return await generate_table_description(table_name)


@app.get("/schema/table/{table_name}/sample", response_class=PlainTextResponse)
async def get_table_sample(table_name: str):
    """
    Returns first 5 rows of the table in human-readable / RAG-friendly text format
    """
    content = await generate_table_sample_rows(table_name, limit=5)
    return content