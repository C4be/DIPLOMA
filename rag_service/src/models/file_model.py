from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import Enum as SAEnum

from db import Base
from enums import FileStatus


class FileModel(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)               # Оригинальное имя (image.png)
    s3_key = Column(String, unique=True, nullable=False)    # Путь в S3 (avatars/uuid-image.png)
    bucket = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True)                   # Размер в байтах
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(SAEnum(FileStatus, name="user_role_enum"), default=FileStatus.PROCESS)
