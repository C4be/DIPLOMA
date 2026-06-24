import re
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import Literal

from utils import extract_sql, call_api
from functions import rag_search
from settings import agent_settings
from .states import State
from .prompts import (
    REWRITE_PROMPT, GENERATE_SQL_PROMPT, EXECUTION_CRITIQUE_TEMPLATE,
    REWRITE_SQL_PROMPT, ANSWER_INSTRUCTION
)
from .llm_provider import llm
from logger import Logger


__logger = Logger('agent')


async def rewrite_rag_query(state: State):
    """Вершина переписывает запрос пользователя под RAG контекст"""
    user_question = state["user_question"].content
    __logger.debug(f"Исходный запрос для RAG: '{user_question}'")
    try:
        response = await llm.ainvoke([REWRITE_PROMPT, HumanMessage(content=user_question)])
        content = response.content.strip()
        __logger.info(f"LLM переписала запрос под RAG: {content}")
        return {"rag_query": f'{content}'}
    except Exception as e:
        __logger.error(f"Ошибка при переписывании запроса под RAG систему: {e}")
        return {"rag_query": user_question.strip()}


async def call_rag(state: State):
    """Вершина вызывает RAG систему и передает запрос"""
    __logger.info(f"Вызов RAG с запросом: '{state['rag_query']}'")
    context = await rag_search.ainvoke(state["rag_query"])
    __logger.info(f"RAG контекст получен ({len(context)} символов)")
    return {
        "rag_context": context,
        "messages": [AIMessage(content=f"[RAG контекст получен ({len(context)} символов)]")]
    }


async def generate_initial_sql(state: State):
    """Вершина генерирует профессиональный SQL код"""
    __logger.info(f"Генерация SQL (попытка №{state['attempts'] + 1})")
    prompt = [
        GENERATE_SQL_PROMPT,
        HumanMessage(content=f"Вопрос: {state['rag_query']}\n\nКонтекст:\n{state['rag_context']}")
    ]
    response = await llm.ainvoke(prompt)

    sql = extract_sql(response.content)
    __logger.info(f"Сгенерирован SQL (попытка №{state['attempts']}):\n{sql}")

    return {
        "sql_query": sql,
        "messages": [AIMessage(content=f"{state['attempts']}-ая версия SQL запроса:\n```sql\n{sql}\n```")],
        "sqls": [sql]
    }


async def execute_sql(state: State):
    """Вершина исполняет SQL запрос на сервере"""
    sql = state['sql_query']
    __logger.info(f"Выполнение SQL запроса:\n{sql}")

    data = await call_api(
        url=agent_settings.db_query_url,
        payload={"sql": sql}
    )

    if isinstance(data, str):
        __logger.error(f"Ошибка при выполнении SQL запроса: {data}")
        return {
            'sql_result': {
                "success": False,
                "rows": 0,
                "query": sql,
                "data": [],
                "csv_text": "",
                "error": data,
            }
        }

    rows_val = data.get('rows', 0)
    success = int(rows_val) > 0 if rows_val is not None else False

    if success:
        __logger.info(f"SQL выполнен успешно, получено строк: {rows_val}")
    else:
        __logger.warning(f"SQL выполнен, но вернул 0 строк. Ошибка: {data.get('error', '—')}")

    return {
        'sql_result': {
            "success": success,
            "rows": int(rows_val) if success else 0,
            "query": data.get('query', sql),
            "data": data.get('results_json', []),
            "csv_text": data.get('results_csv', ''),
            "error": data.get('error', ''),
        }
    }


def parse_critique_response(critique_text: str) -> Dict[str, Any]:
    """
    Парсит ответ критика по заданному шаблону.
    Возвращает структурированный словарь с флагами и данными.
    """
    text_upper = critique_text.upper()
    
    # Извлекаем флаги (Да/Нет), устойчиво к регистру и пробелам
    def extract_flag(key: str) -> bool:
        pattern = rf"{key}:\s*(ДА|НЕТ)"
        match = re.search(pattern, text_upper, re.IGNORECASE)
        return match and match.group(1).strip().upper() == "ДА"
    
    needs_schema = extract_flag("НУЖНА_СХЕМА")
    has_problem_tables = extract_flag("ЕСТЬ_ПРОБЛЕМНЫЕ_ТАБЛИЦЫ")
    
    # Извлекаем список таблиц: ищем строку "ПОБЛЕМЫЕ_ТАБЛИЦЫ:" и всё после до конца строки
    problem_tables: List[str] = []
    if has_problem_tables:
        pattern = r"ТАБЛИЦЫ_ПРОБЛЕМНЫЕ:\s*([^\n]+)"
        match = re.search(pattern, critique_text, re.IGNORECASE)
        if match:
            # Разделяем по запятой, чистим пробелы и кавычки, фильтруем пустые
            raw_tables = match.group(1).strip()
            problem_tables = [
                t.strip().strip('"\'`') 
                for t in raw_tables.split(",") 
                if t.strip()
            ]
    
    return {
        "needs_schema": needs_schema,
        "has_problem_tables": has_problem_tables,
        "problem_tables": problem_tables,
        "critique_text": critique_text  # сохраняем оригинал для логирования
    }


async def critique_execution(state: State):
    """Вершина которая критикует решение, чтобы найти оптимальное"""
    __logger.info(f"Критика SQL (попытка №{state['attempts']})")
    
    result = state["sql_result"]
    result_str = (
        f"Запрос: {result['query']}\n"
        f"Успех: {result['success']}\n"
        f"Строк: {result['rows']}\n"
        f"Ошибка: {result['error']}\n"
        f"Первые 3 строки: {result['data'][:3] if result['data'] else '—'}"
    )

    prompt = EXECUTION_CRITIQUE_TEMPLATE.format_messages(
        question=state['messages'][0].content,
        context=state['rag_context'][:4000],
        sql=state['sql_query'],
        sql_result=result_str
    )

    resp = await llm.ainvoke(prompt)
    critique_text = resp.content
    
    # Парсим ответ
    parsed = parse_critique_response(critique_text)
    
    __logger.info(f"Вердикт критика (попытка №{state['attempts']}):\n{critique_text}")
    __logger.info(f"Нужна схема БД: {parsed['needs_schema']}")
    __logger.info(f"Проблемные таблицы: {parsed['problem_tables']}")

    return {
        'needs_schema': parsed['needs_schema'],
        'problem_tables': parsed['problem_tables'],  # ← добавляем в state
        'attempts': state['attempts'] + 1,
        'critique': parsed['critique_text']
    }

# async def critique_execution(state: State):
#     """Вершина которая критикует решение, чтобы найти оптимальное"""
#     __logger.info(f"Критика SQL (попытка №{state['attempts']})")
#     result = state["sql_result"]
#     result_str = (
#         f"Запрос: {result['query']}\n"
#         f"Успех: {result['success']}\n"
#         f"Строк: {result['rows']}\n"
#         f"Ошибка: {result['error']}\n"
#         f"Первые 3 строки: {result['data'][:3] if result['data'] else '—'}"
#     )

#     prompt = EXECUTION_CRITIQUE_TEMPLATE.format_messages(
#         question=state['messages'][0].content,
#         context=state['rag_context'][:4000],
#         sql=state['sql_query'],
#         sql_result=result_str
#     )

#     resp = await llm.ainvoke(prompt)
#     critique_text = resp.content
#     needs_schema = "НУЖНА_СХЕМА: ДА" in critique_text.upper()

#     __logger.info(f"Вердикт критика (попытка №{state['attempts']}):\n{critique_text}")
#     __logger.info(f"Нужна схема БД: {needs_schema}")

#     return {
#         'needs_schema': needs_schema,
#         'attempts': state['attempts'] + 1,
#         'critique': critique_text
#     }


async def fetch_table_details(table_name: str) -> str:
    """
    Получает схему и пример данных для конкретной таблицы.
    Делает два запроса:
      - GET /schema/table/{table_name}
      - GET /schema/table/{table_name}/sample
    """
    result = ""
    
    # === 1. Получаем схему таблицы ===
    schema_url = f"{agent_settings.db_schema_url.rstrip('/')}/table/{table_name}"
    __logger.debug(f"🔍 Запрос схемы: {schema_url}")
    
    schema_data = await call_api(url=schema_url, method="GET", parse_as='text')
    
    if isinstance(schema_data, str):  # ошибка
        result = f"Schema error: {schema_data}"
        return result

    
    # === 2. Получаем пример данных (опционально, не критично если ошибка) ===
    sample_url = f"{agent_settings.db_schema_url.rstrip('/')}/table/{table_name}/sample"
    __logger.debug(f"📊 Запрос примеров: {sample_url}")
    
    sample_data = await call_api(url=sample_url, method="GET", parse_as='text')
    
    if isinstance(sample_data, str):
        __logger.warning(f"⚠️ Не удалось получить примеры для '{table_name}': {sample_data}")
        result = f"Sample error: {sample_data}"
        return result

    
    # Если схема получена — считаем успехом
    result = f'{schema_data}\n{sample_data}'
    __logger.info(f"✅ Получены данные для таблицы '{table_name}'")
    
    return result


async def fetch_schema_if_needed(state: State):
    """Вершина получает схему БД целиком, чтобы ИИ агент смог исправить ошибки"""
    # === 1. Если нужна полная схема БД ===
    schema = ''
    if state.get("needs_schema"):
        __logger.info(f"🔄 Запрашиваем ПОЛНУЮ схему БД с: {agent_settings.db_schema_url}")
        data = await call_api(url=agent_settings.db_schema_url, method="GET")
        
        if isinstance(data, str):
            __logger.error(f"Ошибка при получении полной схемы БД: {data}")
            return {"extra_schema": ""}
        
        schema = data.get('schema', '')
        __logger.info(f"📦 Полная схема БД получена ({len(schema)} символов)")
        # return {'extra_schema': schema, 'extra_tables': []}
    
    # === 2. Если есть проблемные таблицы — запрашиваем их схемы ===
    problem_tables = state.get("problem_tables", [])
    if not problem_tables:
        __logger.info("⏭ Нет проблемных таблиц и не нужна полная схема — пропускаем")
        return {"extra_schema": schema}

    __logger.info(f"🔍 Запрашиваем схемы для {len(problem_tables)} таблиц: {problem_tables}")

    tables_details = []
    for table in problem_tables:
        details = await fetch_table_details(table)
        tables_details.append(details)
    
    tables_info = "\n".join(tables_details)

    return {
        "extra_schema": f'=== Схема БД ===\n{schema}\n\n=== Проблемные таблицы ===\n{tables_info}'
        if schema else f'=== Проблемные таблицы ===\n{tables_info}',
    }


async def improve_sql(state: State):
    """Вершина, которая улучшает исходный SQL запрос"""
    __logger.info(f"Улучшение SQL (попытка №{state['attempts']})")
    extra = state.get("extra_schema", "")
    prompt = [
        REWRITE_SQL_PROMPT,
        HumanMessage(
            content=f"""Запрос пользователя:
                {state["user_question"].content}
                Предыдущий SQL запросы:
                ```sql
                {'\n'.join(state['sqls'])}
                ```
                Замечания критика:
                {state['critique']}
                Дополнительная схема (схема и таблицы, которые нужно учесть при исправлении):
                {extra}
                Новый SQL (только код):""")
    ]
    __logger.debug(f"\n\n\nПромпт для улучшения SQL:\n{prompt[1].content}\n\n\n")
    resp = await llm.ainvoke(prompt)
    new_sql = extract_sql(resp.content)
    __logger.info(f"Улучшенный SQL (попытка №{state['attempts']}):\n{new_sql}")

    return {
        "sql_query": new_sql,
        "messages": [AIMessage(content=f"Улучшенная версия #{state['attempts']}:\nsql\n{new_sql}\n")],
        "sqls": [*state['sqls'], new_sql]
    }


def decide_after_execution(state: State) -> Literal["improve", "fetch_schema", "final"]:
    critique = state["critique"].lower()
    attempts = state["attempts"]

    if attempts >= 5:
        __logger.warning(f"Достигнут лимит попыток ({attempts}), переходим к финальному ответу")
        return "final"
    if "уверен: да" in critique and state["sql_result"]["success"]:
        __logger.info("Критик доволен результатом, переходим к финальному ответу")
        return "final"
    if state["needs_schema"] or state.get("problem_tables"):
        __logger.info("Требуется схема БД или информация про таблицы, запрашиваем")
        return "fetch_schema"

    __logger.info(f"Улучшаем SQL (попытка №{attempts})")
    return "improve"


async def final_answer(state: State):
    """Вершина формирует итоговый ответ для пользователя"""
    user_question = state["user_question"].content
    __logger.debug(f"Исходный запрос пользователя ({len(user_question)}): '{user_question}'")
    __logger.debug(f"\n\nИнформация из state[\"messages\"]\n{state["messages"]}\n\n")
    context = state['sql_result']
    __logger.info(f"Формирование финального ответа. Успех SQL: {context['success']}, строк: {context.get('rows', 0)}")

    if context["success"]:
        rows = context["rows"]
        data_str = '\n'.join(context["csv_text"].split('\n')[:100])

        user_prompt = f"""
        Вопрос пользователя: {user_question}

        Выполненный SQL-запрос:
        ```sql
        {state['sql_query']}
        ```

        Результат запроса ({rows} строк):
        {data_str}

        Сформируй понятный ответ для бизнес-пользователя.
        """
        __logger.debug(f"Финальный промпт {user_prompt}")
        response = await llm.ainvoke([
            SystemMessage(content=ANSWER_INSTRUCTION),
            HumanMessage(content=user_prompt)
        ])

        __logger.info("Финальный ответ успешно сформирован")
        return {"messages": [response]}

    else:
        __logger.warning(f"Не удалось получить результат после {state['attempts']} попыток. Ошибка: {context['error']}")
        return {
            "messages": [
                AIMessage(content=f"❌ Не удалось выполнить запрос после {state['attempts']} попыток.\nОшибка: {state['sql_result']['error']}\nПопытки:\n{chr(10).join(state['sqls'])}")
            ]
        }


