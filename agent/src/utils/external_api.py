import httpx
from typing import Optional, Any, Dict, Union, Literal

async def call_api(
    url: str,
    method: str = "POST",
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
    timeout: float = 60.0,
    parse_as: Literal["json", "text", "raw"] = "json"  # ← новый параметр
) -> Union[Dict[str, Any], str, httpx.Response]:
    """
    Универсальный асинхронный метод для вызова внешних API.

    :param parse_as: 
        - "json" (по умолчанию) — парсит ответ как JSON
        - "text" — возвращает строку
        - "raw" — возвращает объект httpx.Response для полной кастомизации
    """
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        try:
            method = method.upper()

            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                response = await client.post(url, json=payload)
            else:
                return f"Ошибка: Метод {method} не поддерживается."

            response.raise_for_status()

            # === Возвращаем в нужном формате ===
            if parse_as == "json":
                return response.json()
            elif parse_as == "text":
                return response.text
            else:  # raw
                return response

        except httpx.HTTPStatusError as e:
            return f"Ошибка API: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"Ошибка сети при обращении к {e.request.url}: {e}"
        except Exception as e:
            return f"Непредвиденная ошибка: {str(e)}"


# examples
# result = await call_api(
#     url="http://rag_service:8000/ask_retrieval",
#     payload={"text": "Привет, как дела?"}
# )

# # Отправит запрос вида: http://api.service/status?user_id=123
# status = await call_api(
#     url="http://api.service/status",
#     method="GET",
#     params={"user_id": 123}
# )