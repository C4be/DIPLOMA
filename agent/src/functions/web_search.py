from ddgs import DDGS
from pydantic import Field
from langchain_core.tools import tool


@tool
def web_search(
    query: str = Field(description="Запрос пользователя"),
    max_results: int = Field(description="Количество Search Engine Results Page", default=5)
) -> str:
    """
    Выполняет веб-поиск с использованием DuckDuckGo Search API.

    Осуществляет поиск по запросу пользователя на русском языке с учётом региональных
    настроек (ru-ru) и временного фильтра (последняя неделя). Возвращает ограниченное
    количество результатов в виде строки с заголовками, описаниями и ссылками.

    Используется как инструмент для агентов, чтобы получать актуальную информацию
    из интернета в ответ на вопросы пользователя.

    :param query: Поисковый запрос, сформулированный на основе ввода пользователя.
        Должен быть информативным и понятным для поисковой системы.
    :param max_results: Максимальное количество возвращаемых результатов. По умолчанию — 5.
        Значение должно быть положительным целым числом.

    :return: Строка, содержащая результаты поиска в формате:
        Заголовок: Описание -- Ссылка
        Каждый результат на новой строке.

    :raises Exception: Возникает при сетевой ошибке или недоступности DuckDuckGo API.

    Пример возвращаемого значения:
        Python: Язык программирования общего назначения -- https://example.com/python
        GitHub: Платформа для разработки ПО -- https://example.com/github
    """
    with DDGS() as ddgs:
        hits = ddgs.text(query, region="ru-ru", time="w", max_results=max_results)
        return "\n".join(f"{hit['title']}: {hit['body']} -- {hit['href']}" for hit in hits[:max_results])
