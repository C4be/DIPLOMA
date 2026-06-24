"""
Exact Match Accuracy (EM) — текстовое сравнение SQL-запросов LLM с эталоном.

Сканирует директорию с SQL-файлами, нормализует тексты запросов
и выполняет посимвольное сравнение. БД не требуется.

Использование:
    python exact_matching_accuracy.py
    python exact_matching_accuracy.py --folder ./sqls
    python exact_matching_accuracy.py --folder ./sqls --output results_em.csv
    python exact_matching_accuracy.py --verbose
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------
DEFAULT_SQLS_DIR = Path(__file__).resolve().parent / "sqls"
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
# Нормализация и сравнение
# ---------------------------------------------------------------------------
def normalize_sql(text: str) -> str:
    """Нормализация SQL-текста для Exact Match.

    - Удаление однострочных комментариев (-- ...)
    - Приведение к нижнему регистру
    - Схлопывание пробелов / табов / переносов строк
    - Удаление завершающей точки с запятой
    """
    if not text:
        return ""

    # Убираем однострочные комментарии
    text = re.sub(r"--[^\n]*", "", text)

    # Нижний регистр
    text = text.lower()

    # Схлопываем любые пробельные символы в один пробел
    text = " ".join(text.split())

    # Убираем завершающий ;
    text = text.rstrip(";").strip()

    return text


def check_exact_match(sql_gold: str, sql_pred: str) -> int:
    """Exact Match: посимвольное сравнение нормализованных строк.

    Returns:
        1 — полное совпадение, 0 — расхождение.
    """
    return 1 if normalize_sql(sql_gold) == normalize_sql(sql_pred) else 0


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

    # Проверяем, не является ли файл заглушкой (только комментарии)
    non_comment = [
        line for line in text.splitlines()
        if line.strip() and not line.strip().startswith("--")
    ]
    if not non_comment:
        return None

    return text


# ---------------------------------------------------------------------------
# Основной pipeline
# ---------------------------------------------------------------------------
def run(
    sqls_dir: Path,
    output: Optional[str],
) -> pd.DataFrame:
    """Запускает полный цикл оценки Exact Match."""
    numbers = discover_query_numbers(sqls_dir)
    if not numbers:
        log.error("В директории %s не найдено SQL-файлов", sqls_dir)
        sys.exit(1)

    log.info("Найдено %d уникальных запросов: %s", len(numbers), numbers)

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

        base_norm = normalize_sql(base_sql)
        log.info("─" * 50)
        log.info("Запрос №%d", num)
        log.debug("  Эталон (норм): %s", base_norm[:120])

        for model in MODELS:
            model_path = sqls_dir / f"{num}_{model}.sql"
            model_sql = read_sql_file(model_path)

            if model_sql is None:
                log.info("  %s: файл отсутствует/пуст → EM=0", MODEL_DISPLAY[model])
                row[MODEL_DISPLAY[model]] = 0
                continue

            em = check_exact_match(base_sql, model_sql)
            if em == 0:
                pred_norm = normalize_sql(model_sql)
                log.info("  %s: EM=0", MODEL_DISPLAY[model])
                log.debug("    gold: %s", base_norm[:100])
                log.debug("    pred: %s", pred_norm[:100])
            else:
                log.info("  %s: EM=1 ✓", MODEL_DISPLAY[model])

            row[MODEL_DISPLAY[model]] = em

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
    print("\n" + "=" * 55)
    print("       EXACT MATCH ACCURACY — РЕЗУЛЬТАТЫ")
    print("=" * 55)
    print(df_display.to_string(index=False))
    print("=" * 55)
    print(f"  Giga : {giga_sum / total * 100:5.1f}%  ({giga_sum}/{total})")
    print(f"  Qwen : {qwen_sum / total * 100:5.1f}%  ({qwen_sum}/{total})")
    print(f"  GLM  : {glm_sum / total * 100:5.1f}%  ({glm_sum}/{total})")
    print("=" * 55)

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
        description="Расчёт Exact Match Accuracy для SQL-запросов LLM",
    )
    parser.add_argument(
        "--folder",
        type=Path,
        default=DEFAULT_SQLS_DIR,
        help=f"Путь к директории с SQL-файлами (default: {DEFAULT_SQLS_DIR})",
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
    run(sqls_dir=args.folder, output=args.output)
