from typing import Optional, Dict, Any
from rq import Queue
from rq.job import Job
from redis import Redis
from services.worker.tasks import ingest_file_by_id

class QueueService:
    def __init__(self, redis_conn: Redis):
        self.redis = redis_conn
        self.queue = Queue("ingestion", connection=self.redis)

    def enqueue_ingestion(self, file_id: int) -> str:
        """Помещаем файл в очередь и возвращаем job_id"""
        job = self.queue.enqueue(ingest_file_by_id, file_id, job_timeout=600)
        return job.get_id()

    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Получает расширенную информацию о задаче"""
        try:
            job = Job.fetch(job_id, connection=self.redis)
        except Exception:
            return None

        return {
            "job_id": job.id,
            "status": job.get_status(),
            "exc_info": job.exc_info,
            "result": job.result,
            "meta": job.meta
        }