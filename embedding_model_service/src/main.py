from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from model import EmbeddingModel
from schemas import (
    DocumentRequest,
    DocumentsResponse,
    QueryRequest,
    QueryResponse
)


ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Инициализируем модель один раз и кладем в глобальный словарь
        ml_models["embedding_model"] = EmbeddingModel()
    except Exception as e:
        print(f"Error loading model: {e}")
        raise e

    yield

    ml_models.clear()


app = FastAPI(title="Embedding Service", lifespan=lifespan)


@app.post("/embed/documents", response_model=DocumentsResponse)
async def embed_documents_endpoint(request: DocumentRequest):
    """Эндпоинт для списка документов (passage)."""
    if not request.texts:
        raise HTTPException(status_code=400, detail="List of texts cannot be empty")

    model: EmbeddingModel = ml_models["embedding_model"]
    embeddings = model.embed_documents(request.texts)

    return DocumentsResponse(embeddings=embeddings)


@app.post("/embed/query", response_model=QueryResponse)
async def embed_query_endpoint(request: QueryRequest):
    """Эндпоинт для поискового запроса (query)."""
    if not request.text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    model: EmbeddingModel = ml_models["embedding_model"]
    embedding = model.embed_query(request.text)

    return QueryResponse(embedding=embedding)