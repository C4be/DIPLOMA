from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncConnection
from geoalchemy2 import Geometry
from database import engine


async def run_sync_on_conn(conn: AsyncConnection, func, *args, **kwargs):
    return await conn.run_sync(func, *args, **kwargs)


async def get_table_names():
    async with engine.connect() as conn:
        return await run_sync_on_conn(conn, lambda c: inspect(c).get_table_names())


async def get_table_comment(table_name: str) -> str | None:
    async with engine.connect() as conn:
        dialect = engine.dialect.name
        if dialect == "postgresql":
            stmt = text("""
                SELECT obj_description(c.oid)
                FROM pg_class c
                WHERE c.relname = :table
            """)
            res = await conn.execute(stmt, {"table": table_name})
            return res.scalar()
        elif dialect == "oracle":
            stmt = text("""
                SELECT comments
                FROM all_tab_comments
                WHERE table_name = :table AND owner = USER
            """)
            res = await conn.execute(stmt, {"table": table_name.upper()})
            return res.scalar()
    return None


async def get_column_comments(table_name: str) -> dict:
    async with engine.connect() as conn:
        dialect = engine.dialect.name
        if dialect == "postgresql":
            stmt = text("""
                SELECT a.attname, pg_catalog.col_description(c.oid, a.attnum)
                FROM pg_class c
                JOIN pg_attribute a ON a.attrelid = c.oid
                WHERE c.relname = :table AND a.attnum > 0
            """)
            res = await conn.execute(stmt, {"table": table_name})
            return {row[0]: row[1] for row in res if row[1]}
        elif dialect == "oracle":
            stmt = text("""
                SELECT column_name, comments
                FROM all_col_comments
                WHERE table_name = :table AND owner = USER
            """)
            res = await conn.execute(stmt, {"table": table_name.upper()})
            return {row[0]: row[1] for row in res if row[1]}
    return {}


async def get_row_count(table_name: str) -> int:
    async with engine.connect() as conn:
        res = await conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
        return res.scalar_one()


async def generate_full_schema() -> str:
    tables = await get_table_names()
    lines = ["=== FULL DATABASE SCHEMA (for RAG) ===\n"]

    for table in sorted(tables):
        async with engine.connect() as conn:
            inspector = await run_sync_on_conn(conn, lambda c: inspect(c))

            # Получаем колонки
            columns_info = await run_sync_on_conn(conn, lambda c: inspector.get_columns(table))

            # Primary keys
            pk_info = await run_sync_on_conn(conn, lambda c: inspector.get_pk_constraint(table))
            pk_columns = pk_info.get("constrained_columns", []) if pk_info else []

            # Foreign keys
            fk_info = await run_sync_on_conn(conn, lambda c: inspector.get_foreign_keys(table))
            # Indexes — опционально, если нужно

        comment = await get_table_comment(table) or ""
        col_comments = await get_column_comments(table)
        row_count = await get_row_count(table)

        lines.append(f"Table: {table}")
        if comment:
            lines.append(f"  Comment: {comment}")
        lines.append(f"  Rows: {row_count:,}")

        lines.append("  Columns:")
        for col in columns_info:
            col_name = col["name"]
            col_type = str(col["type"])
            nullable = " NULL" if col["nullable"] else " NOT NULL"
            pk = " PK" if col_name in pk_columns else ""
            default = f" DEFAULT {col['default']}" if col.get("default") else ""
            cmt = col_comments.get(col_name, "")
            cmt = f" → {cmt}" if cmt else ""

            lines.append(f"    {col_name} {col_type}{pk}{nullable}{default}{cmt}")

        # Foreign keys
        if fk_info:
            lines.append("  Foreign Keys:")
            for fk in fk_info:
                constrained = ", ".join(fk["constrained_columns"])
                referred = f"{fk['referred_table']}.{', '.join(fk['referred_columns'])}"
                lines.append(f"    {constrained} → {referred}")

        lines.append("")

    # Граф связей (можно оставить как есть или улучшить)
    lines.append("=== RELATIONS GRAPH ===")
    for table in sorted(tables):
        async with engine.connect() as conn:
            inspector = await run_sync_on_conn(conn, lambda c: inspect(c))
            fks = await run_sync_on_conn(conn, lambda c: inspector.get_foreign_keys(table))
            for fk in fks:
                from_cols = ", ".join(fk["constrained_columns"])
                to_table = fk["referred_table"]
                to_cols = ", ".join(fk["referred_columns"])
                lines.append(f"{table}.{from_cols} → {to_table}.{to_cols}")

    return "\n".join(lines)


async def generate_tables_graph() -> str:
    tables = await get_table_names()
    lines = ["=== TABLES & RELATIONS GRAPH (for RAG) ===\n"]
    edges = []

    for table in sorted(tables):
        async with engine.connect() as conn:
            inspector = await run_sync_on_conn(conn, lambda c: inspect(c))
            fks = await run_sync_on_conn(conn, lambda c: inspector.get_foreign_keys(table))

            for fk in fks:
                from_cols = ", ".join(fk["constrained_columns"])
                to_table = fk["referred_table"]
                to_cols = ", ".join(fk["referred_columns"])
                constraint_name = fk.get("name", "unnamed_fk")

                edge_str = (
                    f"{table}.{from_cols} "
                    f"→ {to_table}.{to_cols} "
                    f"(constraint: {constraint_name})"
                )
                edges.append(edge_str)

    if not edges:
        lines.append("No foreign key relationships found in the database.")
    else:
        lines.append("Edges (relationships):")
        lines.extend([f"  {edge}" for edge in sorted(edges)])

    return "\n".join(lines)


async def generate_table_description(table_name: str) -> str:
    async with engine.connect() as conn:
        inspector = await run_sync_on_conn(conn, lambda c: inspect(c))
        columns_info = await run_sync_on_conn(conn, lambda c: inspector.get_columns(table_name))
        pk_info = await run_sync_on_conn(conn, lambda c: inspector.get_pk_constraint(table_name))
        fk_info = await run_sync_on_conn(conn, lambda c: inspector.get_foreign_keys(table_name))

    pk_columns = pk_info.get("constrained_columns", []) if pk_info else []

    comment = await get_table_comment(table_name) or "—"
    col_comments = await get_column_comments(table_name)
    row_count = await get_row_count(table_name)

    lines = [f"Table: {table_name}", f"Comment: {comment}", f"Rows: {row_count:,}", "\nColumns:"]

    for col in columns_info:
        col_name = col["name"]
        col_type = str(col["type"])
        nullable = " NULL" if col["nullable"] else ""
        pk = " PK" if col_name in pk_columns else ""
        default = f" DEFAULT {col['default']}" if col.get("default") else ""
        cmt = col_comments.get(col_name, "")
        cmt = f" → {cmt}" if cmt else ""
        lines.append(f"  {col_name} {col_type}{pk}{nullable}{default}{cmt}")

    if fk_info:
        lines.append("\nForeign Keys:")
        for fk in fk_info:
            constrained = ", ".join(fk["constrained_columns"])
            referred = f"{fk['referred_table']}.{', '.join(fk['referred_columns'])}"
            lines.append(f"  {constrained} → {referred}")

    return "\n".join(lines)


async def generate_table_sample_rows(table_name: str, limit: int = 5) -> str:
    lines = [f"Table: {table_name} — Sample rows (first {limit})", ""]

    async with engine.connect() as conn:
        # Проверяем существование таблицы (опционально, но полезно)
        inspector = await run_sync_on_conn(conn, lambda c: inspect(c))
        if table_name not in await get_table_names():
            return f"Table '{table_name}' not found."

        # Получаем колонки
        columns = await run_sync_on_conn(conn, lambda c: inspector.get_columns(table_name))
        col_names = [col["name"] for col in columns]

        if not col_names:
            return f"Table '{table_name}' has no columns or access denied."

        # Формируем безопасный запрос
        quoted_cols = ', '.join(f'"{c}"' for c in col_names)
        stmt = text(f'SELECT {quoted_cols} FROM "{table_name}" LIMIT :lim')

        try:
            result = await conn.execute(stmt, {"lim": limit})
            rows = result.mappings().fetchall()
        except Exception as e:
            return f"Error fetching sample rows: {str(e)}"

        if not rows:
            lines.append("→ No rows in the table (or access restricted)")
            return "\n".join(lines)

        # Заголовок
        lines.append("Columns: " + ", ".join(col_names))
        lines.append("")

        # Данные
        for i, row in enumerate(rows, 1):
            lines.append(f"Row {i}:")
            for col in col_names:
                val = row[col]
                # Упрощаем отображение сложных типов
                if val is None:
                    val_str = "NULL"
                elif isinstance(val, (bytes, bytearray)):
                    val_str = "[binary data]"
                else:
                    val_str = str(val).strip()
                    if len(val_str) > 120:
                        val_str = val_str[:117] + "..."
                lines.append(f"  {col: <24} : {val_str}")
            lines.append("")

    return "\n".join(lines)