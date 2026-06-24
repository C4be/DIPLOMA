from pydantic import Field
from langchain_core.tools import tool

from utils import call_api
from logger import Logger
from settings import agent_settings

__logger = Logger(name="rag_search")


@tool
async def rag_search(
    query: str = Field(description="Детализированный поисковый запрос (включая ключевые слова и синонимы) для векторной базы данных")
) -> str:
    """Поиск технической документации, данных о бронированиях и системной информации в базе знаний RAG"""

    # __logger.info(f"RAG запрос: {query}")

    data = await call_api(
        agent_settings.rag_retrieval_url,
        payload={"text": query}
    )

    if isinstance(data, str):
        __logger.error(f"Ошибка RAG сервиса: {data}")
        return f"Ошибка при обращении к RAG: {data}"

    items = data.get("response", [])
    # __logger.info(f"RAG вернул {len(items)} результатов")

    blocks = []
    for el in items:
        content = el.get("content", "")
        distance = el.get("distance", 0)
        metadata = el.get("metadata", {})

        file_source = metadata.get("file_path") or metadata.get("filename") or "Неизвестный файл"
        page_info = f", стр. {metadata['page']}" if "page" in metadata else ""

        block_str = (
            f"**Источник:** {file_source}{page_info}\n"
            f"**Релевантность:** {distance:.4f}\n"
            f"**Текст:**\n{content}"
        )
        blocks.append(block_str)

    if not blocks:
        __logger.warning(f"RAG не нашёл результатов по запросу: {query}")
        return "По вашему запросу ничего не найдено."

    return "\n\n".join(blocks)
