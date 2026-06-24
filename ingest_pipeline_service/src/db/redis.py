from redis import Redis
from settings import settings


def get_redis_connection():
    return Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=False
    )