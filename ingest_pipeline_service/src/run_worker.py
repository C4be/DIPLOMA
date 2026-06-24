from rq import Worker, Queue
from db.redis import get_redis_connection

def start_worker():
    # 1. Получаем твое соединение (уже настроенное)
    redis_conn = get_redis_connection()

    # 2. Создаем объект очереди, привязанный к этому соединению
    # Название 'ingestion' должно совпадать с тем, что в QueueService
    queue = Queue('ingestion', connection=redis_conn)

    # 3. Запускаем воркер, передав ему список очередей и соединение
    worker = Worker([queue], connection=redis_conn)

    print("🚀 RQ Worker started. Connection established.")
    worker.work()

if __name__ == '__main__':
    start_worker()