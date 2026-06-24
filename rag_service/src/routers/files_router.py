import httpx

from fastapi import APIRouter, UploadFile, File, Depends

from services.file_service import FileService, get_file_service
from schemas.file_info_schema import FileInfoRequest, FileInfoResponse
from schemas.retrieval_query import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/upload_and_run")
async def upload_file(
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service)
):

    file_info = await file_service.upload_and_save(file)
    file_id = file_info.id

    # Делаем запрос в embedding model
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url=f"http://ingest_pipeline_service:8000/ingest/{file_id}",
            )
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"Vector service returned {e.response.status_code}: {e.response.text}"
        ) from e

    except httpx.RequestError as e:
        raise RuntimeError(
            f"Failed to connect to vector service: {e}"
        ) from e

    return {
        "id": file_info.id,
        "filename": file_info.filename,
        "status": file_info.status
    }


@router.post('/ask_retrieval', response_model=QueryResponse)
async def ask_retrieval(
    query: QueryRequest
):
    payload = {
        "query": query.text
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url=f"http://retrieval_pipeline_service:8000/retieval",
                json=payload
            )
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"Vector service returned {e.response.status_code}: {e.response.text}"
        ) from e

    except httpx.RequestError as e:
        raise RuntimeError(
            f"Failed to connect to vector service: {e}"
        ) from e

    return response.json()


@router.post("/get_file_info", response_model=FileInfoResponse)
async def get_file_info(
    data: FileInfoRequest,
    file_service: FileService = Depends(get_file_service)
):
    file_id: int = data.file_id
    file_info = await file_service.get_file_info(file_id)
    return FileInfoResponse(**file_info)

