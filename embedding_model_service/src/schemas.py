from pydantic import BaseModel
from typing import List


class DocumentRequest(BaseModel):
    texts: List[str]

class QueryRequest(BaseModel):
    text: str

class DocumentsResponse(BaseModel):
    embeddings: List[List[float]]

class QueryResponse(BaseModel):
    embedding: List[float]