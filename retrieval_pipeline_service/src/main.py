from fastapi import FastAPI

from schemas import Response, Request
from services import VectorService

app = FastAPI()


@app.post("/retieval", response_model=Response)
async def run_retrieval_pipeline(request: Request):
    vector_service = VectorService()
    query = request.query

    # Допустим, здесь возвращается List[dict]
    search_results = await vector_service.search_similar(query)

    # ИМЯ АРГУМЕНТА ДОЛЖНО СОВПАДАТЬ С ИМЕНЕМ В КЛАССЕ Response
    return Response(
        response = search_results
    )
