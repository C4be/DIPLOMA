from langchain_core.messages import HumanMessage

from .llm_graph import graph
from logger import Logger


__logger = Logger(name="agent")


async def run_agent(user_question: str):
    __logger.info(f"Вопрос от пользователя: {user_question}. Запускаем агента...")
    initial_state = {
        "user_question": HumanMessage(content=user_question),
        "messages": [HumanMessage(content=user_question)],
        "attempts": 0,
        "needs_schema": False,
        "rag_query": "",
        "rag_context": "",
        "sql_query": "",
        "sql_result": {"success": False, "rows": 0, "error": "", "data": []},
        "critique": "",
        "extra_schema": ""
    }

    result = await graph.ainvoke(initial_state)
    content = result["messages"][-1].content
    __logger.info(f"Получен ответ от агента: {content}")
    return content