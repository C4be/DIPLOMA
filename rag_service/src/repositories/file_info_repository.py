from typing import Sequence, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from db import get_session
from models import FileModel
from enums import FileStatus


class FileInfoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> FileModel:
        """Создание записи о файле"""
        new_file = FileModel(**kwargs)
        self.session.add(new_file)
        await self.session.flush()  # Получаем ID до коммита
        return new_file

    async def get_by_id(self, file_id: int) -> Optional[FileModel]:
        """Получение одного файла по ID"""
        result = await self.session.execute(
            select(FileModel).where(FileModel.id == file_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[FileModel]:
        """Получение всех файлов"""
        result = await self.session.execute(select(FileModel).order_by(FileModel.created_at.desc()))
        return result.scalars().all()

    async def update_status(self, file_id: int, status: FileStatus) -> Optional[FileModel]:
        """Смена статуса файла (например, с PROCESS на LOADED)"""
        query = (
            update(FileModel)
            .where(FileModel.id == file_id)
            .values(status=status)
            .returning(FileModel)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def delete(self, file_id: int) -> bool:
        """Удаление записи"""
        query = delete(FileModel).where(FileModel.id == file_id)
        result = await self.session.execute(query)
        return result.rowcount > 0


async def get_file_repository(session: AsyncSession = Depends(get_session)) -> FileInfoRepository:
    return FileInfoRepository(session)