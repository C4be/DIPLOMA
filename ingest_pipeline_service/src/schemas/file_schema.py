from pydantic import BaseModel

class FileRecordInfo(BaseModel):
    id: int
    filename: str
    ext: str
    content_type: str
