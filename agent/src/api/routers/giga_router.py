from fastapi import APIRouter
from api.schemas import AgentResponse, AgentRequest
from agent.run_agent import run_agent
from logger import Logger

__logger = Logger(name="giga_router")

giga_router = APIRouter()

@giga_router.post("/giga", response_model=AgentResponse)
async def ask_giga(request: AgentRequest) -> AgentResponse:
    """
    Задать вопрос GigaChat агенту

    Args:
        question: Вопрос пользователя

    Returns:
        Ответ агента в формате JSON
    """
    __logger.info(f"Получен запрос: '{request.question}'")

    answer = await run_agent(request.question)

    __logger.info(f"Отправлен ответ ({len(answer)} символов)")
    return AgentResponse(answer=answer)
