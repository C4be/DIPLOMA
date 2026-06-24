from fastapi import UploadFile, Depends
from botocore.exceptions import ClientError
from typing import Any

from db import get_s3_client
from settings import settings

class MinioRepository:
    def __init__(self, s3_client: Any, bucket: str):
        self.s3 = s3_client  # Получаем уже активный клиент
        self.bucket = bucket

    async def upload_file(self, file: UploadFile, object_key: str) -> str:
        file_content = await file.read()
        content_type = file.content_type
        if content_type == "text/plain":
            content_type = "text/plain; charset=utf-8"

        try:
            await self.s3.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=file_content,
                ContentType=content_type
            )
            return object_key
        except ClientError as e:
            raise e

    async def delete_file(self, object_key: str):
        await self.s3.delete_object(Bucket=self.bucket, Key=object_key)

    async def get_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        return await self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': object_key},
            ExpiresIn=expiration
        )

    async def download_file_stream(self, object_key: str):
        response = await self.s3.get_object(Bucket=self.bucket, Key=object_key)
        return await response["Body"].read()

    async def check_or_create_bucket(self):
        try:
            await self.s3.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                await self.s3.create_bucket(Bucket=self.bucket)
            else:
                raise e


async def get_s3_repository(s3_client = Depends(get_s3_client)) -> MinioRepository:
    return MinioRepository(s3_client=s3_client, bucket=settings.minio_bucket)