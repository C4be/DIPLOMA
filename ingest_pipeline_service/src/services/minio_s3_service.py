import anyio
from pathlib import Path
from fastapi import HTTPException
from repositories.minio_repository import MinioRepository # Твой репозиторий

class MinioS3Service:
    def __init__(self, s3_repo: MinioRepository):
        self.s3_repo = s3_repo
        self.tmp_dir = Path(".tmp")
        self.tmp_dir.mkdir(exist_ok=True)

    async def save_file_in_tmp(self, s3_key: str, filename: str) -> Path:
        """Скачиваем файл напрямую из S3 во временную папку"""
        file_path = self.tmp_dir / filename

        try:
            # 1. Получаем поток байтов напрямую из репозитория
            # (мы его писали ранее в MinioRepository как download_file_stream)
            file_content = await self.s3_repo.download_file_stream(s3_key)

            # 2. Асинхронно записываем на диск
            await anyio.Path(file_path).write_bytes(file_content)

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при сохранении временного файла: {e}"
            )

        return file_path

    async def delete_file_from_tmp(self, file_path: Path):
        """Асинхронно удаляем временный файл"""
        path = anyio.Path(file_path)
        if await path.exists():
            await path.unlink()