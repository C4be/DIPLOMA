"""
Exact Set Match Accuracy (ESM) — структурное сравнение SQL через AST.

Использует sqlglot для парсинга SQL в AST и сравнивает компоненты:
- SELECT: порядок колонок ВАЖЕН
- FROM/JOIN таблицы: порядок НЕ ВАЖЕН
- WHERE условия (через AND): порядок НЕ ВАЖЕН
- GROUP BY, HAVING, ORDER BY, LIMIT: сравниваются как нормализованные строки

Использование:
    python exact_set_match.py
    python exact_set_match.py --folder ./sqls --dialect postgres
    python exact_set_match.py --folder ./sqls --output results_esm.csv
    python exact_set_match.py --verbose
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import List, Optional, Set

import pandas as pd
import sqlglot
from sqlglot import exp, parse_one

# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------
DEFAULT_SQLS_DIR = Path(__file__).resolve().parent / "sqls"
DEFAULT_DIALECT = "postgres"
MODELS = ["giga", "qwen", "glm"]
MODEL_DISPLAY = {"giga": "Giga", "qwen": "Qwen", "glm": "GLM"}

# ---------------------------------------------------------------------------
# Логирование
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# AST-извлечение компонентов
# ---------------------------------------------------------------------------
def _norm(node: exp.Expression) -> str:
    """Нормализованное SQL-представление узла (lowercase)."""
    return node.sql(dialect="postgres").strip().lower()


def extract_select_columns(tree: exp.Select) -> List[str]:
    """Извлекает список выражений SELECT (порядок ВАЖЕН)."""
    return [_norm(e) for e in tree.expressions]


def extract_from_tables(tree: exp.Select) -> Set[str]:
    """Извлекает имена таблиц из FROM/JOIN (порядок НЕ ВАЖЕН).

    Учитывает схему: bookings.seats → seats (для сравнения без схемы).
    """
    tables: Set[str] = set()
    for t in tree.find_all(exp.Table):
        # Берём только имя таблицы без схемы для толерантности
        name = t.name.lower()
        if name:
            tables.add(name)
    return tables


def _collect_and_conditions(node: exp.Expression) -> Set[str]:
    """Рекурсивно разбирает AND-цепочку на отдельные условия."""
    conditions: Set[str] = set()
    if isinstance(node, exp.And):
        conditions |= _collect_and_conditions(node.left)
        conditions |= _collect_and_conditions(node.right)
    else:
        conditions.add(_norm(node))
    return conditions


def extract_where_conditions(tree: exp.Select) -> Set[str]:
    """Извлекает условия WHERE как множество (порядок AND НЕ ВАЖЕН)."""
    where = tree.args.get("where")
    if not where:
        return set()
    return _collect_and_conditions(where.this)


def extract_group_by(tree: exp.Select) -> Set[str]:
    """Извлекает выражения GROUP BY как множество."""
    group = tree.args.get("group")
    if not group:
        return set()
    return {_norm(e) for e in group.expressions}


def extract_having(tree: exp.Select) -> Set[str]:
    """Извлекает условия HAVING (AND-порядок НЕ ВАЖЕН)."""
    having = tree.args.get("having")
    if not having:
        return set()
    return _collect_and_conditions(having.this)


def extract_order_by(tree: exp.Select) -> List[str]:
    """Извлекает ORDER BY (порядок ВАЖЕН)."""
    order = tree.args.get("order")
    if not order:
        return []
    return [_norm(e) for e in order.expressions]


def extract_limit(tree: exp.Select) -> Optional[str]:
    """Извлекает LIMIT как строку."""
    limit = tree.args.get("limit")
    if not limit:
        return None
    return _norm(limit)


def extract_joins(tree: exp.Select) -> Set[str]:
    """Извлекает JOIN-клаузы как множество нормализованных строк."""
    joins: Set[str] = set()
    for join in tree.find_all(exp.Join):
        joins.add(_norm(join))
    return joins


def extract_ctes(tree: exp.Expression) -> Set[str]:
    """Извлекает CTE (WITH) блоки как множество."""
    ctes: Set[str] = set()
    for cte in tree.find_all(exp.CTE):
        ctes.add(_norm(cte))
    return ctes


# ---------------------------------------------------------------------------
# Ядро: структурное сравнение
# ---------------------------------------------------------------------------
def check_structural_match(
    sql_gold: str,
    sql_pred: str,
    dialect: str = DEFAULT_DIALECT,
) -> int:
    """ESM: структурное сравнение двух SQL через AST.

    Сравнивает:
      1. SELECT колонки (порядок важен)
      2. FROM таблицы (порядок не важен)
      3. JOIN клаузы (порядок не важен)
      4. WHERE условия (AND-порядок не важен)
      5. GROUP BY (порядок не важен)
      6. HAVING (AND-порядок не важен)
      7. ORDER BY (порядок важен)
      8. LIMIT
      9. CTE (WITH)

    Returns:
        1 — структурное совпадение, 0 — расхождение или ошибка парсинга.
    """
    try:
        ast_gold = parse_one(sql_gold, read=dialect, error_level=sqlglot.ErrorLevel.RAISE)
        ast_pred = parse_one(sql_pred, read=dialect, error_level=sqlglot.ErrorLevel.RAISE)
    except sqlglot.errors.ParseError as exc:
        log.debug("Ошибка парсинга: %s", exc)
        return 0
    except Exception as exc:
        log.debug("Неожиданная ошибка парсинга: %s", exc)
        return 0

    # Оба должны быть SELECT (или содержать SELECT внутри CTE)
    gold_select = ast_gold.find(exp.Select)
    pred_select = ast_pred.find(exp.Select)

    if gold_select is None or pred_select is None:
        log.debug("Один из запросов не содержит SELECT")
        return 0

    # 1. SELECT колонки (порядок важен)
    gold_cols = extract_select_columns(gold_select)
    pred_cols = extract_select_columns(pred_select)
    if gold_cols != pred_cols:
        log.debug("SELECT не совпал: %s vs %s", gold_cols, pred_cols)
        return 0

    # 2. FROM таблицы
    gold_tables = extract_from_tables(gold_select)
    pred_tables = extract_from_tables(pred_select)
    if gold_tables != pred_tables:
        log.debug("FROM таблицы не совпали: %s vs %s", gold_tables, pred_tables)
        return 0

    # 3. JOIN
    gold_joins = extract_joins(gold_select)
    pred_joins = extract_joins(pred_select)
    if gold_joins != pred_joins:
        log.debug("JOIN не совпали: %s vs %s", gold_joins, pred_joins)
        return 0

    # 4. WHERE
    gold_where = extract_where_conditions(gold_select)
    pred_where = extract_where_conditions(pred_select)
    if gold_where != pred_where:
        log.debug("WHERE не совпали: %s vs %s", gold_where, pred_where)
        return 0

    # 5. GROUP BY
    gold_group = extract_group_by(gold_select)
    pred_group = extract_group_by(pred_select)
    if gold_group != pred_group:
        log.debug("GROUP BY не совпали: %s vs %s", gold_group, pred_group)
        return 0

    # 6. HAVING
    gold_having = extract_having(gold_select)
    pred_having = extract_having(pred_select)
    if gold_having != pred_having:
        log.debug("HAVING не совпали: %s vs %s", gold_having, pred_having)
        return 0

    # 7. ORDER BY (порядок важен)
    gold_order = extract_order_by(gold_select)
    pred_order = extract_order_by(pred_select)
    if gold_order != pred_order:
        log.debug("ORDER BY не совпали: %s vs %s", gold_order, pred_order)
        return 0

    # 8. LIMIT
    gold_limit = extract_limit(gold_select)
    pred_limit = extract_limit(pred_select)
    if gold_limit != pred_limit:
        log.debug("LIMIT не совпали: %s vs %s", gold_limit, pred_limit)
        return 0

    # 9. CTE
    gold_ctes = extract_ctes(ast_gold)
    pred_ctes = extract_ctes(ast_pred)
    if gold_ctes != pred_ctes:
        log.debug("CTE не совпали: %s vs %s", gold_ctes, pred_ctes)
        return 0

    return 1


# ---------------------------------------------------------------------------
# Работа с файлами
# ---------------------------------------------------------------------------
def discover_query_numbers(sqls_dir: Path) -> list[int]:
    """Возвращает отсортированный список уникальных номеров запросов."""
    pattern = re.compile(r"^(\d+)_\w+\.sql$")
    numbers: set[int] = set()
    for f in sqls_dir.iterdir():
        if f.is_file():
            m = pattern.match(f.name)
            if m:
                numbers.add(int(m.group(1)))
    return sorted(numbers)


def read_sql_file(path: Path) -> Optional[str]:
    """Читает SQL из файла. Возвращает None если файл не существует или пуст.

    Файлы-заглушки (содержат только комментарий с ❌) вернут None.
    """
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8").strip()
    except Exception as exc:
        log.warning("Ошибка чтения %s: %s", path.name, exc)
        return None

    if not text:
        return None

    # Убираем однострочные комментарии для проверки «пустоты»
    non_comment = [
        line for line in text.splitlines()
        if line.strip() and not line.strip().startswith("--")
    ]
    if not non_comment:
        return None

    # Возвращаем текст без комментариев для чистого парсинга
    return "\n".join(non_comment).strip()


# ---------------------------------------------------------------------------
# Основной pipeline
# ---------------------------------------------------------------------------
def run(
    sqls_dir: Path,
    dialect: str,
    output: Optional[str],
) -> pd.DataFrame:
    """Запускает полный цикл оценки ESM."""
    numbers = discover_query_numbers(sqls_dir)
    if not numbers:
        log.error("В директории %s не найдено SQL-файлов", sqls_dir)
        sys.exit(1)

    log.info("Найдено %d уникальных запросов: %s", len(numbers), numbers)
    log.info("Диалект SQL: %s", dialect)

    results: list[dict] = []

    for num in numbers:
        row: dict[str, object] = {"Номер": num}

        # --- Эталон ---
        base_path = sqls_dir / f"{num}_base.sql"
        base_sql = read_sql_file(base_path)
        if base_sql is None:
            log.warning("Нет эталонного файла %s — пропуск", base_path.name)
            for model in MODELS:
                row[MODEL_DISPLAY[model]] = 0
            results.append(row)
            continue

        log.info("─" * 50)
        log.info("Запрос №%d", num)

        for model in MODELS:
            model_path = sqls_dir / f"{num}_{model}.sql"
            model_sql = read_sql_file(model_path)

            if model_sql is None:
                log.info("  %s: файл отсутствует/пуст → ESM=0", MODEL_DISPLAY[model])
                row[MODEL_DISPLAY[model]] = 0
                continue

            esm = check_structural_match(base_sql, model_sql, dialect)
            if esm == 0:
                log.info("  %s: ESM=0", MODEL_DISPLAY[model])
            else:
                log.info("  %s: ESM=1 ✓", MODEL_DISPLAY[model])

            row[MODEL_DISPLAY[model]] = esm

        results.append(row)

    # --- Итоговая таблица ---
    df = pd.DataFrame(results)
    df = df[["Номер", "Giga", "Qwen", "GLM"]]

    total = len(df)
    giga_sum = int(df["Giga"].sum())
    qwen_sum = int(df["Qwen"].sum())
    glm_sum = int(df["GLM"].sum())

    summary_row = {
        "Номер": "Итого %",
        "Giga": f"{giga_sum / total * 100:.1f}%",
        "Qwen": f"{qwen_sum / total * 100:.1f}%",
        "GLM": f"{glm_sum / total * 100:.1f}%",
    }
    df_display = pd.concat(
        [df, pd.DataFrame([summary_row])],
        ignore_index=True,
    )

    # --- Вывод ---
    print("\n" + "=" * 58)
    print("       EXACT SET MATCH ACCURACY — РЕЗУЛЬТАТЫ")
    print("=" * 58)
    print(df_display.to_string(index=False))
    print("=" * 58)
    print(f"  Giga : {giga_sum / total * 100:5.1f}%  ({giga_sum}/{total})")
    print(f"  Qwen : {qwen_sum / total * 100:5.1f}%  ({qwen_sum}/{total})")
    print(f"  GLM  : {glm_sum / total * 100:5.1f}%  ({glm_sum}/{total})")
    print("=" * 58)

    # --- Сохранение ---
    if output:
        out_path = Path(output)
        if out_path.suffix in (".xlsx", ".xls"):
            df_display.to_excel(out_path, index=False)
        else:
            df_display.to_csv(out_path, index=False)
        log.info("Результаты сохранены в %s", out_path)

    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Расчёт Exact Set Match Accuracy для SQL-запросов LLM",
    )
    parser.add_argument(
        "--folder",
        type=Path,
        default=DEFAULT_SQLS_DIR,
        help=f"Путь к директории с SQL-файлами (default: {DEFAULT_SQLS_DIR})",
    )
    parser.add_argument(
        "--dialect",
        type=str,
        default=DEFAULT_DIALECT,
        help=f"Диалект SQL для sqlglot (default: {DEFAULT_DIALECT})",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Путь для сохранения результатов (csv/xlsx)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Подробное логирование (DEBUG)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    run(sqls_dir=args.folder, dialect=args.dialect, output=args.output)
