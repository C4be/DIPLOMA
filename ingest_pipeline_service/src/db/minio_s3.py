import aioboto3
from contextlib import asynccontextmanager

from settings import settings


class S3ClientWrapper:
    def __init__(self):
        self.session = aioboto3.Session()
        self.config = {
            "endpoint_url": settings.minio_url,
            "aws_access_key_id": settings.minio_id,
            "aws_secret_access_key": settings.minio_pass,
            "region_name": settings.minio_region,
        }

    @asynccontextmanager
    async def get_client(self):
        async with self.session.client("s3", **self.config) as client:
            yield client


s3_client_wrapper = S3ClientWrapper()
