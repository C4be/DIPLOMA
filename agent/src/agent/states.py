from typing import TypedDict
from langchain_core.messages import HumanMessage, AIMessage

from typing import TypedDict, List, Dict

class State(TypedDict):
    messages: List[HumanMessage | AIMessage]   # исходный вопрос всегда messages[0]
    rag_query: str                             # переписывание запроса для RAG
    rag_context: str                           # получение контекста из RAG
    sql_query: str                             # генерация SQL
    sql_result: Dict                           # получение результата SQL
    critique: str                              # мнение критика
    attempts: int                              # количество попыток
    needs_schema: bool                         # запрос на актуализацию схемы
    extra_schema: str                          # информация про схему
    sqls: list[str]
    user_question: HumanMessage
    problem_tables: List[str]