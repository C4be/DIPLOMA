from langgraph.graph import StateGraph, START, END

from .nodes import *

workflow = StateGraph(State)

workflow.add_node("rewrite_rag_query", rewrite_rag_query)
workflow.add_node("call_rag", call_rag)
workflow.add_node("generate_initial_sql", generate_initial_sql)
workflow.add_node("execute_sql", execute_sql)
workflow.add_node("critique_execution", critique_execution)
workflow.add_node("fetch_schema_if_needed", fetch_schema_if_needed)
workflow.add_node("improve_sql", improve_sql)
workflow.add_node("final_answer", final_answer)

workflow.add_edge(START, "rewrite_rag_query")
workflow.add_edge("rewrite_rag_query", "call_rag")
workflow.add_edge("call_rag", "generate_initial_sql")
workflow.add_edge("generate_initial_sql", "execute_sql")
workflow.add_edge("execute_sql", "critique_execution")

# Главный conditional после выполнения
workflow.add_conditional_edges(
    "critique_execution",
    decide_after_execution,
    {
        "improve": "improve_sql",
        "fetch_schema": "fetch_schema_if_needed",
        "final": "final_answer"
    }
)

workflow.add_edge("fetch_schema_if_needed", "improve_sql")   # после схемы сразу улучшаем
workflow.add_edge("improve_sql", "execute_sql")              # возвращаемся на выполнение
workflow.add_edge("final_answer", END)

graph = workflow.compile()