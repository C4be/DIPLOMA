from fastapi import UploadFile
from botocore.exceptions import ClientError
from typing import Any

class MinioRepository:
    def __init__(self, s3_client: Any, bucket: str):
        """
        s3_client: это асинхронный клиент aioboto3.client('s3')
        bucket: название бакета из настроек
        """
        self.s3 = s3_client
        self.bucket = bucket

    async def upload_file(self, file: UploadFile, object_key: str) -> str:
        """Загрузка файла из FastAPI во внутреннее хранилище"""
        await file.seek(0)

        file_content = await file.read()

        try:
            await self.s3.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=file_content,
                ContentType=file.content_type
            )
            return object_key
        except ClientError as e:
            raise e

    async def download_file_stream(self, object_key: str) -> bytes:
        """Скачивание файла в виде байтов для последующей обработки (например, воркером)"""
        try:
            response = await self.s3.get_object(Bucket=self.bucket, Key=object_key)
            async with response["Body"] as stream:
                return await stream.read()
        except ClientError as e:
            raise e

    async def delete_file(self, object_key: str):
        """Удаление объекта из S3"""
        await self.s3.delete_object(Bucket=self.bucket, Key=object_key)

    # async def get_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
    #     """Генерация временной ссылки (для фронтенда)"""
    #     return await self.s3.generate_presigned_url(
    #         'get_object',
    #         Params={'Bucket': self.bucket, 'Key': object_key},
    #         ExpiresIn=expiration
    #     )