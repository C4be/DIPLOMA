from pydantic import BaseModel


class FileInfoRequest(BaseModel):
    file_id: int


class FileInfoResponse(BaseModel):
    filename: str
    ext: str
    s3_key: str
    content_type: str
    presigned_url: str