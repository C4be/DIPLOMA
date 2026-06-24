from fastapi import FastAPI, HTTPException, Depends
from services.queue_service import QueueService

from dependencies import get_queue_service
from logger import Logger


logger = Logger(__name__)


app = FastAPI(title="RAG Ingestion API")

@app.post("/ingest/{file_id}")
async def ingest_file(
    file_id: int,
    # FastAPI сам создаст QueueService и прокинет туда Redis-соединение
    queue_service: QueueService = Depends(get_queue_service)
):
    """Отправка файла на обработку (Ingestion)"""
    logger.info(f"Получен запрос на обработку для файла с file_id={file_id}")

    try:
        job_id = queue_service.enqueue_ingestion(file_id)
        logger.info(f"Успешно запущена задача (job={job_id}) для файла (file_id={file_id})")


        response = {
            "status": "queued",
            "job_id": job_id,
            "file_id": file_id
        }

        logger.info(f"Подготовили response={response}")
        return response

    except Exception as e:
        logger.exception(f"Ошибка отправки в очередь {file_id}")
        raise HTTPException(status_code=500, detail="Internal server error while queueing")



@app.get("/status/{job_id}")
async def get_ingestion_status(
    job_id: str,
    queue_service: QueueService = Depends(get_queue_service)
):
    """Проверка статуса фоновой задачи"""
    logger.debug(f"Запрос статуса задачи job_id: {job_id}")

    status_info = queue_service.get_job_info(job_id)

    if status_info is None:
        logger.warning(f"Ошибка проверки статуса: Задача {job_id} не найдена в Redis")
        raise HTTPException(
            status_code=404,
            detail=f"Задача {job_id} не найдена"
        )

    current_status = status_info.get('status')
    logger.info(f"Статус задачи {job_id} успешно получен: {current_status}")

    return status_info