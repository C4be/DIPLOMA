import uuid
import httpx
import anyio  # Для асинхронной работы с файловой системой
from pathlib import Path
from fastapi import UploadFile, HTTPException, Depends

from models import FileModel
from repositories.file_info_repository import FileInfoRepository, get_file_repository
from repositories.minio_repository import MinioRepository, get_s3_repository
from enums import FileStatus


class FileService:
    def __init__(self, file_repo: FileInfoRepository, s3_repo: MinioRepository):
        # Теперь зависимости приходят через конструктор (DI)
        self.file_repo = file_repo
        self.s3_repo = s3_repo

        self.tmp_dir = Path(".tmp")
        self.tmp_dir.mkdir(exist_ok=True)

    def _guess_extension(self, content_type: str) -> str | None:
        mapping = {
            "application/pdf": "pdf",
            "text/plain": "txt",
            "text/markdown": "md",
            "image/jpeg": "jpg",
            "image/png": "png",
        }
        return mapping.get(content_type)

    async def save_file_from_url_in_tmp(self, url: str) -> Path:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=400, detail=f"Failed to download: {e}")

        ext = self._guess_extension(response.headers.get("content-type", "")) or "bin"
        file_path = self.tmp_dir / f"{uuid.uuid4()}.{ext}"

        # Используем anyio для асинхронной записи, чтобы не блокировать Event Loop
        await anyio.Path(file_path).write_bytes(response.content)
        return file_path

    async def upload_and_save(self, file: UploadFile) -> FileModel:
        # 1. Подготовка ключа
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
        s3_key = f"uploads/{uuid.uuid4()}.{file_ext}"

        try:
            # 2. Загрузка в S3 через репозиторий
            await self.s3_repo.upload_file(file, s3_key)

            # 3. Сохранение метаданных через FileRepository
            new_file = await self.file_repo.create(
                filename=file.filename,
                s3_key=s3_key,
                bucket=self.s3_repo.bucket,
                content_type=file.content_type,
                size=file.size,
                status=FileStatus.LOADED
            )

            # 4. Фиксируем транзакцию
            await self.file_repo.session.commit()
            return new_file

        except Exception as e:
            # Откат в случае ошибки
            await self.file_repo.session.rollback()
            await self.s3_repo.delete_file(s3_key)
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    async def get_file_url(self, file_id: int) -> str:
        file_record = await self.file_repo.get_by_id(file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        return await self.s3_repo.get_presigned_url(file_record.s3_key)

    async def get_file_info(self, file_id: int):
        file_record = await self.file_repo.get_by_id(file_id)

        return {
            "filename": file_record.filename,
            "ext": Path(file_record.filename).suffix,
            "content_type": file_record.content_type,
            "s3_key": file_record.s3_key,
            "presigned_url": await self.get_file_url(file_id)
        }

async def get_file_service(
    file_repo: FileInfoRepository = Depends(get_file_repository),
    s3_repo: MinioRepository = Depends(get_s3_repository)
) -> FileService:
    return FileService(file_repo=file_repo, s3_repo=s3_repo)