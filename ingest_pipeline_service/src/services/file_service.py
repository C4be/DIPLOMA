import httpx

# locals
from settings import settings
from schemas import FileRecordInfo

class FileService:

    @staticmethod
    async def get_file_record(file_id: int) -> FileRecordInfo:
        """
        Получаем информацию о файле по его ID

        File:
            filename: str
            ext: str
            content_type: str
            presigned_url: str
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f'{settings.file_service_url}/get_file_info',
                json={
                    "file_id": file_id
                }
            )
            data = response.json()

        return FileRecordInfo(**data)

