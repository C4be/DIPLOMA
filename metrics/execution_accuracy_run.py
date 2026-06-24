"""
Execution Accuracy (EA) — скрипт оценки качества SQL-генерации LLM.

Сканирует директорию sqls/, выполняет эталонные и модельные SQL-запросы
через HTTP API, сравнивает результаты и формирует итоговую таблицу.

Использование:
    python execution_accuracy_run.py
    python execution_accuracy_run.py --sqls-dir ./sqls --api-url http://localhost:8899/query
    python execution_accuracy_run.py --output results_ea.csv
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from io import StringIO
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Константы по умолчанию
# ---------------------------------------------------------------------------
DEFAULT_SQLS_DIR = Path(__file__).resolve().parent / "sqls"
DEFAULT_API_URL = "http://localhost:8899/query"
DEFAULT_TIMEOUT = 30  # секунд
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
# Ядро: сравнение результатов
# ---------------------------------------------------------------------------
def check_execution_accuracy(df_gold: pd.DataFrame, df_pred: pd.DataFrame) -> int:
    """Сравнивает результаты эталонного и предсказанного SQL-запросов.

    Возвращает 1 при полном совпадении (с точностью до порядка строк),
    0 — при любом расхождении.
    """
    # Пустые DataFrame обоих — совпадение
    if df_gold.empty and df_pred.empty:
        return 1

    # Сравнение набора и порядка колонок
    if list(df_gold.columns) != list(df_pred.columns):
        log.debug(
            "Колонки не совпадают: gold=%s, pred=%s",
            list(df_gold.columns),
            list(df_pred.columns),
        )
        return 0

    # Сравнение количества строк
    if df_gold.shape[0] != df_pred.shape[0]:
        log.debug(
            "Количество строк: gold=%d, pred=%d",
            df_gold.shape[0],
            df_pred.shape[0],
        )
        return 0

    if df_gold.shape[0] == 0:
        return 1

    try:
        cols = list(df_gold.columns)
        df_gold_sorted = (
            df_gold.sort_values(by=cols, na_position="last")
            .reset_index(drop=True)
        )
        df_pred_sorted = (
            df_pred.sort_values(by=cols, na_position="last")
            .reset_index(drop=True)
        )
    except TypeError:
        log.debug("Невозможно отсортировать — несравнимые типы")
        return 0

    # Приведение типов: попытка привести к числовым для корректного сравнения
    for col in cols:
        try:
            g_num = pd.to_numeric(df_gold_sorted[col], errors="coerce")
            p_num = pd.to_numeric(df_pred_sorted[col], errors="coerce")
            # Если удалось привести без потери данных — используем числовое представление
            if g_num.notna().sum() == df_gold_sorted[col].notna().sum():
                df_gold_sorted[col] = g_num
            if p_num.notna().sum() == df_pred_sorted[col].notna().sum():
                df_pred_sorted[col] = p_num
        except Exception:
            pass

    return 1 if df_gold_sorted.equals(df_pred_sorted) else 0


# ---------------------------------------------------------------------------
# HTTP-клиент
# ---------------------------------------------------------------------------
def execute_sql(
    session: requests.Session,
    api_url: str,
    sql: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> pd.DataFrame:
    """Выполняет SQL через HTTP API и возвращает DataFrame с результатом.

    При любой ошибке возвращает пустой DataFrame.
    """
    try:
        resp = session.post(
            api_url,
            json={"sql": sql},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        log.warning("Таймаут (%ds) при выполнении запроса", timeout)
        return pd.DataFrame()
    except requests.exceptions.ConnectionError as exc:
        log.warning("Ошибка соединения: %s", exc)
        return pd.DataFrame()
    except requests.exceptions.RequestException as exc:
        log.warning("HTTP ошибка: %s", exc)
        return pd.DataFrame()
    except ValueError:
        log.warning("Невалидный JSON в ответе")
        return pd.DataFrame()

    # Проверка поля error
    if data.get("error"):
        log.warning("API вернул ошибку: %s", data["error"])
        return pd.DataFrame()

    # Парсинг CSV
    csv_text: Optional[str] = data.get("results_csv")
    if csv_text:
        try:
            return pd.read_csv(StringIO(csv_text))
        except Exception as exc:
            log.warning("Не удалось распарсить results_csv: %s", exc)
            return pd.DataFrame()

    # Fallback — results_json
    json_data = data.get("results_json")
    if json_data is not None:
        try:
            return pd.DataFrame(json_data)
        except Exception as exc:
            log.warning("Не удалось распарсить results_json: %s", exc)
            return pd.DataFrame()

    log.warning("В ответе нет ни results_csv, ни results_json")
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Сканирование директории
# ---------------------------------------------------------------------------
def discover_query_numbers(sqls_dir: Path) -> list[int]:
    """Возвращает отсортированный список уникальных номеров запросов."""
    pattern = re.compile(r"^(\d+)_\w+\.sql$")
    numbers: set[int] = set()
    for f in sqls_dir.iterdir():
        m = pattern.match(f.name)
        if m:
            numbers.add(int(m.group(1)))
    return sorted(numbers)


def read_sql_file(path: Path) -> Optional[str]:
    """Читает SQL из файла, возвращает None если файл не существует."""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    # Убираем строки-комментарии с ❌ (файлы-заглушки для неудачных попыток)
    lines = text.splitlines()
    non_comment_lines = [
        line for line in lines if not line.strip().startswith("--")
    ]
    sql_body = "\n".join(non_comment_lines).strip()
    return sql_body if sql_body else None


# ---------------------------------------------------------------------------
# Основной pipeline
# ---------------------------------------------------------------------------
def run(
    sqls_dir: Path,
    api_url: str,
    timeout: int,
    output: Optional[str],
) -> pd.DataFrame:
    """Запускает полный цикл оценки EA."""
    numbers = discover_query_numbers(sqls_dir)
    if not numbers:
        log.error("В директории %s не найдено SQL-файлов", sqls_dir)
        sys.exit(1)

    log.info(
        "Найдено %d уникальных запросов: %s",
        len(numbers),
        numbers,
    )

    session = requests.Session()
    results: list[dict] = []

    for num in numbers:
        row: dict = {"Номер": num}

        # --- Эталон ---
        base_path = sqls_dir / f"{num}_base.sql"
        base_sql = read_sql_file(base_path)
        if base_sql is None:
            log.warning("Нет эталонного файла %s — пропуск", base_path.name)
            for model in MODELS:
                row[MODEL_DISPLAY[model]] = 0
            results.append(row)
            continue

        log.info("═" * 60)
        log.info("Запрос №%d — выполняю эталон…", num)
        df_gold = execute_sql(session, api_url, base_sql, timeout)
        if df_gold.empty:
            log.warning(
                "  Эталон вернул пустой результат — все модели получат EA=0"
            )
            # Особый случай: если эталон пуст, модель тоже должна вернуть
            # пустой результат для EA=1.  Но пустой из-за ошибки — ставим 0.

        for model in MODELS:
            model_path = sqls_dir / f"{num}_{model}.sql"
            model_sql = read_sql_file(model_path)

            if model_sql is None:
                log.info("  %s: файл отсутствует или пуст → EA=0", MODEL_DISPLAY[model])
                row[MODEL_DISPLAY[model]] = 0
                continue

            log.info("  %s: выполняю…", MODEL_DISPLAY[model])
            df_pred = execute_sql(session, api_url, model_sql, timeout)

            ea = check_execution_accuracy(df_gold, df_pred)
            log.info(
                "  %s: EA=%d  (gold %s, pred %s)",
                MODEL_DISPLAY[model],
                ea,
                df_gold.shape,
                df_pred.shape,
            )
            row[MODEL_DISPLAY[model]] = ea

        results.append(row)

    # --- Итоговая таблица ---
    df = pd.DataFrame(results)
    df = df[["Номер", "Giga", "Qwen", "GLM"]]

    total = len(df)
    summary_row = {
        "Номер": "Итого %",
        "Giga": f"{df['Giga'].sum() / total * 100:.1f}%",
        "Qwen": f"{df['Qwen'].sum() / total * 100:.1f}%",
        "GLM": f"{df['GLM'].sum() / total * 100:.1f}%",
    }
    df_display = pd.concat(
        [df, pd.DataFrame([summary_row])],
        ignore_index=True,
    )

    print("\n" + "=" * 60)
    print("         EXECUTION ACCURACY — РЕЗУЛЬТАТЫ")
    print("=" * 60)
    print(df_display.to_string(index=False))
    print("=" * 60)

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
        description="Расчёт Execution Accuracy для SQL-запросов LLM",
    )
    parser.add_argument(
        "--sqls-dir",
        type=Path,
        default=DEFAULT_SQLS_DIR,
        help=f"Путь к директории с SQL-файлами (default: {DEFAULT_SQLS_DIR})",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=DEFAULT_API_URL,
        help=f"URL эндпоинта для выполнения SQL (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Таймаут HTTP-запроса в секундах (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Путь для сохранения результатов (csv/xlsx). Если не указан — только stdout",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Включить подробное логирование (DEBUG)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    run(
        sqls_dir=args.sqls_dir,
        api_url=args.api_url,
        timeout=args.timeout,
        output=args.output,
    )
