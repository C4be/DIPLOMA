from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    text: str


class QueryResponse(BaseModel):
    response: List[dict]