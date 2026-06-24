"""
Intelligent Execution Accuracy (IEA) — «умная» оценка результатов SQL.

Отличия от базовой EA:
  • Толерантность к переименованию колонок (сравнение по данным)
  • Толерантность к перестановке колонок (сортировка + сопоставление)
  • Удаление лишних колонок модели, если они не нужны
  • Приведение типов: числа, строки, интервалы
  • Нечёткое сравнение числовых значений (rtol)

Использование:
    python execution_accuracy_intellect.py
    python execution_accuracy_intellect.py --sqls-dir ./sqls --api-url http://localhost:8899/query
    python execution_accuracy_intellect.py --output results_iea.csv --debug
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from io import StringIO
from itertools import permutations
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------
DEFAULT_SQLS_DIR = Path(__file__).resolve().parent / "sqls"
DEFAULT_API_URL = "http://localhost:8899/query"
DEFAULT_TIMEOUT = 30
NUMERIC_RTOL = 1e-5  # относительная погрешность для чисел
MODELS = ["giga", "qwen", "glm"]
MODEL_DISPLAY = {"giga": "Giga", "qwen": "Qwen", "glm": "GLM"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ===================================================================
# Утилиты нормализации
# ===================================================================

def _normalize_col_name(name: str) -> str:
    """lower, strip, replace spaces/hyphens → underscore."""
    return re.sub(r"[\s\-]+", "_", name.strip().lower())


def _try_numeric(series: pd.Series) -> pd.Series:
    """Попытка привести серию к float."""
    return pd.to_numeric(series, errors="coerce")


def _normalize_series(s: pd.Series) -> pd.Series:
    """Приводит серию к наиболее «сравнимому» виду."""
    # 1. Попытка → numeric
    num = _try_numeric(s)
    if num.notna().sum() >= s.notna().sum() * 0.9:
        return num
    # 2. Строковая нормализация (trim, lower)
    try:
        return s.astype(str).str.strip().str.lower()
    except Exception:
        return s


def _column_similarity(a: pd.Series, b: pd.Series) -> float:
    """Оценка схожести двух колонок (0..1) по совпадению значений."""
    if len(a) != len(b) or len(a) == 0:
        return 0.0

    na = _normalize_series(a.reset_index(drop=True))
    nb = _normalize_series(b.reset_index(drop=True))

    # Числовые — с погрешностью
    if pd.api.types.is_numeric_dtype(na) and pd.api.types.is_numeric_dtype(nb):
        both_nan = na.isna() & nb.isna()
        both_val = na.notna() & nb.notna()
        if both_val.sum() == 0:
            return 1.0 if both_nan.all() else 0.0
        close = np.isclose(
            na[both_val].values.astype(float),
            nb[both_val].values.astype(float),
            rtol=NUMERIC_RTOL,
            equal_nan=False,
        )
        match = close.sum() + both_nan.sum()
        return match / len(a)

    # Строковые — точное
    eq = na.astype(str) == nb.astype(str)
    return eq.sum() / len(a)


# ===================================================================
# Сопоставление колонок
# ===================================================================

def _match_columns(
    df_gold: pd.DataFrame,
    df_pred: pd.DataFrame,
) -> Optional[list[str]]:
    """Находит лучшее сопоставление колонок pred → gold.

    Возвращает список колонок pred в порядке gold, или None если
    сопоставление невозможно (не хватает колонок).
    """
    g_cols = list(df_gold.columns)
    p_cols = list(df_pred.columns)
    n = len(g_cols)

    if len(p_cols) < n:
        log.debug("У модели меньше колонок (%d) чем в эталоне (%d)", len(p_cols), n)
        return None

    # --- Фаза 1: точное / case-insensitive совпадение имён ---
    g_norm = [_normalize_col_name(c) for c in g_cols]
    p_norm = [_normalize_col_name(c) for c in p_cols]

    mapping: dict[int, int] = {}  # gold_idx → pred_idx
    used_pred: set[int] = set()

    for gi, gn in enumerate(g_norm):
        for pi, pn in enumerate(p_norm):
            if pi not in used_pred and gn == pn:
                mapping[gi] = pi
                used_pred.add(pi)
                break

    # --- Фаза 2: сопоставление оставшихся по данным ---
    unmatched_g = [i for i in range(n) if i not in mapping]
    unmatched_p = [i for i in range(len(p_cols)) if i not in used_pred]

    if unmatched_g:
        # Считаем матрицу схожести
        sim_matrix: dict[tuple[int, int], float] = {}
        for gi in unmatched_g:
            for pi in unmatched_p:
                sim_matrix[(gi, pi)] = _column_similarity(
                    df_gold.iloc[:, gi], df_pred.iloc[:, pi]
                )

        # Жадное сопоставление по убыванию схожести
        pairs = sorted(sim_matrix.items(), key=lambda x: -x[1])
        matched_g: set[int] = set()
        matched_p: set[int] = set()
        for (gi, pi), score in pairs:
            if gi in matched_g or pi in matched_p:
                continue
            if score >= 0.5:  # порог: хотя бы 50% значений совпадают
                mapping[gi] = pi
                matched_g.add(gi)
                matched_p.add(pi)
                log.debug(
                    "  Сопоставлено по данным: gold[%s] ↔ pred[%s] (sim=%.2f)",
                    g_cols[gi], p_cols[pi], score,
                )

    # --- Фаза 3: если n <= 6 и остались несопоставленные — перебор ---
    still_unmatched_g = [i for i in range(n) if i not in mapping]
    if still_unmatched_g:
        remaining_p = [i for i in range(len(p_cols)) if i not in {mapping[k] for k in mapping}]
        if len(still_unmatched_g) <= len(remaining_p) and len(still_unmatched_g) <= 4:
            best_score = -1.0
            best_perm: Optional[tuple] = None
            for perm in permutations(remaining_p, len(still_unmatched_g)):
                total = sum(
                    _column_similarity(df_gold.iloc[:, gi], df_pred.iloc[:, pi])
                    for gi, pi in zip(still_unmatched_g, perm)
                )
                if total > best_score:
                    best_score = total
                    best_perm = perm
            if best_perm and best_score / len(still_unmatched_g) >= 0.3:
                for gi, pi in zip(still_unmatched_g, best_perm):
                    mapping[gi] = pi
                    log.debug(
                        "  Перебором: gold[%s] ↔ pred[%s]",
                        g_cols[gi], p_cols[pi],
                    )

    if len(mapping) < n:
        log.debug("Не удалось сопоставить все колонки: %d/%d", len(mapping), n)
        return None

    return [p_cols[mapping[gi]] for gi in range(n)]


# ===================================================================
# Сравнение DataFrame
# ===================================================================

def _compare_dataframes(
    df_gold: pd.DataFrame,
    df_pred: pd.DataFrame,
) -> bool:
    """Сравнивает два DataFrame с нормализацией типов."""
    if df_gold.shape != df_pred.shape:
        return False
    if df_gold.shape[0] == 0:
        return True

    # Переименуем в col_0..col_n
    n = df_gold.shape[1]
    col_names = [f"col_{i}" for i in range(n)]
    g = df_gold.copy()
    p = df_pred.copy()
    g.columns = col_names
    p.columns = col_names

    # Нормализация каждого столбца
    for c in col_names:
        g[c] = _normalize_series(g[c])
        p[c] = _normalize_series(p[c])

    # Сортировка
    try:
        g = g.sort_values(by=col_names, na_position="last").reset_index(drop=True)
        p = p.sort_values(by=col_names, na_position="last").reset_index(drop=True)
    except TypeError:
        pass

    # Поэлементное сравнение
    for c in col_names:
        gs, ps = g[c], p[c]
        if pd.api.types.is_numeric_dtype(gs) and pd.api.types.is_numeric_dtype(ps):
            both_nan = gs.isna() & ps.isna()
            both_val = gs.notna() & ps.notna()
            mismatch_nan = gs.isna() != ps.isna()
            if mismatch_nan.any():
                return False
            if both_val.any():
                if not np.allclose(
                    gs[both_val].values.astype(float),
                    ps[both_val].values.astype(float),
                    rtol=NUMERIC_RTOL,
                    equal_nan=False,
                ):
                    return False
        else:
            if not gs.astype(str).equals(ps.astype(str)):
                return False
    return True


def check_execution_accuracy_smart(
    df_gold: pd.DataFrame,
    df_pred: pd.DataFrame,
) -> int:
    """Интеллектуальная EA с сопоставлением колонок.

    1. Если колонки совпадают — прямое сравнение
    2. Иначе — сопоставление по имени + данным
    3. Лишние колонки модели удаляются
    4. Сравнение с нормализацией типов
    """
    if df_gold.empty and df_pred.empty:
        return 1
    if df_gold.empty or df_pred.empty:
        return 0
    if df_gold.shape[0] != df_pred.shape[0]:
        log.debug("Строки: gold=%d, pred=%d", df_gold.shape[0], df_pred.shape[0])
        return 0

    # Быстрый путь: колонки совпадают
    if list(df_gold.columns) == list(df_pred.columns):
        return 1 if _compare_dataframes(df_gold, df_pred) else 0

    # Сопоставление
    matched_cols = _match_columns(df_gold, df_pred)
    if matched_cols is None:
        return 0

    df_pred_aligned = df_pred[matched_cols].copy()
    df_pred_aligned.columns = df_gold.columns

    return 1 if _compare_dataframes(df_gold, df_pred_aligned) else 0


# ===================================================================
# HTTP-клиент (переиспользуется из execution_accuracy_run)
# ===================================================================

def execute_sql(
    session: requests.Session,
    api_url: str,
    sql: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> pd.DataFrame:
    """Выполняет SQL через HTTP API и возвращает DataFrame."""
    try:
        resp = session.post(api_url, json={"sql": sql}, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        log.warning("Таймаут (%ds)", timeout)
        return pd.DataFrame()
    except requests.exceptions.ConnectionError as exc:
        log.warning("Ошибка соединения: %s", exc)
        return pd.DataFrame()
    except requests.exceptions.RequestException as exc:
        log.warning("HTTP ошибка: %s", exc)
        return pd.DataFrame()
    except ValueError:
        log.warning("Невалидный JSON")
        return pd.DataFrame()

    if data.get("error"):
        log.warning("API ошибка: %s", data["error"])
        return pd.DataFrame()

    csv_text: Optional[str] = data.get("results_csv")
    if csv_text:
        try:
            return pd.read_csv(StringIO(csv_text))
        except Exception as exc:
            log.warning("Парсинг CSV: %s", exc)
            return pd.DataFrame()

    json_data = data.get("results_json")
    if json_data is not None:
        try:
            return pd.DataFrame(json_data)
        except Exception as exc:
            log.warning("Парсинг JSON: %s", exc)
            return pd.DataFrame()

    log.warning("Нет results_csv/results_json")
    return pd.DataFrame()


# ===================================================================
# Файлы
# ===================================================================

def discover_query_numbers(sqls_dir: Path) -> list[int]:
    pattern = re.compile(r"^(\d+)_\w+\.sql$")
    numbers: set[int] = set()
    for f in sqls_dir.iterdir():
        if f.is_file():
            m = pattern.match(f.name)
            if m:
                numbers.add(int(m.group(1)))
    return sorted(numbers)


def read_sql_file(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8").strip()
    except Exception:
        return None
    lines = [l for l in text.splitlines() if not l.strip().startswith("--")]
    sql_body = "\n".join(lines).strip()
    return sql_body if sql_body else None


# ===================================================================
# Pipeline
# ===================================================================

def run(
    sqls_dir: Path,
    api_url: str,
    timeout: int,
    output: Optional[str],
) -> pd.DataFrame:
    numbers = discover_query_numbers(sqls_dir)
    if not numbers:
        log.error("Нет SQL-файлов в %s", sqls_dir)
        sys.exit(1)

    log.info("Запросов: %d — %s", len(numbers), numbers)
    session = requests.Session()
    results: list[dict] = []

    for num in numbers:
        row: dict = {"Номер": num}

        base_sql = read_sql_file(sqls_dir / f"{num}_base.sql")
        if base_sql is None:
            log.warning("Нет эталона %d_base.sql", num)
            for m in MODELS:
                row[MODEL_DISPLAY[m]] = 0
            results.append(row)
            continue

        log.info("═" * 60)
        log.info("Запрос №%d — эталон…", num)
        df_gold = execute_sql(session, api_url, base_sql, timeout)

        for model in MODELS:
            model_sql = read_sql_file(sqls_dir / f"{num}_{model}.sql")
            if model_sql is None:
                log.info("  %s: нет файла → IEA=0", MODEL_DISPLAY[model])
                row[MODEL_DISPLAY[model]] = 0
                continue

            log.info("  %s: выполняю…", MODEL_DISPLAY[model])
            df_pred = execute_sql(session, api_url, model_sql, timeout)
            iea = check_execution_accuracy_smart(df_gold, df_pred)
            log.info(
                "  %s: IEA=%d  (gold %s, pred %s)",
                MODEL_DISPLAY[model], iea, df_gold.shape, df_pred.shape,
            )
            row[MODEL_DISPLAY[model]] = iea

        results.append(row)

    df = pd.DataFrame(results)[["Номер", "Giga", "Qwen", "GLM"]]
    total = len(df)
    sums = {m: int(df[m].sum()) for m in ["Giga", "Qwen", "GLM"]}

    summary = {"Номер": "Итого %"}
    for m, s in sums.items():
        summary[m] = f"{s / total * 100:.1f}%"

    df_display = pd.concat([df, pd.DataFrame([summary])], ignore_index=True)

    print("\n" + "=" * 62)
    print("    INTELLIGENT EXECUTION ACCURACY — РЕЗУЛЬТАТЫ")
    print("=" * 62)
    print(df_display.to_string(index=False))
    print("=" * 62)
    for m, s in sums.items():
        print(f"  {m:5s}: {s / total * 100:5.1f}%  ({s}/{total})")
    print("=" * 62)

    if output:
        out_path = Path(output)
        if out_path.suffix in (".xlsx", ".xls"):
            df_display.to_excel(out_path, index=False)
        else:
            df_display.to_csv(out_path, index=False)
        log.info("Сохранено: %s", out_path)

    return df


# ===================================================================
# CLI
# ===================================================================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Intelligent Execution Accuracy для SQL-запросов LLM",
    )
    p.add_argument("--sqls-dir", type=Path, default=DEFAULT_SQLS_DIR)
    p.add_argument("--api-url", type=str, default=DEFAULT_API_URL)
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    p.add_argument("--output", "-o", type=str, default=None)
    p.add_argument("--debug", action="store_true")
    return p.parse_args()


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
