"""
Собирает результаты из CSV-файлов в папке results/ в единый Markdown-файл.

Ожидаемые файлы в results/:
  - results_ea.csv   → Execution Accuracy
  - results_em.csv   → Exact Matching Accuracy
  - results_esm.csv  → Exact Set Match
  - results_iea.csv  → Intelligent Execution Accuracy

Использование:
    python compact_all.py
    python compact_all.py --results-dir ./results --output all_out.md
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------
DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "all_out.md"

METRIC_FILES = {
    "EA": "results_ea.csv",
    "EM": "results_em.csv",
    "ESM": "results_esm.csv",
    "IEA": "results_iea.csv",
}

METRIC_HEADERS = {
    "EA": "Execution Accuracy (точность выполнения)",
    "EM": "Exact Matching Accuracy (текст SQL)",
    "ESM": "ESM — Exact Set Match (сравнение синтаксиса)",
    "IEA": "Intellect",
}

MODELS = ["Qwen", "GLM", "GigaChat"]
MODEL_CSV_MAP = {"Qwen": "Qwen", "GLM": "GLM", "GigaChat": "Giga"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Загрузка CSV
# ---------------------------------------------------------------------------
def load_metric(results_dir: Path, filename: str) -> Optional[pd.DataFrame]:
    """Загружает CSV с результатами метрики, возвращает None если не найден."""
    path = results_dir / filename
    if not path.exists():
        log.warning("Файл не найден: %s", path)
        return None
    try:
        df = pd.read_csv(path)
        # Убираем строку "Итого %"
        df = df[df["Номер"].apply(lambda x: str(x).isdigit())].copy()
        df["Номер"] = df["Номер"].astype(int)
        return df
    except Exception as exc:
        log.warning("Ошибка чтения %s: %s", path, exc)
        return None


def get_value(df: Optional[pd.DataFrame], num: int, col: str) -> str:
    """Извлекает значение метрики для запроса num и колонки col."""
    if df is None:
        return ""
    row = df[df["Номер"] == num]
    if row.empty:
        return ""
    val = row.iloc[0].get(col, "")
    if pd.isna(val):
        return ""
    return str(int(float(val))) if str(val).replace(".", "").replace("-", "").isdigit() else str(val)


# ---------------------------------------------------------------------------
# Генерация Markdown
# ---------------------------------------------------------------------------
def generate_md(results_dir: Path, output: Path) -> None:
    """Генерирует all_out.md из CSV-файлов."""
    # Загружаем все метрики
    metrics: dict[str, Optional[pd.DataFrame]] = {}
    for key, filename in METRIC_FILES.items():
        metrics[key] = load_metric(results_dir, filename)
        if metrics[key] is not None:
            log.info("Загружено: %s (%d строк)", filename, len(metrics[key]))

    # Определяем все номера запросов
    all_numbers: set[int] = set()
    for df in metrics.values():
        if df is not None:
            all_numbers.update(df["Номер"].tolist())

    if not all_numbers:
        log.error("Нет данных ни в одном CSV")
        sys.exit(1)

    numbers = sorted(all_numbers)
    log.info("Всего запросов: %d", len(numbers))

    # Генерируем MD
    lines: list[str] = []
    lines.append("# Сводные результаты метрик\n")

    for num in numbers:
        lines.append(f"## №{num}\n")

        # Заголовок таблицы
        header_cols = ["Модель"] + [METRIC_HEADERS[k] for k in METRIC_FILES]
        sep_cols = ["--------"] + ["-" * len(h) for h in header_cols[1:]]

        lines.append("| " + " | ".join(header_cols) + " |")
        lines.append("| " + " | ".join(sep_cols) + " |")

        for model in MODELS:
            csv_col = MODEL_CSV_MAP[model]
            vals = [model]
            for key in METRIC_FILES:
                vals.append(get_value(metrics[key], num, csv_col))
            lines.append("| " + " | ".join(vals) + " |")

        lines.append("")  # пустая строка после таблицы

    # Сводная таблица
    lines.append("---\n")
    lines.append("## Сводная таблица\n")
    lines.append("| Метрика | Qwen | GLM | GigaChat |")
    lines.append("| ------- | ---- | --- | -------- |")

    total = len(numbers)
    for key in METRIC_FILES:
        df = metrics[key]
        if df is None:
            lines.append(f"| {METRIC_HEADERS[key]} | — | — | — |")
            continue
        vals = []
        for model in MODELS:
            csv_col = MODEL_CSV_MAP[model]
            col_data = df.get(csv_col)
            if col_data is not None:
                s = pd.to_numeric(col_data, errors="coerce").sum()
                pct = s / total * 100
                vals.append(f"{pct:.1f}% ({int(s)}/{total})")
            else:
                vals.append("—")
        lines.append(f"| {METRIC_HEADERS[key]} | {' | '.join(vals)} |")

    lines.append("")

    # Запись
    output.write_text("\n".join(lines), encoding="utf-8")
    log.info("Результат записан в %s", output)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Сборка результатов метрик в единый Markdown",
    )
    p.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help=f"Папка с CSV-результатами (default: {DEFAULT_RESULTS_DIR})",
    )
    p.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Выходной MD-файл (default: {DEFAULT_OUTPUT})",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_md(results_dir=args.results_dir, output=args.output)
